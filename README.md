# Buscador Semântico Catmat v3.0 - Versão Modular

## 🎯 Estrutura Atual

Esta pasta contém apenas os **arquivos essenciais** para o funcionamento do buscador semântico:

### 📦 Módulos Principais
- **`buscador_catmat.py`** - Classe principal coordenadora
- **`config_manager.py`** - Gerenciamento de configurações
- **`data_handler.py`** - Manipulação de dados CSV
- **`embeddings_engine.py`** - Geração de embeddings e indexação FAISS
- **`search_engine.py`** - Motor de busca semântica
- **`ai_recommender.py`** - Recomendações com IA (OpenAI)
- **`export_utils.py`** - Utilitários de exportação
- **`batch_processor.py`** - Processamento em lote
- **`__init__.py`** - Configuração do pacote Python

### 📊 Dados e Configuração
- **`catmat.csv`** - Base de dados principal
- **`config.json`** - Configurações do sistema
- **`requirements.txt`** - Dependências Python

### 📁 Pastas
- **`resultados/`** - Resultados exportados
- **`legacy/`** - Arquivos antigos e não-essenciais
- **`venv/`** - Ambiente virtual Python

## 🚀 Como Usar

### Instalação
```bash
pip install -r requirements.txt
```

### Uso Básico

#### Interface Web (Gradio)
```bash
python app_gradio.py
# Acesse: http://localhost:7860
```

#### Uso Programático
```python
from buscador_catmat import BuscadorSemanticoCatmat

# Inicializa o buscador
buscador = BuscadorSemanticoCatmat()
buscador.initialize()

# Busca simples
resultados = buscador.search("computador")

# Busca com IA
resultados, recomendacao = buscador.search_with_ai("computador")

# Exporta resultados
arquivo = buscador.export_results(resultados, "computador", "csv")
```

### Processamento em Lote
```python
# Lista de itens
itens = ["computador", "mouse", "teclado"]

# Processa lote
resultados = buscador.process_batch(itens, top_k=5, use_ai=True)

# Exporta lote
arquivo = buscador.export_batch_results(resultados, format='xlsx')
```

## 🗂️ Pasta Legacy

A pasta `legacy/` contém:
- **Versões anteriores** do código (`agente.py`, `agente_melhorado.py`)
- **Interfaces web** (`app_streamlit.py`, `app_gradio.py`)
- **Scripts de teste** (`test_*.py`)
- **Documentação antiga** 
- **Arquivos de exemplo**

Estes arquivos foram movidos para manter a pasta principal limpa e organizada.

## ⚡ Performance

O sistema utiliza:
- **FAISS HNSW** para busca rápida
- **Paralelização** na geração de embeddings
- **Cache** de embeddings e índices
- **Modelo E5-base-v2** para embeddings semânticos

## 🔧 Configuração

Edite o arquivo `config.json` para personalizar:
```json
{
  "model_name": "intfloat/e5-base-v2",
  "hnsw_m": 32,
  "batch_size": 64,
  "n_workers": 8,
  "openai_model": "gpt-4o-mini"
}
```

## 📈 Vantagens da Nova Arquitetura

- ✅ **Código limpo e organizado**
- ✅ **Módulos independentes**
- ✅ **Fácil manutenção**
- ✅ **Melhor testabilidade**
- ✅ **Escalabilidade**

---

*Para acessar as versões anteriores ou interfaces web, consulte a pasta `legacy/`*