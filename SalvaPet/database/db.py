"""Camada de acesso ao banco SQLite.

Responsável por criar a conexão, inicializar o schema e popular dados
de exemplo na primeira execução.
"""
from __future__ import annotations

import os
import sqlite3
from datetime import date, timedelta

# O banco fica na raiz do projeto, ao lado de app.py.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "petconnect.db")


def get_connection() -> sqlite3.Connection:
    """Abre uma conexão nova com row_factory configurado para dicts."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db() -> None:
    """Cria as tabelas caso não existam e popula o seed na primeira vez."""
    conn = get_connection()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS abrigos (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                nome      TEXT NOT NULL,
                cidade    TEXT NOT NULL,
                telefone  TEXT,
                email     TEXT,
                endereco  TEXT
            );

            CREATE TABLE IF NOT EXISTS usuarios (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                nome        TEXT NOT NULL,
                email       TEXT NOT NULL UNIQUE,
                senha_hash  TEXT NOT NULL,
                nivel       INTEGER NOT NULL,          -- 1 = pessoa física, 2 = ONG/petshop
                documento   TEXT NOT NULL UNIQUE,      -- CPF (nível 1) ou CNPJ (nível 2)
                telefone    TEXT,
                endereco    TEXT,
                cidade      TEXT,
                abrigo_id   INTEGER,                   -- vínculo do nível 2 com seu abrigo
                criado_em   TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (abrigo_id) REFERENCES abrigos (id)
            );

            CREATE TABLE IF NOT EXISTS animais (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                nome          TEXT,
                especie       TEXT NOT NULL,
                raca          TEXT,
                porte         TEXT,
                sexo          TEXT,
                idade_anos    REAL,
                cor           TEXT,
                descricao     TEXT,
                status        TEXT NOT NULL,
                cidade        TEXT,
                bairro        TEXT,
                latitude      REAL,
                longitude     REAL,
                data_evento   TEXT,
                foto_url      TEXT,
                foto_path     TEXT,
                contato_nome  TEXT,
                contato_tel   TEXT,
                abrigo_id     INTEGER,
                tutor_nome    TEXT,
                tutor_tel     TEXT,
                criado_em     TEXT DEFAULT (datetime('now')),
                atualizado_em TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (abrigo_id) REFERENCES abrigos (id)
            );

            CREATE TABLE IF NOT EXISTS historico (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                animal_id  INTEGER NOT NULL,
                evento     TEXT NOT NULL,
                detalhe    TEXT,
                criado_em  TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (animal_id) REFERENCES animais (id)
            );
            """
        )
        conn.commit()

        # Migração leve: garante que colunas novas existam em bancos antigos.
        _migrar_colunas(conn)

        # Popula apenas se o banco ainda estiver vazio.
        count = conn.execute("SELECT COUNT(*) AS c FROM animais").fetchone()["c"]
        if count == 0:
            _seed(conn)
    finally:
        conn.close()


def _migrar_colunas(conn: sqlite3.Connection) -> None:
    """Adiciona colunas introduzidas depois da criação inicial do banco.

    Mantém compatibilidade com bancos 'petconnect.db' já existentes, sem
    precisar apagar o arquivo.
    """
    colunas = {row["name"] for row in conn.execute("PRAGMA table_info(animais)")}
    if "foto_path" not in colunas:
        conn.execute("ALTER TABLE animais ADD COLUMN foto_path TEXT")
        conn.commit()
    if "bairro" not in colunas:
        conn.execute("ALTER TABLE animais ADD COLUMN bairro TEXT")
        conn.commit()

    colunas_abrigo = {row["name"] for row in conn.execute("PRAGMA table_info(abrigos)")}
    if "endereco" not in colunas_abrigo:
        conn.execute("ALTER TABLE abrigos ADD COLUMN endereco TEXT")
        conn.commit()


