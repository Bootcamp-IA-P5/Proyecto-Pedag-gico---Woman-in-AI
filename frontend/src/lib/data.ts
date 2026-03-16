import { supabase } from "@/lib/supabase";

export type SongRow = {
  id: number;
  title: string;
  artist: string;
  genre: string | null;
  year: number | null;
  streams: number | string | null;
  duration_seg: number | null;
  artist_gender: string | null;
  created_at: string | null;
};

export type EvaluationRow = {
  id: number;
  song_id: number;
  total_score: number | null;
  dominant_narrative: string | null;
  evaluated_at: string | null;
};

export function parseStreams(value: number | string | null | undefined): number {
  if (value == null) return 0;
  if (typeof value === "number") return Number.isFinite(value) ? value : 0;
  const clean = value.replace(/[^0-9.]/g, "");
  const parsed = Number(clean);
  return Number.isFinite(parsed) ? parsed : 0;
}

export function formatStreams(value: number): string {
  return new Intl.NumberFormat("es-CO").format(Math.round(value));
}

export function formatDuration(seconds: number | null | undefined): string {
  if (!seconds || seconds < 1) return "--:--";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}

export function normalizeArtistGender(value: string | null | undefined): "Masculino" | "Femenino" | "Grupo" | "No definido" {
  if (!value) return "No definido";
  const v = value.trim().toLowerCase();
  if (v === "m" || v.includes("mascul")) return "Masculino";
  if (v === "f" || v.includes("femen")) return "Femenino";
  if (v.includes("grupo") || v.includes("duo") || v.includes("duo")) return "Grupo";
  if (v.includes("desconocido")) return "No definido";
  return "No definido";
}

export function normalizeGenre(value: string | null | undefined): string {
  if (!value) return "Desconocido";
  const clean = value.trim();
  return clean.length ? clean : "Desconocido";
}

async function fetchAllRows<T>(table: string, select: string, orderBy: string, ascending = true): Promise<T[]> {
  const pageSize = 1000;
  let from = 0;
  let all: T[] = [];

  while (true) {
    const to = from + pageSize - 1;
    const { data, error } = await supabase
      .from(table)
      .select(select)
      .order(orderBy, { ascending })
      .range(from, to);

    if (error) throw error;
    const page = (data ?? []) as T[];
    all = all.concat(page);
    if (page.length < pageSize) break;
    from += pageSize;
  }

  return all;
}

export async function fetchSongs(): Promise<SongRow[]> {
  return fetchAllRows<SongRow>(
    "songs",
    "id,title,artist,genre,year,streams,duration_seg,artist_gender,created_at",
    "id",
    true,
  );
}

export async function fetchEvaluations(): Promise<EvaluationRow[]> {
  return fetchAllRows<EvaluationRow>(
    "llm_evaluations",
    "id,song_id,total_score,dominant_narrative,evaluated_at",
    "id",
    false,
  );
}
