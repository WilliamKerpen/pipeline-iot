# Pipeline IoT - Monitoramento de Temperatura

Este projeto faz parte da entrega na disciplina de Disruptive Architectures IOT Big Data e IA para o curso de ADS pela UniFECAF.
Este projeto realiza a ingestão de dados de sensores IoT em formato CSV, armazena os registros em PostgreSQL e apresenta um dashboard interativo em Streamlit para análise de temperatura, médias diárias e comparação entre períodos.
Foi utilizado o csv gerado pelo: (https://www.kaggle.com/datasets/atulanandjha/temperature-readings-iot-devices)

## 1. Objetivo

O objetivo geral do projeto é demonstrar uma arquitetura prática de pipeline IoT com:

- coleta de dados em arquivo CSV;
- processamento e limpeza dos registros;
- persistência em banco relacional PostgreSQL;
- criação de views analíticas;
- visualização em dashboard para tomada de decisão.

## 2. Tecnologias utilizadas

- Python 3.10+
- Pandas
- SQLAlchemy
- PostgreSQL 15
- Streamlit
- Docker
- Docker Compose
- psycopg2-binary

## 3. Estrutura do projeto

```text
Pipeline-IOT/
├── data/
│   └── temperature_readings.csv
├── src/
│   ├── db_connection.py
│   ├── ingest_csv.py
│   ├── create_views.sql
│   └── dashboard.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .gitignore
├── README.md
└── .env.example (se necessário)
```

## 4. Requisitos

Antes de executar o projeto, certifique-se de que o ambiente atende aos requisitos abaixo:

- Python 3.10 ou superior instalado
- Docker Desktop instalado e em execução
- Docker Compose habilitado
- Git instalado
- Acesso à internet para baixar dependências e imagens Docker

## 5. Clonando o projeto

Abra o terminal e execute:

```bash
git clone https://github.com/seu-usuario/Pipeline-IOT.git
cd Pipeline-IOT
```

Se o repositório for local, também pode usar:

```bash
git clone <caminho-do-repositorio>
cd Pipeline-IOT
```

## 6. Como executar o projeto

### Opção A: executar com Docker (recomendado)

Na raiz do projeto, digite no terminal:

```bash
docker compose up --build
```

Esse comando irá subir:

- banco PostgreSQL em `localhost:5432`
- dashboard Streamlit em `http://localhost:8501`

Acesse o dashboard no navegador em:

```text
http://localhost:8501
```

Para encerrar os containers:

```bash
docker compose down
```

Se quiser remover também os dados persistidos do banco:

```bash
docker compose down -v
```

### Opção B: executar localmente sem Docker

Crie um ambiente virtual:

```bash
python -m venv .venv
```

No Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

No macOS/Linux:

```bash
source .venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

Execute a ingestão:

```bash
python src/ingest_csv.py
```

Inicie o dashboard:

```bash
streamlit run src/dashboard.py
```

O dashboard ficará disponível em:

```text
http://localhost:8501
```

## 7. Fluxo de execução do sistema

1. O arquivo CSV localizado em `data/temperature_readings.csv` é lido;
2. Os dados são limpos e padronizados;
3. A tabela `temperature_readings` é criada no PostgreSQL;
4. As views analíticas são geradas via `src/create_views.sql`;
5. O dashboard Streamlit consulta os dados e apresenta métricas e gráficos.

## 8. Banco de dados e configuração

As configurações padrão do projeto são:

- usuário: `iot_user`
- senha: `iot_password`
- host: `localhost`
- porta: `5432`
- banco: `iot_db`

Essas configurações são definidas no projeto e usadas pela aplicação para se conectar ao PostgreSQL.
Caso voce queira usar como um projeto em producao, crie um .env e ou secrets e altere as variaveis de ambiente.

## 9. Funcionalidades do dashboard

O dashboard inclui:

- filtro por período;
- comparação entre períodos;
- média de temperatura por dia;
- temperatura máxima e mínima por dia;
- quantidade de leituras por dia;
- visão resumida do dia selecionado quando o filtro é específico.

## 10. Sessão de prints dos dashboards

Abaixo está o espaço reservado para incluir os prints do dashboard finalizado.

### Dashboard principal

![Dashboard principal](insira-o-caminho-da-imagem-aqui)

### Comparação entre períodos

![Comparação entre períodos](insira-o-caminho-da-imagem-aqui)

### Filtro por dia

![Filtro por dia](insira-o-caminho-da-imagem-aqui)

> Substitua os caminhos acima pelos arquivos de imagem reais do projeto antes de entregar a apresentação.

## 11. Comandos úteis

### Verificar containers

```bash
docker ps
```

### Ver logs do projeto

```bash
docker compose logs -f
```

### Reiniciar tudo

```bash
docker compose down
docker compose up --build
```

## 12. Observações finais

- O projeto foi pensado para demonstrar um pipeline prático de IoT com armazenamento em banco de dados e análise em dashboard.
- Os dados de exemplo estão em `data/temperature_readings.csv`.
- O arquivo `src/create_views.sql` gera automaticamente as consultas analíticas que alimentam o dashboard.
- O projeto está pronto para execução em ambiente local ou via Docker.

## 13. Como entregar o projeto

Para entregar a solução em aula ou em apresentação:

1. Garanta que o ambiente tenha Docker instalado e funcionando;
2. Faça o clone do repositório;
3. Execute `docker compose up --build`;
4. Abra `http://localhost:8501`;
5. Capture os prints dos dashboards;
6. Organize o material em apresentação com os resultados obtidos.

## 14. Referência de dataset

Para complementar os dados, você pode buscar exemplos de sensores IoT em datasets públicos, como por exemplo:

```text
https://www.kaggle.com/search?q=temperature+readings+iot
```

---

Projeto desenvolvido para demonstrar um pipeline de dados IoT com PostgreSQL + Streamlit + Docker.
