# Aviation Data Intelligence — Plataforma de Inteligência Operacional do Tráfego Aéreo

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Apache Airflow](https://img.shields.io/badge/Apache_Airflow-2.9.3-017CEE?logo=apacheairflow&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?logo=streamlit&logoColor=white)
![Pytest](https://img.shields.io/badge/Pytest-23_passed_3_skipped-0A9EDC?logo=pytest&logoColor=white)
[![CI](https://github.com/rodrigodesouza7/aviation-data-intelligence/actions/workflows/ci.yml/badge.svg)](https://github.com/rodrigodesouza7/aviation-data-intelligence/actions/workflows/ci.yml)

Plataforma demonstrativa de **Engenharia de Dados e Business Intelligence** para coleta, processamento, análise e avaliação da qualidade de dados de tráfego aéreo provenientes da OpenSky Network.

O projeto integra **Python, PostgreSQL, Apache Airflow, Streamlit e GitHub Actions**, implementando uma arquitetura de dados em camadas Bronze, Silver e Gold, com ingestão periódica, reconciliação, reprocessamento e visualização analítica.

> **Escopo:** análise de snapshots históricos de aeronaves observadas. A plataforma não constitui um sistema de rastreamento em tempo real nem de controle de tráfego aéreo.

---

## 1. Visão Geral

### Problema de Negócio

Organizações que analisam informações do setor aéreo precisam transformar registros operacionais em indicadores confiáveis e interpretáveis.

Dados coletados de fontes externas podem apresentar diferenças de cobertura, campos ausentes, registros duplicados e intervalos irregulares de atualização.

Essas características dificultam responder a perguntas como:

- Quantas aeronaves foram observadas em determinada coleta?
- Como o volume observado varia entre snapshots?
- Qual é a disponibilidade de informações de posição e altitude?
- Quantos registros recebidos foram carregados na camada analítica?
- Os dados disponíveis são suficientes para apoiar uma análise exploratória?

### Solução

O **Aviation Data Intelligence** implementa um pipeline para coletar dados da OpenSky Network, armazená-los no PostgreSQL e disponibilizar indicadores consolidados em um dashboard Streamlit.

A solução contempla:

1. Ingestão de dados por API.
2. Persistência de payloads brutos.
3. Transformação em registros estruturados.
4. Agregação de indicadores analíticos.
5. Reconciliação e reprocessamento.
6. Orquestração com Apache Airflow.
7. Monitoramento da qualidade dos dados.
8. Visualização e exportação de indicadores.

### Objetivo

Demonstrar como uma arquitetura de Engenharia de Dados pode transformar dados aeronáuticos em informações úteis para análise operacional, com rastreabilidade, qualidade e automação.

### Público-alvo

Projeto demonstrativo direcionado a cenários de:

- Inteligência operacional do setor aéreo.
- Análise exploratória de tráfego aéreo.
- Engenharia e qualidade de dados.
- Business Intelligence e observabilidade de pipelines.

---

## 2. Tech Stack

### Linguagem e Processamento

| Tecnologia    | Aplicação                      |
| ------------- | ------------------------------ |
| Python        | Desenvolvimento do pipeline    |
| Pandas        | Manipulação e análise de dados |
| Requests      | Comunicação com a OpenSky API  |
| SQLAlchemy    | Integração com PostgreSQL      |
| Psycopg       | Driver PostgreSQL              |
| Python-dotenv | Configuração local             |

### Armazenamento

| Tecnologia | Aplicação                              |
| ---------- | -------------------------------------- |
| PostgreSQL | Persistência e processamento dos dados |
| SQL        | Consultas, agregações e validações     |
| JSONB      | Armazenamento dos payloads originais   |
| DBeaver    | Administração e inspeção do banco      |

### Orquestração e Infraestrutura

| Tecnologia           | Aplicação                            |
| -------------------- | ------------------------------------ |
| Apache Airflow 2.9.3 | Agendamento e execução dos pipelines |
| Docker               | Containerização do ambiente Airflow  |
| Docker Compose       | Gerenciamento dos serviços           |
| GitHub Actions       | Integração contínua                  |

### Analytics e Qualidade

| Tecnologia     | Aplicação                              |
| -------------- | -------------------------------------- |
| Streamlit      | Dashboard analítico                    |
| Pandas         | Preparação dos indicadores             |
| Pytest         | Testes automatizados                   |
| PostgreSQL SQL | Consultas de qualidade e reconciliação |

---

## 3. Arquitetura do Sistema

A plataforma utiliza uma arquitetura em camadas inspirada no padrão **Medallion Architecture**.

```text
                  OpenSky Network API
                           |
                           v
                Python — API Client
                           |
                           v
             +-------------------------+
             |         BRONZE          |
             |    bronze.raw_aviation  |
             |                         |
             |    Payloads JSONB       |
             +-------------------------+
                           |
                           v
             +-------------------------+
             |         SILVER          |
             |  silver.aircraft_states |
             |                         |
             |  Registros estruturados |
             +-------------------------+
                           |
                           v
             +-------------------------+
             |          GOLD           |
             | gold.air_traffic_summary|
             |                         |
             |  Indicadores agregados  |
             +-------------------------+
                           |
                           v
             +-------------------------+
             |   STREAMLIT DASHBOARD   |
             |                         |
             |  Operational Analytics  |
             +-------------------------+

       Apache Airflow — Orquestração
       Pytest — Testes automatizados
       GitHub Actions — Integração contínua
```

### Responsabilidades

**Bronze:** preserva os dados brutos obtidos da fonte externa, permitindo rastreabilidade e reprocessamento.

**Silver:** transforma os estados de aeronaves em registros estruturados, adequados para consultas SQL.

**Gold:** consolida indicadores por lote de observação, utilizados nas análises e visualizações.

**Dashboard:** apresenta indicadores operacionais, qualidade dos dados e histórico de snapshots.

### Separação dos Bancos

O ambiente utiliza dois contextos de armazenamento:

- **PostgreSQL analítico:** contém as tabelas Bronze, Silver e Gold.
- **PostgreSQL do Airflow:** armazena os metadados da orquestração.

O PostgreSQL de metadados do Airflow é executado em container separado do banco analítico local.

---

## 4. Modelo de Dados

### Schema Bronze

**Tabela:** `bronze.raw_aviation`

Responsável pelo armazenamento das respostas brutas da OpenSky.

Principais campos:

| Campo         | Descrição                  |
| ------------- | -------------------------- |
| `id`          | Identificador do lote      |
| `source`      | Origem dos dados           |
| `payload`     | Conteúdo original em JSONB |
| `ingested_at` | Horário da ingestão        |

A camada Bronze preserva os payloads para permitir auditoria e reprocessamento.

### Schema Silver

**Tabela:** `silver.aircraft_states`

Armazena os estados de aeronaves extraídos dos payloads.

Principais campos:

| Campo              | Descrição                      |
| ------------------ | ------------------------------ |
| `bronze_id`        | Referência ao lote de origem   |
| `icao24`           | Identificador ICAO da aeronave |
| `callsign`         | Indicativo de chamada          |
| `origin_country`   | País de origem informado       |
| `longitude`        | Longitude                      |
| `latitude`         | Latitude                       |
| `baro_altitude`    | Altitude barométrica           |
| `velocity`         | Velocidade                     |
| `observation_time` | Horário de observação          |
| `processed_at`     | Horário do processamento       |

### Schema Gold

**Tabela:** `gold.air_traffic_summary`

Consolida indicadores por lote.

| Campo                    | Descrição                     |
| ------------------------ | ----------------------------- |
| `bronze_id`              | Identificador do lote         |
| `observation_time`       | Horário da observação         |
| `total_aircraft`         | Total de aeronaves observadas |
| `aircraft_with_position` | Aeronaves com posição         |
| `aircraft_with_altitude` | Aeronaves com altitude        |
| `avg_altitude_m`         | Altitude média em metros      |
| `avg_velocity_ms`        | Velocidade média em m/s       |
| `processed_at`           | Horário do processamento      |

**Granularidade:** cada linha da Gold representa um lote consolidado.

Uma aeronave pode aparecer em diferentes lotes. Portanto, a soma dos totais não representa necessariamente aeronaves distintas.

---

## 5. Engenharia de Dados

### Ingestão

A ingestão utiliza a OpenSky Network API e autenticação configurada por variáveis de ambiente.

O processo:

1. Solicita os dados à API.
2. Recebe os estados de aeronaves.
3. Persiste o payload original na Bronze.
4. Disponibiliza os registros para transformação.

A disponibilidade das informações depende da API, de suas condições de acesso e da cobertura da fonte.

### Transformação Bronze → Silver

Os payloads JSONB são processados para extrair atributos estruturados das aeronaves.

O processo considera campos ausentes e regras de transformação necessárias ao armazenamento relacional.

### Transformação Silver → Gold

A camada Gold agrega os estados processados para produzir indicadores por snapshot.

Entre os indicadores estão:

- Total de aeronaves observadas.
- Quantidade de aeronaves com posição.
- Quantidade de aeronaves com altitude.
- Altitude média.
- Velocidade média.

### Reconciliação

O projeto possui uma etapa de reconciliação entre Silver e Gold.

A implementação utiliza transações PostgreSQL para preservar a consistência das operações de processamento.

### Reprocessamento

Os registros já armazenados na Bronze podem ser reprocessados sem realizar uma nova consulta à OpenSky.

Esse recurso permite reconstruir os dados derivados a partir dos payloads persistidos.

### Idempotência

As transformações utilizam mecanismos de tratamento de conflitos para evitar duplicações indevidas durante reexecuções.

A consistência do reprocessamento é coberta por testes automatizados.

---

## 6. Orquestração com Apache Airflow

O projeto implementa duas DAGs.

### Ingestão Agendada

**DAG:** `aviation_ingestion_scheduled_test`

Responsabilidades:

- Executar a ingestão OpenSky.
- Processar os dados nas camadas Bronze, Silver e Gold.
- Executar o pipeline a cada 30 minutos.
- Evitar execuções simultâneas da mesma DAG.
- Aplicar política de tentativa adicional em caso de falha.

Configurações principais:

| Parâmetro       | Configuração   |
| --------------- | -------------- |
| Schedule        | `*/30 * * * *` |
| Catchup         | `False`        |
| Max active runs | `1`            |
| Retries         | `1`            |
| Retry delay     | 5 minutos      |
| Task timeout    | 10 minutos     |

A DAG é criada pausada e precisa ser ativada no Airflow.

### Reprocessamento Manual

**DAG:** `aviation_reprocess_test`

Executa o reprocessamento Bronze → Silver → Gold sem consultar novamente a API.

O acionamento é manual.

### Proteção do Ambiente

As duas DAGs foram configuradas para operar exclusivamente no banco:

`aviation_data_intelligence_test`

Execuções com outro valor de `DB_NAME` são bloqueadas.

### Evidências de Execução

Na validação local realizada em novembro de 2026, foram observadas execuções bem-sucedidas das DAGs de ingestão e reprocessamento.

A execução do Airflow depende do ambiente local e não é reproduzida integralmente pelo workflow de CI.

---

## 7. Indicadores Implementados

Os indicadores foram definidos para responder a perguntas de negócio relacionadas à atividade aeronáutica observada e à qualidade da informação.

| Indicador                | Definição                                        | Finalidade                          |
| ------------------------ | ------------------------------------------------ | ----------------------------------- |
| Aeronaves observadas     | Total no snapshot                                | Avaliar o volume observado          |
| Variação entre snapshots | Diferença percentual entre coletas               | Identificar mudanças                |
| Cobertura de posição     | Aeronaves com posição / total                    | Avaliar completude geográfica       |
| Cobertura de altitude    | Aeronaves com altitude / total                   | Avaliar disponibilidade de altitude |
| Altitude média           | Média consolidada na Gold                        | Caracterizar o snapshot             |
| Velocidade média         | Média consolidada na Gold                        | Caracterizar o snapshot             |
| Estados recebidos        | Registros identificados na Bronze                | Avaliar volume de entrada           |
| Registros na Silver      | Registros estruturados persistidos               | Avaliar carregamento                |
| Não carregados           | Diferença calculada entre recebidos e carregados | Investigar divergências             |
| Taxa de carregamento     | Carregados / recebidos                           | Avaliar persistência                |

### Fórmulas

**Cobertura de posição**

```text
Cobertura de posição (%) =
    aeronaves com posição
    --------------------- × 100
      total de aeronaves
```

**Cobertura de altitude**

```text
Cobertura de altitude (%) =
    aeronaves com altitude
    ---------------------- × 100
      total de aeronaves
```

**Variação entre snapshots**

```text
Variação (%) =
    (valor atual - valor anterior)
    ------------------------------ × 100
             valor anterior
```

A variação é considerada indisponível quando não existe uma base anterior positiva para comparação.

**Taxa de carregamento**

```text
Taxa de carregamento (%) =
      registros na Silver
      ------------------- × 100
        estados recebidos
```

### Interpretação

Os indicadores descrevem as observações disponíveis na base.

Eles não comprovam, isoladamente:

- Crescimento ou redução do tráfego aéreo real.
- Congestionamento aeroportuário.
- Atrasos de voos.
- Capacidade operacional de aeroportos.
- Eficiência de rotas.

Essas análises exigiriam fontes de dados e critérios adicionais.

---

## 8. Dashboard — Operational Analytics

O dashboard foi desenvolvido em Streamlit para transformar os dados consolidados em informações interpretáveis.

A interface está organizada em três áreas.

### Visão Executiva

Apresenta:

- Aeronaves observadas.
- Variação em relação ao snapshot anterior.
- Cobertura de posição e altitude.
- Altitude e velocidade médias.
- Quantidade de snapshots analisados.
- Evolução histórica das observações.
- Interpretação das variações.

### Qualidade dos Dados

Apresenta:

- Estados recebidos na Bronze.
- Registros persistidos na Silver.
- Registros não carregados.
- Taxa de carregamento.
- Posição ausente.
- Coordenadas fora dos intervalos esperados.
- Indicadores de qualidade por lote.

Os diagnósticos de posição ausente ou inválida não significam necessariamente rejeição automática dos registros.

### Exploração Analítica

Permite:

- Filtrar os snapshots por período.
- Consultar o histórico consolidado.
- Identificar média e máximo observado por snapshot.
- Comparar indicadores entre coletas.
- Exportar resultados em CSV.

### Recursos Implementados

| Funcionalidade             | Disponibilidade     |
| -------------------------- | ------------------- |
| Filtro de período          | Implementado        |
| KPIs executivos            | Implementado        |
| Comparação entre snapshots | Implementado        |
| Indicadores de qualidade   | Implementado        |
| Histórico consolidado      | Implementado        |
| Exportação CSV             | Validada localmente |
| Cache de consultas         | Implementado        |

### Evidências Visuais

As capturas reais do dashboard devem ser adicionadas ao diretório `docs/images/` antes de ativar as referências abaixo.

<!--
![Visão Executiva](docs/images/dashboard-executive.png)

![Qualidade dos Dados](docs/images/dashboard-quality.png)

![Exploração Analítica](docs/images/dashboard-exploration.png)
-->

---

## 9. Qualidade e Integridade dos Dados

A qualidade é avaliada por consultas SQL e testes automatizados.

Entre as verificações realizadas estão:

- Integridade referencial entre Bronze e Silver.
- Integridade referencial entre Bronze e Gold.
- Consistência dos indicadores agregados.
- Detecção de grupos duplicados.
- Validação de campos estruturados.
- Reconciliação entre registros recebidos e processados.

### Resultado da Validação Local

Uma verificação consolidada realizada em novembro de 2026 apresentou:

| Verificação                | Resultado |
| -------------------------- | --------: |
| Lotes Bronze               |        11 |
| Registros Silver           |       783 |
| Registros Gold             |        11 |
| Registros Silver órfãos    |         0 |
| Registros Gold órfãos      |         0 |
| Campos nulos verificados   |         0 |
| Indicadores Gold inválidos |         0 |
| Totais divergentes         |         0 |
| Grupos duplicados          |         0 |

**Resultado:** aprovado nas verificações executadas.

Esses números representam um estado observado durante a validação, não valores fixos ou atualizados continuamente.

---

## 10. Testes Automatizados

O projeto utiliza Pytest para verificar componentes do pipeline.

A suíte contempla testes relacionados a:

- Validação da Bronze.
- Qualidade dos dados.
- Integridade da Gold.
- Transformação Silver.
- Pipeline de processamento.
- Reconciliação atômica.
- Reprocessamento.
- Comportamento com lotes vazios.
- Configuração da DAG agendada.

### Resultado Local

Validação realizada em novembro de 2026:

```text
23 passed, 3 skipped in 0.87s
```

**Resumo:**

- 23 testes aprovados.
- 3 testes ignorados.
- Nenhuma falha entre os testes executados.

Os testes ignorados não são considerados aprovados.

### Executar os Testes

Na raiz do repositório:

```bash
PYTHONPATH="$PWD/src" python -m pytest -q
```

---

## 11. CI/CD — GitHub Actions

O repositório utiliza GitHub Actions para executar verificações automatizadas.

**Workflow:** `.github/workflows/ci.yml`

O workflow é acionado em:

- Push para `main`.
- Pull requests direcionados à `main`.
- Execução manual.

### Etapas do Pipeline

1. Checkout do repositório.
2. Configuração do Python 3.12.
3. Instalação das dependências.
4. Inicialização de PostgreSQL 16.
5. Criação dos schemas e tabelas.
6. Inserção de dados sintéticos de teste.
7. Execução das transformações.
8. Execução dos testes Pytest.

### Ambiente de CI

O workflow utiliza um PostgreSQL temporário com dados sintéticos.

Não depende de credenciais reais da OpenSky para executar os testes.

### Evidência

Na verificação de 17/11/2026, a execução mais recente observada na branch `main` foi concluída com sucesso.

- Workflow: `Aviation Data Intelligence CI`
- Commit: `bcf4342`
- Duração: 52 segundos
- Resultado: sucesso

[Consultar execuções do GitHub Actions](https://github.com/rodrigodesouza7/aviation-data-intelligence/actions)

> O CI valida código, transformações e testes. Ele não comprova, por si só, a operação contínua do scheduler Airflow.

---

## 12. Ambiente de Desenvolvimento

O projeto foi desenvolvido e validado em ambiente local, utilizando:

- macOS.
- Python com ambiente virtual.
- PostgreSQL local.
- Docker Desktop.
- Apache Airflow em containers.
- DBeaver para consultas SQL.
- Streamlit para visualização.
- Git e GitHub para versionamento.

O Docker Compose gerencia os serviços do Airflow e seu banco de metadados.

O banco analítico PostgreSQL deve ser configurado separadamente no host.

---

## 13. Como Reproduzir

### Pré-requisitos

- Git.
- Python 3.12.
- PostgreSQL.
- Docker Desktop com Docker Compose.
- Credenciais válidas da OpenSky para executar a ingestão.
- DBeaver (opcional).

### 1. Clonar o Repositório

```bash
git clone https://github.com/rodrigodesouza7/aviation-data-intelligence.git

cd aviation-data-intelligence
```

### 2. Criar o Ambiente Virtual

```bash
python3 -m venv .venv

source .venv/bin/activate
```

Instalar as dependências:

```bash
python -m pip install -r requirements.txt
```

### 3. Configurar as Variáveis de Ambiente

Criar o arquivo local:

```bash
cp .env.example .env
```

Configurar os parâmetros conforme o ambiente PostgreSQL:

```dotenv
DB_HOST=localhost
DB_PORT=5432
DB_NAME=aviation_data_intelligence_test
DB_USER=SEU_USUARIO
DB_PASSWORD=SUA_SENHA

OPENSKY_CLIENT_ID=SEU_CLIENT_ID
OPENSKY_CLIENT_SECRET=SEU_CLIENT_SECRET
```

Os valores acima são exemplos e devem ser substituídos localmente.

Nunca versionar credenciais reais.

### 4. Preparar o Banco de Dados

Criar previamente o banco PostgreSQL e um usuário com as permissões necessárias.

Aplicar os scripts SQL disponíveis no repositório, na seguinte ordem:

```text
sql/00_create_schemas.sql

sql/bronze/01_create_raw_aviation.sql

sql/silver/01_create_aircraft_states.sql

sql/gold/01_create_air_traffic_summary.sql
```

A criação do banco e a configuração das permissões dependem do ambiente PostgreSQL utilizado.

### 5. Executar o Pipeline Python

Pipeline completo:

```bash
PYTHONPATH="$PWD/src" python -m aviation.pipeline
```

Reprocessamento sem nova consulta à API:

```bash
PYTHONPATH="$PWD/src" python -m aviation.pipeline --mode reprocess
```

### 6. Executar o Dashboard

```bash
PYTHONPATH="$PWD/src" python -m streamlit run dashboard/app.py
```

Acessar:

http://localhost:8501

### 7. Configurar o Airflow

Criar o arquivo de configuração do Docker Compose:

```bash
cp .env.compose.example .env.compose
```

Definir uma senha local para o PostgreSQL de metadados do Airflow.

Criar também o arquivo privado `.env.airflow`:

```dotenv
DB_HOST=host.docker.internal
DB_PORT=5432
DB_NAME=aviation_data_intelligence_test
DB_USER=SEU_USUARIO
DB_PASSWORD=SUA_SENHA

OPENSKY_CLIENT_ID=SEU_CLIENT_ID
OPENSKY_CLIENT_SECRET=SEU_CLIENT_SECRET
```

O banco analítico deve estar acessível a partir do container Airflow.

Iniciar os serviços:

```bash
docker compose --env-file .env.compose up -d --build
```

Verificar os containers:

```bash
docker compose --env-file .env.compose ps
```

Acessar a interface:

http://localhost:8080

Na interface do Airflow, conferir as DAGs e ativar manualmente a ingestão agendada quando apropriado.

### 8. Executar os Testes

```bash
PYTHONPATH="$PWD/src" python -m pytest -q
```

### 9. Encerrar o Airflow

```bash
docker compose --env-file .env.compose down
```

O comando interrompe os serviços sem excluir os volumes persistentes.

Não utilizar `down -v` quando for necessário preservar os dados dos volumes.

---

## 14. Estrutura do Projeto

```text
aviation-data-intelligence/
|
|-- .github/
|   `-- workflows/
|       `-- ci.yml
|
|-- dags/
|   |-- aviation_ingestion_scheduled_test.py
|   `-- aviation_reprocess_test.py
|
|-- dashboard/
|   `-- app.py
|
|-- sql/
|   |-- 00_create_schemas.sql
|   |-- bronze/
|   |-- silver/
|   `-- gold/
|
|-- src/
|   `-- aviation/
|       |-- database/
|       |   `-- connection.py
|       |
|       |-- ingestion/
|       |   |-- opensky_client.py
|       |   `-- save_bronze.py
|       |
|       |-- processing/
|       |   |-- bronze_to_silver.py
|       |   |-- silver_to_gold.py
|       |   `-- reconcile.py
|       |
|       |-- pipeline.py
|       `-- quality.py
|
|-- tests/
|   |-- test_atomic_reconciliation.py
|   |-- test_bronze_validation.py
|   |-- test_data_quality.py
|   |-- test_gold_empty_batch.py
|   |-- test_gold_integrity.py
|   |-- test_pipeline.py
|   |-- test_reprocessing.py
|   |-- test_scheduled_dag.py
|   `-- test_silver_data_quality.py
|
|-- .env.example
|-- .env.compose.example
|-- .gitignore
|-- compose.yaml
|-- Dockerfile
|-- requirements.txt
`-- README.md
```

Arquivos privados como `.env`, `.env.airflow` e `.env.compose` não devem ser enviados ao repositório.

---

## 15. Segurança e Boas Práticas

O projeto utiliza práticas de segurança proporcionais ao ambiente demonstrativo.

### Credenciais

Credenciais PostgreSQL e OpenSky são configuradas por variáveis de ambiente.

Os arquivos privados não devem ser versionados.

### Banco de Testes

As DAGs possuem proteção para impedir sua execução em bancos diferentes de `aviation_data_intelligence_test`.

### Controle de Execução

A ingestão agendada utiliza:

- Limitação de execuções simultâneas.
- Política de retry.
- Timeout de tarefa.
- Configuração de agendamento explícita.

### Integridade

O pipeline implementa mecanismos de reconciliação e tratamento de conflitos.

### Segurança do Repositório

Antes de disponibilizar o projeto publicamente, devem ser verificados:

- Ausência de credenciais nos arquivos.
- Ausência de segredos no histórico Git.
- Revogação de credenciais anteriormente expostas.
- Configuração correta do `.gitignore`.
- Ausência de dados pessoais ou confidenciais.

A remoção de um segredo do código não substitui sua revogação.

---

## 16. Aprendizados Técnicos

### Engenharia de Dados

- Integração com API externa.
- Autenticação e configuração de credenciais.
- Armazenamento de payloads JSONB.
- Transformações Bronze → Silver → Gold.
- Modelagem de dados para analytics.
- Processamento incremental.
- Reconciliação e reprocessamento.
- Integridade e rastreabilidade.

### Business Intelligence

- Definição de indicadores operacionais.
- Construção de métricas com granularidade explícita.
- Análise de snapshots históricos.
- Avaliação da completude dos dados.
- Construção de dashboard Streamlit.
- Filtros, tabelas e exportação CSV.
- Interpretação de indicadores e suas limitações.

### DevOps e DataOps

- Orquestração com Apache Airflow.
- Containerização com Docker.
- Configuração de serviços com Docker Compose.
- Automação de testes com GitHub Actions.
- Uso de ambientes isolados.
- Versionamento com Git e GitHub.

---

## 17. Resultados e Evidências

### Resultados Técnicos

| Componente                  | Evidência                             |
| --------------------------- | ------------------------------------- |
| Pipeline Bronze/Silver/Gold | Execução local validada               |
| Reconciliação               | Verificações de integridade aprovadas |
| Reprocessamento             | Execuções e testes bem-sucedidos      |
| Airflow                     | DAGs executadas com sucesso           |
| Dashboard                   | Interface funcional no ambiente local |
| Exportação CSV              | Funcionamento confirmado              |
| Testes                      | 23 passed, 3 skipped                  |
| GitHub Actions              | Workflow executado com sucesso        |

### Resultados Analíticos

O dashboard permite:

- Acompanhar o volume observado em diferentes coletas.
- Identificar variações entre snapshots.
- Avaliar cobertura de posição e altitude.
- Comparar registros recebidos e carregados.
- Consultar e exportar o histórico consolidado.

### Limitações

Os resultados demonstram funcionamento técnico, mas não comprovam ganhos financeiros, redução de custos ou melhorias operacionais em uma organização real.

---

## 18. Status do Projeto

| Componente                | Status                       |
| ------------------------- | ---------------------------- |
| Integração OpenSky        | Implementado                 |
| Armazenamento Bronze      | Implementado                 |
| Transformação Silver      | Implementado                 |
| Agregação Gold            | Implementado                 |
| Reconciliação             | Validada                     |
| Reprocessamento           | Validado                     |
| Ingestão agendada Airflow | Validada localmente          |
| Dashboard Streamlit       | Funcional localmente         |
| Exportação CSV            | Validada                     |
| Testes automatizados      | 23 aprovados, 3 ignorados    |
| CI/CD                     | Validado na versão publicada |
| Documentação final        | Em atualização               |

### Limitações Conhecidas

- A cobertura da OpenSky pode variar.
- Os snapshots não representam uma série contínua.
- Os dados não garantem observação de todas as aeronaves.
- A aplicação não realiza previsão de tráfego.
- A aplicação não calcula atrasos ou capacidade aeroportuária.
- O ambiente demonstrativo depende de infraestrutura local.
- A execução agendada exige que o Airflow esteja disponível.

---

## 19. Sobre o Autor

**Rodrigo de Souza Silva**

Profissional de Tecnologia da Informação, com formação em Sistemas de Informação e pós-graduação em Data Science, Machine Learning e Inteligência Artificial.

Interesses e atuação técnica em Engenharia de Dados, Análise de Dados, Business Intelligence, Python, SQL e Inteligência Artificial.

- **GitHub:** [rodrigodesouza7](https://github.com/rodrigodesouza7)
- **LinkedIn:** [rodrigodesouzasilva](https://www.linkedin.com/in/rodrigodesouzasilva/)

---

## 20. Licença

A licença de distribuição do projeto ainda precisa ser definida e adicionada ao repositório.

Até essa definição, não se deve presumir autorização para reutilização, modificação ou redistribuição do código.

---

**Aviation Data Intelligence** — Projeto demonstrativo de Engenharia de Dados, Business Intelligence e automação de pipelines.
