"""Integração Animais Perdidos <-> Adoção.

Fluxo do diferencial do projeto:
  1. Animal encontrado (registro de resgate/localização)
  2. Verificação e busca pelo tutor (conferir se já tem responsável)
  3a. Se achar o tutor -> reunir com o tutor
  3b. Se não houver tutor e estiver disponível -> encaminhar para adoção (ONG)

A tela mostra todos os animais que passam pelo fluxo (encontrados, reunidos
e em adoção), para que o histórico fique sempre navegável. As ações de
verificação só ficam disponíveis para animais ainda 'encontrados'.
"""
from __future__ import annotations

import math

import streamlit as st

from services.animals import (
    buscar_possiveis_tutores,
    disponibilizar_para_adocao,
    legenda_foto,
    listar_abrigos,
    listar_animais,
    listar_historico,
    metricas_gerais,
    resolver_foto,
    reunir_com_tutor,
)
from utils.constants import (
    STATUS_ENCONTRADO,
    STATUS_LABELS,
    STATUS_PARA_ADOCAO,
    STATUS_REUNIDO,
)
from utils.formatacao import formatar_data, formatar_localizacao


def _txt(valor, padrao: str = "-") -> str:
    """Texto seguro: trata None e o NaN (float) que o pandas usa em vazios."""
    if valor is None or (isinstance(valor, float) and math.isnan(valor)):
        return padrao
    texto = str(valor).strip()
    return texto or padrao


def render() -> None:
    st.header("🔗 Integração — do resgate ao destino do animal")
    st.caption(
        "Acompanhe os animais que passam pelo fluxo: encontrados, reunidos com "
        "o tutor e encaminhados para adoção."
    )

    st.markdown(
        """
        **Como funciona o fluxo**
        1. Animal **encontrado** é registrado (resgate/localização).
        2. O sistema **busca possíveis tutores** entre os animais perdidos compatíveis.
        3. Se o tutor for identificado → **reunir com o tutor**.
        4. Se não houver tutor e o animal estiver disponível → **encaminhar para adoção**.
        """
    )

    # Resumo sempre visível.
    m = metricas_gerais()
    c1, c2, c3 = st.columns(3)
    c1.metric("Aguardando verificação", m["encontrados"])
    c2.metric("Reunidos com tutor", m["reunidos"])
    c3.metric("Encaminhados p/ adoção", m["para_adocao"])

    st.divider()

    # Filtro: qual grupo do fluxo olhar. Começa em "Aguardando verificação".
    grupos = {
        STATUS_ENCONTRADO: "Aguardando verificação",
        STATUS_REUNIDO: "Reunidos com tutor",
        STATUS_PARA_ADOCAO: "Encaminhados p/ adoção",
        "todos": "Todos do fluxo",
    }
    grupo = st.radio(
        "Ver animais",
        list(grupos.keys()),
        index=0,
        horizontal=True,
        format_func=lambda s: grupos[s],
    )

    if grupo == "todos":
        status_filtro = [STATUS_ENCONTRADO, STATUS_REUNIDO, STATUS_PARA_ADOCAO]
    else:
        status_filtro = [grupo]

    df = listar_animais(status=status_filtro)

    if df.empty:
        st.info(
            f"Nenhum animal em **{grupos[grupo]}** no momento. "
            "Troque o filtro acima para ver outros grupos, ou cadastre um "
            "animal do tipo **Encontrado** para iniciar o fluxo."
        )
        return

    opcoes = df["id"].tolist()
    animal_id = st.selectbox(
        "Selecione o animal",
        opcoes,
        format_func=lambda i: _rotulo(df, i),
    )
    animal = df[df["id"] == animal_id].iloc[0].to_dict()
    status_atual = animal.get("status")

    colf, cold = st.columns([1, 2])
    with colf:
        foto = resolver_foto(animal)
        if foto:
            st.image(foto, caption=legenda_foto(animal), use_container_width=True)
    with cold:
        st.write(f"**Status atual:** {STATUS_LABELS.get(status_atual, status_atual)}")
        st.write(
            f"**Espécie:** {_txt(animal.get('especie'))} · "
            f"**Porte:** {_txt(animal.get('porte'))}"
        )
        st.write(
            f"**Cor:** {_txt(animal.get('cor'))} · "
            f"**Cidade:** {_txt(animal.get('cidade'))}"
        )
        st.write(f"**Data do evento:** {formatar_data(animal.get('data_evento'))}")
        st.write(f"**Local:** {formatar_localizacao(animal)}")
        st.write(f"**Descrição:** {_txt(animal.get('descricao'))}")
        if _txt(animal.get("tutor_nome"), "") not in ("", "-"):
            st.write(
                f"**Tutor:** {_txt(animal.get('tutor_nome'))} "
                f"({_txt(animal.get('tutor_tel'))})"
            )

    st.divider()

    # Ações de verificação só fazem sentido para quem ainda está 'encontrado'.
    if status_atual == STATUS_ENCONTRADO:
        _fluxo_verificacao(animal, animal_id)
    else:
        st.success(
            f"Este animal já foi processado no fluxo "
            f"(**{STATUS_LABELS.get(status_atual, status_atual)}**)."
        )
        _mostrar_historico(animal_id)


