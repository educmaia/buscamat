#!/usr/bin/env python3
"""
Interface Web Gradio para Buscador Semântico Catmat v3.0 - Versão Modular
Interface alternativa mais simples e rápida usando nova arquitetura modular

Autor: Assistente Claude
Data: 2025
"""

import gradio as gr
import pandas as pd
import time
import io
import json
import tempfile
import shutil
import os
from datetime import datetime
from buscador_catmat import BuscadorSemanticoCatmat

# Variável global para o buscador
buscador = None

def inicializar_sistema():
    """Inicializa o buscador (chamado uma vez)"""
    global buscador
    try:
        if buscador is None:
            print("Inicializando sistema modular...")
            buscador = BuscadorSemanticoCatmat()
            buscador.initialize(force_rebuild=False)
            print("Sistema modular inicializado!")
        return "Sistema modular inicializado com sucesso!"
    except Exception as e:
        error_msg = f"Erro na inicializacao: {str(e)}"
        print(error_msg)
        return error_msg

def processar_lista_itens(texto_lista):
    """Processa texto da lista de itens"""
    if not texto_lista.strip():
        return []

    # Divide por linhas e limpa
    itens = [linha.strip() for linha in texto_lista.strip().split('\n') if linha.strip()]

    # Remove numeração se existir (ex: "1. item" -> "item")
    import re
    itens_limpos = []
    for item in itens:
        # Remove numeração no início (1., 2., etc.)
        item_limpo = re.sub(r'^\d+\.\s*', '', item)
        # Remove bullets (-, *, •)
        item_limpo = re.sub(r'^[-*•]\s*', '', item_limpo)
        if item_limpo:
            itens_limpos.append(item_limpo)

    return itens_limpos

def buscar_individual(query, top_k, usar_ia):
    """Realiza busca individual"""
    global buscador

    if not query or query.strip() == "":
        return "Por favor, digite uma consulta para buscar.", None, None, None

    try:
        # Inicializa sistema se necessário
        if buscador is None:
            print("Inicializando sistema modular pela primeira vez...")
            buscador = BuscadorSemanticoCatmat()
            buscador.initialize(force_rebuild=False)
            print("Sistema modular inicializado!")

        start_time = time.time()

        if usar_ia:
            resultados, recomendacao = buscador.search_with_ai(query, top_k)
        else:
            resultados = buscador.search(query, top_k)
            recomendacao = "Recomendacoes IA desabilitadas."

        search_time = time.time() - start_time

        # Prepara resumo
        resumo = f"""
## Resumo da Busca

**Query:** {query}
**Resultados encontrados:** {len(resultados)}
**Tempo de busca:** {search_time:.3f}s
**Top-K:** {top_k}
**IA habilitada:** {'Sim' if usar_ia else 'Nao'}

**Melhor resultado:** {resultados.iloc[0]['Descrição do Item'][:100]}... (Score: {resultados.iloc[0]['Score_Similaridade']:.3f})
"""

        # Prepara DataFrame para exibição
        df_display = resultados[['Score_Similaridade', 'Código do Item', 'Descrição do Item']].copy()
        df_display['Score_Similaridade'] = df_display['Score_Similaridade'].round(3)

        # Prepara dados CSV
        csv_data = resultados.to_csv(index=False)

        return resumo, recomendacao, df_display, csv_data

    except Exception as e:
        error_msg = f"Erro na busca: {str(e)}"
        print(error_msg)
        return error_msg, None, None, None

