"""Tela de login e cadastro de usuários (níveis 1 e 2)."""
from __future__ import annotations

import streamlit as st

from services.auth import (
    NIVEL_ORG,
    NIVEL_PESSOA,
    autenticar,
    criar_usuario,
)
from utils.constants import CIDADE_ATENDIDA


def render() -> None:
    st.header("🔐 Acesso ao Salva Pet")
    st.caption(
        "Entre com sua conta ou cadastre-se. Pessoa física (CPF) tem acesso "
        "a Animais Perdidos e Adoção. ONG/petshop (CNPJ) tem acesso completo. "
        "Atendimento exclusivo à cidade de São Paulo."
    )

    aba_login, aba_cadastro = st.tabs(["Entrar", "Criar conta"])

    with aba_login:
        _form_login()

    with aba_cadastro:
        _form_cadastro()


def _form_login() -> None:
    with st.form("login"):
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Entrar", type="primary")

    if entrar:
        usuario = autenticar(email, senha)
        if usuario:
            st.session_state["usuario"] = usuario
            saudacao = f"Bem-vindo(a), {usuario['nome']}!" if usuario["nome"] else "Bem-vindo(a)!"
            st.success(saudacao)
            st.rerun()
        else:
            st.error("E-mail ou senha incorretos.")


def _form_cadastro() -> None:
    tipo = st.radio(
        "Tipo de conta",
        [NIVEL_PESSOA, NIVEL_ORG],
        format_func=lambda n: (
            "Pessoa física (CPF)" if n == NIVEL_PESSOA else "ONG / Petshop (CNPJ)"
        ),
        horizontal=True,
    )

    with st.form("cadastro", clear_on_submit=False):
        nome_ong = ""
        if tipo == NIVEL_ORG:
            nome_ong = st.text_input("Nome da ONG / Petshop")
            nome = st.text_input("Nome do responsável (opcional)")
        else:
            nome = st.text_input("Nome completo")
        email = st.text_input("E-mail")
        col1, col2 = st.columns(2)
        with col1:
            senha = st.text_input("Senha (mín. 6 caracteres)", type="password")
        with col2:
            senha2 = st.text_input("Confirmar senha", type="password")

        documento = st.text_input(
            "CPF" if tipo == NIVEL_PESSOA else "CNPJ",
            help=(
                "Digite 14 números, com ou sem pontos, barra e hífen."
                if tipo == NIVEL_ORG else None
            ),
        )
        telefone = st.text_input("Telefone")

        endereco = cidade = ""
        if tipo == NIVEL_ORG:
            st.markdown("**Dados para o resgate** (aparecem no mapa de perdidos)")
            cidade = CIDADE_ATENDIDA
            st.caption(f"Cidade: {cidade}")
            endereco = st.text_input("Endereço")

        criar = st.form_submit_button("Criar conta", type="primary")

    if criar:
        if senha != senha2:
            st.error("As senhas não conferem.")
            return
        try:
            criar_usuario(
                nome=nome,
                email=email,
                senha=senha,
                nivel=tipo,
                documento=documento,
                telefone=telefone,
                endereco=endereco,
                cidade=cidade,
                nome_ong=nome_ong,
            )
        except ValueError as e:
            st.error(str(e))
            return
        st.success("Conta criada com sucesso! Agora é só entrar na aba 'Entrar'.")
