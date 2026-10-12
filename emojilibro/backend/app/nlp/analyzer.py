"""Análisis gramatical con spaCy: detecta sustantivos comunes, su lema y su número."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import spacy
from spacy.language import Language

from .languages import obtener_idioma


@dataclass(frozen=True)
class Sustantivo:
    texto: str
    inicio: int  # posición de carácter dentro del texto analizado
    fin: int
    lema: str
    plural: bool


@lru_cache(maxsize=None)
def cargar_modelo(codigo: str) -> Language:
    idioma = obtener_idioma(codigo)
    for nombre in idioma.modelos:
        if spacy.util.is_package(nombre):
            # No necesitamos el parser de dependencias; el NER sí, para excluir entidades.
            return spacy.load(nombre, disable=["parser"])
    raise RuntimeError(
        f"No hay modelo spaCy instalado para {idioma.nombre}. "
        f"Instala uno con: python -m spacy download {idioma.modelos[0]}"
    )


class Analizador:
    def __init__(self, idioma: str):
        self.idioma = obtener_idioma(idioma).codigo
        self.nlp = cargar_modelo(self.idioma)

    def sustantivos(self, texto: str) -> list[Sustantivo]:
        """Sustantivos comunes del texto. Excluye nombres propios y entidades nombradas."""
        if not texto.strip():
            return []
        doc = self.nlp(texto)
        # Solo cuentan las entidades con algún nombre propio ("Banco de España"). El NER
        # marca a veces frases comunes como MISC ("Los niños jugaban con sus perros")
        # o TIME/DATE ("the night"), y esos sustantivos sí deben convertirse.
        en_entidad = {
            i
            for ent in doc.ents
            if any(t.pos_ == "PROPN" for t in ent)
            for i in range(ent.start, ent.end)
        }
        resultado = []
        for token in doc:
            if token.pos_ != "NOUN" or token.i in en_entidad or not token.is_alpha:
                continue
            resultado.append(
                Sustantivo(
                    texto=token.text,
                    inicio=token.idx,
                    fin=token.idx + len(token.text),
                    lema=token.lemma_.lower(),
                    plural="Plur" in token.morph.get("Number"),
                )
            )
        return resultado
