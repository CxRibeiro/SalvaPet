"""Regras de negócio e acesso aos dados dos animais.

Concentra o CRUD, as consultas usadas pelas telas, o upload de fotos e o
fluxo de integração entre o PetFinder (perdidos/encontrados) e o
AdotaPet (adoção).
"""
from __future__ import annotations

import base64
import mimetypes
import os
import uuid
from typing import Any, Optional

import pandas as pd

from database.db import BASE_DIR, get_connection
from services.auth import obter_ong_usuario
from utils.constants import (
    CIDADE_ATENDIDA,
    STATUS_ADOTADO,
    STATUS_ENCONTRADO,
    STATUS_PARA_ADOCAO,
    STATUS_PERDIDO,
    STATUS_REUNIDO,
)

# Pasta onde as fotos enviadas pelos usuários são guardadas.
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
EXEMPLOS_DIR = os.path.join(BASE_DIR, "assets", "exemplos")

# Extensões de imagem aceitas no upload.
EXTENSOES_IMAGEM = ("png", "jpg", "jpeg", "gif", "webp")


# ---------------------------------------------------------------------------
# Upload / resolução de fotos
# ---------------------------------------------------------------------------
def salvar_foto(arquivo: Any) -> Optional[str]:
    """Salva uma foto enviada (objeto de st.file_uploader) em uploads/.

    Recebe o UploadedFile do Streamlit (que tem .name e .getbuffer()) ou
    qualquer objeto com atributos equivalentes. Retorna o caminho absoluto
    do arquivo salvo, ou None se nada foi enviado.
    """
    if arquivo is None:
        return None

    os.makedirs(UPLOADS_DIR, exist_ok=True)

    nome_original = getattr(arquivo, "name", "foto")
    ext = nome_original.rsplit(".", 1)[-1].lower() if "." in nome_original else "png"
    if ext not in EXTENSOES_IMAGEM:
        ext = "png"

    nome_arquivo = f"{uuid.uuid4().hex}.{ext}"
    destino = os.path.join(UPLOADS_DIR, nome_arquivo)

    # UploadedFile expõe getbuffer(); um arquivo comum expõe read().
    if hasattr(arquivo, "getbuffer"):
        conteudo = arquivo.getbuffer()
    else:
        conteudo = arquivo.read()

    with open(destino, "wb") as f:
        f.write(conteudo)

    return destino


def _valor_str(valor) -> Optional[str]:
    """Normaliza um valor para str não-vazia, ou None.

    O pandas usa NaN (float) para células vazias; sem este tratamento o
    NaN passaria como 'verdadeiro' e quebraria os/str mais adiante.
    """
    if valor is None:
        return None
    if isinstance(valor, float) and pd.isna(valor):
        return None
    texto = str(valor).strip()
    return texto or None


def resolver_foto(animal: dict) -> Optional[str]:
    """Decide qual imagem exibir para um animal.

    Prioriza o arquivo enviado (foto_path); se não houver ou o arquivo tiver
    sumido, cai para a foto_url (link). Retorna None se não houver nenhuma.
    Trata None e NaN (pandas) com segurança.
    """
    caminho = _valor_str(animal.get("foto_path"))
    if caminho:
        candidatos = [
            caminho if os.path.isabs(caminho) else os.path.join(BASE_DIR, caminho),
            os.path.join(UPLOADS_DIR, os.path.basename(caminho.replace("\\", "/"))),
        ]
        for candidato in candidatos:
            if os.path.isfile(candidato):
                return candidato
    return _valor_str(animal.get("foto_url"))


def foto_para_mapa(animal: dict) -> Optional[str]:
    """Incorpora fotos locais no pop-up, que é exibido no navegador."""
    foto = resolver_foto(animal)
    if not foto:
        return None
    if foto.startswith(("https://", "http://")):
        return foto
    try:
        with open(foto, "rb") as arquivo:
            dados = arquivo.read()
    except OSError:
        return None
    tipo = mimetypes.guess_type(foto)[0]
    if not tipo or not tipo.startswith("image/"):
        return None
    return f"data:{tipo};base64,{base64.b64encode(dados).decode('ascii')}"


