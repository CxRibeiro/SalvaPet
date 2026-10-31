"""Animações decorativas de confirmação do Salva Pet."""
from __future__ import annotations

import uuid

import streamlit as st


def celebrar_com_patinhas() -> None:
    """Mostra patinhas de gatos e cachorros por alguns segundos após cadastrar."""
    patinhas = []
    cores = ["#e995bb", "#78b9ee", "#f4c36c", "#baa1e3"]
    for indice in range(28):
        gato = indice % 2 == 0
        almofada = (
            "M12 11 C9 11 7 14 6 17 C4 21 7 23 10 21 Q12 20 14 21 "
            "C17 23 20 21 18 17 C17 14 15 11 12 11Z"
            if gato else
            "M12 11 C7 11 3 17 5 21 C7 24 10 21 12 21 "
            "C14 21 17 24 19 21 C21 17 17 11 12 11Z"
        )
        estilo = (
            f"--x:{(indice * 37) % 100}%;--tamanho:{28 + (indice % 4) * 7}px;"
            f"--atraso:{(indice % 7) * 0.12:.2f}s;--duracao:{3.5 + (indice % 4) * 0.25:.2f}s;"
            f"--deriva:{(-1 if gato else 1) * (30 + indice % 4 * 10)}px;"
            f"--rotacao:{indice % 5 * 15 - 30}deg;--cor:{cores[indice % len(cores)]}"
        )
        patinhas.append(
            f'<span class="salvapet-patinha" style="{estilo}">'
            '<svg viewBox="0 0 24 26" aria-hidden="true">'
            '<ellipse cx="4" cy="9" rx="2.5" ry="3.5" transform="rotate(-22 4 9)"/>'
            '<ellipse cx="9" cy="5" rx="2.5" ry="3.5"/>'
            '<ellipse cx="15" cy="5" rx="2.5" ry="3.5"/>'
            '<ellipse cx="20" cy="9" rx="2.5" ry="3.5" transform="rotate(22 20 9)"/>'
            f'<path d="{almofada}"/></svg></span>'
        )

    # O identificador novo reinicia a animação em cada envio do formulário.
    identificador = f"salvapet-patinhas-{uuid.uuid4().hex}"
    st.html(
        """
        <style>
        .salvapet-celebracao {
            position: fixed; inset: 0; z-index: 9999;
            pointer-events: none; overflow: hidden;
            animation: salvapet-fim 0s 5.5s forwards;
        }
        .salvapet-patinha {
            position: absolute; bottom: -70px; left: var(--x);
            width: var(--tamanho); color: var(--cor); opacity: 0;
            filter: drop-shadow(0 2px 3px #0002);
            animation: salvapet-subir var(--duracao) var(--atraso) ease-out both;
        }
        .salvapet-patinha svg { width: 100%; fill: currentColor; }
        @keyframes salvapet-subir {
            0% { opacity: 0; transform: translate3d(0,0,0) rotate(var(--rotacao)); }
            12% { opacity: 1; }
            75% { opacity: .9; }
            100% {
                opacity: 0;
                transform: translate3d(var(--deriva),-112vh,0) rotate(calc(var(--rotacao) + 150deg));
            }
        }
        @keyframes salvapet-fim { to { visibility: hidden; } }
        @media (prefers-reduced-motion: reduce) {
            .salvapet-celebracao { display: none; }
        }
        </style>
        """
        f'<div id="{identificador}" class="salvapet-celebracao" aria-hidden="true">'
        + "".join(patinhas)
        + "</div>"
    )
