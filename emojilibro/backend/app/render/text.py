"""Aplica reemplazos sobre un texto plano según el modo de lectura."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Reemplazo:
    inicio: int
    fin: int
    emoji: str
    plural: bool = False


def forma_emoji(emoji: str, plural: bool, estrategia: str) -> str:
    if not plural or estrategia == "mismo":
        return emoji
    if estrategia == "duplicar":
        return emoji * 2
    if estrategia == "marcador":
        return emoji + "ˢ"
    raise ValueError(f"Plural desconocido: {estrategia!r}")


def aplicar(texto: str, reemplazos: list[Reemplazo], modo: str, plural: str = "mismo") -> str:
    """Reescribe ``texto``. Las posiciones de ``reemplazos`` se refieren al texto original."""
    partes = []
    cursor = 0
    for r in sorted(reemplazos, key=lambda r: r.inicio):
        if r.inicio < cursor:  # solapado: se ignora
            continue
        palabra = texto[r.inicio : r.fin]
        emoji = forma_emoji(r.emoji, r.plural, plural)
        partes.append(texto[cursor : r.inicio])
        if modo == "reemplazo":
            partes.append(emoji)
        elif modo == "acompañado":
            partes.append(f"{palabra} {emoji}")
        else:
            raise ValueError(f"Modo desconocido: {modo!r}")
        cursor = r.fin
    partes.append(texto[cursor:])
    return "".join(partes)
