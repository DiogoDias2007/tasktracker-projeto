# TaskTracker

Sistema de gerenciamento de tarefas em linha de comando (CLI), escrito em Python 3.

Projeto da disciplina **Bootcamp II** — Análise e Desenvolvimento de Sistemas.
Autor: **Diogo de Oliveira Dias** (Turma B) · diogo.oliveira07@sempreceub.com

📺 **Vídeo da Fase 3 (Docker):** https://youtu.be/Xe2dOUZ-iUY
📺 **Vídeo da Fase 2 (CLI em Python):** https://youtu.be/4Ol3YwMUDJc

---

## 🐳 Como executar com Docker (Fase 3)

O TaskTracker está empacotado em uma imagem Docker. Assim ele roda de forma idêntica
em qualquer máquina, sem instalar Python. O único requisito é ter o
[Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows/macOS) ou o
Docker Engine (Linux) instalado e aberto.

Primeiro, baixe o projeto e entre na pasta:

```bash
git clone https://github.com/DiogoDias2007/tasktracker-projeto.git
cd tasktracker-projeto
```

### 1. Como construir a imagem

```bash
docker build -t tasktracker .
```

### 2. Como rodar o container em modo isolado

```bash
docker run -it --rm tasktracker
```

`-i` mantém a entrada do teclado aberta e `-t` cria um terminal virtual. Os dois são
necessários porque o menu usa `input()`. `--rm` apaga o container ao sair. Neste modo,
as tarefas não ficam salvas entre uma execução e outra.

### 3. Como rodar via orquestração (Recomendado)

```bash
docker compose run --rm tasktracker-app
```

O `docker-compose.yml` faz o mesmo que `-it` (com `stdin_open: true` e `tty: true`),
constrói a imagem se ela ainda não existir e guarda as tarefas no volume
`tasktracker-dados`. Por isso elas continuam lá na próxima execução.

> Use `docker compose run`, e não `docker compose up`. O `up` não conecta o seu teclado
> ao menu.

### Dicas

| Para… | Comando |
| :--- | :--- |
| Reconstruir a imagem depois de mudar o código | `docker compose build` |
| Repetir o teste de mesa com a data de 10/09/2026 | `docker compose run --rm -e TASKTRACKER_HOJE=2026-09-10 tasktracker-app` |
| Apagar as tarefas salvas e começar do zero | `docker compose down -v` |
| Ver a imagem criada | `docker images tasktracker` |

### Decisões técnicas

| No `Dockerfile` | Por quê |
| :--- | :--- |
| `FROM python:3.11-slim` | Base leve, com só o necessário. O TaskTracker usa apenas a biblioteca padrão do Python, então não há `pip install`. |
| `WORKDIR /app` | Pasta central da aplicação dentro do container. |
| `ENV PYTHONUNBUFFERED=1` | Cada mensagem aparece na hora, sem esperar o buffer do Python. Importante num programa interativo. |
| `ENV TASKTRACKER_ARQUIVO=/app/dados/tasktracker.json` | Separa os dados do código, para guardá-los num volume. |
| `RUN useradd …` + `USER tasktracker` | O programa roda como usuário comum, não como administrador (root). |
| `COPY src/ /app/src/` | Copia só o código. O `.dockerignore` deixa de fora `.git`, `docs` e `tests`. |
| `CMD ["python", "src/main.py"]` | Abre o menu quando o container inicia. |

O relógio do container usa o horário UTC (3 horas à frente de Brasília). Entre 21h e
meia-noite, o "hoje" do container já é o dia seguinte. Isso afeta só a regra R3, de não
aceitar data limite anterior a hoje.

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

## Como executar sem Docker

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
├── .gitignore                   # Arquivos que o Git ignora (base local, cache do Python)
├── .dockerignore                # Arquivos que ficam fora da imagem Docker
├── docs/
│   └── planejamento_logico.pdf  # Fase 1: planejamento lógico (mantido para rastreabilidade)
├── src/
│   └── main.py                  # Fase 2: programa principal (menu e sub-rotinas da seção 3.8)
├── tests/
│   └── test_tasktracker.py      # Fase 2: testes automatizados do teste de mesa
├── Dockerfile                   # Fase 3: receita da imagem (empacotar)
├── docker-compose.yml           # Fase 3: execução interativa (orquestrar)
└── README.md                    # Este arquivo
```

| Fase | Papel | Entrega |
| :---: | :--- | :--- |
| 1 | Arquiteto(a) de Software | Planejamento lógico e pseudocódigo (`docs/`) |
| 2 | Desenvolvedor(a) | Menu CLI e regras de negócio em Python (`src/`, `tests/`) |
| 3 | Engenheiro(a) DevOps | Imagem Docker e orquestração (`Dockerfile`, `docker-compose.yml`) |

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
`feature/consultas`, e a conteinerização da Fase 3 na branch `feature/docker`. As duas
foram integradas à `main` com um merge. Para ver o histórico:

```bash
git log --oneline --graph --all
```
