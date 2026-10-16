#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TaskTracker - gerenciador de tarefas em linha de comando (CLI).

Bootcamp II - Fase 2 (Etapa Intermediária)
Autor: Diogo de Oliveira Dias

Este programa é a tradução do planejamento lógico da Fase 1
(docs/planejamento_logico.pdf). Cada validação traz em comentário
a regra de negócio que aplica (R1 a R10, seção 2.3 do planejamento).

Como executar (a partir da pasta do projeto):
    python src/main.py
"""

import json
import os
import unicodedata
from datetime import date, datetime

# ----------------------------------------------------------------------
# Constantes e estado global (seção 3.8.1 do planejamento)
# ----------------------------------------------------------------------

MAX_TAREFAS = 1000
ARQUIVO = os.environ.get("TASKTRACKER_ARQUIVO", "tasktracker.json")

PRIORIDADES = ("ALTA", "MEDIA", "BAIXA")
SITUACOES = ("PENDENTE", "EM_ANDAMENTO", "CONCLUIDA", "CANCELADA")
SITUACOES_FINAIS = ("CONCLUIDA", "CANCELADA")

# Textos com acento, usados apenas na hora de exibir na tela.
NOMES = {
    "ALTA": "Alta",
    "MEDIA": "Média",
    "BAIXA": "Baixa",
    "PENDENTE": "Pendente",
    "EM_ANDAMENTO": "Em andamento",
    "CONCLUIDA": "Concluída",
    "CANCELADA": "Cancelada",
}

tarefas = []      # lista de tarefas; cada tarefa é um dicionário (REGISTRO Tarefa)
proximo_id = 1    # contador de identificadores, nunca reutilizado (R6)


# ----------------------------------------------------------------------
# Funções auxiliares
# ----------------------------------------------------------------------

def ler(mensagem):
    """Lê uma linha do teclado, já sem espaços nas pontas."""
    return input(mensagem).strip()


def normalizar(texto):
    """Deixa o texto pronto para comparação, ignorando acentos,
    maiúsculas/minúsculas e espaços extras.
    Exemplos: 'Média' -> 'MEDIA'; 'em andamento' -> 'EM_ANDAMENTO'."""
    sem_acento = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return "_".join(sem_acento.upper().split())


def data_atual():
    """Data de hoje. A variável de ambiente TASKTRACKER_HOJE (aaaa-mm-dd)
    permite fixar a data, o que é usado para reproduzir o teste de mesa."""
    fixa = os.environ.get("TASKTRACKER_HOJE")
    if fixa:
        return date.fromisoformat(fixa)
    return date.today()


def converter_data(texto):
    """Converte 'dd/mm/aaaa' em data. Devolve None se o texto for inválido."""
    try:
        return datetime.strptime(texto, "%d/%m/%Y").date()
    except ValueError:
        return None


def formatar_data(d):
    """Converte uma data em 'dd/mm/aaaa'; datas vazias viram '-'."""
    return d.strftime("%d/%m/%Y") if d else "-"


def nome(codigo):
    """Nome amigável de uma prioridade ou situação."""
    return NOMES.get(codigo, codigo)


# ----------------------------------------------------------------------
# Leitura validada dos campos (usada no cadastro e na edição)
# ----------------------------------------------------------------------

def ler_titulo():
    # R1: título obrigatório, de 3 a 100 caracteres
    while True:
        titulo = ler("Título: ")
        if 3 <= len(titulo) <= 100:
            return titulo
        print("ERRO: o título é obrigatório e deve ter de 3 a 100 caracteres.")


def ler_descricao():
    while True:
        descricao = ler("Descrição (opcional): ")
        if len(descricao) <= 500:
            return descricao
        print("ERRO: a descrição pode ter no máximo 500 caracteres.")


def ler_prioridade():
    # R2: prioridade somente Alta, Média ou Baixa
    while True:
        prioridade = normalizar(ler("Prioridade [Alta / Média / Baixa]: "))
        if prioridade in PRIORIDADES:
            return prioridade
        print("ERRO: a prioridade deve ser Alta, Média ou Baixa.")


def ler_categoria():
    return ler("Categoria (opcional): ")


def ler_data_limite():
    # R3: a data limite não pode ser anterior a hoje (dia da criação)
    while True:
        texto = ler("Data limite [dd/mm/aaaa] (Enter = sem prazo): ")
        if texto == "":
            return None
        limite = converter_data(texto)
        if limite is None:
            print("ERRO: data inválida. Use o formato dd/mm/aaaa.")
        elif limite < data_atual():
            print("ERRO: a data limite não pode ser anterior a hoje.")
        else:
            return limite


# ----------------------------------------------------------------------
# 3.8.3 Cadastrar tarefa
# ----------------------------------------------------------------------

def cadastrar_tarefa():
    global proximo_id

    if len(tarefas) >= MAX_TAREFAS:
        print("ERRO: base cheia, não é possível cadastrar.")
        return

    titulo = ler_titulo()
    descricao = ler_descricao()
    prioridade = ler_prioridade()
    categoria = ler_categoria()
    data_limite = ler_data_limite()

    # Campos que só o sistema preenche (R4 e R5)
    nova = {
        "id": proximo_id,
        "titulo": titulo,
        "descricao": descricao,
        "prioridade": prioridade,
        "situacao": "PENDENTE",
        "categoria": categoria,
        "data_criacao": data_atual(),
        "data_limite": data_limite,
        "data_conclusao": None,
    }

    tarefas.append(nova)
    proximo_id += 1

    salvar_dados()
    print(f"Tarefa cadastrada com o identificador {nova['id']}.")


# ----------------------------------------------------------------------
# Persistência (será implementada no commit "Adiciona persistência em arquivo")
# Por enquanto as tarefas ficam apenas na memória.
# ----------------------------------------------------------------------

def carregar_dados():
    pass


def salvar_dados():
    pass


# ----------------------------------------------------------------------
# 3.8.2 Programa principal
# ----------------------------------------------------------------------

MENU = [
    ("1", "Cadastrar tarefa", cadastrar_tarefa),
]


def exibir_menu():
    print()
    print("=" * 44)
    print("   TASKTRACKER - Gerenciador de Tarefas")
    print("=" * 44)
    for opcao, texto, _ in MENU:
        print(f"{opcao:>2} - {texto}")
    print(" 0 - Sair")


def main():
    carregar_dados()

    acoes = {opcao: acao for opcao, _, acao in MENU}
    try:
        while True:
            exibir_menu()
            opcao = ler("Escolha uma opção: ")
            if opcao == "0":
                print("Encerrando o sistema.")
                break
            acao = acoes.get(opcao)
            if acao is None:
                print("ERRO: opção inválida.")
            else:
                print()
                acao()
    except (KeyboardInterrupt, EOFError):
        print("\nInterrompido pelo usuário.")

    salvar_dados()
    print("Dados gravados. Sistema encerrado.")


if __name__ == "__main__":
    main()
