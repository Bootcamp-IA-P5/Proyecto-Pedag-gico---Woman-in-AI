"""
Archivo: backend/app/tests/test_lyrics_scraper.py

Prueba rápida para verificar que Genius responde correctamente.

✅ NO toca Supabase
✅ Necesita GENIUS_ACCESS_TOKEN en backend/.env

Cómo ejecutarlo (desde backend/):
  uv run python -m app.tests.test_lyrics_scraper

Qué verás si funciona:
  - La letra limpia de una canción de prueba
  - El hash SHA256 generado
  - La variante de idioma detectada
"""

from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

from app.src.scraper.lyrics_scraper import buscar_letra, limpiar_letra, generar_hash, detectar_idioma


# Canción de prueba — conocida y en español
TITLE_PRUEBA  = "Hawái"
ARTIST_PRUEBA = "Maluma"


# ─── Test 1: ¿El token de Genius funciona? ───────────────────────────────────

def test_conexion_genius() -> bool:
    print("\n🔑 TEST 1 — Conexión con Genius")
    print("-" * 40)
    try:
        from app.src.config.genius_config import obtener_cliente_genius
        genius = obtener_cliente_genius()
        print("✅ Cliente Genius creado correctamente")
        return True
    except EnvironmentError as e:
        print(f"❌ {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False


# ─── Test 2: ¿Encuentra una canción? ─────────────────────────────────────────

def test_buscar_letra() -> dict | None:
    print(f"\n🔍 TEST 2 — Buscar letra en Genius")
    print("-" * 40)
    print(f"   Buscando: {ARTIST_PRUEBA} — {TITLE_PRUEBA}")

    letra = buscar_letra(TITLE_PRUEBA, ARTIST_PRUEBA)

    if letra:
        print(f"✅ Letra encontrada")
        print(f"   word_count        : {letra['word_count']}")
        print(f"   verse_count       : {letra['verse_count']}")
        print(f"   language_detected : {letra['language_detected']}")
        print(f"   lyrics_hash       : {letra['lyrics_hash'][:16]}...")
        print(f"   source            : {letra['source']}")
        print(f"   url_source        : {letra['url_source']}")
        return letra
    else:
        print("❌ No se encontró la letra")
        return None


# ─── Test 3: ¿La letra está limpia? ──────────────────────────────────────────

def test_letra_limpia(letra: dict) -> bool:
    print(f"\n🧹 TEST 3 — Verificar limpieza de letra")
    print("-" * 40)

    texto = letra["lyrics_text"]

    # Verificar que no quedan etiquetas [Coro], [Verso], etc.
    import re
    etiquetas = re.findall(r'\[.*?\]', texto)

    if etiquetas:
        print(f"⚠️  Aún quedan etiquetas: {etiquetas[:3]}")
        return False
    else:
        print("✅ Sin etiquetas [Coro], [Verso], etc.")

    # Mostrar primeras 3 líneas
    primeras_lineas = [l for l in texto.split('\n') if l.strip()][:3]
    print(f"\n   Primeras líneas de la letra:")
    for linea in primeras_lineas:
        print(f"   → {linea}")

    return True


# ─── Test 4: ¿El hash es consistente? ────────────────────────────────────────

def test_hash_consistente(letra: dict) -> bool:
    print(f"\n#️⃣  TEST 4 — Hash SHA256 consistente")
    print("-" * 40)

    hash1 = generar_hash(letra["lyrics_text"])
    hash2 = generar_hash(letra["lyrics_text"])

    if hash1 == hash2 == letra["lyrics_hash"]:
        print(f"✅ Hash consistente: {hash1[:16]}...")
        return True
    else:
        print("❌ Hash inconsistente — error en generar_hash()")
        return False


# ─── Ejecutar todos los tests ─────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 40)
    print("🧪 PRUEBA — Lyrics Scraper (sin Supabase)")
    print("=" * 40)

    ok1 = test_conexion_genius()

    if ok1:
        letra = test_buscar_letra()

        if letra:
            ok3 = test_letra_limpia(letra)
            ok4 = test_hash_consistente(letra)

            print("\n" + "=" * 40)
            if ok3 and ok4:
                print("✅ Todo correcto — puedes ejecutar scraping_lyrics.py")
            else:
                print("⚠️  Revisa los warnings antes de ejecutar el scraper real")
        else:
            print("\n⚠️  Genius no encontró la canción de prueba")
            print("   Verifica que el token es correcto")
    else:
        print("\n❌ Corrige el GENIUS_ACCESS_TOKEN en backend/.env")

    print("=" * 40)