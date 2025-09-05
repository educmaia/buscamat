#!/usr/bin/env python3
"""
Buscador Semântico Catmat v3.0 - Versão Modular
Autor: Eduardo Maia + IAs
Data: 2025

Classe principal que coordena todos os módulos
"""

import logging
from pathlib import Path
from typing import Tuple, List, Optional, Callable
import pandas as pd

from config_manager import ConfigManager
from data_handler import DataHandler
from embeddings_engine import EmbeddingsEngine
from search_engine import SearchEngine
from ai_recommender import AIRecommender
from export_utils import ExportUtils
from batch_processor import BatchProcessor
from special_exporter import SpecialExporter

# Configuração de logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BuscadorSemanticoCatmat:
    """
    Buscador Semântico Catmat - Versão Modular
    
    Coordena todos os módulos para realizar buscas semânticas
    inteligentes no Catálogo de Materiais (Catmat)
    """
    
    def __init__(self, config_path: str = "config.json"):
        """
        Inicializa o buscador semântico
        
        Args:
            config_path: Caminho para arquivo de configuração
        """
        # Inicializa gerenciador de configuração
        self.config_manager = ConfigManager(config_path)
        
        # Cria diretório de resultados
        results_dir = Path(self.config_manager.get("results_dir", "resultados"))
        results_dir.mkdir(exist_ok=True)
        
        # Inicializa componentes
        self.data_handler = DataHandler()
        
        self.embeddings_engine = EmbeddingsEngine(
            model_name=self.config_manager.get("model_name", "intfloat/e5-base-v2"),
            embeddings_path=self.config_manager.get("embeddings_path", "catmat_embeddings.npy"),
            index_path=self.config_manager.get("index_path", "catmat_hnsw_index.pkl"),
            hnsw_m=self.config_manager.get("hnsw_m", 32),
            hnsw_ef_construction=self.config_manager.get("hnsw_ef_construction", 200),
            hnsw_ef_search=self.config_manager.get("hnsw_ef_search", 100),
            n_workers=self.config_manager.get("n_workers", 8),
            batch_size=self.config_manager.get("batch_size", 64)
        )
        
        self.search_engine = SearchEngine(self.embeddings_engine)
        
        self.ai_recommender = AIRecommender(
            openai_model=self.config_manager.get("openai_model", "gpt-4o-mini")
        )
        
        self.export_utils = ExportUtils(
            results_dir=str(results_dir)
        )
        
        self.batch_processor = BatchProcessor(
            self.search_engine, 
            self.ai_recommender
        )
        
        self.special_exporter = SpecialExporter(
            results_dir=str(results_dir)
        )
        
        # Estado da inicialização
        self._initialized = False
    
    def initialize(self, force_rebuild: bool = False):
        """
        Inicializa todo o sistema
        
        Args:
            force_rebuild: Se True, força recriação de embeddings e índices
        """
        logger.info("🚀 Inicializando Buscador Semântico Catmat v3.0 (Modular)...")
        logger.info("=" * 70)
        
        # Carrega dados
        csv_path = self.config_manager.get("csv_path", "catmat.csv")
        self.data_handler.load_data(csv_path)
        
        # Carrega modelo e gera embeddings
        self.embeddings_engine.load_model()
        descriptions = self.data_handler.get_descriptions()
        self.embeddings_engine.generate_embeddings(descriptions, force_rebuild)
        
        # Cria índice HNSW
        self.embeddings_engine.create_hnsw_index(force_rebuild)
        
        # Configura OpenAI
        openai_key = self.config_manager.get("openai_api_key")
        self.ai_recommender.configure_openai(openai_key)
        
        self._initialized = True
        
        logger.info("=" * 70)
        logger.info("✅ Sistema modular pronto para buscas inteligentes!")
        logger.info("💡 Nova arquitetura: Modular, escalável e maintível")
    
    def search(self, query: str, top_k: int = 15) -> pd.DataFrame:
        """
        Realiza busca semântica
        
        Args:
            query: Texto da consulta
            top_k: Número de resultados a retornar
            
        Returns:
            DataFrame com os resultados mais relevantes
        """
        if not self._initialized:
            raise ValueError("Sistema não inicializado. Execute initialize() primeiro.")
        
        df = self.data_handler.get_dataframe()
        return self.search_engine.search(query, df, top_k)
    
    def search_with_ai(self, query: str, top_k: int = 15) -> Tuple[pd.DataFrame, str]:
        """
        Realiza busca semântica + análise IA
        
        Args:
            query: Texto da consulta
            top_k: Número de resultados para busca semântica
            
        Returns:
            Tuple com (resultados_dataframe, recomendacao_ia)
        """
        # Busca semântica
        results = self.search(query, top_k)
        
        # Análise IA
        recommendation = self.ai_recommender.generate_recommendation(query, results)
        
        return results, recommendation
    
    def process_batch(self, item_list: List[str], top_k: int = 5, 
                     use_ai: bool = True, progress_callback: Optional[Callable] = None) -> pd.DataFrame:
        """
        Processa uma lista de itens fazendo busca para cada um
        
        Args:
            item_list: Lista de strings com os itens para buscar
            top_k: Número de resultados por item
            use_ai: Se deve usar recomendações IA
            progress_callback: Função para callback de progresso
            
        Returns:
            DataFrame com resultados consolidados
        """
        if not self._initialized:
            raise ValueError("Sistema não inicializado. Execute initialize() primeiro.")
        
        df = self.data_handler.get_dataframe()
        return self.batch_processor.process_batch(
            item_list, df, top_k, use_ai, progress_callback
        )
    
    def generate_batch_report(self, batch_df: pd.DataFrame, format: str = 'html') -> str:
        """
        Gera relatório detalhado do processamento em lote
        
        Args:
            batch_df: DataFrame com resultados do lote
            format: 'html', 'markdown' ou 'text'
            
        Returns:
            String com o relatório formatado
        """
        return self.batch_processor.generate_batch_report(batch_df, format)
    
    def export_results(self, results: pd.DataFrame, query: str,
                      format: str = "csv", ai_recommendation: str = None) -> str:
        """
        Exporta resultados para arquivo
        
        Args:
            results: DataFrame com resultados
            query: Query original (para nome do arquivo)
            format: "csv" ou "json"
            ai_recommendation: Texto da recomendação IA (opcional)
            
        Returns:
            Caminho do arquivo salvo
        """
        return self.export_utils.export_search_results(
            results, query, format, ai_recommendation
        )
    
    def export_batch_results(self, batch_results: pd.DataFrame, 
                           filename: Optional[str] = None, format: str = 'xlsx') -> str:
        """
        Exporta resultados de lote em diferentes formatos
        
        Args:
            batch_results: DataFrame com resultados do lote
            filename: Nome do arquivo (opcional)
            format: 'xlsx', 'csv', 'json'
            
        Returns:
            Caminho do arquivo gerado
        """
        return self.export_utils.export_batch_results(batch_results, filename, format)
    
    def export_special_csv(self, batch_results: pd.DataFrame, filename: str = None) -> str:
        """
        Exporta CSV especial com formato customizado (#-separated)
        
        Args:
            batch_results: DataFrame com resultados do lote
            filename: Nome do arquivo (opcional)
            
        Returns:
            Caminho do arquivo gerado
        """
        return self.special_exporter.export_special_csv(batch_results, filename)
    
    def get_config(self, key: str, default=None):
        """Obtém valor da configuração"""
        return self.config_manager.get(key, default)
    
    def update_config(self, updates: dict):
        """Atualiza configurações"""
        self.config_manager.update(updates)
    
    def save_config(self):
        """Salva configurações no arquivo"""
        self.config_manager.save()