def processar_lote(lista_texto, top_k, usar_ia, progress=gr.Progress()):
    """Processa lista de itens em lote"""
    global buscador

    if not lista_texto or not lista_texto.strip():
        return "Por favor, cole uma lista de itens para processar.", None, None, None, None

    try:
        # Inicializa sistema se necessário
        if buscador is None:
            progress(0.1, desc="Inicializando sistema...")
            buscador = BuscadorSemanticoCatmat()
            buscador.initialize(force_rebuild=False)

        # Processa lista
        itens_processados = processar_lista_itens(lista_texto)

        if not itens_processados:
            return "Nenhum item valido encontrado na lista.", None, None, None, None

        progress(0.2, desc=f"Processando {len(itens_processados)} itens...")

        # Callback de progresso
        def callback_progresso(atual, total, item_atual):
            progresso = 0.2 + (atual / total) * 0.7  # 20% a 90%
            progress(progresso, desc=f"Processando {atual}/{total}: {item_atual[:30]}...")

        start_time = time.time()

        # Processa lote
        df_resultados = buscador.process_batch(
            itens_processados,
            top_k=top_k,
            use_ai=usar_ia,
            progress_callback=callback_progresso
        )

        total_time = time.time() - start_time

        progress(0.95, desc="Gerando relatórios...")

        if df_resultados.empty:
            return "Nenhum resultado foi processado.", None, None, None, None

        # Estatísticas
        total_itens = df_resultados['Numero_Item'].nunique()
        itens_sucesso = len(df_resultados[df_resultados['Status'] == 'Sucesso']['Numero_Item'].unique())
        itens_erro = len(df_resultados[df_resultados['Status'] == 'Erro']['Numero_Item'].unique())
        score_medio = df_resultados[df_resultados['Status'] == 'Sucesso']['Score_Similaridade'].mean()

        # Resumo
        resumo = f"""
## Resumo do Processamento em Lote

**Total de itens processados:** {total_itens}
**Sucessos:** {itens_sucesso}
**Erros:** {itens_erro}
**Tempo total:** {total_time:.1f}s
**Score medio:** {score_medio:.3f}
**IA habilitada:** {'Sim' if usar_ia else 'Nao'}
"""

        # Gera relatório HTML
        relatorio_html = buscador.generate_batch_report(df_resultados, format='html')

        # Prepara dados para download
        csv_data = df_resultados.to_csv(index=False)
        json_data = df_resultados.to_json(orient='records', indent=2)

        progress(1.0, desc="Concluído!")

        return resumo, df_resultados, relatorio_html, csv_data, json_data

    except Exception as e:
        error_msg = f"Erro no processamento: {str(e)}"
        print(error_msg)
        return error_msg, None, None, None, None

def preparar_csv_individual(csv_data):
    """Prepara arquivo CSV para download individual"""
    if csv_data:
        
        # Nome mais descritivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"busca_individual_{timestamp}.csv"
        
        # Cria arquivo temporário com nome descritivo
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, filename)
        
        with open(temp_path, 'w', encoding='utf-8-sig') as temp_file:
            temp_file.write(csv_data)
        
        return gr.update(value=temp_path, visible=True)
    return gr.update(visible=False)

def preparar_json_individual(resultados_df):
    """Prepara arquivo JSON para download individual"""
    if resultados_df is not None and not resultados_df.empty:
        
        json_data = resultados_df.to_json(orient='records', indent=2)
        
        # Nome mais descritivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"busca_individual_{timestamp}.json"
        
        # Cria arquivo temporário com nome descritivo
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, filename)
        
        with open(temp_path, 'w', encoding='utf-8') as temp_file:
            temp_file.write(json_data)
        
        return gr.update(value=temp_path, visible=True)
    return gr.update(visible=False)

def preparar_csv_lote(csv_data):
    """Prepara arquivo CSV para download do lote"""
    if csv_data:
        
        # Nome mais descritivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"lote_resultados_{timestamp}.csv"
        
        # Cria arquivo temporário com nome descritivo
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, filename)
        
        with open(temp_path, 'w', encoding='utf-8-sig') as temp_file:
            temp_file.write(csv_data)
        
        return gr.update(value=temp_path, visible=True)
    return gr.update(visible=False)

def preparar_json_lote(json_data):
    """Prepara arquivo JSON para download do lote"""
    if json_data:
        
        # Nome mais descritivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"lote_resultados_{timestamp}.json"
        
        # Cria arquivo temporário com nome descritivo
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, filename)
        
        with open(temp_path, 'w', encoding='utf-8') as temp_file:
            temp_file.write(json_data)
        
        return gr.update(value=temp_path, visible=True)
    return gr.update(visible=False)

def preparar_relatorio_lote(relatorio_html):
    """Prepara relatório HTML para download"""
    if relatorio_html:
        
        # Nome mais descritivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"relatorio_completo_{timestamp}.html"
        
        # Cria arquivo temporário com nome descritivo
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, filename)
        
        with open(temp_path, 'w', encoding='utf-8') as temp_file:
            temp_file.write(relatorio_html)
        
        return gr.update(value=temp_path, visible=True)
    return gr.update(visible=False)

