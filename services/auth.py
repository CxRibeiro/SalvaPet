"""Autenticação e gestão de usuários (níveis 1 e 2).

- Nível 1: pessoa física, identificada por CPF. Acesso a Início, PetFinder
  e AdotaPet.
- Nível 2: ONG/petshop contratante, identificada por CNPJ. Acesso a todas
  as páginas.

Observação: o hash de senha (PBKDF2-SHA256 + salt) e a validação de
documentos atendem a um contexto didático/de aplicação. Não substituem uma
camada de segurança de produção (rate limiting, verificação de e-mail, etc.).
"""
from __future__ import annotations

import hashlib
import os
import re
from typing import Optional

from database.db import get_connection
from utils.constants import CIDADE_ATENDIDA

NIVEL_PESSOA = 1
NIVEL_ORG = 2

_ITERACOES = 120_000


# ---------------------------------------------------------------------------
# Senha
# ---------------------------------------------------------------------------
def hash_senha(senha: str, salt: Optional[bytes] = None) -> str:
    """Gera 'salt$hash' usando PBKDF2-HMAC-SHA256."""
    if salt is None:
        salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt, _ITERACOES)
    return salt.hex() + "$" + dk.hex()


def verificar_senha(senha: str, armazenado: str) -> bool:
    try:
        salt_hex, _ = armazenado.split("$", 1)
        salt = bytes.fromhex(salt_hex)
    except (ValueError, TypeError):
        return False
    return hash_senha(senha, salt) == armazenado


# ---------------------------------------------------------------------------
# Validação de documentos
# ---------------------------------------------------------------------------
def _so_digitos(valor: str) -> str:
    return re.sub(r"\D", "", valor or "")


def validar_cpf(cpf: str) -> bool:
    cpf = _so_digitos(cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for i in (9, 10):
        soma = sum(int(cpf[j]) * ((i + 1) - j) for j in range(i))
        dig = (soma * 10) % 11
        dig = 0 if dig == 10 else dig
        if dig != int(cpf[i]):
            return False
    return True


def validar_cnpj(cnpj: str) -> bool:
    """Confere somente os 14 números, aceitando a pontuação do CNPJ."""
    numeros = re.sub(r"[./\-\s]", "", cnpj or "")
    return re.fullmatch(r"[0-9]{14}", numeros) is not None


def formatar_documento(doc: str, nivel: int) -> str:
    d = _so_digitos(doc)
    if nivel == NIVEL_PESSOA and len(d) == 11:
        return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"
    if nivel == NIVEL_ORG and len(d) == 14:
        return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}"
    return doc


# ---------------------------------------------------------------------------
# Usuários
# ---------------------------------------------------------------------------
def criar_usuario(nome: str, email: str, senha: str, nivel: int, documento: str,
                  telefone: str = "", endereco: str = "", cidade: str = "",
                  abrigo_id: Optional[int] = None, nome_ong: str = "") -> int:
    """Cria um usuário. Lança ValueError com mensagem amigável em caso de erro."""
    nome = (nome or "").strip()
    email = (email or "").strip().lower()
    nome_ong = (nome_ong or "").strip()
    documento_num = _so_digitos(documento)

    if not nome and nivel != NIVEL_ORG:
        raise ValueError("Informe o nome.")
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        raise ValueError("E-mail inválido.")
    if len(senha or "") < 6:
        raise ValueError("A senha deve ter ao menos 6 caracteres.")
    if nivel == NIVEL_PESSOA and not validar_cpf(documento_num):
        raise ValueError("CPF inválido.")
    if nivel == NIVEL_ORG and not validar_cnpj(documento):
        raise ValueError("Informe um CNPJ com exatamente 14 números, sem letras.")
    if nivel == NIVEL_ORG and abrigo_id is None and not nome_ong:
        raise ValueError("Informe o nome da ONG / petshop.")
    if cidade and cidade.strip() != CIDADE_ATENDIDA:
        raise ValueError("O Salva Pet atende apenas a cidade de São Paulo.")
    cidade = CIDADE_ATENDIDA

    conn = get_connection()
    try:
        if nivel == NIVEL_ORG and abrigo_id is not None:
            abrigo = conn.execute(
                "SELECT 1 FROM abrigos WHERE id = ? AND cidade = ?",
                (abrigo_id, CIDADE_ATENDIDA),
            ).fetchone()
            if not abrigo:
                raise ValueError("Selecione um abrigo da cidade de São Paulo.")

        existe = conn.execute(
            "SELECT 1 FROM usuarios WHERE email = ? OR documento = ?",
            (email, documento_num),
        ).fetchone()
        if existe:
            raise ValueError("Já existe um usuário com este e-mail ou documento.")

        # Para nível 2, cria também um abrigo vinculado (aparece no mapa/adoção).
        if nivel == NIVEL_ORG and abrigo_id is None:
            cur = conn.execute(
                "INSERT INTO abrigos (nome, cidade, telefone, email, endereco) "
                "VALUES (?, ?, ?, ?, ?)",
                (nome_ong, cidade or "", telefone or "", email, endereco or ""),
            )
            abrigo_id = cur.lastrowid

        cur = conn.execute(
            "INSERT INTO usuarios "
            "(nome, email, senha_hash, nivel, documento, telefone, endereco, "
            " cidade, abrigo_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (nome, email, hash_senha(senha), nivel, documento_num,
             telefone or None, endereco or None, cidade or None, abrigo_id),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def obter_ong_usuario(usuario_id: int) -> Optional[dict]:
    """Consulta a ONG da conta no banco, inclusive para sessões já abertas."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT ab.* FROM usuarios u "
            "JOIN abrigos ab ON ab.id = u.abrigo_id "
            "WHERE u.id = ? AND u.nivel = ? AND ab.cidade = ?",
            (usuario_id, NIVEL_ORG, CIDADE_ATENDIDA),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def autenticar(email: str, senha: str) -> Optional[dict]:
    """Retorna o usuário (dict) se as credenciais baterem, senão None."""
    email = (email or "").strip().lower()
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM usuarios WHERE email = ?", (email,)
        ).fetchone()
    finally:
        conn.close()

    if row and verificar_senha(senha, row["senha_hash"]):
        u = dict(row)
        u.pop("senha_hash", None)
        return u
    return None
