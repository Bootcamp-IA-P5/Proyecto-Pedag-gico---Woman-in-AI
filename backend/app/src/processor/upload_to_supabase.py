from app.src.config.supabase_client import supabase

def subir_cancion(datos_cancion):
    """
    Recibe un diccionario con: ranking_position, title, artist, etc.
    """
    try:
        response = supabase.table("songs").insert(datos_cancion).execute()
        print(f"✅ Guardada: {datos_cancion['title']}")
        return response
    except Exception as e:
        print(f"❌ Error: {e}")