def _seed(conn: sqlite3.Connection) -> None:
    """Insere abrigos e animais de exemplo para o app já abrir com dados."""
    abrigos = [
        ("ONG Patas Felizes", "São Paulo", "(11) 90000-0001",
         "contato@patasfelizes.org", "Rua das Acácias, 120 - Pinheiros"),
        ("Abrigo Amigo Fiel", "São Paulo", "(11) 90000-0002",
         "adote@amigofiel.org", "Av. Brasil, 4500 - Jardins"),
        ("Lar Temporário Miau", "São Paulo", "(11) 90000-0003",
         "miau@lartemporario.org", "Rua dos Gatos, 33 - Centro"),
    ]
    conn.executemany(
        "INSERT INTO abrigos (nome, cidade, telefone, email, endereco) "
        "VALUES (?, ?, ?, ?, ?)",
        abrigos,
    )

    hoje = date.today()

    def d(dias_atras: int) -> str:
        return (hoje - timedelta(days=dias_atras)).isoformat()

    # status, nome, especie, raca, porte, sexo, idade, cor, descricao,
    # cidade, bairro, lat, lon, data_evento, foto_url, foto_path, contato_nome, contato_tel,
    # abrigo_id, tutor_nome, tutor_tel
    animais = [
        ("perdido", "Thor", "Cachorro", "Labrador", "Grande", "Macho", 3, "Caramelo",
         "Coleira azul, muito dócil. Sumiu perto do parque.",
         "São Paulo", "Bela Vista", -23.5610, -46.6560, d(5),
         "https://placedog.net/500/400?id=1", None, "Marina", "(11) 98888-1111",
         None, None, None),
        ("perdido", "Mel", "Gato", "SRD", "Pequeno", "Fêmea", 2, "Tricolor",
         "Assustada, fugiu pela janela. Tem micro-chip.",
         "São Paulo", "República", -23.5450, -46.6400, d(2),
         None, "assets/exemplos/gata_tricolor.jpg", "Rafael", "(11) 97777-2222",
         None, None, None),
        ("encontrado", None, "Cachorro", "SRD", "Médio", "Macho", None, "Preto",
         "Encontrado vagando, sem coleira, aparenta boa saúde.",
         "São Paulo", "Liberdade", -23.5700, -46.6400, d(1),
         None, "assets/exemplos/cachorro_preto.jpg", "Protetora Ana", "(11) 96666-3333",
         None, None, None),
        ("para_adocao", "Luna", "Cachorro", "Poodle", "Pequeno", "Fêmea", 4, "Branco",
         "Castrada e vacinada. Ótima com crianças.",
         "São Paulo", "Sé", -23.5500, -46.6300, d(20),
         "https://placedog.net/500/400?id=3", None, None, None,
         1, None, None),
        ("para_adocao", "Simba", "Gato", "SRD", "Pequeno", "Macho", 1, "Laranja",
         "Brincalhão, usa caixa de areia. Vermifugado.",
         "São Paulo", "Bela Vista", -23.5600, -46.6450, d(15),
         "https://placekitten.com/501/400", None, None, None,
         2, None, None),
        ("para_adocao", "Bob", "Cachorro", "Vira-lata", "Grande", "Macho", 5, "Caramelo",
         "Calmo e companheiro. Ideal para apartamento grande ou casa.",
         "São Paulo", "Bela Vista", -23.56226, -46.64124, d(30),
         "https://placedog.net/500/400?id=4", None, None, None,
         3, None, None),
        ("adotado", "Nina", "Gato", "Siamês", "Pequeno", "Fêmea", 3, "Creme",
         "Adotada em família com outro gato.",
         "São Paulo", "Sé", -23.5520, -46.6350, d(45),
         None, "assets/exemplos/gata_siamesa.jpg", None, None,
         1, None, None),
    ]
    conn.executemany(
        """
        INSERT INTO animais
            (status, nome, especie, raca, porte, sexo, idade_anos, cor, descricao,
             cidade, bairro, latitude, longitude, data_evento, foto_url, foto_path,
             contato_nome, contato_tel, abrigo_id, tutor_nome, tutor_tel)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        animais,
    )
    conn.commit()
