#!/usr/bin/env python3
"""
Módulo de Gerenciamento de Configuração
Responsável por carregar e gerenciar configurações do sistema
"""

import json
import os
import logging
from typing import Dict, Any
from multiprocessing import cpu_count

logger = logging.getLogger(__name__)


class ConfigManager:
    """Gerencia configurações do sistema"""
    
    def __init__(self, config_path: str = "config.json"):
        """
        Inicializa o gerenciador de configuração
        
        Args:
            config_path: Caminho para arquivo de configuração
        """
        self.config_path = config_path
        self.config = self._load_configuration()
    
    def _load_configuration(self) -> Dict[str, Any]:
        """Carrega configuração de arquivo JSON ou usa padrões"""
        config_default = {
            "csv_path": "catmat.csv",
            "model_name": "intfloat/e5-base-v2",
            "index_path": "catmat_hnsw_index.pkl",
            "embeddings_path": "catmat_embeddings.npy",
            "results_dir": "resultados",
            "hnsw_m": 32,
            "hnsw_ef_construction": 200,
            "hnsw_ef_search": 100,
            "n_workers": min(cpu_count(), 8),
            "batch_size": 64,
            "openai_model": "gpt-4o-mini"
        }

        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_file = json.load(f)
                config_default.update(config_file)
                logger.info(f"Configuração carregada de {self.config_path}")
            except Exception as e:
                logger.warning(
                    f"Erro ao carregar configuração: {e}. Usando padrões.")
        else:
            # Cria arquivo de configuração padrão
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_default, f, indent=2, ensure_ascii=False)
            logger.info(
                f"Arquivo de configuração padrão criado: {self.config_path}")

        return config_default
    
    def get(self, key: str, default=None):
        """Obtém valor da configuração"""
        return self.config.get(key, default)
    
    def update(self, updates: Dict[str, Any]):
        """Atualiza configurações"""
        self.config.update(updates)
    
    def save(self):
        """Salva configurações no arquivo"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
        logger.info(f"Configuração salva em {self.config_path}")