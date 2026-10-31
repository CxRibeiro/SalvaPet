"""Adoção — catálogo de animais disponíveis para adoção."""
from __future__ import annotations

import streamlit as st

from services.animals import legenda_foto, listar_animais, registrar_adocao, resolver_foto
from utils.constants import ESPECIES, PORTES, STATUS_PARA_ADOCAO
from utils.formatacao import formatar_localizacao


def _selecionar_todos(chave: str, opcoes: list[str]) -> None:
    if "Todos" in st.session_state[chave]:
        st.session_state[chave] = opcoes


def _filtro(label: str, opcoes: list[str], chave: str) -> list[str]:
    return st.multiselect(
        label,
        ["Todos", *opcoes] if opcoes else [],
        placeholder="Escolha uma opção" if opcoes else "Nenhuma opção disponível",
        select_all=False,
        filter_mode=None,
        disabled=not opcoes,
        key=chave,
        on_change=_selecionar_todos,
        args=(chave, opcoes),
    )


def render() -> None:
    st.header("🐾 Adoção — Adoção de animais")
    st.caption("Catálogo de cães e gatos disponíveis para adoção responsável.")

    df = listar_animais(status=[STATUS_PARA_ADOCAO])

    if df.empty:
        st.info("Nenhum animal disponível para adoção no momento.")
        return

    # Filtros.
    col1, col2, col3 = st.columns(3)
    with col1:
        f_especie = _filtro("Espécie", ESPECIES, "adocao_especie")
    with col2:
        f_porte = _filtro("Porte", PORTES, "adocao_porte")
    with col3:
        bairros = sorted(df["bairro"].dropna().unique().tolist())
        f_bairro = _filtro("Bairro", bairros, "adocao_bairro")

    if f_especie:
        df = df[df["especie"].isin(f_especie)]
    if f_porte:
        df = df[df["porte"].isin(f_porte)]
    if f_bairro:
        df = df[df["bairro"].isin(f_bairro)]

    if df.empty:
        st.warning("Nenhum animal corresponde aos filtros selecionados.")
        return

    st.write(f"**{len(df)}** animal(is) disponível(is).")

    # Catálogo em grade de 3 colunas.
    registros = df.to_dict("records")
    for i in range(0, len(registros), 3):
        cols = st.columns(3)
        for col, animal in zip(cols, registros[i : i + 3]):
            with col:
                _card(animal)


def _card(animal: dict) -> None:
    with st.container(border=True):
        foto = resolver_foto(animal)
        if foto:
            st.image(foto, caption=legenda_foto(animal), use_container_width=True)
        st.subheader(animal.get("nome") or "Sem nome")
        st.write(f"**{animal.get('especie')}** · {animal.get('raca') or 'SRD'}")
        idade = animal.get("idade_anos")
        idade_txt = f"{idade:g} ano(s)" if idade else "idade não informada"
        st.write(f"Porte {animal.get('porte')} · {idade_txt}")
        st.write(f"📍 {formatar_localizacao(animal)}")
        if animal.get("abrigo_nome"):
            st.caption(f"Abrigo: {animal['abrigo_nome']} · {animal.get('abrigo_tel') or ''}")
        with st.popover("Adotar"):
            st.write(f"Adoção de **{animal.get('nome') or 'animal'}**")
            nome = st.text_input("Seu nome", key=f"ad_nome_{animal['id']}")
            tel = st.text_input("Seu telefone", key=f"ad_tel_{animal['id']}")
            if st.button("Confirmar adoção", key=f"ad_btn_{animal['id']}"):
                if not nome or not tel:
                    st.error("Preencha nome e telefone.")
                else:
                    registrar_adocao(animal["id"], nome, tel)
                    st.success("Adoção registrada! O abrigo entrará em contato.")
                    st.rerun()
