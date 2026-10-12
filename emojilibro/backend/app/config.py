"""Configuración de una conversión (sección 9 de PLAN.md)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

MODOS = ("reemplazo", "acompañado")
PLURALES = ("mismo", "duplicar", "marcador")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def normalizar_modo(modo: str) -> str:
    """Acepta 'acompanado' sin tilde para facilitar su uso desde la terminal."""
    modo = modo.strip().lower()
    if modo == "acompanado":
        modo = "acompañado"
    if modo not in MODOS:
        raise ValueError(f"Modo desconocido: {modo!r}. Opciones: {', '.join(MODOS)}")
    return modo


@dataclass
class Config:
    modo: str = "acompañado"
    # Código ISO 639-1 ('es', 'en'). None = detectar desde los metadatos del EPUB.
    idioma: str | None = None
    umbral_confianza: float = 0.7
    plural: str = "mismo"
    convertir_titulos: bool = False

    def __post_init__(self) -> None:
        self.modo = normalizar_modo(self.modo)
        if self.plural not in PLURALES:
            raise ValueError(f"Plural desconocido: {self.plural!r}. Opciones: {', '.join(PLURALES)}")
        if not 0.0 <= self.umbral_confianza <= 1.0:
            raise ValueError("umbral_confianza debe estar entre 0 y 1")
