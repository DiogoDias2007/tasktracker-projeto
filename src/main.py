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
# 3.8.5 Excluir tarefa
# ----------------------------------------------------------------------

def excluir_tarefa():
    indice = localizar_tarefa()
    if indice == -1:
        return

    # R10: exclusão exige confirmação e não pode ser desfeita
    print(f"Excluir a tarefa '{tarefas[indice]['titulo']}'?")
    confirmacao = ler("Esta ação não pode ser desfeita. Digite SIM para confirmar: ")
    if confirmacao != "SIM":
        print("Operação cancelada.")
        return

    tarefas.pop(indice)
    # proximo_id não diminui: o identificador nunca se repete (R6)

    salvar_dados()
    print("Tarefa excluída.")


# ----------------------------------------------------------------------
# 3.8.6 Persistência em arquivo JSON
# ----------------------------------------------------------------------

CAMPOS_DATA = ("data_criacao", "data_limite", "data_conclusao")


def tarefa_para_json(t):
    """Converte as datas em texto (aaaa-mm-dd) para gravar no arquivo."""
    copia = dict(t)
    for campo in CAMPOS_DATA:
        copia[campo] = t[campo].isoformat() if t[campo] else None
    return copia


def tarefa_de_json(d):
    """Converte o texto gravado no arquivo de volta para datas."""
    t = dict(d)
    for campo in CAMPOS_DATA:
        t[campo] = date.fromisoformat(d[campo]) if d.get(campo) else None
    return t


def carregar_dados():
    global proximo_id

    tarefas.clear()
    proximo_id = 1

    if not os.path.exists(ARQUIVO):
        return

    try:
        with open(ARQUIVO, "r", encoding="utf-8") as f:
            dados = json.load(f)
        lidas = [tarefa_de_json(d) for d in dados["tarefas"]]
        contador_salvo = int(dados.get("proximo_id", 1))
    except (OSError, ValueError, KeyError, TypeError) as erro:
        # Arquivo corrompido: guarda uma cópia para não perder nada e começa vazio.
        copia = ARQUIVO + ".corrompido"
        os.replace(ARQUIVO, copia)
        print(f"AVISO: não foi possível ler {ARQUIVO} ({erro}).")
        print(f"O arquivo foi preservado como {copia} e o sistema começa vazio.")
        return

    tarefas.extend(lidas)

    # Recalcula o contador para nunca repetir identificador (R6).
    # Ajuste em relação à Fase 1: o contador também é gravado no arquivo.
    # Usando só o maior id existente, excluir a tarefa de maior número e
    # reabrir o programa faria esse número voltar a ser usado.
    maior_id = max((t["id"] for t in tarefas), default=0)
    proximo_id = max(contador_salvo, maior_id + 1)


def salvar_dados():
    # Grava num arquivo temporário e só então substitui o original,
    # para que uma falha no meio da gravação não estrague a base.
    temporario = ARQUIVO + ".tmp"
    dados = {
        "proximo_id": proximo_id,
        "total": len(tarefas),
        "tarefas": [tarefa_para_json(t) for t in tarefas],
    }
    with open(temporario, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    os.replace(temporario, ARQUIVO)


# ----------------------------------------------------------------------
# Buscar e editar tarefa
# ----------------------------------------------------------------------

def exibir_detalhes(t):
    atraso = "  (ATRASADA)" if esta_atrasada(t) else ""
    print(f"Identificador ....: {t['id']}")
    print(f"Título ...........: {t['titulo']}")
    print(f"Descrição ........: {t['descricao'] or '-'}")
    print(f"Prioridade .......: {nome(t['prioridade'])}")
    print(f"Categoria ........: {t['categoria'] or '-'}")
    print(f"Situação .........: {nome(t['situacao'])}{atraso}")
    print(f"Data de criação ..: {formatar_data(t['data_criacao'])}")
    print(f"Data limite ......: {formatar_data(t['data_limite'])}")
    print(f"Data de conclusão : {formatar_data(t['data_conclusao'])}")


def buscar_tarefa():
    indice = localizar_tarefa()
    if indice != -1:
        exibir_detalhes(tarefas[indice])


def editar_tarefa():
    indice = localizar_tarefa()
    if indice == -1:
        return
    tarefa = tarefas[indice]

    # R7: tarefa concluída ou cancelada só pode ser consultada ou excluída
    if tarefa["situacao"] in SITUACOES_FINAIS:
        print("ERRO: tarefa encerrada não pode ser editada.")
        return

    campos = {
        "1": ("titulo", ler_titulo),
        "2": ("descricao", ler_descricao),
        "3": ("prioridade", ler_prioridade),
        "4": ("categoria", ler_categoria),
        "5": ("data_limite", ler_data_limite),
    }
    print("Campos: 1-Título  2-Descrição  3-Prioridade  4-Categoria  5-Data limite")
    escolha = ler("Campo a alterar: ")
    if escolha not in campos:
        print("ERRO: campo inválido. Escolha de 1 a 5.")
        return

    chave, ler_campo = campos[escolha]
    tarefa[chave] = ler_campo()   # o novo valor passa pelas mesmas regras do cadastro

    salvar_dados()
    print("Tarefa atualizada.")


# ----------------------------------------------------------------------
# 3.8.2 Programa principal
# ----------------------------------------------------------------------

MENU = [
    ("1", "Cadastrar tarefa", cadastrar_tarefa),
    ("2", "Listar todas as tarefas", listar_tarefas),
    ("3", "Buscar tarefa por identificador", buscar_tarefa),
    ("4", "Editar tarefa", editar_tarefa),
    ("5", "Iniciar tarefa", lambda: mudar_situacao("EM_ANDAMENTO")),
    ("6", "Concluir tarefa", lambda: mudar_situacao("CONCLUIDA")),
    ("7", "Cancelar tarefa", lambda: mudar_situacao("CANCELADA")),
    ("8", "Excluir tarefa", excluir_tarefa),
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
