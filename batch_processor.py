#!/usr/bin/env python3
"""
Módulo de Processamento em Lote
Responsável por processar múltiplos itens e gerar relatórios
"""

import pandas as pd
import logging
from typing import List, Callable, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class BatchProcessor:
    """Processador de lotes para múltiplas buscas"""
    
    def __init__(self, search_engine, ai_recommender):
        """
        Inicializa o processador de lotes
        
        Args:
            search_engine: Instância do motor de busca
            ai_recommender: Instância do recomendador IA
        """
        self.search_engine = search_engine
        self.ai_recommender = ai_recommender
    
    def process_batch(self, item_list: List[str], df: pd.DataFrame, top_k: int = 5, 
                     use_ai: bool = True, progress_callback: Optional[Callable] = None) -> pd.DataFrame:
        """
        Processa uma lista de itens fazendo busca para cada um
        
        Args:
            item_list: Lista de strings com os itens para buscar
            df: DataFrame com os dados
            top_k: Número de resultados por item
            use_ai: Se deve usar recomendações IA
            progress_callback: Função para callback de progresso
            
        Returns:
            DataFrame com resultados consolidados
        """
        print(f"🔄 Processando lote de {len(item_list)} itens...")
        
        batch_results = []
        
        for i, item in enumerate(item_list):
            if progress_callback:
                progress_callback(i + 1, len(item_list), item)
            
            print(f"📋 Processando item {i+1}/{len(item_list)}: {item[:50]}...")
            
            try:
                # Realiza busca
                results = self.search_engine.search(item.strip(), df, top_k)
                
                # Gera recomendação IA se solicitado
                if use_ai:
                    recommendation = self.ai_recommender.generate_recommendation(
                        item.strip(), results)
                else:
                    recommendation = "IA desabilitada"
                
                # Adiciona informações do lote
                item_results = results.copy()
                item_results['Item_Original'] = item.strip()
                item_results['Numero_Item'] = i + 1
                item_results['Recomendacao_IA'] = recommendation
                item_results['Status'] = 'Sucesso'
                
                # Adiciona ranking dentro do item
                item_results['Ranking_Item'] = range(1, len(item_results) + 1)
                
                batch_results.append(item_results)
                
            except Exception as e:
                print(f"❌ Erro ao processar item '{item}': {e}")
                
                # Cria entrada de erro
                error_df = pd.DataFrame({
                    'Item_Original': [item.strip()],
                    'Numero_Item': [i + 1],
                    'Status': ['Erro'],
                    'Recomendacao_IA': [f"Erro: {str(e)}"],
                    'Score_Similaridade': [0.0],
                    'Código do Item': ['N/A'],
                    'Descrição do Item': [f'Erro ao processar: {str(e)}'],
                    'Ranking_Item': [1]
                })
                
                batch_results.append(error_df)
        
        # Consolida todos os resultados
        if batch_results:
            final_df = pd.concat(batch_results, ignore_index=True)
            
            # Reordena colunas para melhor visualização
            column_order = [
                'Numero_Item', 'Item_Original', 'Status', 'Ranking_Item',
                'Score_Similaridade', 'Código do Item', 'Descrição do Item',
                'Recomendacao_IA'
            ]
            
            # Adiciona outras colunas que possam existir
            other_columns = [
                col for col in final_df.columns if col not in column_order]
            column_order.extend(other_columns)
            
            final_df = final_df[column_order]
            
            print(f"✅ Processamento concluído: {len(final_df)} resultados para {len(item_list)} itens")
            return final_df
        else:
            print("❌ Nenhum resultado foi processado")
            return pd.DataFrame()
    
    def generate_batch_report(self, batch_df: pd.DataFrame, format: str = 'html') -> str:
        """
        Gera relatório detalhado do processamento em lote
        
        Args:
            batch_df: DataFrame com resultados do lote
            format: 'html', 'markdown' ou 'text'
            
        Returns:
            String com o relatório formatado
        """
        if batch_df.empty:
            return "Nenhum dado para gerar relatório."
        
        # Estatísticas gerais
        total_items = batch_df['Numero_Item'].nunique()
        total_results = len(batch_df)
        success_items = len(batch_df[batch_df['Status'] == 'Sucesso'])
        error_items = len(batch_df[batch_df['Status'] == 'Erro'])
        avg_score = batch_df[batch_df['Status'] == 'Sucesso']['Score_Similaridade'].mean()
        
        if format == 'html':
            report = f"""
            <div style="font-family: 'Segoe UI', Arial, sans-serif; font-size: 14px; line-height: 1.6; max-width: 1200px; margin: 0 auto; background: #f8f9fa; padding: 20px; border-radius: 10px;">
                <h1 style="color: #2c3e50; text-align: center; border-bottom: 3px solid #3498db; padding-bottom: 15px; font-size: 28px; margin-bottom: 30px;">
                    Relatório de Busca em Lote
                </h1>
                
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 25px; border-radius: 10px; color: white; margin: 20px 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    <h2 style="margin: 0; text-align: center; font-size: 24px; margin-bottom: 20px;">Estatísticas Gerais</h2>
                    
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 15px;">
                        <div style="background: white; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <h3 style="color: #28a745; margin: 0;">{total_items}</h3>
                            <p style="margin: 5px 0; color: #6c757d;">Itens Processados</p>
                        </div>
                        <div style="background: white; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <h3 style="color: #007bff; margin: 0;">{total_results}</h3>
                            <p style="margin: 5px 0; color: #6c757d;">Total de Resultados</p>
                        </div>
                        <div style="background: white; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <h3 style="color: #28a745; margin: 0;">{success_items}</h3>
                            <p style="margin: 5px 0; color: #6c757d;">Sucessos</p>
                        </div>
                        <div style="background: white; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <h3 style="color: #dc3545; margin: 0;">{error_items}</h3>
                            <p style="margin: 5px 0; color: #6c757d;">Erros</p>
                        </div>
                        <div style="background: white; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <h3 style="color: #ffc107; margin: 0;">{avg_score:.3f}</h3>
                            <p style="margin: 5px 0; color: #6c757d;">Score Médio</p>
                        </div>
                    </div>
                </div>
            """
            
            # Adiciona detalhes por item
            report += '<div style="background: white; padding: 25px; border-radius: 10px; margin: 20px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">'
            report += '<h2 style="color: #495057; font-size: 22px; margin-bottom: 25px; border-bottom: 2px solid #e9ecef; padding-bottom: 10px;">Detalhes por Item</h2>'
            
            for item_num in sorted(batch_df['Numero_Item'].unique()):
                item_data = batch_df[batch_df['Numero_Item'] == item_num]
                item_original = item_data['Item_Original'].iloc[0]
                status = item_data['Status'].iloc[0]
                
                status_color = '#28a745' if status == 'Sucesso' else '#dc3545'
                
                report += f"""
                <div style="border-left: 4px solid {status_color}; margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <h3 style="color: #495057; margin-top: 0; font-size: 18px; margin-bottom: 15px;">Item {item_num}: {item_original}</h3>
                    <p style="font-size: 14px; margin-bottom: 15px;"><strong>Status:</strong> <span style="color: {status_color}; font-weight: bold;">{status}</span></p>
                """
                
                if status == 'Sucesso':
                    best_results = item_data.head(3)
                    report += '<h4 style="color: #495057; font-size: 16px; margin: 15px 0 10px 0;">Melhores Resultados:</h4><ul style="padding-left: 0; list-style: none;">'
                    
                    for _, result in best_results.iterrows():
                        report += f"""
                        <li style="margin: 12px 0; padding: 15px; background: white; border-radius: 6px; border: 1px solid #e9ecef; font-size: 13px; line-height: 1.5;">
                            <div style="margin-bottom: 8px;">
                                <strong style="color: #495057; font-size: 14px;">#{result['Ranking_Item']}</strong> -
                                Score: <span style="color: #007bff; font-weight: bold; font-size: 14px;">{result['Score_Similaridade']:.3f}</span>
                            </div>
                            <div style="margin-bottom: 6px;"><strong>Código:</strong> <span style="color: #6c757d;">{result['Código do Item']}</span></div>
                            <div><strong>Descrição:</strong> <span style="color: #495057;">{result['Descrição do Item'][:100]}...</span></div>
                        </li>
                        """
                    report += '</ul>'
                    
                    # Adiciona recomendação IA se disponível
                    recommendation = item_data['Recomendacao_IA'].iloc[0]
                    if recommendation and recommendation != 'IA desabilitada':
                        report += f'''<div style="background: #e3f2fd; padding: 15px; border-radius: 8px; margin-top: 15px; border: 1px solid #bbdefb;">
                            <h5 style="color: #1976d2; margin: 0 0 10px 0; font-size: 14px;">Recomendação IA:</h5>
                            <div style="color: #424242; font-size: 13px; line-height: 1.5; font-family: 'Segoe UI', Arial, sans-serif; white-space: pre-wrap;">{recommendation[:500]}{'...' if len(recommendation) > 500 else ''}</div>
                        </div>'''
                
                report += '</div>'
            
            report += '</div></div>'
            
        elif format == 'markdown':
            report = f"""# 📊 Relatório de Busca em Lote

## 📈 Estatísticas Gerais

- **Itens Processados:** {total_items}
- **Total de Resultados:** {total_results}
- **Sucessos:** {success_items}
- **Erros:** {error_items}
- **Score Médio:** {avg_score:.3f}

## 📋 Detalhes por Item

"""
            for item_num in sorted(batch_df['Numero_Item'].unique()):
                item_data = batch_df[batch_df['Numero_Item'] == item_num]
                item_original = item_data['Item_Original'].iloc[0]
                status = item_data['Status'].iloc[0]
                
                report += f"### Item {item_num}: {item_original}\n\n"
                report += f"**Status:** {status}\n\n"
                
                if status == 'Sucesso':
                    best_results = item_data.head(3)
                    report += "**🏆 Melhores Resultados:**\n\n"
                    
                    for _, result in best_results.iterrows():
                        report += f"- **#{result['Ranking_Item']}** - Score: {result['Score_Similaridade']:.3f}\n"
                        report += f"  - **Código:** {result['Código do Item']}\n"
                        report += f"  - **Descrição:** {result['Descrição do Item'][:100]}...\n\n"
        
        else:  # format text
            report = f"""
RELATÓRIO DE BUSCA EM LOTE
{'='*50}

ESTATÍSTICAS GERAIS:
- Itens Processados: {total_items}
- Total de Resultados: {total_results}
- Sucessos: {success_items}
- Erros: {error_items}
- Score Médio: {avg_score:.3f}

DETALHES POR ITEM:
{'-'*50}
"""
            for item_num in sorted(batch_df['Numero_Item'].unique()):
                item_data = batch_df[batch_df['Numero_Item'] == item_num]
                item_original = item_data['Item_Original'].iloc[0]
                status = item_data['Status'].iloc[0]
                
                report += f"\nItem {item_num}: {item_original}\n"
                report += f"Status: {status}\n"
                
                if status == 'Sucesso':
                    best_results = item_data.head(3)
                    report += "Melhores Resultados:\n"
                    
                    for _, result in best_results.iterrows():
                        report += f"  #{result['Ranking_Item']} - Score: {result['Score_Similaridade']:.3f}\n"
                        report += f"    Código: {result['Código do Item']}\n"
                        report += f"    Descrição: {result['Descrição do Item'][:80]}...\n"
        
        return report