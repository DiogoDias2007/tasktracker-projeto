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
# 3.8.4 Ordenar e listar
# ----------------------------------------------------------------------

def peso_prioridade(p):
    """Transforma o texto da prioridade em número para permitir comparação."""
    if p == "ALTA":
        return 3
    if p == "MEDIA":
        return 2
    if p == "BAIXA":
        return 1
    return 0


def prazo_para_ordenar(t):
    """Tarefa sem data limite fica depois das que têm prazo."""
    return t["data_limite"] or date.max


def vem_depois(anterior, atual):
    """True se 'anterior' deve ficar depois de 'atual' na lista."""
    peso_ant = peso_prioridade(anterior["prioridade"])
    peso_atu = peso_prioridade(atual["prioridade"])
    return peso_ant < peso_atu or (
        peso_ant == peso_atu and prazo_para_ordenar(anterior) > prazo_para_ordenar(atual)
    )


def ordenar_tarefas(lista):
    """Ordenação por inserção (seção 3.6).
    Critério principal: prioridade da mais alta para a mais baixa.
    Desempate: data limite mais próxima primeiro."""
    for i in range(1, len(lista)):
        atual = lista[i]
        j = i - 1
        while j >= 0 and vem_depois(lista[j], atual):
            lista[j + 1] = lista[j]
            j -= 1
        lista[j + 1] = atual


def esta_atrasada(t):
    # R9: atrasada = prazo já passou e a situação não é final
    return (
        t["situacao"] not in SITUACOES_FINAIS
        and t["data_limite"] is not None
        and t["data_limite"] < data_atual()
    )


def indicador_atraso(t):
    if esta_atrasada(t):
        return "ATRASADA"
    if t["situacao"] in SITUACOES_FINAIS:
        return "-"
    return "EM DIA"


def exibir_tabela(lista):
    print(f"{'ID':>4} | {'TÍTULO':<30} | {'PRIORIDADE':<10} | "
          f"{'SITUAÇÃO':<12} | {'DATA LIMITE':<11} | ATRASO")
    print("-" * 92)
    for t in lista:
        titulo = t["titulo"] if len(t["titulo"]) <= 30 else t["titulo"][:27] + "..."
        print(f"{t['id']:>4} | {titulo:<30} | {nome(t['prioridade']):<10} | "
              f"{nome(t['situacao']):<12} | {formatar_data(t['data_limite']):<11} | "
              f"{indicador_atraso(t)}")


def listar_tarefas():
    if not tarefas:
        print("Nenhuma tarefa cadastrada.")
        return
    ordenar_tarefas(tarefas)
    exibir_tabela(tarefas)
    print(f"Total exibido: {len(tarefas)} tarefa(s).")


# ----------------------------------------------------------------------
# 3.8.5 Buscar índice e mudar situação (ciclo de vida, seção 3.7)
# ----------------------------------------------------------------------

def buscar_indice_por_id(id_procurado):
    """Busca sequencial: devolve a posição na lista, ou -1 se não existir."""
    for i, t in enumerate(tarefas):
        if t["id"] == id_procurado:
            return i
    return -1


def localizar_tarefa():
    """Pede o identificador ao usuário e devolve o índice da tarefa, ou -1."""
    texto = ler("Identificador da tarefa: ")
    if not texto.isdigit():
        print("ERRO: o identificador deve ser um número inteiro.")
        return -1
    indice = buscar_indice_por_id(int(texto))
    if indice == -1:
        print("ERRO: tarefa não encontrada.")
    return indice


def transicao_valida(origem, destino):
    """Caminhos permitidos do ciclo de vida (tabela da seção 3.7)."""
    return (origem, destino) in {
        ("PENDENTE", "EM_ANDAMENTO"),
        ("PENDENTE", "CONCLUIDA"),
        ("PENDENTE", "CANCELADA"),
        ("EM_ANDAMENTO", "CONCLUIDA"),
        ("EM_ANDAMENTO", "CANCELADA"),
    }


def mudar_situacao(nova_situacao):
    indice = localizar_tarefa()
    if indice == -1:
        return
    tarefa = tarefas[indice]

    # Situações finais não mudam mais (R7)
    if tarefa["situacao"] in SITUACOES_FINAIS:
        print("ERRO: a tarefa já está encerrada e não pode ser alterada.")
        return

    if not transicao_valida(tarefa["situacao"], nova_situacao):
        print(f"ERRO: mudança inválida de {nome(tarefa['situacao'])} "
              f"para {nome(nova_situacao)}.")
        return

    tarefa["situacao"] = nova_situacao
    if nova_situacao == "CONCLUIDA":
        tarefa["data_conclusao"] = data_atual()   # R8

    salvar_dados()
    print(f"Situação atualizada para {nome(nova_situacao)}.")


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
    ("2", "Listar todas as tarefas", listar_tarefas),
    ("5", "Iniciar tarefa", lambda: mudar_situacao("EM_ANDAMENTO")),
    ("6", "Concluir tarefa", lambda: mudar_situacao("CONCLUIDA")),
    ("7", "Cancelar tarefa", lambda: mudar_situacao("CANCELADA")),
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
