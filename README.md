# Aviation Data Intelligence

Projeto de Engenharia de Dados para ingestão, processamento e análise de dados de tráfego aéreo, utilizando Python, PostgreSQL, SQL e Apache Airflow.

## Objetivo

Construir um pipeline de dados organizado em três camadas:

- **Bronze:** armazenamento dos dados brutos obtidos da API OpenSky Network.
- **Silver:** transformação dos registros de aeronaves em dados estruturados.
- **Gold:** agregação de indicadores de tráfego aéreo para análise.

## Tecnologias

- Python
- PostgreSQL
- SQLAlchemy
- Pandas
- Streamlit
- Pytest
- Docker e Docker Compose
- Apache Airflow 2.9.3

## Arquitetura

```text
OpenSky Network API
        |
        v
Bronze - bronze.raw_aviation
        |
        v
Silver - silver.aircraft_states
        |
        v
Gold - gold.air_traffic_summary
```

O PostgreSQL armazena os dados do pipeline. O Airflow utiliza um banco PostgreSQL separado para seus metadados.

## Estrutura do projeto

- `src/aviation/ingestion/`: integração com a API e persistência Bronze.
- `src/aviation/processing/`: transformações Silver e Gold.
- `src/aviation/database/`: configuração da conexão PostgreSQL.
- `src/aviation/pipeline.py`: orquestração do pipeline Python.
- `sql/`: scripts de criação dos schemas e tabelas.
- `dags/`: definição dos workflows do Airflow.
- `tests/`: testes automatizados.
- `dashboard/app.py`: dashboard analítico desenvolvido com Streamlit.
- `Dockerfile`: imagem local do Airflow.
- `compose.yaml`: serviços Docker.
- `requirements.txt`: dependências do ambiente Python local.

## Configuração local

Pré-requisitos:

- Python e ambiente virtual
- PostgreSQL
- Docker Desktop, para execução do Airflow

Crie o ambiente virtual e instale as dependências:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Crie o arquivo de configuração local:

```bash
cp .env.example .env
```

Configure as variáveis de conexão PostgreSQL e, quando necessário, as credenciais da API OpenSky.

Os bancos de dados, schemas e tabelas devem existir antes da execução do pipeline. Os scripts de estrutura estão disponíveis no diretório `sql/`.

## Execução do pipeline Python

Pipeline completo, incluindo a etapa de ingestão:

```bash
PYTHONPATH=src python -m aviation.pipeline
```

Reprocessamento dos registros já armazenados, sem consultar a API:

```bash
PYTHONPATH=src python -m aviation.pipeline --mode reprocess
```

As transformações utilizam operações incrementais com tratamento de conflitos para evitar a reinserção dos mesmos registros.

## Dashboard Streamlit

O dashboard consulta a camada Gold do PostgreSQL e apresenta indicadores do ultimo snapshot, comparacao entre lotes por barras agrupadas e historico consolidado.

Para iniciar, com o PostgreSQL ativo e o ambiente virtual configurado:

```bash
PYTHONPATH=src python -m streamlit run dashboard/app.py
```

Acesse http://localhost:8501.

Os dados representam snapshots historicos, nao monitoramento em tempo real.

## Apache Airflow

O ambiente Docker contém:

- PostgreSQL 16 para metadados do Airflow.
- Apache Airflow 2.9.3 com LocalExecutor.
- Código Python do projeto disponibilizado ao contêiner.

Crie o arquivo local de senha do banco de metadados:

```bash
cp .env.compose.example .env.compose
```

Substitua o valor de exemplo por uma senha local de desenvolvimento.

Crie também o arquivo privado `.env.airflow` com as variáveis:

```dotenv
DB_HOST=host.docker.internal
DB_PORT=5432
DB_NAME=aviation_data_intelligence_test
DB_USER=aviation_pipeline
DB_PASSWORD=SUBSTITUA_PELA_CREDENCIAL_LOCAL
```

O banco de testes, o usuário e suas permissões devem ser configurados previamente no PostgreSQL do host.

Inicie os serviços:

```bash
docker compose --env-file .env.compose up -d --build
```

Interface web do Airflow:

http://localhost:8080

O DAG `aviation_reprocess_test` executa manualmente o reprocessamento Bronze → Silver → Gold no banco `aviation_data_intelligence_test`.

Por segurança, o DAG bloqueia a execução quando a variável `DB_NAME` aponta para outro banco.

Para verificar os serviços:

```bash
docker compose --env-file .env.compose ps
```

Para interrompê-los sem excluir os volumes:

```bash
docker compose --env-file .env.compose down
```

## Testes

Execute os testes automatizados:

```bash
PYTHONPATH=src python -m pytest -q
```

Na validação local realizada em novembro de 2026, os 23 testes existentes foram aprovados.

## Segurança

Os arquivos `.env`, `.env.airflow` e `.env.compose` são privados e não devem ser versionados.

Os arquivos de exemplo documentam a configuração sem incluir credenciais reais.

O Airflow utiliza o driver `psycopg2`, compatível com a versão do SQLAlchemy presente na imagem utilizada. O ambiente Python local utiliza `psycopg` por padrão.

## Estado atual e limitações

- Pipeline Bronze, Silver e Gold implementado.
- Reprocessamento incremental disponível.
- Testes automatizados implementados.
- DAG de reprocessamento manual validado no banco de testes.
- A ingestão automática periódica pelo Airflow ainda não está implementada.
- O ambiente Docker depende de um PostgreSQL acessível no host.
- Dashboard Streamlit implementado para visualização dos indicadores da camada Gold.
- O histórico validado contém apenas dois snapshots reais, insuficientes para análise de tendências.
- A aplicação não realiza monitoramento de tráfego aéreo em tempo real.