def legenda_foto(animal: dict) -> Optional[str]:
    foto = resolver_foto(animal)
    if foto and os.path.normcase(os.path.dirname(foto)) == os.path.normcase(EXEMPLOS_DIR):
        return "Foto ilustrativa do cadastro de exemplo."
    return None


# ---------------------------------------------------------------------------
# Leitura
# ---------------------------------------------------------------------------
def listar_animais(status: Optional[list[str]] = None) -> pd.DataFrame:
    """Retorna os animais de São Paulo, opcionalmente filtrando por status."""
    conn = get_connection()
    try:
        query = (
            "SELECT a.*, ab.nome AS abrigo_nome, ab.telefone AS abrigo_tel, "
            "ab.cidade AS abrigo_cidade, ab.endereco AS abrigo_endereco "
            "FROM animais a LEFT JOIN abrigos ab ON a.abrigo_id = ab.id "
            "WHERE a.cidade = ?"
        )
        params: list[Any] = [CIDADE_ATENDIDA]
        if status:
            placeholders = ",".join("?" for _ in status)
            query += f" AND a.status IN ({placeholders})"
            params.extend(status)
        query += " ORDER BY a.data_evento DESC, a.id DESC"
        return pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()


def obter_animal(animal_id: int) -> Optional[dict]:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM animais WHERE id = ? AND cidade = ?",
            (animal_id, CIDADE_ATENDIDA),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def listar_abrigos() -> pd.DataFrame:
    conn = get_connection()
    try:
        return pd.read_sql_query(
            "SELECT * FROM abrigos WHERE cidade = ? ORDER BY nome",
            conn, params=[CIDADE_ATENDIDA],
        )
    finally:
        conn.close()


def listar_organizacoes() -> pd.DataFrame:
    """Lista apenas as ONGs/petshops de São Paulo para ajudar no resgate."""
    return listar_abrigos()


def listar_historico(animal_id: int) -> pd.DataFrame:
    conn = get_connection()
    try:
        return pd.read_sql_query(
            "SELECT h.* FROM historico h "
            "JOIN animais a ON a.id = h.animal_id "
            "WHERE h.animal_id = ? AND a.cidade = ? ORDER BY h.id DESC",
            conn,
            params=[animal_id, CIDADE_ATENDIDA],
        )
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Escrita
# ---------------------------------------------------------------------------
def _validar_animal_da_cidade(conn, animal_id: int) -> None:
    if not conn.execute(
        "SELECT 1 FROM animais WHERE id = ? AND cidade = ?",
        (animal_id, CIDADE_ATENDIDA),
    ).fetchone():
        raise ValueError("Selecione um animal cadastrado na cidade de São Paulo.")


def _validar_abrigo_da_cidade(conn, abrigo_id: int) -> None:
    if not conn.execute(
        "SELECT 1 FROM abrigos WHERE id = ? AND cidade = ?",
        (abrigo_id, CIDADE_ATENDIDA),
    ).fetchone():
        raise ValueError("Selecione um abrigo da cidade de São Paulo.")


