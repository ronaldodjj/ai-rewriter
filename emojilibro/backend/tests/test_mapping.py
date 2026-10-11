import json

import pytest

from app.config import DATA_DIR, Config
from app.mapping.dictionary import Asignacion, DiccionarioEmojis, cargar_diccionario
from app.nlp.languages import IDIOMAS
from app.render.text import Reemplazo, aplicar, forma_emoji


@pytest.mark.parametrize("idioma", sorted(IDIOMAS))
def test_hay_diccionario_por_idioma(idioma):
    d = cargar_diccionario(idioma)
    assert len(d) >= 100


@pytest.mark.parametrize("idioma", sorted(IDIOMAS))
def test_diccionario_bien_formado(idioma):
    datos = json.loads((DATA_DIR / "emoji_dict" / f"{idioma}.json").read_text(encoding="utf-8"))
    for lema, valor in datos.items():
        assert lema == lema.lower(), lema
        if isinstance(valor, dict):
            assert valor["emoji"] and 0 <= valor["confianza"] <= 1, lema
        else:
            assert valor, lema


def test_busqueda_basica():
    assert cargar_diccionario("es").buscar("rey") == Asignacion("👑", 1.0)
    assert cargar_diccionario("en").buscar("King") == Asignacion("👑", 1.0)
    assert cargar_diccionario("es").buscar("justicia") is None


def test_palabras_ambiguas_quedan_bajo_el_umbral():
    umbral = Config().umbral_confianza
    for idioma, palabra in (("es", "banco"), ("en", "bank"), ("es", "pueblo")):
        assert cargar_diccionario(idioma).buscar(palabra).confianza < umbral


def test_desde_json_admite_ambos_formatos(tmp_path):
    ruta = tmp_path / "x.json"
    ruta.write_text('{"Sol": "☀️", "banco": {"emoji": "🏦", "confianza": 0.4}}', encoding="utf-8")
    d = DiccionarioEmojis.desde_json(ruta)
    assert d.buscar("sol") == Asignacion("☀️", 1.0)
    assert d.buscar("banco") == Asignacion("🏦", 0.4)


@pytest.mark.parametrize("estrategia,esperado", [("mismo", "👑"), ("duplicar", "👑👑"), ("marcador", "👑ˢ")])
def test_forma_plural(estrategia, esperado):
    assert forma_emoji("👑", True, estrategia) == esperado
    assert forma_emoji("👑", False, estrategia) == "👑"


def test_aplicar_modos():
    texto = "El rey miró la ciudad."
    r = [Reemplazo(3, 6, "👑"), Reemplazo(15, 21, "🏙️")]
    assert aplicar(texto, r, "reemplazo") == "El 👑 miró la 🏙️."
    assert aplicar(texto, r, "acompañado") == "El rey 👑 miró la ciudad 🏙️."


def test_aplicar_plural_duplicado():
    assert aplicar("Los reyes.", [Reemplazo(4, 9, "👑", True)], "reemplazo", "duplicar") == "Los 👑👑."


def test_config_valida():
    assert Config(modo="acompanado").modo == "acompañado"
    with pytest.raises(ValueError):
        Config(modo="ruby")
    with pytest.raises(ValueError):
        Config(umbral_confianza=2)
