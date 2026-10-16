# TaskTracker

Sistema de gerenciamento de tarefas em linha de comando (CLI), escrito em Python 3.

Projeto da disciplina **Bootcamp II** — Análise e Desenvolvimento de Sistemas.
Autor: **Diogo de Oliveira Dias** (Turma B) · diogo.oliveira07@sempreceub.com

📺 **Vídeo de demonstração:** https://youtu.be/4Ol3YwMUDJc

---

## O problema

Sem um sistema, as tarefas ficam espalhadas em bilhetes, mensagens, e-mails e na memória.
O resultado é esquecimento, prioridade decidida "pela sensação", prazos que vencem sem
ninguém perceber e nenhuma noção do progresso.

O TaskTracker existe para responder com segurança a três perguntas:

1. **O que falta fazer?**
2. **O que fazer primeiro?**
3. **O que já está atrasado?**

## Funcionalidades

| Opção | O que faz |
| :---: | :--- |
| 1 | Cadastrar tarefa (título, descrição, prioridade, categoria e data limite) |
| 2 | Listar todas as tarefas, ordenadas por prioridade e data limite, com indicação de atraso |
| 3 | Buscar uma tarefa pelo identificador e ver todos os detalhes |
| 4 | Editar um campo de uma tarefa (com as mesmas validações do cadastro) |
| 5 / 6 / 7 | Iniciar, concluir ou cancelar uma tarefa, respeitando o ciclo de vida |
| 8 | Excluir uma tarefa (exige digitar `SIM`) |
| 9 | Filtrar por situação, prioridade ou categoria |
| 10 | Listar tarefas atrasadas com os dias de atraso |
| 11 | Relatório de produtividade: quantidade por situação, taxa de conclusão e tempo médio de execução |
| 0 | Sair, gravando os dados |

Os dados ficam no arquivo `tasktracker.json`, gravado automaticamente após cada alteração
e recarregado ao abrir o programa. Ao abrir, o sistema avisa se há tarefas atrasadas.

## Como executar

Requisito: **Python 3.8 ou superior** (não usa nenhuma biblioteca externa).

```bash
git clone https://github.com/DiogoDias2007/tasktracker-projeto.git
cd tasktracker-projeto
python src/main.py
```

> No macOS/Linux, se `python` não existir, use `python3`.

### Exemplo de uso

```
============================================
   TASKTRACKER - Gerenciador de Tarefas
============================================
 1 - Cadastrar tarefa
 2 - Listar todas as tarefas
 ...
 0 - Sair
Escolha uma opção: 2

  ID | TÍTULO                         | PRIORIDADE | SITUAÇÃO     | DATA LIMITE | ATRASO
--------------------------------------------------------------------------------------------
   1 | Entregar relatório             | Alta       | Pendente     | 12/09/2026  | EM DIA
   3 | Estudar SQL                    | Alta       | Pendente     | 15/09/2026  | EM DIA
   2 | Revisar código                 | Média      | Pendente     | 20/09/2026  | EM DIA
Total exibido: 3 tarefa(s).
```

## Regras de negócio

Cada regra está marcada no código com o seu código (`R1` a `R10`).

| Código | Regra |
| :---: | :--- |
| R1 | Título obrigatório, de 3 a 100 caracteres |
| R2 | Prioridade apenas Alta, Média ou Baixa |
| R3 | Data limite não pode ser anterior à data de criação |
| R4 | Toda tarefa começa como Pendente |
| R5 | O identificador é gerado pelo sistema |
| R6 | O identificador nunca é reaproveitado, nem depois de uma exclusão |
| R7 | Tarefa concluída ou cancelada não pode ser editada |
| R8 | A data de conclusão é preenchida pelo sistema |
| R9 | Atrasada = prazo vencido e situação diferente de Concluída/Cancelada |
| R10 | Exclusão só com confirmação `SIM`, sem desfazer |

### Ciclo de vida de uma tarefa

```
Pendente ──► Em andamento ──► Concluída
   │               │
   ├──────────────►├──────────► Cancelada
   └──────────────────────────► Concluída
```

Concluída e Cancelada são situações finais: não mudam mais.

## Testes

Os testes automatizados reproduzem os 12 passos do **teste de mesa** da Fase 1
(seção 3.9) e as verificações extras de cada regra:

```bash
python -m unittest discover -s tests -v
```

Para repetir o teste de mesa à mão com a mesma data do planejamento, fixe a data
de hoje com a variável `TASKTRACKER_HOJE`:

```bash
# macOS / Linux
TASKTRACKER_HOJE=2026-09-10 python src/main.py
# Windows (PowerShell)
$env:TASKTRACKER_HOJE="2026-09-10"; python src/main.py
```

## Estrutura do repositório

```
tasktracker-projeto/
├── README.md                    # Este arquivo
├── .gitignore                   # Arquivos que o Git ignora (base local, cache do Python)
├── docs/
│   └── planejamento_logico.pdf  # Planejamento lógico da Fase 1
├── src/
│   └── main.py                  # Programa principal (menu e sub-rotinas da seção 3.8)
└── tests/
    └── test_tasktracker.py      # Testes automatizados do teste de mesa
```

## Do planejamento ao código

O código segue o pseudocódigo da Fase 1 função por função
(`cadastrarTarefa` → `cadastrar_tarefa`, `ordenarTarefas` → `ordenar_tarefas`, e assim por diante),
inclusive a ordenação por inserção da seção 3.6 e a gravação segura em arquivo temporário.

Ajustes feitos durante a implementação:

- **R6 depois de reabrir o programa.** No planejamento, o contador era recalculado como
  "maior identificador + 1" ao carregar o arquivo. Isso falha quando a tarefa excluída é
  justamente a de maior número: ao reabrir, o número voltaria a ser usado. Agora o
  contador também é gravado no arquivo.
- **Data limite opcional.** A tabela 2.1.1 define a data limite como não obrigatória;
  basta apertar Enter. Tarefas sem prazo aparecem depois das que têm prazo e nunca ficam atrasadas.
- **Entrada mais tolerante.** Prioridade e situação aceitam acentos e minúsculas
  (`média`, `MEDIA`, `Média`).
- **Arquivo corrompido.** Se o `tasktracker.json` não puder ser lido, ele é preservado
  como `tasktracker.json.corrompido` em vez de ser sobrescrito.
- **Filtro ampliado.** A opção 9 filtra por situação, prioridade ou categoria, como
  prometido na seção 1.3.

## Histórico de desenvolvimento

O histórico de commits segue a sequência planejada na seção 4.3 do planejamento.
As consultas (busca, edição, filtros e relatório) foram desenvolvidas na branch
`feature/consultas` e integradas à `main` com um merge. Para ver o histórico:

```bash
git log --oneline --graph --all
```
