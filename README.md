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

## Daily Reports Dashboard & Analysis System

Este projeto combina FastAPI e Streamlit para criar um sistema completo de análise e visualização de relatórios diários.

## 🚀 Funcionalidades

- **Dashboard Interativo**
  - Visualização em tempo real de métricas diárias
  - Filtros por data e equipe
  - Gráficos interativos com Plotly
  - Layout responsivo e intuitivo

- **API Robusta**
  - Endpoints RESTful para acesso aos dados
  - Documentação automática com Swagger
  - Sistema de cache para melhor performance
  - Validação de dados com Pydantic

## 📊 Métricas Disponíveis

- **Métricas Principais**
  - Demandas Resolvidas
  - Em Análise
  - Pendentes (Ativo)
  - Pendentes (Receptivo)

- **Métricas Adicionais**
  - Quitados
  - Aprovados
  - Receptivo Total
  - Análise do Dia

## 🛠️ Tecnologias

- **Backend**
  - FastAPI
  - Pydantic
  - Python 3.8+
  - Uvicorn

- **Frontend**
  - Streamlit
  - Plotly
  - Pandas
  - Requests

## 📦 Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/Igorofyeshu4/keepgoing.git
   cd keepgoing
   ```

2. Crie e ative o ambiente virtual:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Executando o Projeto

1. Inicie o servidor FastAPI:
   ```bash
   cd api
   uvicorn app.main:app --reload --port 8000
   ```

2. Em outro terminal, inicie o dashboard Streamlit:
   ```bash
   cd api/dashboard
   streamlit run main.py
   ```

3. Acesse:
   - Dashboard: http://localhost:8501
   - API Docs: http://localhost:8000/docs

## 📁 Estrutura do Projeto

```
api/
├── app/
│   ├── api/
│   │   └── endpoints/    # Endpoints da API
│   ├── services/         # Lógica de negócios
│   └── models/          # Modelos de dados
├── dashboard/
│   └── main.py         # Interface Streamlit
└── requirements.txt    # Dependências
```

## 📝 Endpoints da API

- `GET /api/v1/metrics/daily`: Métricas diárias
- `GET /api/v1/metrics/teams`: Lista de equipes
- `GET /api/v1/metrics/date-range`: Intervalo de datas disponível

## 👥 Contribuição

1. Faça um Fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request
