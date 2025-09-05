#!/usr/bin/env python3
"""
Módulo de Embeddings e Indexação
Responsável por gerar embeddings e criar índices FAISS para busca semântica
"""

import numpy as np
import faiss
import pickle
import os
import time
import logging
from typing import List
from concurrent.futures import ThreadPoolExecutor
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class EmbeddingsEngine:
    """Gerencia geração de embeddings e indexação FAISS"""
    
    def __init__(self, model_name: str, embeddings_path: str, index_path: str,
                 hnsw_m: int = 32, hnsw_ef_construction: int = 200,
                 hnsw_ef_search: int = 100, n_workers: int = 8, batch_size: int = 64):
        """
        Inicializa o motor de embeddings
        
        Args:
            model_name: Nome do modelo SentenceTransformer
            embeddings_path: Caminho para salvar embeddings
            index_path: Caminho para salvar índice FAISS
            hnsw_m: Número de conexões bidirecionais
            hnsw_ef_construction: Tamanho da lista dinâmica durante construção
            hnsw_ef_search: Tamanho da lista dinâmica durante busca
            n_workers: Número de workers para paralelização
            batch_size: Tamanho do batch para processamento
        """
        self.model_name = model_name
        self.embeddings_path = embeddings_path
        self.index_path = index_path
        self.hnsw_m = hnsw_m
        self.hnsw_ef_construction = hnsw_ef_construction
        self.hnsw_ef_search = hnsw_ef_search
        self.n_workers = n_workers
        self.batch_size = batch_size
        
        self.model = None
        self.embeddings = None
        self.index = None
    
    def load_model(self):
        """Carrega o modelo E5-base-v2"""
        logger.info("🤖 Carregando modelo E5-base-v2...")
        self.model = SentenceTransformer(self.model_name)
        logger.info("✅ Modelo carregado com sucesso!")
    
    def _generate_embeddings_batch(self, texts_batch: List[str]) -> np.ndarray:
        """Gera embeddings para um batch de textos"""
        return self.model.encode(
            texts_batch,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False
        )
    
    def generate_embeddings(self, descriptions: List[str], force_rebuild: bool = False):
        """
        Gera embeddings com paralelização para melhor performance
        
        Args:
            descriptions: Lista de descrições para gerar embeddings
            force_rebuild: Se True, força recriação mesmo se já existir
        """
        if not force_rebuild and os.path.exists(self.embeddings_path):
            logger.info("📦 Carregando embeddings salvos...")
            self.embeddings = np.load(self.embeddings_path)
            logger.info(f"✅ Embeddings carregados: {self.embeddings.shape}")
            return

        logger.info("🔄 Gerando embeddings com paralelização...")
        logger.info(
            f"⚙️ Usando {self.n_workers} workers, batch_size={self.batch_size}")

        # Prepara textos com prefixo E5
        texts = [f"passage: {desc}" for desc in descriptions]

        start_time = time.time()

        # Divide textos em batches
        batches = [texts[i:i + self.batch_size]
                   for i in range(0, len(texts), self.batch_size)]

        # Processa batches em paralelo (usando threads para I/O bound operations)
        embeddings_list = []

        with ThreadPoolExecutor(max_workers=self.n_workers) as executor:
            # Mapeia batches para workers
            futures = [executor.submit(
                self._generate_embeddings_batch, batch) for batch in batches]

            # Coleta resultados
            for i, future in enumerate(futures):
                batch_embeddings = future.result()
                embeddings_list.append(batch_embeddings)

                # Progress feedback
                if (i + 1) % 10 == 0:
                    progress = (i + 1) / len(futures) * 100
                    logger.info(
                        f"📊 Progresso: {progress:.1f}% ({i + 1}/{len(futures)} batches)")

        # Concatena todos os embeddings
        self.embeddings = np.vstack(embeddings_list)

        elapsed = time.time() - start_time
        logger.info(f"✅ Embeddings gerados em {elapsed:.1f}s")
        logger.info(f"📊 Shape: {self.embeddings.shape}")
        logger.info(f"⚡ Performance: {len(texts)/elapsed:.1f} textos/segundo")

        # Salva embeddings
        np.save(self.embeddings_path, self.embeddings)
        logger.info(f"💾 Embeddings salvos em {self.embeddings_path}")
    
    def create_hnsw_index(self, force_rebuild: bool = False):
        """
        Cria índice HNSW para melhor performance em datasets grandes
        
        Args:
            force_rebuild: Se True, força recriação mesmo se já existir
        """
        if not force_rebuild and os.path.exists(self.index_path):
            logger.info("📦 Carregando índice HNSW salvo...")
            with open(self.index_path, 'rb') as f:
                self.index = pickle.load(f)
            logger.info("✅ Índice HNSW carregado!")
            return

        if self.embeddings is None:
            raise ValueError("Embeddings não foram gerados. Execute generate_embeddings() primeiro.")

        logger.info("🏗️ Criando índice HNSW...")
        logger.info(
            f"⚙️ Parâmetros: M={self.hnsw_m}, ef_construction={self.hnsw_ef_construction}")

        start_time = time.time()

        # Cria índice HNSW
        dimension = self.embeddings.shape[1]
        self.index = faiss.IndexHNSWFlat(dimension, self.hnsw_m)
        self.index.hnsw.ef_construction = self.hnsw_ef_construction

        # Adiciona embeddings ao índice
        self.index.add(self.embeddings.astype('float32'))

        # Configura ef para busca
        self.index.hnsw.ef = self.hnsw_ef_search

        elapsed = time.time() - start_time
        logger.info(
            f"✅ Índice HNSW criado em {elapsed:.1f}s com {self.index.ntotal:,} vetores")

        # Salva índice
        with open(self.index_path, 'wb') as f:
            pickle.dump(self.index, f)
        logger.info(f"💾 Índice salvo em {self.index_path}")
    
    def generate_query_embedding(self, query: str) -> np.ndarray:
        """
        Gera embedding para uma query
        
        Args:
            query: Texto da consulta
            
        Returns:
            Embedding da query
        """
        if self.model is None:
            raise ValueError("Modelo não carregado. Execute load_model() primeiro.")
        
        # Prepara query com prefixo E5
        query_text = f"query: {query}"
        
        # Gera embedding da query
        query_embedding = self.model.encode(
            [query_text],
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        
        return query_embedding
    
    def search(self, query_embedding: np.ndarray, top_k: int = 15):
        """
        Realiza busca no índice HNSW
        
        Args:
            query_embedding: Embedding da query
            top_k: Número de resultados a retornar
            
        Returns:
            Tuple com (scores, indices)
        """
        if self.index is None:
            raise ValueError("Índice não criado. Execute create_hnsw_index() primeiro.")
        
        # Busca no índice HNSW
        scores, indices = self.index.search(
            query_embedding.astype('float32'), top_k)
        
        return scores, indices