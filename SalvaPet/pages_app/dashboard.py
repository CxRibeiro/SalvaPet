"""Dashboard — análise de dados (Pandas) e gráficos (Plotly)."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from services.animals import legenda_foto, listar_animais, metricas_gerais, resolver_foto
from utils.constants import STATUS_LABELS
from utils.formatacao import formatar_data, formatar_localizacao, texto_ou_padrao


@st.dialog("Foto do animal", width="large", on_dismiss="rerun")
def _mostrar_foto_ampliada(animal: dict) -> None:
    st.subheader(texto_ou_padrao(animal.get("nome"), "Sem nome"))
    foto = resolver_foto(animal)
    if foto:
        st.image(foto, caption=legenda_foto(animal), width="stretch")
    else:
        st.info("Este animal ainda não possui foto cadastrada.")
    st.caption(formatar_localizacao(animal))
    if st.button("Fechar", key="dashboard_fechar_foto"):
        st.rerun()


def _selecionar_foto_da_tabela(ids_exibidos: tuple[int, ...]) -> None:
    clique = st.session_state.get("dashboard_clique_foto")
    if clique is not None and 0 <= clique["row"] < len(ids_exibidos):
        st.session_state["dashboard_foto_ampliada_id"] = ids_exibidos[clique["row"]]


def render() -> None:
    st.header("📊 Dashboard & Análise")
    st.caption("Visão geral dos registros, com análise em Pandas e gráficos em Plotly.")

    m = metricas_gerais()
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total", m["total"])
    c2.metric("Perdidos", m["perdidos"])
    c3.metric("Encontrados", m["encontrados"])
    c4.metric("Para adoção", m["para_adocao"])
    c5.metric("Adotados", m["adotados"])
    c6.metric("Reunidos", m["reunidos"])

    df = listar_animais()
    if df.empty:
        st.info("Ainda não há dados para análise.")
        return

    st.divider()

    col1, col2 = st.columns(2)

    # Gráfico 1: distribuição por status.
    with col1:
        st.subheader("Registros por status")
        por_status = (
            df["status"].map(STATUS_LABELS).value_counts().reset_index()
        )
        por_status.columns = ["Status", "Quantidade"]
        fig = px.pie(por_status, names="Status", values="Quantidade", hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

    # Gráfico 2: distribuição por espécie.
    with col2:
        st.subheader("Registros por espécie")
        por_especie = df["especie"].value_counts().reset_index()
        por_especie.columns = ["Espécie", "Quantidade"]
        fig2 = px.bar(
            por_especie, x="Espécie", y="Quantidade", color="Espécie", text="Quantidade"
        )
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)

    # Gráfico 3: registros por bairro de São Paulo.
    with col3:
        st.subheader("Registros por bairro")
        por_bairro = df["bairro"].fillna("Não informado").value_counts().reset_index()
        por_bairro.columns = ["Bairro", "Quantidade"]
        fig3 = px.bar(por_bairro, x="Quantidade", y="Bairro", orientation="h")
        st.plotly_chart(fig3, use_container_width=True)

    # Gráfico 4: linha do tempo de eventos.
    with col4:
        st.subheader("Eventos ao longo do tempo")
        tmp = df.copy()
        tmp["data_evento"] = pd.to_datetime(tmp["data_evento"], errors="coerce")
        linha = (
            tmp.dropna(subset=["data_evento"])
            .groupby([tmp["data_evento"].dt.date, "status"])
            .size()
            .reset_index(name="Quantidade")
        )
        if linha.empty:
            st.info("Sem datas suficientes para a linha do tempo.")
        else:
            linha["status"] = linha["status"].map(STATUS_LABELS)
            linha.columns = ["Data", "Status", "Quantidade"]
            fig4 = px.line(linha, x="Data", y="Quantidade", color="Status", markers=True)
            fig4.update_xaxes(tickformat="%d/%m/%Y", hoverformat="%d/%m/%Y")
            st.plotly_chart(fig4, use_container_width=True)

    st.divider()
    st.subheader("Tabela de dados")

    # Seleção de colunas mais relevantes para a análise tabular.
    colunas = [
        "id", "nome", "especie", "raca", "porte", "sexo", "idade_anos",
        "cor", "status", "cidade", "bairro", "data_evento", "abrigo_nome",
    ]
    colunas = [c for c in colunas if c in df.columns]
    tabela = df[colunas].copy()
    tabela["status"] = tabela["status"].map(STATUS_LABELS)
    tabela["data_evento"] = tabela["data_evento"].map(formatar_data)
    tabela_visual = tabela.copy()
    tabela_visual["nome"] = tabela_visual["nome"].map(
        lambda nome: texto_ou_padrao(nome, "Sem nome")
    )
    tabela_visual.insert(
        tabela_visual.columns.get_loc("nome") + 1,
        "ver_foto",
        ":material/open_in_full:",
    )
    st.caption("Clique no ícone de ampliar ao lado do nome para ver a foto.")
    st.dataframe(
        tabela_visual,
        width="stretch",
        hide_index=True,
        key="dashboard_tabela_animais",
        column_config={
            "ver_foto": st.column_config.ButtonColumn(
                "Foto",
                width=60,
                help="Ampliar a foto do animal",
                type="tertiary",
                key="dashboard_clique_foto",
                on_click=_selecionar_foto_da_tabela,
                args=(tuple(int(identificador) for identificador in tabela["id"]),),
            ),
        },
    )

    foto_solicitada = st.session_state.pop("dashboard_foto_ampliada_id", None)
    if foto_solicitada is not None:
        selecionado = df.loc[df["id"] == foto_solicitada]
        if not selecionado.empty:
            _mostrar_foto_ampliada(selecionado.iloc[0].to_dict())

    # Download da análise em CSV.
    csv = tabela.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Baixar dados (CSV)",
        data=csv,
        file_name="animais.csv",
        mime="text/csv",
    )