def preparar_csv_especial(resultados_lote):
    """Prepara CSV especial para download"""
    
    if resultados_lote is None or resultados_lote.empty:
        return gr.update(visible=False)
    
    try:
        
        # Gera CSV especial no local original
        arquivo_csv = buscador.export_special_csv(resultados_lote)
        
        # Nome mais descritivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"csv_especial_{timestamp}.csv"
        
        # Cria arquivo temporário com nome descritivo
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, filename)
        
        # Copia conteúdo para arquivo temporário
        with open(arquivo_csv, 'r', encoding='utf-8-sig') as original:
            with open(temp_path, 'w', encoding='utf-8-sig') as temp_file:
                temp_file.write(original.read())
        
        return gr.update(value=temp_path, visible=True)
        
    except Exception as e:
        print(f"Erro ao preparar CSV especial: {e}")
        return gr.update(visible=False)

def criar_interface():
    """Cria a interface Gradio"""

    with gr.Blocks(
        title="Buscador Semantico CATMAT - Modular",
        theme=gr.themes.Soft(),
        css="""
        .gradio-container {
            max-width: 1200px !important;
        }
        .tab-nav {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .batch-container {
            border: 2px dashed #ccc;
            border-radius: 10px;
            padding: 20px;
            margin: 10px 0;
        }
        """
    ) as interface:

        # Header
        gr.Markdown("""
        # Buscador Semantico CATMAT v3.0 - Versao Modular

        **Sistema avancado de busca semantica no catalogo CATMAT com IA integrada**
        **Nova arquitetura modular - Melhor performance e organizacao**

        Escolha entre busca individual ou processamento em lote de multiplos itens.
        """)

        # Tabs principais
        with gr.Tabs():
            # Tab 1: Busca Individual
            with gr.Tab("Busca Individual"):
                gr.Markdown("### Digite o item que voce esta procurando")

                with gr.Row():
                    with gr.Column(scale=3):
                        query_input = gr.Textbox(
                            label="Consulta",
                            placeholder="Ex: parafuso aco inox M6 x 20mm",
                            lines=2
                        )

                    with gr.Column(scale=1):
                        top_k_individual = gr.Slider(
                            label="Numero de resultados",
                            minimum=1,
                            maximum=20,
                            value=5,
                            step=1
                        )

                        usar_ia_individual = gr.Checkbox(
                            label="Usar recomendacoes IA",
                            value=True
                        )

                        btn_buscar = gr.Button(
                            "Buscar",
                            variant="primary",
                            size="lg"
                        )

                # Resultados individuais
                resumo_individual = gr.Markdown(visible=False)
                recomendacao_individual = gr.Markdown(visible=False)
                resultados_individual = gr.Dataframe(
                    visible=False,
                    interactive=False,
                    wrap=True
                )

                # Downloads individuais
                gr.Markdown("### Downloads")
                with gr.Row():
                    with gr.Column():
                        csv_download_individual = gr.File(
                            label="Download CSV",
                            visible=False,
                            file_count="single"
                        )
                        btn_csv_individual = gr.Button("Preparar CSV", variant="secondary")

                    with gr.Column():
                        json_download_individual = gr.File(
                            label="Download JSON",
                            visible=False,
                            file_count="single"
                        )
                        btn_json_individual = gr.Button("Preparar JSON", variant="secondary")

            # Tab 2: Busca em Lote
            with gr.Tab("Busca em Lote"):
                gr.Markdown("""
                ### Processamento em Lote

                Cole sua lista de itens abaixo, um por linha. O sistema processara cada item individualmente.

                **Formatos aceitos:**
                - Lista simples (um item por linha)
                - Lista numerada (1. item, 2. item, etc.)
                - Lista com bullets (- item, * item, etc.)
                """)

                with gr.Row():
                    with gr.Column(scale=2):
                        lista_input = gr.Textbox(
                            label="Lista de Itens",
                            placeholder="""Cole sua lista aqui, exemplo:
parafuso aco inox M6
cabo eletrico 2.5mm
tinta acrilica branca
parafuso phillips M4
fita isolante preta""",
                            lines=10,
                            max_lines=20
                        )

                    with gr.Column(scale=1):
                        top_k_lote = gr.Slider(
                            label="Resultados por item",
                            minimum=1,
                            maximum=10,
                            value=3,
                            step=1
                        )

                        usar_ia_lote = gr.Checkbox(
                            label="Usar recomendacoes IA",
                            value=True
                        )

                        btn_processar = gr.Button(
                            "Processar Lote",
                            variant="primary",
                            size="lg"
                        )

                # Resultados do lote
                resumo_lote = gr.Markdown(visible=False)

                with gr.Tabs() as tabs_resultados:
                    with gr.Tab("Tabela de Resultados"):
                        resultados_lote = gr.Dataframe(
                            visible=False,
                            interactive=False,
                            wrap=True
                        )

                    with gr.Tab("Relatorio Detalhado"):
                        relatorio_lote = gr.HTML(visible=False)

                # Downloads do lote
                gr.Markdown("### Downloads")
                with gr.Row():
                    with gr.Column():
                        csv_download_lote = gr.File(
                            label="Download CSV Normal",
                            visible=False,
                            file_count="single"
                        )
                        btn_csv_lote = gr.Button("Preparar CSV Normal", variant="secondary")

                    with gr.Column():
                        csv_especial_download = gr.File(
                            label="Download CSV Especial (#-separated)",
                            visible=False,
                            file_count="single"
                        )
                        btn_csv_especial = gr.Button("Preparar CSV Especial", variant="primary")
                        
                with gr.Row():
                    with gr.Column():
                        json_download_lote = gr.File(
                            label="Download JSON",
                            visible=False,
                            file_count="single"
                        )
                        btn_json_lote = gr.Button("Preparar JSON", variant="secondary")

                    with gr.Column():
                        relatorio_download_lote = gr.File(
                            label="Download Relatorio HTML",
                            visible=False,
                            file_count="single"
                        )
                        btn_relatorio_lote = gr.Button("Preparar Relatorio HTML", variant="secondary")

        # Variáveis de estado para armazenar dados
        csv_data_individual = gr.State()
        dados_lote_csv = gr.State()
        dados_lote_json = gr.State()
        dados_lote_html = gr.State()

        # Eventos - Busca Individual
        btn_buscar.click(
            fn=buscar_individual,
            inputs=[query_input, top_k_individual, usar_ia_individual],
            outputs=[resumo_individual, recomendacao_individual, resultados_individual, csv_data_individual]
        ).then(
            fn=lambda resumo, rec, res, csv: [
                gr.update(visible=bool(resumo and resumo.strip())),
                gr.update(visible=bool(rec and rec.strip() and rec != "Recomendacoes IA desabilitadas.")),
                gr.update(visible=bool(res is not None and not res.empty) if res is not None else False)
            ],
            inputs=[resumo_individual, recomendacao_individual, resultados_individual, csv_data_individual],
            outputs=[resumo_individual, recomendacao_individual, resultados_individual]
        )

        # Downloads individuais
        btn_csv_individual.click(
            fn=preparar_csv_individual,
            inputs=[csv_data_individual],
            outputs=[csv_download_individual]
        )

        btn_json_individual.click(
            fn=preparar_json_individual,
            inputs=[resultados_individual],
            outputs=[json_download_individual]
        )

        # Eventos - Busca em Lote
        btn_processar.click(
            fn=processar_lote,
            inputs=[lista_input, top_k_lote, usar_ia_lote],
            outputs=[resumo_lote, resultados_lote, relatorio_lote, dados_lote_csv, dados_lote_json]
        ).then(
            fn=lambda resumo, res, rel, csv, json_data: [
                gr.update(visible=bool(resumo and resumo.strip())),
                gr.update(visible=bool(res is not None and not res.empty) if res is not None else False),
                gr.update(visible=bool(rel and rel.strip())),
                rel  # Armazena HTML no estado
            ],
            inputs=[resumo_lote, resultados_lote, relatorio_lote, dados_lote_csv, dados_lote_json],
            outputs=[resumo_lote, resultados_lote, relatorio_lote, dados_lote_html]
        )

        # Downloads do lote
        btn_csv_lote.click(
            fn=preparar_csv_lote,
            inputs=[dados_lote_csv],
            outputs=[csv_download_lote]
        )

        btn_json_lote.click(
            fn=preparar_json_lote,
            inputs=[dados_lote_json],
            outputs=[json_download_lote]
        )

        btn_relatorio_lote.click(
            fn=preparar_relatorio_lote,
            inputs=[dados_lote_html],
            outputs=[relatorio_download_lote]
        )
        
        btn_csv_especial.click(
            fn=preparar_csv_especial,
            inputs=[resultados_lote],
            outputs=[csv_especial_download]
        )

        # Footer
        gr.Markdown("""
        ---
        **Buscador Semantico CATMAT v3.0 - Versao Modular** | Desenvolvido usando Gradio e IA
        """)

    return interface

def main():
    """Função principal"""
    print("Iniciando Buscador Semantico CATMAT - Versao Modular...")

    # Cria interface
    interface = criar_interface()

    # Lança aplicação
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        debug=False
    )

if __name__ == "__main__":
    main()