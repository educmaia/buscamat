#!/usr/bin/env python3
"""
Exportador Especial - CSV com formato customizado
Gera CSV com separador # e estrutura específica para relatórios
"""

import pandas as pd
import re
import os
from datetime import datetime
from pathlib import Path


class SpecialExporter:
    """Exportador para formatos especiais de CSV"""
    
    def __init__(self, results_dir: str = "resultados"):
        """
        Inicializa o exportador especial
        
        Args:
            results_dir: Diretório para salvar arquivos
        """
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
    
    def extract_ai_recommendations(self, ai_text: str) -> dict:
        """
        Extrai as 3 principais recomendações da IA estruturada
        
        Args:
            ai_text: Texto completo da recomendação IA
            
        Returns:
            Dict com códigos e justificativas dos top 3
        """
        if not ai_text or ai_text == "IA desabilitada":
            return {
                'codigo_1': 'N/A', 'justificativa_1': 'IA não utilizada',
                'codigo_2': 'N/A', 'justificativa_2': 'IA não utilizada', 
                'codigo_3': 'N/A', 'justificativa_3': 'IA não utilizada'
            }
        
        recommendations = {
            'codigo_1': 'N/A', 'justificativa_1': 'Não extraída',
            'codigo_2': 'N/A', 'justificativa_2': 'Não extraída',
            'codigo_3': 'N/A', 'justificativa_3': 'Não extraída'
        }
        
        try:
            # Padrões para extrair informações estruturadas
            patterns = {
                'primeira_opcao': r'🥇\s*PRIMEIRA\s+OPÇÃO.*?Código:\s*([^\n]+).*?Por que:\s*([^\n🥈]+)',
                'segunda_opcao': r'🥈\s*SEGUNDA\s+OPÇÃO.*?Código:\s*([^\n]+).*?Por que:\s*([^\n🥉]+)',
                'terceira_opcao': r'🥉\s*TERCEIRA\s+OPÇÃO.*?Código:\s*([^\n]+).*?Por que:\s*([^\n💡]+)'
            }
            
            # Alternativas sem emojis
            alt_patterns = {
                'primeira_opcao': r'PRIMEIRA\s+OPÇÃO.*?Código:\s*([^\n]+).*?Por que:\s*([^\n]+?)(?=SEGUNDA|$)',
                'segunda_opcao': r'SEGUNDA\s+OPÇÃO.*?Código:\s*([^\n]+).*?Por que:\s*([^\n]+?)(?=TERCEIRA|$)',
                'terceira_opcao': r'TERCEIRA\s+OPÇÃO.*?Código:\s*([^\n]+).*?Por que:\s*([^\n]+?)(?=OBSERVAÇÕES|$)'
            }
            
            # Tenta extrair com emojis primeiro
            for key, pattern in patterns.items():
                match = re.search(pattern, ai_text, re.DOTALL | re.IGNORECASE)
                if match:
                    if 'primeira' in key:
                        recommendations['codigo_1'] = match.group(1).strip()
                        recommendations['justificativa_1'] = match.group(2).strip()
                    elif 'segunda' in key:
                        recommendations['codigo_2'] = match.group(1).strip()
                        recommendations['justificativa_2'] = match.group(2).strip()
                    elif 'terceira' in key:
                        recommendations['codigo_3'] = match.group(1).strip()
                        recommendations['justificativa_3'] = match.group(2).strip()
            
            # Se não encontrou com emojis, tenta sem emojis
            if recommendations['codigo_1'] == 'N/A':
                for key, pattern in alt_patterns.items():
                    match = re.search(pattern, ai_text, re.DOTALL | re.IGNORECASE)
                    if match:
                        if 'primeira' in key:
                            recommendations['codigo_1'] = match.group(1).strip()
                            recommendations['justificativa_1'] = match.group(2).strip()
                        elif 'segunda' in key:
                            recommendations['codigo_2'] = match.group(1).strip()
                            recommendations['justificativa_2'] = match.group(2).strip()
                        elif 'terceira' in key:
                            recommendations['codigo_3'] = match.group(1).strip()
                            recommendations['justificativa_3'] = match.group(2).strip()
            
        except Exception as e:
            print(f"Erro ao extrair recomendações IA: {e}")
        
        return recommendations
    
    def export_special_csv(self, batch_results: pd.DataFrame, filename: str = None) -> str:
        """
        Exporta CSV especial com formato:
        Item#Descrição#Código Catmat 1#Descrição 1#Porque IA 1#Código 2#Descrição 2#Porque IA 2#Código 3#Descrição 3#Porque IA 3
        
        Args:
            batch_results: DataFrame com resultados do lote
            filename: Nome do arquivo (opcional)
            
        Returns:
            Caminho do arquivo gerado
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"relatorio_especial_{timestamp}.csv"
        
        # Garante extensão .csv
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        file_path = self.results_dir / filename
        
        # Lista para armazenar as linhas do CSV
        csv_lines = []
        
        # Cabeçalho
        header = [
            "Item",
            "Descricao", 
            "Codigo_Catmat_1",
            "Descricao_Catmat_1", 
            "Porque_IA_1",
            "Codigo_Catmat_2", 
            "Descricao_Catmat_2",
            "Porque_IA_2",
            "Codigo_Catmat_3",
            "Descricao_Catmat_3", 
            "Porque_IA_3"
        ]
        csv_lines.append("#".join(header))
        
        # Processa cada item único
        for item_num in sorted(batch_results['Numero_Item'].unique()):
            item_data = batch_results[batch_results['Numero_Item'] == item_num]
            
            if item_data.empty:
                continue
            
            # Informações do item
            item_original = item_data['Item_Original'].iloc[0]
            status = item_data['Status'].iloc[0]
            
            if status != 'Sucesso':
                # Item com erro
                row = [
                    item_original,
                    f"ERRO: {status}",
                    "N/A", "Erro no processamento", "Erro no processamento",
                    "N/A", "Erro no processamento", "Erro no processamento", 
                    "N/A", "Erro no processamento", "Erro no processamento"
                ]
                csv_lines.append("#".join(row))
                continue
            
            # Pega os 3 melhores resultados
            top_3 = item_data.head(3)
            
            # Extrai recomendação IA se disponível
            ai_text = item_data['Recomendacao_IA'].iloc[0] if 'Recomendacao_IA' in item_data.columns else ""
            ai_recs = self.extract_ai_recommendations(ai_text)
            
            # Monta linha com os dados
            row = [item_original]  # Item original
            row.append(item_original)  # Descrição (igual ao item)
            
            # Adiciona os 3 códigos e descrições
            for i in range(3):
                if i < len(top_3):
                    result = top_3.iloc[i]
                    codigo = str(result['Código do Item'])
                    descricao = str(result['Descrição do Item'])
                    
                    # Mapeia justificativa da IA baseada no ranking
                    if i == 0:
                        justificativa = ai_recs['justificativa_1']
                    elif i == 1:
                        justificativa = ai_recs['justificativa_2']
                    else:
                        justificativa = ai_recs['justificativa_3']
                else:
                    codigo = "N/A"
                    descricao = "Sem resultado suficiente"
                    justificativa = "Não disponível"
                
                row.extend([codigo, descricao, justificativa])
            
            csv_lines.append("#".join(row))
        
        # Escreve arquivo
        with open(file_path, 'w', encoding='utf-8-sig') as f:
            f.write('\n'.join(csv_lines))
        
        print(f"CSV especial exportado: {file_path}")
        return str(file_path)