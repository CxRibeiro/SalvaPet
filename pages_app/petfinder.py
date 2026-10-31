"""Animais Perdidos — mapa interativo de animais perdidos e encontrados."""
from __future__ import annotations

import html

import folium
from folium.plugins import MarkerCluster
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from services.animals import foto_para_mapa, legenda_foto, listar_animais, resolver_foto
from utils.constants import (
    MAPA_CENTRO,
    MAPA_ZOOM,
    STATUS_CORES,
    STATUS_ENCONTRADO,
    STATUS_LABELS,
    STATUS_PERDIDO,
)
from utils.formatacao import formatar_data, formatar_localizacao


def _txt(valor, padrao: str = "") -> str:
    """Converte qualquer valor em texto seguro para HTML.

    Trata None e o NaN (float) que o pandas usa para células vazias —
    ambos viram o texto padrão em vez de quebrar o html.escape().
    """
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return padrao
    return html.escape(str(valor))


def _popup_html(animal: dict) -> str:
    nome = _txt(animal.get("nome"), "Sem nome")
    especie = _txt(animal.get("especie"))
    descricao = _txt(animal.get("descricao"))
    status = STATUS_LABELS.get(animal.get("status"), _txt(animal.get("status")))
    data = _txt(formatar_data(animal.get("data_evento")))
    contato = _txt(animal.get("contato_nome"))
    tel = _txt(animal.get("contato_tel"))
    localizacao = _txt(formatar_localizacao(animal))

    foto = foto_para_mapa(animal)
    img_tag = (
        f'<img src="{html.escape(foto)}" alt="Foto de {nome}" width="180" '
        'style="border-radius:6px;max-height:160px;object-fit:cover;">'
        if foto
        else ""
    )
    legenda = legenda_foto(animal)
    if foto and legenda:
        img_tag += f"<br><small>{html.escape(legenda)}</small>"

    # Cada registro mostra somente a ONG à qual o animal está vinculado.
    resgate_html = ""
    if _txt(animal.get("abrigo_nome")):
        resgate_html = (
            "<hr style='margin:4px 0;'>"
            "<b>ONG responsável:</b><br>"
            f"{_txt(animal.get('abrigo_nome'))} — {_txt(animal.get('abrigo_tel'))}<br>"
            f"<small>{_txt(animal.get('abrigo_endereco'))}</small>"
        )

    return f"""
    <div style="font-family:sans-serif; max-width:220px;">
        {img_tag}
        <h4 style="margin:4px 0;">{nome} <small>({especie})</small></h4>
        <b>{status}</b><br>
        <small>{data}</small>
        <br><small>{localizacao}</small>
        <p style="margin:4px 0;">{descricao}</p>
        <small>Contato: {contato} {tel}</small>
        {resgate_html}
    </div>
    """


def _criar_mapa(df: pd.DataFrame) -> tuple[folium.Map, int]:
    """Mantém acessíveis os animais cujos marcadores ocupam o mesmo ponto."""
    mapa = folium.Map(location=MAPA_CENTRO, zoom_start=MAPA_ZOOM, control_scale=True)
    grupo = MarkerCluster(
        name="Animais perdidos e encontrados",
        show_coverage_on_hover=False,
        spiderfy_on_max_zoom=True,
        spiderfy_distance_multiplier=1.5,
        max_cluster_radius=40,
    ).add_to(mapa)

    marcadores = 0
    for _, row in df.iterrows():
        if pd.isna(row.get("latitude")) or pd.isna(row.get("longitude")):
            continue
        animal = row.to_dict()
        rotulo = (
            f"{_txt(animal.get('nome'), 'Sem nome')} — "
            f"{STATUS_LABELS.get(row['status'])}"
        )
        folium.Marker(
            location=[float(row["latitude"]), float(row["longitude"])],
            popup=folium.Popup(_popup_html(animal), max_width=250),
            tooltip=rotulo,
            title=rotulo,
            icon=folium.Icon(
                color=STATUS_CORES.get(row["status"], "gray"),
                icon="paw",
                prefix="fa",
            ),
        ).add_to(grupo)
        marcadores += 1

    if marcadores:
        mapa.fit_bounds(grupo.get_bounds(), max_zoom=14)
    return mapa, marcadores


