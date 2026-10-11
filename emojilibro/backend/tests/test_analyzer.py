import pytest

from app.nlp.analyzer import Analizador
from app.nlp.languages import normalizar_codigo, obtener_idioma
from conftest import requiere_modelo


@requiere_modelo("es")
def test_es_detecta_sustantivos_comunes():
    a = Analizador("es")
    lemas = [s.lema for s in a.sustantivos("El rey miró la ciudad desde la torre y sintió una profunda tristeza.")]
    assert lemas == ["rey", "ciudad", "torre", "tristeza"]


@requiere_modelo("es")
def test_es_excluye_nombres_propios():
    textos = [s.texto for s in Analizador("es").sustantivos("Juan vio un perro en Madrid.")]
    assert "Juan" not in textos and "Madrid" not in textos
    assert "perro" in textos


@requiere_modelo("es")
def test_es_lematiza_plurales():
    s = {x.texto: x for x in Analizador("es").sustantivos("Los reyes tenían dos perros.")}
    assert s["reyes"].lema == "rey" and s["reyes"].plural
    assert s["perros"].lema == "perro" and s["perros"].plural


@requiere_modelo("es")
def test_es_no_toma_verbos_ni_adjetivos():
    lemas = {s.lema for s in Analizador("es").sustantivos("El niño corre feliz.")}
    assert lemas == {"niño"}


@requiere_modelo("es")
def test_posiciones_corresponden_al_texto():
    texto = "La luna brilla sobre el mar."
    for s in Analizador("es").sustantivos(texto):
        assert texto[s.inicio : s.fin] == s.texto


@requiere_modelo("en")
def test_en_detecta_sustantivos_comunes():
    lemas = [s.lema for s in Analizador("en").sustantivos("The king looked at the city from the tower and felt a deep sadness.")]
    assert lemas == ["king", "city", "tower", "sadness"]


@requiere_modelo("en")
def test_en_excluye_nombres_propios_y_lematiza():
    s = {x.texto: x for x in Analizador("en").sustantivos("John saw the kings and two dogs in London.")}
    assert "John" not in s and "London" not in s
    assert s["kings"].lema == "king" and s["kings"].plural
    assert s["dogs"].lema == "dog" and s["dogs"].plural


def test_texto_vacio():
    # No necesita modelo: el texto vacío se resuelve antes de llamar a spaCy.
    a = Analizador.__new__(Analizador)
    assert a.sustantivos("   ") == []


@pytest.mark.parametrize("entrada,esperado", [("es-ES", "es"), ("en_US", "en"), ("EN", "en"), ("fr", None), (None, None)])
def test_normalizar_codigo(entrada, esperado):
    assert normalizar_codigo(entrada) == esperado


def test_idioma_no_soportado():
    with pytest.raises(ValueError):
        obtener_idioma("fr")


@requiere_modelo("es")
def test_es_no_descarta_sustantivos_por_entidades_espurias():
    # El NER marca esta frase como MISC aunque no tiene nombres propios.
    lemas = {s.lema for s in Analizador("es").sustantivos("Los niños jugaban con sus perros en el jardín.")}
    assert {"niño", "perro", "jardín"} <= lemas


@requiere_modelo("es")
def test_es_excluye_sustantivos_dentro_de_entidades_con_nombre_propio():
    textos = [s.texto for s in Analizador("es").sustantivos("Trabaja en el Banco de España desde hace un año.")]
    assert "Banco" not in textos
