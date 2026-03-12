# backend/app/src/scraper/artist_gender.py
import json
from groq import Groq
from app.src.config.supabase_client import supabase

client = Groq()
LOTE = 50

def get_gender_lote(artistas: list[str]) -> dict[str, str]:
    lista = "\n".join(f"- {a}" for a in artistas)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=1000,
        messages=[{"role": "user", "content": (
            "Para cada artista musical de la lista indica su género.\n"
            "Responde SOLO con un JSON válido, sin explicaciones ni markdown:\n"
            '{"artistas": [{"artist": "nombre", "artist_gender": "genero"}, ...]}\n'
            "Valores permitidos para artist_gender:\n"
            "  - masculino   → artista hombre\n"
            "  - femenino    → artista mujer\n"
            "  - duo         → dos artistas (hombre+mujer, hombre+hombre, mujer+mujer)\n"
            "  - grupo       → tres o más artistas\n"
            "  - desconocido → no se puede determinar\n"
            "IMPORTANTE: incluir TODOS los artistas sin excepción.\n\n"
            f"{lista}"
        )}]
    )
    data = json.loads(response.choices[0].message.content.strip())
    return {item["artist"].strip(): item["artist_gender"].strip() for item in data["artistas"]}


def run():
    # 1. Todos los artistas únicos del dataset
    rows = (
        supabase.table("songs")
        .select("artist")
        .execute()
        .data
    )

    artistas = list({r["artist"] for r in rows})
    print(f"🎤 {len(artistas)} artistas — reescribiendo con nueva nomenclatura en lotes de {LOTE}")

    # 2. Procesa en lotes
    for i in range(0, len(artistas), LOTE):
        lote = artistas[i:i + LOTE]
        print(f"  📦 Lote {i // LOTE + 1} ({len(lote)} artistas)...")

        try:
            gender_map = get_gender_lote(lote)
        except Exception as e:
            print(f"  ❌ Error en lote: {e}")
            continue

        # 3. Sobreescribe en Supabase
        for artist, gender in gender_map.items():
            supabase.table("songs")\
                .update({"artist_gender": gender})\
                .eq("artist", artist)\
                .execute()
            print(f"    ✅ {artist} → {gender}")

if __name__ == "__main__":
    run()