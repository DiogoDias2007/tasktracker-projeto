# ---------------------------------------------------------------
# TaskTracker - imagem Docker (Fase 3)
# Empacota a aplicação CLI e tudo de que ela precisa para rodar
# de forma idêntica em qualquer máquina.
# ---------------------------------------------------------------

# Base leve: Debian mínimo com Python 3.11 (o TaskTracker usa só a biblioteca padrão)
FROM python:3.11-slim

# Pasta central de operações dentro do container
WORKDIR /app

# PYTHONUNBUFFERED=1  -> mostra cada print na hora, sem esperar o buffer encher
# PYTHONDONTWRITEBYTECODE=1 -> não gera arquivos .pyc dentro da imagem
# TASKTRACKER_ARQUIVO -> grava as tarefas numa pasta própria para dados
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TASKTRACKER_ARQUIVO=/app/dados/tasktracker.json

# Usuário comum (sem poderes de administrador) e a pasta onde ficam os dados
RUN useradd --create-home --shell /usr/sbin/nologin tasktracker \
    && mkdir -p /app/dados \
    && chown tasktracker:tasktracker /app/dados

# Injeta o código da aplicação no container
COPY src/ /app/src/

# Daqui em diante tudo roda como o usuário comum
USER tasktracker

# Gatilho que dispara a execução: abre o menu do TaskTracker
CMD ["python", "src/main.py"]