def _fluxo_verificacao(animal: dict, animal_id: int) -> None:
    # Passo 2: busca de possíveis tutores.
    st.subheader("1. Verificação e busca pelo tutor")
    candidatos = buscar_possiveis_tutores(animal)

    if candidatos.empty:
        st.warning("Nenhum tutor compatível encontrado entre os animais perdidos.")
    else:
        st.write("Possíveis correspondências (ordenadas por compatibilidade):")
        for _, cand in candidatos.iterrows():
            c = cand.to_dict()
            with st.container(border=True):
                cc1, cc2 = st.columns([3, 1])
                with cc1:
                    st.write(
                        f"**{_txt(c.get('nome'), 'Sem nome')}** · "
                        f"{_txt(c.get('especie'))} · "
                        f"porte {_txt(c.get('porte'))} · "
                        f"cor {_txt(c.get('cor'))} · "
                        f"{formatar_localizacao(c)}"
                    )
                    st.caption(
                        f"Tutor: {_txt(c.get('tutor_nome'))} "
                        f"({_txt(c.get('tutor_tel'), 'sem telefone')}) · "
                        f"compatibilidade: {int(c.get('score', 0))}"
                    )
                with cc2:
                    if st.button("Reunir com tutor", key=f"reunir_{c['id']}"):
                        reunir_com_tutor(
                            animal_id,
                            _txt(c.get("tutor_nome"), "Tutor"),
                            _txt(c.get("tutor_tel"), ""),
                            registro_perdido_id=int(c["id"]),
                        )
                        st.success(
                            "Animal reunido com o tutor! Os registros saíram "
                            "do mapa de perdidos/encontrados."
                        )
                        st.rerun()

    st.divider()

    # Passo 3b: encaminhar para adoção.
    st.subheader("2. Adoção responsável (quando não há tutor)")
    st.caption(
        "Use quando não houver tutor identificado e o animal estiver "
        "legalmente disponível para adoção."
    )
    abrigos_df = listar_abrigos()
    if abrigos_df.empty:
        st.warning("Cadastre um abrigo/ONG para encaminhar o animal para adoção.")
        return

    abrigo_id = st.selectbox(
        "Abrigo/ONG responsável",
        abrigos_df["id"].tolist(),
        format_func=lambda i: abrigos_df.loc[abrigos_df["id"] == i, "nome"].iloc[0],
    )
    obs = st.text_input("Observação (opcional)")
    if st.button("Encaminhar para adoção", type="primary"):
        disponibilizar_para_adocao(animal_id, int(abrigo_id), obs)
        st.success("Animal encaminhado para adoção! Já aparece na página Adoção.")
        st.rerun()


def _mostrar_historico(animal_id: int) -> None:
    hist = listar_historico(animal_id)
    if hist.empty:
        return
    st.subheader("Histórico do animal")
    for _, h in hist.iterrows():
        st.write(
            f"- **{_txt(h.get('evento'))}** · {_txt(h.get('detalhe'), '')} "
            f"_({formatar_data(h.get('criado_em'), incluir_hora=True)})_"
        )


def _rotulo(df, i: int) -> str:
    row = df[df["id"] == i].iloc[0]
    nome = _txt(row.get("nome"), "Sem nome")
    status = STATUS_LABELS.get(row.get("status"), row.get("status"))
    return f"#{i} · {nome} · {_txt(row.get('especie'))} · {status}"
