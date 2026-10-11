"""Orquesta el flujo: leer → analizar → asignar emoji → aplicar → exportar."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bs4 import NavigableString

from .config import Config
from .extract.epub_reader import bloques_de_texto, leer_epub
from .mapping.dictionary import DiccionarioEmojis, cargar_diccionario
from .nlp.analyzer import Analizador
from .render.epub_writer import escribir_epub
from .render.text import Reemplazo, aplicar


@dataclass
class Estadisticas:
    sustantivos: int = 0
    reemplazos: int = 0


class Conversor:
    def __init__(self, config: Config, idioma: str):
        self.config = config
        self.analizador = Analizador(idioma)
        self.diccionario: DiccionarioEmojis = cargar_diccionario(idioma)
        self.estadisticas = Estadisticas()

    def reemplazos(self, texto: str) -> list[Reemplazo]:
        resultado = []
        for s in self.analizador.sustantivos(texto):
            self.estadisticas.sustantivos += 1
            asignacion = self.diccionario.buscar(s.lema) or self.diccionario.buscar(s.texto)
            if asignacion and asignacion.confianza >= self.config.umbral_confianza:
                resultado.append(Reemplazo(s.inicio, s.fin, asignacion.emoji, s.plural))
        self.estadisticas.reemplazos += len(resultado)
        return resultado

    def convertir_texto(self, texto: str) -> str:
        return aplicar(texto, self.reemplazos(texto), self.config.modo, self.config.plural)

    def convertir_bloque(self, nodos: list[NavigableString]) -> None:
        """Analiza el bloque completo y reparte los reemplazos entre sus nodos de texto."""
        texto = "".join(str(n) for n in nodos)
        reemplazos = self.reemplazos(texto)
        if not reemplazos:
            return
        inicio = 0
        for nodo in nodos:
            fin = inicio + len(nodo)
            # Solo los que caen enteros en este nodo; una palabra partida por etiquetas se deja igual.
            propios = [
                Reemplazo(r.inicio - inicio, r.fin - inicio, r.emoji, r.plural)
                for r in reemplazos
                if inicio <= r.inicio and r.fin <= fin
            ]
            if propios:
                nuevo = aplicar(str(nodo), propios, self.config.modo, self.config.plural)
                nodo.replace_with(NavigableString(nuevo))
            inicio = fin


def convertir_libro(entrada: str | Path, salida: str | Path, config: Config) -> Estadisticas:
    entrada = Path(entrada)
    if entrada.suffix.lower() != ".epub":
        raise ValueError("Por ahora solo se admiten archivos .epub")

    libro = leer_epub(entrada)
    idioma = config.idioma or libro.idioma
    if not idioma:
        raise ValueError("No se pudo detectar el idioma del libro; indícalo con --idioma (es, en).")

    conversor = Conversor(config, idioma)
    for capitulo in libro.capitulos:
        for nodos in bloques_de_texto(capitulo.soup, config.convertir_titulos):
            conversor.convertir_bloque(nodos)

    escribir_epub(libro, salida)
    return conversor.estadisticas
