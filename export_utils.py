#!/usr/bin/env python3
"""
Módulo de Utilitários de Exportação
Responsável por exportar resultados em diferentes formatos (CSV, JSON, Excel)
"""

import json
import os
import pandas as pd
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ExportUtils:
    """Utilitários para exportação de resultados"""
    
    def __init__(self, results_dir: str = "resultados"):
        """
        Inicializa utilitários de exportação
        
        Args:
            results_dir: Diretório para salvar arquivos
        """
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
    
    def export_search_results(self, results: pd.DataFrame, query: str,
                             format: str = "csv", ai_recommendation: Optional[str] = None) -> str:
        """
        Exporta resultados de busca para arquivo
        
        Args:
            results: DataFrame com resultados
            query: Query original (para nome do arquivo)
            format: "csv" ou "json"
            ai_recommendation: Texto da recomendação IA (opcional)
            
        Returns:
            Caminho do arquivo salvo
        """
        # Cria nome do arquivo baseado na query e timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        query_clean = "".join(c for c in query if c.isalnum()
                              or c in (' ', '-', '_')).rstrip()
        query_clean = query_clean.replace(' ', '_')[:50]  # Limita tamanho
        
        if format.lower() == "csv":
            filename = f"busca_{query_clean}_{timestamp}.csv"
            filepath = self.results_dir / filename
            
            # Salva CSV
            results.to_csv(filepath, index=False, encoding='utf-8-sig')
            
            # Se há recomendação IA, salva em arquivo separado
            if ai_recommendation:
                rec_filename = f"recomendacao_{query_clean}_{timestamp}.txt"
                rec_filepath = self.results_dir / rec_filename
                with open(rec_filepath, 'w', encoding='utf-8') as f:
                    f.write(f"Query: {query}\n")
                    f.write(f"Timestamp: {timestamp}\n")
                    f.write("="*50 + "\n")
                    f.write(ai_recommendation)
        
        elif format.lower() == "json":
            filename = f"busca_{query_clean}_{timestamp}.json"
            filepath = self.results_dir / filename
            
            # Prepara dados para JSON
            export_data = {
                "query": query,
                "timestamp": timestamp,
                "total_resultados": len(results),
                "resultados": results.to_dict('records')
            }
            
            if ai_recommendation:
                export_data["recomendacao_ia"] = ai_recommendation
            
            # Salva JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        else:
            raise ValueError("Formato deve ser 'csv' ou 'json'")
        
        logger.info(f"📁 Resultados exportados para: {filepath}")
        return str(filepath)
    
    def export_batch_results(self, batch_results: pd.DataFrame, filename: Optional[str] = None, 
                           format: str = 'xlsx') -> str:
        """
        Exporta resultados de lote em diferentes formatos
        
        Args:
            batch_results: DataFrame com resultados do lote
            filename: Nome do arquivo (opcional)
            format: 'xlsx', 'csv', 'json'
            
        Returns:
            Caminho do arquivo gerado
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"busca_lote_{timestamp}"
        
        # Remove extensão se fornecida
        base_name = filename.replace('.xlsx', '').replace(
            '.csv', '').replace('.json', '')
        
        if format == 'xlsx':
            file_path = self.results_dir / f"{base_name}.xlsx"
            
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # Aba principal com todos os resultados
                batch_results.to_excel(
                    writer, sheet_name='Todos_Resultados', index=False)
                
                # Aba com resumo por item
                summary_items = []
                for item_num in sorted(batch_results['Numero_Item'].unique()):
                    item_data = batch_results[batch_results['Numero_Item'] == item_num]
                    best_result = item_data.iloc[0]
                    
                    summary_items.append({
                        'Numero_Item': item_num,
                        'Item_Original': best_result['Item_Original'],
                        'Status': best_result['Status'],
                        'Melhor_Score': best_result['Score_Similaridade'],
                        'Melhor_Codigo': best_result['Código do Item'],
                        'Melhor_Descricao': best_result['Descrição do Item'],
                        'Total_Resultados': len(item_data)
                    })
                
                summary_df = pd.DataFrame(summary_items)
                summary_df.to_excel(
                    writer, sheet_name='Resumo_por_Item', index=False)
                
                # Aba com estatísticas
                stats = {
                    'Métrica': [
                        'Total de Itens',
                        'Itens com Sucesso',
                        'Itens com Erro',
                        'Total de Resultados',
                        'Score Médio',
                        'Score Máximo',
                        'Score Mínimo'
                    ],
                    'Valor': [
                        batch_results['Numero_Item'].nunique(),
                        len(batch_results[batch_results['Status'] == 'Sucesso']
                            ['Numero_Item'].unique()),
                        len(batch_results[batch_results['Status'] == 'Erro']
                            ['Numero_Item'].unique()),
                        len(batch_results),
                        batch_results[batch_results['Status'] ==
                                    'Sucesso']['Score_Similaridade'].mean(),
                        batch_results[batch_results['Status'] ==
                                    'Sucesso']['Score_Similaridade'].max(),
                        batch_results[batch_results['Status'] ==
                                    'Sucesso']['Score_Similaridade'].min()
                    ]
                }
                
                stats_df = pd.DataFrame(stats)
                stats_df.to_excel(
                    writer, sheet_name='Estatisticas', index=False)
        
        elif format == 'csv':
            file_path = self.results_dir / f"{base_name}.csv"
            batch_results.to_csv(file_path, index=False, encoding='utf-8-sig')
        
        elif format == 'json':
            file_path = self.results_dir / f"{base_name}.json"
            
            # Estrutura JSON organizada
            json_data = {
                'metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'total_itens': int(batch_results['Numero_Item'].nunique()),
                    'total_resultados': len(batch_results),
                    'itens_sucesso': len(batch_results[batch_results['Status'] == 'Sucesso']['Numero_Item'].unique()),
                    'score_medio': float(batch_results[batch_results['Status'] == 'Sucesso']['Score_Similaridade'].mean())
                },
                'itens': []
            }
            
            for item_num in sorted(batch_results['Numero_Item'].unique()):
                item_data = batch_results[batch_results['Numero_Item'] == item_num]
                
                item_json = {
                    'numero_item': int(item_num),
                    'item_original': item_data['Item_Original'].iloc[0],
                    'status': item_data['Status'].iloc[0],
                    'resultados': []
                }
                
                for _, result in item_data.iterrows():
                    item_json['resultados'].append({
                        'ranking': int(result['Ranking_Item']),
                        'score': float(result['Score_Similaridade']),
                        'codigo': result['Código do Item'],
                        'descricao': result['Descrição do Item'],
                        'recomendacao_ia': result.get('Recomendacao_IA', '')
                    })
                
                json_data['itens'].append(item_json)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        else:
            raise ValueError("Formato deve ser 'xlsx', 'csv' ou 'json'")
        
        logger.info(f"✅ Arquivo exportado: {file_path}")
        return str(file_path)