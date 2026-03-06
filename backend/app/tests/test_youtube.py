from app.src.scraper.youtube_scraper import obtener_tracks_region
from app.src.processor.normalizer import normalizar_track, reset_sesion


def test_youtube_scraper():

    print("\n🚀 TEST YOUTUBE SCRAPER\n")

    # reset para evitar duplicados en sesión
    reset_sesion()

    pais = "PE"

    tracks = obtener_tracks_region(pais)

    # ─────────────
    # TEST 1: existen tracks
    # ─────────────
    assert tracks is not None, "❌ El scraper devolvió None"
    assert len(tracks) > 0, "❌ No se obtuvieron canciones de YouTube"

    print(f"✅ Tracks obtenidos: {len(tracks)}")

    tracks_validos = []
    titulos = set()

    for track in tracks:

        # ─────────────
        # TEST 2: campos mínimos
        # ─────────────
        assert "title" in track, "❌ falta title"
        assert "artist" in track, "❌ falta artist"
        assert "url_source" in track, "❌ falta url_source"

        # ─────────────
        # pasar por normalizador
        # ─────────────
        track_normalizado = normalizar_track(track)

        if track_normalizado is None:
            continue

        tracks_validos.append(track_normalizado)

        # ─────────────
        # TEST 3: no duplicados
        # ─────────────
        titulo = track_normalizado["title"]

        assert titulo not in titulos, f"❌ duplicado detectado: {titulo}"

        titulos.add(titulo)

    # ─────────────
    # TEST 4: normalizador produjo resultados
    # ─────────────
    assert len(tracks_validos) > 0, "❌ ningún track pasó el normalizador"

    print(f"✅ Tracks después de normalizar: {len(tracks_validos)}")

    # ─────────────
    # mostrar ejemplos
    # ─────────────
    print("\n🎵 EJEMPLOS NORMALIZADOS\n")

    for track in tracks_validos[:5]:

        print("------")
        print("artista:", track["artist"])
        print("titulo :", track["title"])
        print("streams:", track.get("streams"))
        print("url    :", track.get("url_source"))

    print("\n✅ TEST COMPLETADO\n")


if __name__ == "__main__":
    test_youtube_scraper()