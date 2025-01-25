# Data Analysis and Dashboard Project

Este projeto contém uma coleção de scripts Python para análise de dados, geração de dashboards e APIs para processamento de dados.

## Estrutura do Projeto

```
organized_project/
├── api/              # APIs e serviços web
├── dashboard/        # Dashboards e visualizações
├── scripts/         # Scripts utilitários
├── src/             # Código fonte principal
└── tests/           # Testes unitários e de integração
```

## Dependências

O projeto utiliza Python 3.8+ e as seguintes bibliotecas principais:
- FastAPI para APIs
- Streamlit para dashboards
- Pandas para análise de dados
- Plotly e Altair para visualizações
- Google Sheets API para integração com planilhas

## Instalação

1. Clone o repositório
2. Crie um ambiente virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

## Uso

### Dashboard
```bash
streamlit run dashboard/streamlit_app.py
```

### API
```bash
uvicorn api.main:app --reload
```

## Testes
```bash
python -m pytest tests/
```
