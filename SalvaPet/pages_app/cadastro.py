"""Tela de cadastro de animais (perdido, encontrado ou para adoção)."""
from __future__ import annotations

from datetime import date

import streamlit as st

from services.animals import cadastrar_animal, salvar_foto
from services.auth import obter_ong_usuario
from utils.animacoes import celebrar_com_patinhas
from utils.constants import (
    CIDADE_ATENDIDA,
    ESPECIES,
    PORTES,
    SEXOS,
    STATUS_ENCONTRADO,
    STATUS_LABELS,
    STATUS_PARA_ADOCAO,
    STATUS_PERDIDO,
)
from utils.localizacao import bairros_da_cidade


def render() -> None:
    st.header("📝 Cadastro de animais")
    st.caption(
        "Cadastre um animal perdido, encontrado ou disponível para adoção. "
        "Cada registro recebe um status próprio."
    )

    usuario = st.session_state.get("usuario") or {}
    ong = obter_ong_usuario(usuario.get("id"))
    if not ong:
        st.error("Sua conta precisa estar vinculada a uma ONG da cidade de São Paulo.")
        return
    st.text_input("ONG responsável", value=ong["nome"], disabled=True)
    st.caption("O animal será cadastrado automaticamente na ONG da sua conta.")

    # Status fora do form para que os campos condicionais reajam na hora.
    status_opcoes = [STATUS_PERDIDO, STATUS_ENCONTRADO, STATUS_PARA_ADOCAO]
    status = st.selectbox(
        "Tipo de registro",
        status_opcoes,
        format_func=lambda s: STATUS_LABELS[s],
    )

    # Fora do formulário para mostrar o campo de outro bairro imediatamente.
    st.markdown("**Localização aproximada**")
    cidade = CIDADE_ATENDIDA
    st.caption(f"Cidade: {cidade}")
    bairros = bairros_da_cidade(cidade)
    bairro_opcao = st.selectbox(
        "Bairro",
        [*sorted(bairros), "Outro bairro"],
        index=None,
        placeholder="Selecione o bairro",
    )
    if bairro_opcao == "Outro bairro":
        bairro = st.text_input("Nome do bairro").strip()
        st.caption("Este bairro será exibido nos registros, sem um ponto no mapa.")
    else:
        bairro = bairro_opcao
        st.caption("O mapa indica uma localização aproximada no bairro selecionado.")

    with st.form("form_cadastro", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome do animal (se souber)")
            especie = st.selectbox("Espécie", ESPECIES)
            raca = st.text_input("Raça", value="SRD")
            porte = st.selectbox("Porte", PORTES)
            sexo = st.selectbox("Sexo", SEXOS)
        with col2:
            idade = st.number_input("Idade (anos)", min_value=0.0, max_value=30.0, step=0.5)
            cor = st.text_input("Cor predominante")
            data_evento = st.date_input("Data do evento", value=date.today(), format="DD/MM/YYYY")

        descricao = st.text_area(
            "Descrição",
            placeholder="Características, comportamento, onde foi visto pela última vez...",
        )

        st.markdown("**Foto do animal**")
        foto_arquivo = st.file_uploader(
            "Enviar foto (opcional)",
            type=["png", "jpg", "jpeg", "gif", "webp"],
        )
        foto_url = st.text_input(
            "...ou cole o link de uma foto (opcional)",
            placeholder="https://...",
        )

        # Campos condicionais por status.
        contato_nome = contato_tel = tutor_nome = tutor_tel = ""

        if status in (STATUS_PERDIDO, STATUS_ENCONTRADO):
            st.markdown("**Contato de quem registrou**")
            colc1, colc2 = st.columns(2)
            with colc1:
                contato_nome = st.text_input("Nome do contato")
            with colc2:
                contato_tel = st.text_input("Telefone do contato")

        if status == STATUS_PERDIDO:
            st.markdown("**Dados do tutor**")
            colt1, colt2 = st.columns(2)
            with colt1:
                tutor_nome = st.text_input("Nome do tutor")
            with colt2:
                tutor_tel = st.text_input("Telefone do tutor")

        enviado = st.form_submit_button("Cadastrar animal", type="primary")

    if enviado:
        if not bairro:
            st.error("Informe o bairro do animal em São Paulo.")
            return

        latitude, longitude = bairros.get(bairro_opcao, (None, None))
        caminho_foto = salvar_foto(foto_arquivo)

        dados = {
            "nome": nome or None,
            "especie": especie,
            "raca": raca or None,
            "porte": porte,
            "sexo": sexo,
            "idade_anos": idade or None,
            "cor": cor or None,
            "descricao": descricao or None,
            "status": status,
            "cidade": cidade or None,
            "bairro": bairro,
            "latitude": latitude,
            "longitude": longitude,
            "data_evento": data_evento.isoformat(),
            "foto_url": foto_url or None,
            "foto_path": caminho_foto,
            "contato_nome": contato_nome or None,
            "contato_tel": contato_tel or None,
            "tutor_nome": tutor_nome or None,
            "tutor_tel": tutor_tel or None,
        }
        try:
            novo_id = cadastrar_animal(dados, usuario_id=usuario["id"])
        except ValueError as exc:
            st.error(str(exc))
            return
        st.success(f"Animal cadastrado com sucesso! (ID #{novo_id})")
        celebrar_com_patinhas()
