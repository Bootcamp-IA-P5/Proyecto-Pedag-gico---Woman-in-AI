from app.src.config.supabase_client import supabase

def reset_letras():
    print("🔹 Eliminando todas las letras de lyrics_raw ...")
    supabase.table("lyrics_raw").delete().neq("song_id", 0).execute()

    print("🔹 Eliminando todas las letras de lyrics ...")
    supabase.table("lyrics").delete().neq("song_id", 0).execute()

    print("🔹 Marcando todas las canciones como pendientes de letra ...")
    supabase.table("songs").update({"lyrics_status": "pending"}).neq("id", 0).execute()

    print("✅ Tablas reseteadas y canciones marcadas como 'pending'.")

if __name__ == "__main__":
    reset_letras()