def main():
    """Função principal para teste"""
    print("BUSCADOR SEMANTICO CATMAT v3.0 - VERSAO MODULAR")
    print("Nova arquitetura: Modular, escalavel e maintivel")
    print()
    
    # Inicializa buscador
    buscador = BuscadorSemanticoCatmat()
    
    try:
        # Pergunta se quer forçar rebuild
        rebuild = input(
            "Forcar recriacao de embeddings? (s/N): ").lower().startswith('s')
        
        # Inicializa sistema
        buscador.initialize(force_rebuild=rebuild)
        
        # Teste rápido
        print("\nTESTE RAPIDO:")
        query_teste = "drone para agricultura"
        resultados, recomendacao = buscador.search_with_ai(query_teste, top_k=5)
        
        print(f"\nTeste: '{query_teste}'")
        print(f"{len(resultados)} resultados encontrados")
        print("\nRecomendacao IA:")
        print(recomendacao[:200] + "..." if len(recomendacao) > 200 else recomendacao)
        
        # Teste de export
        arquivo_csv = buscador.export_results(
            resultados, query_teste, "csv", recomendacao)
        arquivo_json = buscador.export_results(
            resultados, query_teste, "json", recomendacao)
        
        print(f"\nArquivos exportados:")
        print(f"   CSV: {arquivo_csv}")
        print(f"   JSON: {arquivo_json}")
        
    except FileNotFoundError:
        print("ERRO: Arquivo CSV nao encontrado!")
        print("Certifique-se que o arquivo CSV esta na pasta correta")
    except Exception as e:
        print(f"ERRO inesperado: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()