"""Regressões do vínculo com a ONG e de marcadores no mesmo local."""
from contextlib import closing
import base64
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import folium
from folium.plugins import MarkerCluster
import pandas as pd

from database import db
from pages_app.petfinder import _criar_mapa, _popup_html
from services import animals, auth
from utils.constants import CIDADE_ATENDIDA


class CadastroONGTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="salvapet-test-")
        self.database_patch = patch.object(
            db, "DB_PATH", str(Path(self.directory.name) / "teste.db")
        )
        self.database_patch.start()
        db.init_db()
        self.usuario_a = self.criar_ong("ONG A", "11222333000181", "a@example.test")
        self.usuario_b = self.criar_ong("ONG B", "04252011000110", "b@example.test")
        self.ong_a = auth.obter_ong_usuario(self.usuario_a)
        self.ong_b = auth.obter_ong_usuario(self.usuario_b)

    def tearDown(self):
        self.database_patch.stop()
        self.directory.cleanup()

    def criar_ong(self, nome_ong, documento, email):
        return auth.criar_usuario(
            nome="Responsável", email=email, senha="teste123",
            nivel=auth.NIVEL_ORG, documento=documento, nome_ong=nome_ong,
        )

    def test_nome_da_ong_e_responsavel_sao_independentes(self):
        usuario = auth.autenticar("a@example.test", "teste123")
        self.assertEqual(usuario["nome"], "Responsável")
        self.assertEqual(self.ong_a["nome"], "ONG A")
        self.assertEqual(usuario["abrigo_id"], self.ong_a["id"])
        self.assertEqual(self.ong_a["cidade"], CIDADE_ATENDIDA)

    def test_nome_da_ong_obrigatorio_sem_criar_registros_parciais(self):
        with closing(db.get_connection()) as conn:
            antes = conn.execute("SELECT COUNT(*) FROM abrigos").fetchone()[0]
        with self.assertRaisesRegex(ValueError, "nome da ONG"):
            auth.criar_usuario(
                nome="Responsável", email="nova@example.test", senha="teste123",
                nivel=auth.NIVEL_ORG, documento="11444777000161", nome_ong="   ",
            )
        with closing(db.get_connection()) as conn:
            self.assertEqual(
                conn.execute("SELECT COUNT(*) FROM abrigos").fetchone()[0], antes
            )

    def test_todos_os_status_usam_a_ong_da_conta(self):
        for usuario_id, ong in [(self.usuario_a, self.ong_a), (self.usuario_b, self.ong_b)]:
            for status in ["perdido", "encontrado", "para_adocao"]:
                with self.subTest(usuario=usuario_id, status=status):
                    animal_id = animals.cadastrar_animal(
                        {"nome": "Animal", "especie": "Gato", "status": status,
                         "bairro": "Pinheiros", "latitude": -23.56642, "longitude": -46.69479},
                        usuario_id=usuario_id,
                    )
                    animal = animals.obter_animal(animal_id)
                    self.assertEqual(animal["abrigo_id"], ong["id"])
                    self.assertEqual(animal["cidade"], CIDADE_ATENDIDA)
                    self.assertEqual(animal["status"], status)

    def test_cadastro_nao_permite_escolher_outra_ong(self):
        antes = len(animals.listar_animais())
        with self.assertRaisesRegex(ValueError, "ONG da sua conta"):
            animals.cadastrar_animal(
                {"especie": "Gato", "status": "perdido", "abrigo_id": self.ong_b["id"]},
                usuario_id=self.usuario_a,
            )
        self.assertEqual(len(animals.listar_animais()), antes)

    def test_popup_exibe_apenas_a_ong_do_animal(self):
        animal_id = animals.cadastrar_animal(
            {"nome": "Animal", "especie": "Gato", "status": "perdido",
             "bairro": "Liberdade", "data_evento": "2026-10-30"},
            usuario_id=self.usuario_a,
        )
        registros = animals.listar_animais()
        animal = registros.loc[registros["id"] == animal_id].iloc[0].to_dict()
        popup = _popup_html(animal)
        self.assertIn("ONG A", popup)
        self.assertNotIn("ONG B", popup)
        self.assertIn("30/10/2026", popup)
        self.assertIn("Liberdade — São Paulo", popup)

    def test_pessoa_fisica_e_conta_inexistente_nao_cadastram_animais(self):
        pessoa = auth.criar_usuario(
            nome="Pessoa", email="pessoa@example.test", senha="teste123",
            nivel=auth.NIVEL_PESSOA, documento="52998224725",
        )
        for usuario_id in [pessoa, -1]:
            with self.subTest(usuario=usuario_id), self.assertRaises(ValueError):
                animals.cadastrar_animal(
                    {"especie": "Gato", "status": "perdido"}, usuario_id=usuario_id
                )

    def test_ong_de_outra_cidade_nao_cadastra_animais(self):
        with closing(db.get_connection()) as conn:
            conn.execute("UPDATE abrigos SET cidade = 'Guarulhos' WHERE id = ?", (self.ong_a["id"],))
            conn.commit()
        with self.assertRaises(ValueError):
            animals.cadastrar_animal(
                {"especie": "Gato", "status": "perdido"}, usuario_id=self.usuario_a
            )


class MapaTests(unittest.TestCase):
    def test_animais_no_mesmo_ponto_permanecem_acessiveis_no_grupo(self):
        df = pd.DataFrame([
            {"nome": "sub", "status": "perdido", "latitude": -23.55052, "longitude": -46.633308},
            {"nome": "Cachorro Caramelo", "status": "perdido", "latitude": -23.55052, "longitude": -46.633308},
            {"nome": "Sem localização", "status": "perdido", "latitude": None, "longitude": None},
        ])
        mapa, quantidade = _criar_mapa(df)
        grupo = next(child for child in mapa._children.values() if isinstance(child, MarkerCluster))
        marcadores = [child for child in grupo._children.values() if isinstance(child, folium.Marker)]
        self.assertEqual(quantidade, 2)
        self.assertEqual(len(marcadores), 2)
        self.assertEqual(marcadores[0].location, marcadores[1].location)
        html = mapa.get_root().render()
        self.assertRegex(html, r'"spiderfyOnMaxZoom"\s*:\s*true')
        self.assertIn("L.markerClusterGroup", html)
        self.assertIn("sub", html)
        self.assertIn("Cachorro Caramelo", html)


class FotosTests(unittest.TestCase):
    def test_foto_local_e_incorporada_ao_popup(self):
        imagem = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aB1sAAAAASUVORK5CYII="
        )
        with tempfile.TemporaryDirectory(prefix="salvapet-foto-") as directory:
            caminho = Path(directory) / "foto.png"
            caminho.write_bytes(imagem)
            animal = {"nome": "Animal", "status": "perdido", "foto_path": str(caminho)}
            popup = _popup_html(animal)
            self.assertIn("data:image/png;base64,", popup)
            self.assertIn(base64.b64encode(imagem).decode("ascii"), popup)
            self.assertNotIn(str(caminho), popup)

    def test_foto_de_pasta_antiga_usa_o_arquivo_em_uploads(self):
        with tempfile.TemporaryDirectory(prefix="salvapet-foto-") as directory:
            caminho = Path(directory) / "foto.png"
            caminho.write_bytes(b"imagem de teste")
            animal = {"foto_path": r"C:\Users\Aluno\Desktop\teste\uploads\foto.png"}
            with patch.object(animals, "UPLOADS_DIR", directory):
                self.assertEqual(animals.resolver_foto(animal), str(caminho))


if __name__ == "__main__":
    unittest.main()