def render() -> None:
    st.header("🗺️ Animais Perdidos — perdidos e encontrados")
    st.caption(
        "Mapa com registros de animais perdidos (vermelho) e encontrados (laranja). "
        "Os pontos indicam localizações aproximadas."
    )

    df = listar_animais(status=[STATUS_PERDIDO, STATUS_ENCONTRADO])

    # Filtro opcional: começa em "Todos", então o mapa já aparece sem exigir
    # que o usuário selecione nada previamente.
    TODOS = "todos"
    opcoes = [TODOS, STATUS_PERDIDO, STATUS_ENCONTRADO]
    rotulos = {
        TODOS: "Todos",
        STATUS_PERDIDO: STATUS_LABELS[STATUS_PERDIDO],
        STATUS_ENCONTRADO: STATUS_LABELS[STATUS_ENCONTRADO],
    }
    escolha = st.radio(
        "Mostrar",
        opcoes,
        index=0,
        horizontal=True,
        format_func=lambda s: rotulos[s],
    )
    st.caption(
        "Perdido: o tutor procura o animal. Encontrado: alguém localizou ou resgatou "
        "o animal e está procurando seu tutor."
    )

    if escolha != TODOS:
        df = df[df["status"] == escolha]

    if df.empty:
        if escolha == STATUS_PERDIDO:
            st.info("Nenhum animal perdido registrado por enquanto.")
        elif escolha == STATUS_ENCONTRADO:
            st.info("Nenhum animal encontrado registrado por enquanto.")
        else:
            st.info("Nenhum registro de animal perdido ou encontrado por enquanto.")
        return

    mapa, marcadores = _criar_mapa(df)
    st_folium(mapa, width=1100, height=500, returned_objects=[])
    st.caption(f"{marcadores} animal(is) no mapa.")
    st.caption(
        "Os números agrupam animais próximos. Clique no grupo para ampliar; "
        "quando estiverem no mesmo ponto, os marcadores se separam para você abrir cada um."
    )

    st.subheader("Registros")
    for _, row in df.iterrows():
        animal = row.to_dict()
        with st.expander(
            f"{_txt(animal.get('nome'), 'Sem nome')} — "
            f"{STATUS_LABELS.get(row['status'])} ({_txt(formatar_localizacao(animal))})"
        ):
            colf, colt = st.columns([1, 2])
            with colf:
                foto = resolver_foto(animal)
                if foto:
                    st.image(foto, caption=legenda_foto(animal), use_container_width=True)
            with colt:
                st.write(f"**Espécie:** {_txt(animal.get('especie'), '-')}")
                st.write(
                    f"**Porte:** {_txt(animal.get('porte'), '-')} | "
                    f"**Sexo:** {_txt(animal.get('sexo'), '-')}"
                )
                st.write(f"**Cor:** {_txt(animal.get('cor'), '-')}")
                st.write(f"**Bairro:** {_txt(animal.get('bairro'), 'Não informado')}")
                st.write(f"**Data:** {formatar_data(animal.get('data_evento'))}")
                st.write(f"**Descrição:** {_txt(animal.get('descricao'), '-')}")
                contato = _txt(animal.get("contato_nome"))
                tel = _txt(animal.get("contato_tel"))
                if contato or tel:
                    st.write(f"**Contato:** {contato or ''} {tel or ''}")

            _bloco_resgate(animal)


def _bloco_resgate(animal: dict) -> None:
    if not _txt(animal.get("abrigo_nome")):
        st.caption("ONG responsável não informada.")
        return
    st.markdown("**🏥 ONG responsável:**")
    st.write(
        f"**{_txt(animal.get('abrigo_nome'))}** · 📞 {_txt(animal.get('abrigo_tel'))}"
    )
    st.write(
        f"📍 {_txt(animal.get('abrigo_endereco'))} "
        f"({_txt(animal.get('abrigo_cidade'))})"
    )