def cadastrar_animal(dados: dict, *, usuario_id: int) -> int:
    """Cadastra o animal na ONG da conta e registra a criação no histórico.

    O campo 'foto_path' deve ser preenchido previamente com salvar_foto(),
    e/ou 'foto_url' com um link. Ambos são opcionais.
    """
    if dados.get("cidade") and dados["cidade"].strip() != CIDADE_ATENDIDA:
        raise ValueError("O Salva Pet atende apenas a cidade de São Paulo.")
    ong = obter_ong_usuario(usuario_id)
    if not ong:
        raise ValueError("Sua conta precisa estar vinculada a uma ONG de São Paulo.")
    if dados.get("abrigo_id") is not None and dados["abrigo_id"] != ong["id"]:
        raise ValueError("O animal deve ser cadastrado na ONG da sua conta.")
    dados = {**dados, "cidade": CIDADE_ATENDIDA, "abrigo_id": ong["id"]}
    campos = [
        "nome", "especie", "raca", "porte", "sexo", "idade_anos", "cor",
        "descricao", "status", "cidade", "bairro", "latitude", "longitude",
        "data_evento", "foto_url", "foto_path", "contato_nome", "contato_tel",
        "abrigo_id", "tutor_nome", "tutor_tel",
    ]
    valores = [dados.get(c) for c in campos]
    placeholders = ",".join("?" for _ in campos)

    conn = get_connection()
    try:
        if dados.get("abrigo_id") is not None:
            _validar_abrigo_da_cidade(conn, dados["abrigo_id"])
        cur = conn.execute(
            f"INSERT INTO animais ({','.join(campos)}) VALUES ({placeholders})",
            valores,
        )
        animal_id = cur.lastrowid
        conn.execute(
            "INSERT INTO historico (animal_id, evento, detalhe) VALUES (?, ?, ?)",
            (animal_id, "cadastro", f"Cadastrado com status '{dados.get('status')}'"),
        )
        conn.commit()
        return int(animal_id)
    finally:
        conn.close()


def atualizar_foto(animal_id: int, foto_path: Optional[str] = None,
                   foto_url: Optional[str] = None) -> None:
    """Atualiza a foto de um animal já cadastrado (upload e/ou URL)."""
    conn = get_connection()
    try:
        _validar_animal_da_cidade(conn, animal_id)
        sets, params = [], []
        if foto_path is not None:
            sets.append("foto_path = ?")
            params.append(foto_path)
        if foto_url is not None:
            sets.append("foto_url = ?")
            params.append(foto_url)
        if not sets:
            return
        sets.append("atualizado_em = datetime('now')")
        params.append(animal_id)
        conn.execute(f"UPDATE animais SET {', '.join(sets)} WHERE id = ?", params)
        _registrar_evento(conn, animal_id, "foto_atualizada", "Foto do animal atualizada")
        conn.commit()
    finally:
        conn.close()


def _registrar_evento(conn, animal_id: int, evento: str, detalhe: str) -> None:
    conn.execute(
        "INSERT INTO historico (animal_id, evento, detalhe) VALUES (?, ?, ?)",
        (animal_id, evento, detalhe),
    )


def atualizar_status(animal_id: int, novo_status: str, detalhe: str = "") -> None:
    conn = get_connection()
    try:
        _validar_animal_da_cidade(conn, animal_id)
        conn.execute(
            "UPDATE animais SET status = ?, atualizado_em = datetime('now') WHERE id = ?",
            (novo_status, animal_id),
        )
        _registrar_evento(conn, animal_id, f"status:{novo_status}", detalhe)
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Integração PetFinder <-> AdotaPet
# ---------------------------------------------------------------------------
def buscar_possiveis_tutores(animal: dict) -> pd.DataFrame:
    """Para um animal encontrado, busca registros de 'perdido' compatíveis.

    A compatibilidade é simples e explicável: mesma espécie e, quando
    informados, mesmo porte/cor/cidade. Serve para a ONG conferir se o
    animal já possui um tutor procurando por ele.
    """
    conn = get_connection()
    try:
        df = pd.read_sql_query(
            "SELECT * FROM animais WHERE status = ? AND especie = ? AND cidade = ?",
            conn,
            params=[STATUS_PERDIDO, animal.get("especie"), CIDADE_ATENDIDA],
        )
    finally:
        conn.close()

    if df.empty:
        return df

    df["score"] = 0
    if animal.get("porte"):
        df.loc[df["porte"] == animal["porte"], "score"] += 1
    if animal.get("cor"):
        df.loc[
            df["cor"].fillna("").str.lower() == str(animal["cor"]).lower(), "score"
        ] += 1
    if animal.get("cidade"):
        df.loc[df["cidade"] == animal["cidade"], "score"] += 1

    return df.sort_values("score", ascending=False)


