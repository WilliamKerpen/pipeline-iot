FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# O diretório único mantém os caminhos iguais no container e na aplicação.
WORKDIR /app

COPY requirements.txt ./requirements.txt
COPY requirements-dev.txt ./requirements-dev.txt
RUN pip install --upgrade pip && pip install -r requirements.txt -r requirements-dev.txt

COPY . /app

EXPOSE 8501

# O Compose substitui este comando para executar a carga inicial antes da interface.
CMD ["streamlit", "run", "src/dashboard.py", "--server.address", "0.0.0.0", "--server.port", "8501"]
