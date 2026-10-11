"""Registro de idiomas soportados.

Para añadir un idioma: agregar una entrada aquí y un diccionario
``data/emoji_dict/<codigo>.json``.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Idioma:
    codigo: str
    nombre: str
    # Modelos spaCy en orden de preferencia; se usa el primero instalado.
    modelos: tuple[str, ...]


IDIOMAS: dict[str, Idioma] = {
    "es": Idioma("es", "Español", ("es_core_news_lg", "es_core_news_md", "es_core_news_sm")),
    "en": Idioma("en", "English", ("en_core_web_lg", "en_core_web_md", "en_core_web_sm")),
}


def normalizar_codigo(codigo: str | None) -> str | None:
    """'es-ES', 'en_US', 'EN' → 'es', 'en'. Devuelve None si no está soportado."""
    if not codigo:
        return None
    base = codigo.strip().lower().replace("_", "-").split("-")[0]
    return base if base in IDIOMAS else None


def obtener_idioma(codigo: str) -> Idioma:
    normalizado = normalizar_codigo(codigo)
    if normalizado is None:
        raise ValueError(
            f"Idioma no soportado: {codigo!r}. Disponibles: {', '.join(sorted(IDIOMAS))}"
        )
    return IDIOMAS[normalizado]
