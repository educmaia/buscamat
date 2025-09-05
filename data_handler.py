#!/usr/bin/env python3
"""
Módulo de Manipulação de Dados
Responsável por carregar, limpar e preparar dados do CSV
"""

import pandas as pd
import logging
from typing import List

logger = logging.getLogger(__name__)


class DataHandler:
    """Gerencia carregamento e limpeza de dados"""
    
    def __init__(self):
        self.df = None
    
    def load_data(self, csv_path: str) -> pd.DataFrame:
        """
        Carrega o CSV do Catmat com tratamento robusto de encoding
        
        Args:
            csv_path: Caminho para o arquivo CSV
            
        Returns:
            DataFrame com os dados carregados
        """
        logger.info("📂 Carregando dados do CSV...")

        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']

        for encoding in encodings:
            try:
                self.df = pd.read_csv(csv_path, encoding=encoding)
                logger.info(f"✅ CSV carregado com encoding {encoding}")
                break
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.error(f"Erro ao carregar CSV: {e}")
                raise

        if self.df is None:
            raise ValueError(
                "Não foi possível carregar o CSV com nenhum encoding testado")

        logger.info(f"✅ Carregados {len(self.df):,} itens do Catmat")
        logger.info(f"📋 Colunas: {list(self.df.columns)}")

        # Limpa e prepara dados
        self._clean_data()
        
        return self.df
    
    def _clean_data(self):
        """Limpa e prepara os dados"""
        # Identifica coluna de descrição (pode ter nomes diferentes)
        desc_columns = ['Descrição do Item', 'Descricao do Item',
                        'Descrição', 'Descricao', 'Description']
        desc_col = None

        for col in desc_columns:
            if col in self.df.columns:
                desc_col = col
                break

        if desc_col is None:
            raise ValueError("Coluna de descrição não encontrada no CSV")

        # Padroniza nome da coluna
        if desc_col != 'Descrição do Item':
            self.df = self.df.rename(columns={desc_col: 'Descrição do Item'})

        # Remove linhas com descrições vazias/nulas
        initial_count = len(self.df)
        self.df = self.df.dropna(subset=['Descrição do Item'])
        self.df['Descrição do Item'] = self.df['Descrição do Item'].astype(str)

        # Remove descrições muito curtas (menos de 10 caracteres)
        self.df = self.df[self.df['Descrição do Item'].str.len() >= 10]

        final_count = len(self.df)
        logger.info(
            f"🧹 Limpeza concluída: {initial_count:,} → {final_count:,} itens válidos")
    
    def get_descriptions(self) -> List[str]:
        """Retorna lista de descrições para geração de embeddings"""
        if self.df is None:
            raise ValueError("Dados não carregados. Execute load_data() primeiro.")
        
        return self.df['Descrição do Item'].tolist()
    
    def get_dataframe(self) -> pd.DataFrame:
        """Retorna o DataFrame completo"""
        return self.df