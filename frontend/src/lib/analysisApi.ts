export type AnalysisDimension = {
  dimension: string;
  puntuacion_groq?: number;
  puntuacion_openrouter?: number;
  fragmentos_groq?: string[];
  fragmentos_openrouter?: string[];
};

export type AnalysisResult = {
  song_id: string;
  titulo: string;
  artista: string;
  genero_musical: string;
  puntuacion_global: number;
  nivel_global: string;
  dimensiones: AnalysisDimension[];
  sin_sesgo: string[];
  dimensiones_discrepantes: string[];
  requiere_revision_humana: boolean;
  prompt_version: string;
  errores?: Array<{ error: string }>;
};

export type AnalyzeLyricsInput = {
  titulo: string;
  artista: string;
  genero_musical: string;
  letra: string;
};

const rawApiBase = import.meta.env.VITE_API_BASE_URL || "https://vertice-x243o.ondigitalocean.app";
const API_BASE = rawApiBase.trim().replace(/^['\"]|['\"]$/g, "").replace(/\/+$/, "");

async function fetchWithTimeout(url: string, options: RequestInit = {}, timeoutMs = 60000) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } finally {
    clearTimeout(timeout);
  }
}

async function parseResponseBody(response: Response) {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

export async function analyzeLyrics(payload: AnalyzeLyricsInput): Promise<AnalysisResult> {
  let response: Response;
  try {
    response = await fetchWithTimeout(`${API_BASE}/analysis/lyrics`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }, 120000);
  } catch (err: any) {
    if (err?.name === "AbortError") {
      throw new Error("El análisis está tardando demasiado. Intenta con una letra más corta o revisa el backend.");
    }
    throw new Error(`No hay conexión con el backend (${API_BASE}). ${err?.message || "Verifica despliegue activo y CORS para el origen actual."}`);
  }

  const data = await parseResponseBody(response);
  if (!response.ok) {
    const detail = typeof data?.detail === "string" ? data.detail : "No se pudo analizar la canción.";
    throw new Error(detail);
  }

  return data as AnalysisResult;
}

export async function analyzeSongById(songId: number): Promise<AnalysisResult> {
  let response: Response;
  try {
    response = await fetchWithTimeout(`${API_BASE}/analysis/song/${songId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    }, 120000);
  } catch (err: any) {
    if (err?.name === "AbortError") {
      throw new Error("El análisis por ID está tardando demasiado. Verifica si el backend está disponible.");
    }
    throw new Error(`No hay conexión con el backend (${API_BASE}). ${err?.message || "Verifica despliegue activo y CORS para el origen actual."}`);
  }

  const data = await parseResponseBody(response);
  if (!response.ok) {
    const detail = typeof data?.detail === "string" ? data.detail : "No se pudo analizar la canción por ID.";
    throw new Error(detail);
  }

  return data as AnalysisResult;
}
