"""Capa 1: diccionario curado lema → emoji, uno por idioma.

Formato de ``data/emoji_dict/<idioma>.json``::

    {
      "rey": "👑",                                  # confianza 1.0
      "banco": {"emoji": "🏦", "confianza": 0.5}    # ambiguo: bajo el umbral por defecto
    }
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from ..config import DATA_DIR
from ..nlp.languages import obtener_idioma


@dataclass(frozen=True)
class Asignacion:
    emoji: str
    confianza: float


class DiccionarioEmojis:
    def __init__(self, entradas: dict[str, Asignacion]):
        self._entradas = entradas

    @classmethod
    def desde_json(cls, ruta: Path) -> "DiccionarioEmojis":
        datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
        entradas = {}
        for lema, valor in datos.items():
            if isinstance(valor, str):
                asignacion = Asignacion(valor, 1.0)
            else:
                asignacion = Asignacion(valor["emoji"], float(valor.get("confianza", 1.0)))
            entradas[lema.lower()] = asignacion
        return cls(entradas)

    def buscar(self, lema: str) -> Asignacion | None:
        return self._entradas.get(lema.lower())

    def __len__(self) -> int:
        return len(self._entradas)

    def __contains__(self, lema: str) -> bool:
        return lema.lower() in self._entradas


@lru_cache(maxsize=None)
def cargar_diccionario(idioma: str) -> DiccionarioEmojis:
    codigo = obtener_idioma(idioma).codigo
    return DiccionarioEmojis.desde_json(DATA_DIR / "emoji_dict" / f"{codigo}.json")
