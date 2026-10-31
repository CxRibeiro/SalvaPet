"""Salva Pet — app que integra PetFinder (perdidos) e AdotaPet (adoção).

Ponto de entrada do Streamlit. Inicializa o banco, cuida da autenticação e
faz a navegação entre as telas conforme o nível do usuário:
  - Nível 1 (pessoa física/CPF): Início, PetFinder, AdotaPet.
  - Nível 2 (ONG ou petshop/CNPJ): acesso a todas as páginas.

Para rodar:
    streamlit run app.py
"""
from __future__ import annotations

import streamlit as st

from database.db import init_db
from pages_app import (
    adotapet,
    cadastro,
    dashboard,
    integracao,
    login,
    petfinder,
)
from services.auth import NIVEL_ORG, formatar_documento, obter_ong_usuario

st.set_page_config(
    page_title="Salva Pet",
    page_icon="🐾",
    layout="wide",
)

# Garante que o banco e o seed existam antes de qualquer tela.
init_db()


# Cada página declara o nível mínimo necessário para acessá-la.
PAGINAS = {
    "🏠 Início": ("inicio", 1),
    "🗺️ Animais Perdidos": ("petfinder", 1),
    "🐾 Adoção": ("adotapet", 1),
    "📝 Cadastrar animal": ("cadastro", 2),
    "🔗 Integração": ("integracao", 2),
    "📊 Dashboard": ("dashboard", 2),
}


def _inicio(usuario: dict) -> None:
    st.title("🐾 Salva Pet")
    st.subheader("Localizar animais perdidos e conectar resgatados a adotantes em São Paulo")
    st.write(
        """
        O **Salva Pet** reúne dois sistemas integrados:

        - **Animais Perdidos** — mapa interativo de animais perdidos e encontrados.
        - **Adoção** — catálogo de animais disponíveis para adoção.
        """
    )

    if usuario["nivel"] >= NIVEL_ORG:
        st.write(
            "Como **ONG/petshop**, você também gerencia o cadastro de animais, "
            "a integração (resgate → tutor → adoção) e o dashboard."
        )
        st.info("Use o menu na barra lateral para navegar entre todas as telas.")
        col1, col2, col3 = st.columns(3)
        col1.success("**1. Registrar**\n\nPerdido, encontrado ou para adoção.")
        col2.warning("**2. Verificar**\n\nBuscar o tutor de um animal encontrado.")
        col3.info("**3. Adotar**\n\nSem tutor? Encaminhar para adoção responsável.")
    else:
        st.info(
            "Você pode consultar **Animais Perdidos** (perdidos/encontrados) "
            "e **Adoção** (animais para adoção) pelo menu lateral."
        )


def _barra_usuario(usuario: dict) -> None:
    nivel_txt = "ONG/Petshop" if usuario["nivel"] >= NIVEL_ORG else "Pessoa física"
    doc = formatar_documento(usuario.get("documento", ""), usuario["nivel"])
    ong = obter_ong_usuario(usuario.get("id")) if usuario["nivel"] >= NIVEL_ORG else None
    nome_exibido = usuario.get("nome") or (ong["nome"] if ong else "Sua conta")
    st.sidebar.markdown(f"**{nome_exibido}**")
    st.sidebar.caption(f"{nivel_txt} · {doc}")
    if ong and usuario.get("nome"):
        st.sidebar.caption(f"ONG: {ong['nome']}")
    if st.sidebar.button("Sair"):
        st.session_state.pop("usuario", None)
        st.rerun()


def main() -> None:
    st.sidebar.title("🐾 Salva Pet")

    usuario = st.session_state.get("usuario")
    if not usuario:
        login.render()
        return

    _barra_usuario(usuario)
    st.sidebar.divider()

    # Menu mostra apenas as páginas permitidas para o nível do usuário.
    disponiveis = {
        rotulo: info
        for rotulo, info in PAGINAS.items()
        if usuario["nivel"] >= info[1]
    }
    escolha = st.sidebar.radio("Navegação", list(disponiveis.keys()))
    destino, nivel_min = disponiveis[escolha]

    # Guarda extra: mesmo que algo force uma página restrita, bloqueia aqui.
    if usuario["nivel"] < nivel_min:
        st.error("Você não tem permissão para acessar esta página.")
        return

    if destino == "inicio":
        _inicio(usuario)
    elif destino == "petfinder":
        petfinder.render()
    elif destino == "adotapet":
        adotapet.render()
    elif destino == "cadastro":
        cadastro.render()
    elif destino == "integracao":
        integracao.render()
    elif destino == "dashboard":
        dashboard.render()


if __name__ == "__main__":
    main()
