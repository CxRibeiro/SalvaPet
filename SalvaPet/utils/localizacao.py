"""Bairros sugeridos e pontos de referência para a localização aproximada."""
from __future__ import annotations

import unicodedata

# Referências em locais públicos, não endereços exatos dos animais.
# Fonte: Prefeitura de São Paulo, relação de pontos culturais e praças:
# https://prefeitura.sp.gov.br/cidade/secretarias/upload/240%20pontos%20edital.pdf
BAIRROS_POR_CIDADE = {
    "sao paulo": {
        "Aclimação": (-23.57277, -46.62910),
        "Alto de Pinheiros": (-23.55412, -46.70288),
        "Artur Alvim": (-23.54645, -46.48468),
        "Bela Vista": (-23.56226, -46.64124),
        "Consolação": (-23.54845, -46.64622),
        "Ipiranga": (-23.58779, -46.60236),
        "Itaim Bibi": (-23.58684, -46.68412),
        "Jardim São Paulo": (-23.49841, -46.61941),
        "Jardim da Saúde": (-23.61240, -46.61708),
        "Lapa": (-23.52150, -46.69644),
        "Liberdade": (-23.57072, -46.64025),
        "Moema": (-23.60328, -46.66117),
        "Mooca": (-23.55035, -46.59951),
        "Pari": (-23.52687, -46.61148),
        "Pinheiros": (-23.56642, -46.69479),
        "República": (-23.54739, -46.64212),
        "Santana": (-23.49696, -46.62749),
        "Santo Amaro": (-23.65067, -46.70848),
        "Sé": (-23.54917, -46.63725),
        "Tatuapé": (-23.53603, -46.57206),
        "Tucuruvi": (-23.48163, -46.60426),
        "Vila Buarque": (-23.54498, -46.64933),
        "Vila Mariana": (-23.58346, -46.62348),
        "Vila Prudente": (-23.58195, -46.58313),
    },
}


def bairros_da_cidade(cidade: str) -> dict[str, tuple[float, float]]:
    """Busca sugestões sem diferenciar maiúsculas, acentos ou espaços extras."""
    normalizada = unicodedata.normalize("NFKD", cidade)
    chave = " ".join(
        "".join(c for c in normalizada if not unicodedata.combining(c)).split()
    ).casefold()
    return BAIRROS_POR_CIDADE.get(chave, {})
