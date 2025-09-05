#!/usr/bin/env python3
"""
Módulo de Recomendações com IA
Responsável por gerar recomendações inteligentes usando OpenAI
"""

import json
import time
import os
import logging
import pandas as pd
from typing import Optional
from openai import OpenAI

logger = logging.getLogger(__name__)


class AIRecommender:
    """Gerador de recomendações usando IA"""
    
    def __init__(self, openai_model: str = "gpt-4o-mini"):
        """
        Inicializa o recomendador IA
        
        Args:
            openai_model: Nome do modelo OpenAI a usar
        """
        self.openai_model = openai_model
        self.client = None
        self.api_key = os.getenv("OPENAI_API_KEY")
    
    def configure_openai(self, api_key: Optional[str] = None):
        """
        Configura cliente OpenAI
        
        Args:
            api_key: Chave da API OpenAI (opcional, pode usar variável de ambiente)
        """
        if api_key:
            self.api_key = api_key
        
        if not self.api_key:
            logger.warning(
                "Chave OpenAI não encontrada. Recomendações IA indisponíveis.")
            return
        
        try:
            self.client = OpenAI(api_key=self.api_key)
            
            # Testa a conexão
            response = self.client.chat.completions.create(
                model=self.openai_model,
                messages=[{"role": "user", "content": "teste"}],
                max_tokens=5
            )
            logger.info("✅ API OpenAI configurada com sucesso!")
            
        except Exception as e:
            logger.error(f"Erro ao configurar OpenAI: {e}")
            self.client = None
    
    def generate_recommendation(self, query: str, results: pd.DataFrame) -> str:
        """
        Usa LLM para analisar resultados e fazer recomendações inteligentes
        
        Args:
            query: Consulta original do usuário
            results: DataFrame com resultados da busca semântica
            
        Returns:
            Recomendação textual do LLM
        """
        if not self.client:
            return "❌ API OpenAI não configurada. Recomendações IA indisponíveis."
        
        logger.info("🧠 Analisando resultados com IA...")
        
        # Prepara dados dos resultados para o LLM (só os top 10)
        top_results = results.head(10)
        
        # Formata resultados para o prompt
        formatted_items = []
        for idx, row in top_results.iterrows():
            item_info = {
                'codigo': row.get('Código do Item', 'N/A'),
                'descricao': row['Descrição do Item'],
                'score': f"{row['Score_Similaridade']:.3f}",
                'classe': row.get('Nome da Classe', 'N/A'),
                'grupo': row.get('Nome do Grupo', 'N/A')
            }
            formatted_items.append(item_info)
        
        # Prompt melhorado
        prompt = f"""Você é um especialista em compras públicas e análise do Catmat (Catálogo de Materiais).

SOLICITAÇÃO DO USUÁRIO: "{query}"

ITENS ENCONTRADOS NA BUSCA SEMÂNTICA:
{json.dumps(formatted_items, indent=2, ensure_ascii=False)}

TAREFA:
1. Analise os itens encontrados considerando a solicitação do usuário
2. Recomende os 3 MELHORES itens que atendem à necessidade
3. Para cada recomendação, explique BREVEMENTE por que é adequada
4. Se houver diferenças importantes entre os itens, destaque-as
5. Se nenhum item for realmente adequado, mencione isso

FORMATO DA RESPOSTA:
🎯 RECOMENDAÇÕES PARA: [solicitação]

🥇 PRIMEIRA OPÇÃO
Código: [código]
Por que: [justificativa breve]

🥈 SEGUNDA OPÇÃO
Código: [código]
Por que: [justificativa breve]

🥉 TERCEIRA OPÇÃO
Código: [código]
Por que: [justificativa breve]

💡 OBSERVAÇÕES IMPORTANTES:
[diferenças relevantes, alertas, ou comentários adicionais]

Seja objetivo e prático. Foque no que realmente importa para a decisão de compra."""
        
        try:
            start_time = time.time()
            
            response = self.client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": "Você é um especialista em compras públicas e análise do Catmat. Seja objetivo, prático e focado nas necessidades reais do usuário."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.3
            )
            
            ai_time = time.time() - start_time
            logger.info(f"🧠 Análise IA concluída em {ai_time:.1f}s")
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Erro na análise IA: {e}")
            return f"❌ Erro na análise IA: {e}"