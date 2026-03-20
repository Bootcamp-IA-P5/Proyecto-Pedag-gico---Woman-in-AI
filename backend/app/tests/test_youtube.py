
from unittest.mock import patch, MagicMock
from app.src.scraper.youtube_scraper import obtener_tracks_region  # ← quitamos reset_sesion


def test_youtube_scraper():
    print("\n🚀 TEST YOUTUBE SCRAPER\n")

    # Simulamos la respuesta de YouTube sin necesitar API key
    respuesta_falsa = MagicMock()
    respuesta_falsa.raise_for_status = MagicMock()
    respuesta_falsa.json.return_value = {
        "items": [{
            "id": "abc123",
            "snippet": {
                "title": "Canción Test",
                "channelTitle": "Artista Test",
                "publishedAt": "2024-01-01T00:00:00Z",
                "thumbnails": {
                    "high": {
                        "url": "http://ejemplo.com/thumb.jpg"
                    }
                }
            },
            "statistics": {"viewCount": "1000000"},
            "contentDetails": {"duration": "PT3M30S"},
        }]
    }

    with patch("requests.get", return_value=respuesta_falsa):
        tracks = obtener_tracks_region("PE")

    assert isinstance(tracks, list)
    assert len(tracks) > 0