"""Constantes compartilhadas do app (status, espécies, portes, etc.)."""

CIDADE_ATENDIDA = "São Paulo"

# Status possíveis de um registro de animal.
STATUS_PERDIDO = "perdido"
STATUS_ENCONTRADO = "encontrado"
STATUS_PARA_ADOCAO = "para_adocao"
STATUS_ADOTADO = "adotado"
STATUS_REUNIDO = "reunido"  # devolvido ao tutor original

STATUS_LABELS = {
    STATUS_PERDIDO: "Perdido",
    STATUS_ENCONTRADO: "Encontrado",
    STATUS_PARA_ADOCAO: "Disponível para adoção",
    STATUS_ADOTADO: "Adotado",
    STATUS_REUNIDO: "Reunido com o tutor",
}

STATUS_CORES = {
    STATUS_PERDIDO: "red",
    STATUS_ENCONTRADO: "orange",
    STATUS_PARA_ADOCAO: "green",
    STATUS_ADOTADO: "blue",
    STATUS_REUNIDO: "purple",
}

ESPECIES = ["Cachorro", "Gato", "Outro"]

PORTES = ["Pequeno", "Médio", "Grande"]

SEXOS = ["Macho", "Fêmea", "Desconhecido"]

# Centro aproximado do mapa (Brasil / São Paulo) usado como padrão.
MAPA_CENTRO = [-23.55052, -46.633308]
MAPA_ZOOM = 11
