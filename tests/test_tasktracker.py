"""
Testes automatizados do TaskTracker.

Reproduzem o teste de mesa da seção 3.9 do planejamento lógico
(data de hoje fixada em 10/09/2026) e verificam as regras R1 a R10.

Como executar (a partir da pasta do projeto):
    python -m unittest discover -s tests -v
"""

import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import main  # noqa: E402

HOJE = "2026-09-10"


class TesteBase(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        main.ARQUIVO = os.path.join(self.pasta.name, "tasktracker.json")
        main.tarefas.clear()
        main.proximo_id = 1
        self.env = patch.dict(os.environ, {"TASKTRACKER_HOJE": HOJE})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.pasta.cleanup()

    def executar(self, funcao, entradas):
        """Chama uma função do sistema simulando o que o usuário digita.
        Devolve tudo o que foi escrito na tela."""
        saida = io.StringIO()
        with patch("builtins.input", side_effect=entradas), redirect_stdout(saida):
            funcao()
        return saida.getvalue()

    def cadastrar(self, titulo, prioridade, limite, categoria=""):
        return self.executar(main.cadastrar_tarefa, [titulo, "", prioridade, categoria, limite])


class TesteDeMesa(TesteBase):
    """Os 12 passos da seção 3.9, na mesma ordem."""

    def test_doze_passos(self):
        # Passo 1
        saida = self.cadastrar("Entregar relatório", "Alta", "12/09/2026")
        self.assertIn("identificador 1", saida)
        self.assertEqual((len(main.tarefas), main.proximo_id), (1, 2))

        # Passos 2 e 3 (R1)
        saida = self.executar(main.cadastrar_tarefa,
                              ["Ok", "Revisar código", "", "Média", "", "20/09/2026"])
        self.assertIn("ERRO: o título é obrigatório", saida)
        self.assertIn("identificador 2", saida)
        self.assertEqual((len(main.tarefas), main.proximo_id), (2, 3))

        # Passos 4, 5 e 6 (R2 e R3)
        saida = self.executar(main.cadastrar_tarefa,
                              ["Estudar SQL", "", "Urgente", "Alta", "",
                               "01/09/2026", "15/09/2026"])
        self.assertIn("ERRO: a prioridade deve ser Alta, Média ou Baixa", saida)
        self.assertIn("ERRO: a data limite não pode ser anterior a hoje", saida)
        self.assertIn("identificador 3", saida)
        self.assertEqual((len(main.tarefas), main.proximo_id), (3, 4))

        # Passo 7: ordem id1 (Alta, 12/09), id3 (Alta, 15/09), id2 (Média, 20/09)
        self.executar(main.listar_tarefas, [])
        self.assertEqual([t["id"] for t in main.tarefas], [1, 3, 2])

        # Passo 8 (R8)
        saida = self.executar(lambda: main.mudar_situacao("CONCLUIDA"), ["1"])
        self.assertIn("Situação atualizada para Concluída", saida)
        tarefa1 = main.tarefas[main.buscar_indice_por_id(1)]
        self.assertEqual(tarefa1["data_conclusao"], date(2026, 9, 10))

        # Passo 9 (R7)
        saida = self.executar(main.editar_tarefa, ["1"])
        self.assertIn("ERRO: tarefa encerrada não pode ser editada", saida)

        # Passo 10 (R10 e R6)
        saida = self.executar(main.excluir_tarefa, ["2", "SIM"])
        self.assertIn("Tarefa excluída", saida)
        self.assertEqual((len(main.tarefas), main.proximo_id), (2, 4))

        # Passo 11
        saida = self.executar(main.gerar_relatorio, [])
        self.assertIn("Total de tarefas .......: 2", saida)
        self.assertIn("Concluídas .............: 1", saida)
        self.assertIn("Pendentes ..............: 1", saida)
        self.assertIn("50,0%", saida)

        # Passo 12: dados gravados e recarregados
        main.salvar_dados()
        main.carregar_dados()
        self.assertEqual((len(main.tarefas), main.proximo_id), (2, 4))


class VerificacoesExtras(TesteBase):
    """As seis verificações extras da seção 3.10 e outras regras."""

    def test_reabrir_tarefa_concluida_e_recusado(self):
        self.cadastrar("Tarefa X", "Baixa", "")
        self.executar(lambda: main.mudar_situacao("CONCLUIDA"), ["1"])
        saida = self.executar(lambda: main.mudar_situacao("EM_ANDAMENTO"), ["1"])
        self.assertIn("ERRO: a tarefa já está encerrada", saida)
        self.assertEqual(main.tarefas[0]["situacao"], "CONCLUIDA")

    def test_buscar_identificador_inexistente(self):
        self.assertEqual(main.buscar_indice_por_id(99), -1)
        saida = self.executar(main.buscar_tarefa, ["99"])
        self.assertIn("ERRO: tarefa não encontrada", saida)

    def test_excluir_sem_sim_cancela(self):
        self.cadastrar("Tarefa X", "Baixa", "")
        saida = self.executar(main.excluir_tarefa, ["1", "sim, pode"])
        self.assertIn("Operação cancelada", saida)
        self.assertEqual(len(main.tarefas), 1)

    def test_tarefa_nasce_pendente_com_data_de_criacao(self):   # R4 e R5
        self.cadastrar("Tarefa X", "Média", "")
        t = main.tarefas[0]
        self.assertEqual(t["situacao"], "PENDENTE")
        self.assertEqual(t["data_criacao"], date(2026, 9, 10))
        self.assertEqual(t["id"], 1)

    def test_transicao_invalida(self):
        self.cadastrar("Tarefa X", "Média", "")
        self.executar(lambda: main.mudar_situacao("EM_ANDAMENTO"), ["1"])
        saida = self.executar(lambda: main.mudar_situacao("EM_ANDAMENTO"), ["1"])
        self.assertIn("ERRO: mudança inválida", saida)

    def test_id_nao_reaproveitado_apos_reabrir(self):   # R6 (ajuste da Fase 2)
        self.cadastrar("Tarefa 1", "Alta", "")
        self.cadastrar("Tarefa 2", "Alta", "")
        self.executar(main.excluir_tarefa, ["2", "SIM"])   # exclui a de maior id
        main.carregar_dados()                               # simula reabrir o programa
        self.cadastrar("Tarefa 3", "Alta", "")
        self.assertEqual(main.tarefas[-1]["id"], 3)

    def test_atrasada(self):   # R9
        self.cadastrar("Prazo curto", "Alta", "11/09/2026")
        self.cadastrar("Já feita", "Alta", "11/09/2026")
        self.executar(lambda: main.mudar_situacao("CONCLUIDA"), ["2"])
        with patch.dict(os.environ, {"TASKTRACKER_HOJE": "2026-09-14"}):
            saida = self.executar(main.listar_atrasadas, [])
        self.assertIn("Prazo curto", saida)
        self.assertNotIn("Já feita", saida)
        self.assertIn("| 3", saida)   # 3 dias de atraso

    def test_filtro_por_situacao(self):
        self.cadastrar("Tarefa A", "Alta", "")
        self.cadastrar("Tarefa B", "Baixa", "")
        self.executar(lambda: main.mudar_situacao("CONCLUIDA"), ["1"])
        saida = self.executar(main.filtrar_tarefas, ["1", "pendente"])
        self.assertIn("Tarefa B", saida)
        self.assertNotIn("Tarefa A", saida)
        self.assertIn("Tarefas encontradas: 1", saida)

    def test_edicao_respeita_regras_do_cadastro(self):
        self.cadastrar("Tarefa X", "Baixa", "")
        saida = self.executar(main.editar_tarefa, ["1", "3", "Urgente", "Alta"])
        self.assertIn("ERRO: a prioridade deve ser", saida)
        self.assertEqual(main.tarefas[0]["prioridade"], "ALTA")


if __name__ == "__main__":
    unittest.main()
