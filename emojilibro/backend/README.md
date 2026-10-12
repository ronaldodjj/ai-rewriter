# EmojiLibro: backend (Fase 1, MVP)

Convierte un libro EPUB en una versión con emojis: detecta los sustantivos comunes
con spaCy y los reemplaza (o acompaña) con el emoji de un diccionario curado.
Conserva el HTML del libro: solo se modifican los nodos de texto.

Idiomas soportados: **español (`es`)** e **inglés (`en`)**.

## Instalación

```bash
cd emojilibro/backend
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
python -m spacy download es_core_news_lg
python -m spacy download en_core_web_lg
```

La instalación debe ser editable (`-e`): los diccionarios se leen desde `data/`.
Si no está el modelo `lg`, se usa el `md` o `sm` que esté instalado.

## Uso

```bash
emojilibro convertir libro.epub --modo acompañado
emojilibro convertir book.epub --modo reemplazo --plural duplicar -o salida.epub
```

| Opción | Valores | Por defecto |
|---|---|---|
| `--modo` | `reemplazo`, `acompañado` (o `acompanado`) | `acompañado` |
| `--idioma` | `es`, `en` | se detecta de `dc:language` del EPUB |
| `--plural` | `mismo` (👑), `duplicar` (👑👑), `marcador` (👑ˢ) | `mismo` |
| `--umbral` | confianza mínima, 0–1 | `0.7` |
| `--convertir-titulos` | también convierte `h1`–`h6` | desactivado |

Ejemplo (`reemplazo`): *El rey miró la ciudad desde la torre* → *El 👑 miró la 🏙️ desde la 🗼*.

## Cómo funciona

1. `extract/epub_reader.py` abre el EPUB y agrupa los nodos de texto por bloque
   (`<p>`, `<li>`…), para que spaCy analice la oración completa aunque tenga `<b>` o `<i>`.
   Ignora `script`, `style`, `code`, `ruby` y, por defecto, los títulos.
2. `nlp/analyzer.py` toma los tokens `NOUN` (nunca `PROPN`), con su lema y número.
   Descarta sustantivos dentro de entidades que contienen un nombre propio ("Banco de España").
3. `mapping/dictionary.py` busca el lema en `data/emoji_dict/<idioma>.json`.
   Solo se reemplaza si la confianza alcanza el umbral; las palabras ambiguas
   (`banco`, `pueblo`, `carta`, `tiempo`…) tienen confianza baja y se dejan igual hasta la Fase 2.
4. `render/text.py` aplica el modo y la regla de plural; `render/epub_writer.py` reempaqueta el EPUB.

## Diccionario

```json
{
  "rey": "👑",
  "banco": {"emoji": "🏦", "confianza": 0.5}
}
```

Un valor de texto equivale a confianza 1.0. Las claves son lemas en minúscula.

## Añadir un idioma

1. Añade una entrada en `app/nlp/languages.py` con los modelos spaCy del idioma.
2. Crea `data/emoji_dict/<codigo>.json`.
3. Los tests de diccionario se aplican automáticamente a todos los idiomas registrados.

## Tests

```bash
pytest
```

Los tests que necesitan un modelo de spaCy se saltan si no está instalado.
