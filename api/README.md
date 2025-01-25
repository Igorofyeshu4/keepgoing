# Demandas API

API RESTful para análise de demandas e métricas diárias.

## Requisitos

- Python 3.10+
- pip (gerenciador de pacotes Python)

## Instalação

1. Clone o repositório:
```bash
git clone <repository_url>
cd organized_project/api
```

2. Crie um ambiente virtual:
```bash
python -m venv venv
```

3. Ative o ambiente virtual:
- Windows:
```bash
.\venv\Scripts\activate
```
- Linux/Mac:
```bash
source venv/bin/activate
```

4. Instale as dependências:
```bash
pip install -r requirements.txt
```

5. Configure as variáveis de ambiente:
```bash
cp env.example .env
```
Edite o arquivo `.env` conforme necessário.

## Executando a API

1. Execute o servidor de desenvolvimento:
```bash
python run.py
```

2. Acesse a documentação da API:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Endpoints Principais

- `GET /api/v1/metrics/daily`: Retorna métricas diárias
  - Parâmetros:
    - `date`: Data para buscar métricas (formato: YYYY-MM-DD)
    - `team`: Equipe específica (opcional)

- `GET /api/v1/metrics/teams`: Lista todas as equipes disponíveis

- `GET /api/v1/metrics/date-range`: Retorna o intervalo de datas disponível nos dados

## Desenvolvimento

A estrutura do projeto segue as melhores práticas para APIs FastAPI:

```
api/
├── app/
│   ├── api/
│   │   ├── endpoints/
│   │   │   └── metrics.py
│   │   └── __init__.py
│   ├── models/
│   │   └── metrics.py
│   ├── services/
│   │   └── data_service.py
│   ├── __init__.py
│   ├── config.py
│   └── main.py
├── tests/
├── .env
├── requirements.txt
└── run.py
```