def reunir_com_tutor(animal_id: int, tutor_nome: str, tutor_tel: str,
                     registro_perdido_id: Optional[int] = None) -> None:
    """Marca o animal como reunido ao tutor identificado.

    Quando a reunião parte de uma correspondência com um registro de animal
    perdido, informe 'registro_perdido_id' para que esse registro também
    seja fechado (status 'reunido'). Assim nenhum dos dois lados continua
    aparecendo no mapa de perdidos/encontrados.
    """
    conn = get_connection()
    try:
        _validar_animal_da_cidade(conn, animal_id)
        if registro_perdido_id and registro_perdido_id != animal_id:
            _validar_animal_da_cidade(conn, registro_perdido_id)
        conn.execute(
            "UPDATE animais SET status = ?, tutor_nome = ?, tutor_tel = ?, "
            "atualizado_em = datetime('now') WHERE id = ?",
            (STATUS_REUNIDO, tutor_nome, tutor_tel, animal_id),
        )
        _registrar_evento(
            conn, animal_id, "reunido",
            f"Tutor identificado: {tutor_nome} ({tutor_tel})",
        )

        # Fecha também o registro 'perdido' correspondente, se houver e for
        # diferente do próprio animal.
        if registro_perdido_id and registro_perdido_id != animal_id:
            conn.execute(
                "UPDATE animais SET status = ?, atualizado_em = datetime('now') "
                "WHERE id = ?",
                (STATUS_REUNIDO, registro_perdido_id),
            )
            _registrar_evento(
                conn, registro_perdido_id, "reunido",
                f"Reunido via correspondência com o animal #{animal_id}.",
            )

        conn.commit()
    finally:
        conn.close()


def disponibilizar_para_adocao(animal_id: int, abrigo_id: int, obs: str = "") -> None:
    """Fluxo-chave da integração: um animal encontrado e sem tutor passa a
    estar disponível para adoção sob responsabilidade de uma ONG/abrigo.
    """
    conn = get_connection()
    try:
        _validar_animal_da_cidade(conn, animal_id)
        _validar_abrigo_da_cidade(conn, abrigo_id)
        conn.execute(
            "UPDATE animais SET status = ?, abrigo_id = ?, "
            "atualizado_em = datetime('now') WHERE id = ?",
            (STATUS_PARA_ADOCAO, abrigo_id, animal_id),
        )
        _registrar_evento(
            conn, animal_id, "disponibilizado_adocao",
            f"Sem tutor identificado. Encaminhado para adoção. {obs}".strip(),
        )
        conn.commit()
    finally:
        conn.close()


def registrar_adocao(animal_id: int, adotante_nome: str, adotante_tel: str) -> None:
    conn = get_connection()
    try:
        _validar_animal_da_cidade(conn, animal_id)
        conn.execute(
            "UPDATE animais SET status = ?, atualizado_em = datetime('now') WHERE id = ?",
            (STATUS_ADOTADO, animal_id),
        )
        _registrar_evento(
            conn, animal_id, "adotado",
            f"Adotado por {adotante_nome} ({adotante_tel})",
        )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Métricas para o dashboard
# ---------------------------------------------------------------------------
def metricas_gerais() -> dict:
    df = listar_animais()
    return {
        "total": len(df),
        "perdidos": int((df["status"] == STATUS_PERDIDO).sum()),
        "encontrados": int((df["status"] == STATUS_ENCONTRADO).sum()),
        "para_adocao": int((df["status"] == STATUS_PARA_ADOCAO).sum()),
        "adotados": int((df["status"] == STATUS_ADOTADO).sum()),
        "reunidos": int((df["status"] == STATUS_REUNIDO).sum()),
    }
