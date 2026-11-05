import tempfile
import unittest
from pathlib import Path

import pandas as pd

from backend.consumer import consumir_planilha


class ConsumirPlanilhaTest(unittest.TestCase):
    def _salvar_planilha(self, diretorio: str, dados: dict) -> Path:
        caminho = Path(diretorio) / "planilha.xlsx"
        pd.DataFrame(dados).to_excel(caminho, index=False)
        return caminho

    def test_planilha_valida(self):
        with tempfile.TemporaryDirectory() as diretorio:
            caminho = self._salvar_planilha(
                diretorio,
                {
                    "PRODUTO": ["Fone"],
                    "VALOR": ["129,90"],
                    "CUPOM": ["SOM10"],
                    "LINK": ["https://exemplo.com/produto"],
                },
            )

            dados = consumir_planilha(caminho)

            self.assertEqual(len(dados), 1)
            self.assertEqual(dados[0]["produto"], "Fone")
            self.assertAlmostEqual(dados[0]["valor"], 129.90)
            self.assertEqual(dados[0]["cupom"], "SOM10")
            self.assertEqual(dados[0]["link"], "https://exemplo.com/produto")

    def test_links_normalizados(self):
        with tempfile.TemporaryDirectory() as diretorio:
            caminho = self._salvar_planilha(
                diretorio,
                {
                    "PRODUTO": ["A", "B", "C", "D"],
                    "VALOR": [10, 20, 30, 40],
                    "CUPOM": ["A", "B", "C", "D"],
                    "LINK": [
                        "www.exemplo.com/produto",
                        "wa.me/5511999999999",
                        "http://exemplo.com",
                        "https://exemplo.com",
                    ],
                },
            )

            dados = consumir_planilha(caminho)

            self.assertEqual(
                [item["link"] for item in dados],
                [
                    "https://www.exemplo.com/produto",
                    "https://wa.me/5511999999999",
                    "http://exemplo.com",
                    "https://exemplo.com",
                ],
            )

    def test_colunas_obrigatorias_ausentes(self):
        with tempfile.TemporaryDirectory() as diretorio:
            caminho = self._salvar_planilha(
                diretorio,
                {
                    "PRODUTO": ["Fone"],
                    "VALOR": [129.90],
                },
            )

            with self.assertRaises(ValueError) as contexto:
                consumir_planilha(caminho)

            self.assertIn("CUPOM", str(contexto.exception))
            self.assertIn("LINK", str(contexto.exception))

    def test_planilha_vazia(self):
        with tempfile.TemporaryDirectory() as diretorio:
            caminho = self._salvar_planilha(
                diretorio,
                {
                    "PRODUTO": [],
                    "VALOR": [],
                    "CUPOM": [],
                    "LINK": [],
                },
            )

            with self.assertRaises(ValueError):
                consumir_planilha(caminho)

    def test_valores_invalidos(self):
        with tempfile.TemporaryDirectory() as diretorio:
            caminho = self._salvar_planilha(
                diretorio,
                {
                    "PRODUTO": ["Fone"],
                    "VALOR": ["abc"],
                    "CUPOM": [""],
                    "LINK": ["exemplo.com/produto"],
                },
            )

            with self.assertRaises(ValueError) as contexto:
                consumir_planilha(caminho)

            mensagem = str(contexto.exception)
            self.assertIn("VALOR inválido", mensagem)
            self.assertIn("CUPOM vazio", mensagem)
            self.assertIn("LINK inválido", mensagem)

    def test_arquivo_inexistente(self):
        with self.assertRaises(ValueError):
            consumir_planilha("arquivo-que-nao-existe.xlsx")


if __name__ == "__main__":
    unittest.main()
