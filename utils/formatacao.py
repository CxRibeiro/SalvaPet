"""Formatação de datas e locais para exibição nas telas."""
from __future__ import annotations

from datetime import date, datetime


def texto_ou_padrao(valor, padrao: str = "Não informado") -> str:
    """Evita exibir valores ausentes do banco ou do pandas como texto."""
    if not isinstance(valor, str):
        return padrao
    return valor.strip() or padrao


def formatar_data(valor, *, incluir_hora: bool = False) -> str:
    """Exibe uma data ISO em formato brasileiro, mantendo o valor do banco."""
    if isinstance(valor, (date, datetime)):
        data = valor
    elif isinstance(valor, str) and valor.strip():
        try:
            data = datetime.fromisoformat(valor.strip())
        except ValueError:
            return "Não informado"
    else:
        return "Não informado"
    formato = "%d/%m/%Y %H:%M" if incluir_hora and isinstance(data, datetime) else "%d/%m/%Y"
    try:
        return data.strftime(formato)
    except ValueError:
        return "Não informado"


def formatar_localizacao(animal: dict) -> str:
    bairro = texto_ou_padrao(animal.get("bairro"), "Bairro não informado")
    cidade = texto_ou_padrao(animal.get("cidade"), "São Paulo")
    return f"{bairro} — {cidade}"
