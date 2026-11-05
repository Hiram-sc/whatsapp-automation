import unittest

from backend import status


class StatusTest(unittest.TestCase):
    def setUp(self):
        status.resetar_estado()

    def test_reserva_unica_da_automacao(self):
        self.assertTrue(status.reservar_automacao(3))

        estado = status.obter_status()
        self.assertEqual(estado["automacao"], "iniciando")
        self.assertEqual(estado["total"], 3)
        self.assertTrue(status.automacao_ativa())

        self.assertFalse(status.reservar_automacao(1))
        self.assertEqual(status.obter_status()["total"], 3)

    def test_fluxo_de_contagem(self):
        status.reservar_automacao(2)
        status.marcar_em_execucao()
        status.registrar_envio()
        status.registrar_envio()
        status.finalizar_automacao()

        estado = status.obter_status()
        self.assertEqual(estado["automacao"], "finalizada")
        self.assertEqual(estado["mensagens_enviadas"], 2)
        self.assertFalse(status.automacao_ativa())

    def test_erro_registra_detalhe(self):
        status.reservar_automacao(1)
        status.marcar_em_execucao()
        status.falhar_automacao("Falha de teste")

        estado = status.obter_status()
        self.assertEqual(estado["automacao"], "erro")
        self.assertEqual(estado["automacao_detalhe"], "Falha de teste")

    def test_conexao(self):
        status.definir_conexao("conectado")
        self.assertEqual(status.obter_status()["conexao"], "conectado")

        status.definir_conexao("erro")
        self.assertEqual(status.obter_status()["conexao"], "erro")


if __name__ == "__main__":
    unittest.main()
