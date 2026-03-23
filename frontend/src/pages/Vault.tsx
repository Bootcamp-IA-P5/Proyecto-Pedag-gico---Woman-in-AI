import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Database, Search, ArrowUpDown, Sparkles, Loader2, MessageSquare, PlayCircle } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { GlassCard } from "@/components/ui/GlassCard";
import { GenreTag } from "@/components/ui/GenreTag";
import { FeedbackBox } from "@/components/feedback/FeedbackBox";
import { cn } from "@/lib/utils";
import { fetchSongs, formatDuration, parseStreams } from "@/lib/data";
import { analyzeSongById, AnalysisResult } from "@/lib/analysisApi";

type SortField = "title" | "artist" | "streams" | "year";

export default function Vault() {
  const { data: songs = [], isLoading, error } = useQuery({ queryKey: ["songs"], queryFn: fetchSongs });

  const [search, setSearch] = useState("");
  const [sortField, setSortField] = useState<SortField>("streams");
  const [sortAsc, setSortAsc] = useState(false);
  const [analyzingId, setAnalyzingId] = useState<number | null>(null);
  const [feedbackSongId, setFeedbackSongId] = useState<number | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [visibleCount, setVisibleCount] = useState(100);

  const filtered = useMemo(() => {
    return songs
      .filter((s) => {
        const q = search.toLowerCase();
        const title = (s.title || "").toLowerCase();
        const artist = (s.artist || "").toLowerCase();
        return title.includes(q) ||
          artist.includes(q) ||
          (s.genre || "").toLowerCase().includes(q);
      })
      .sort((a, b) => {
        let cmp = 0;
        if (sortField === "title") cmp = a.title.localeCompare(b.title);
        else if (sortField === "artist") cmp = a.artist.localeCompare(b.artist);
        else if (sortField === "year") cmp = (a.year || 0) - (b.year || 0);
        else cmp = parseStreams(a.streams) - parseStreams(b.streams);
        return sortAsc ? cmp : -cmp;
      });
  }, [songs, search, sortField, sortAsc]);

  const visibleRows = useMemo(() => filtered.slice(0, visibleCount), [filtered, visibleCount]);
  const canShowMore = filtered.length > visibleCount;

  useEffect(() => {
    setVisibleCount(100);
  }, [search, sortField, sortAsc]);

  const toggleSort = (field: SortField) => {
    if (sortField === field) setSortAsc(!sortAsc);
    else { setSortField(field); setSortAsc(false); }
  };

  const runAnalysisById = async (songId: number) => {
    setAnalysisError(null);
    setAnalyzingId(songId);
    try {
      const result = await analyzeSongById(songId);
      setAnalysisResult(result);
    } catch (err: any) {
      setAnalysisError(err?.message || "No se pudo analizar la canción seleccionada.");
    } finally {
      setAnalyzingId(null);
    }
  };

  const openSongReference = (title: string, artist: string) => {
    const query = encodeURIComponent(`${title} ${artist}`.trim());
    window.open(`https://open.spotify.com/search/${query}`, "_blank", "noopener,noreferrer");
  };

  const SortHeader = ({ field, label }: { field: SortField; label: string }) => (
    <button
      onClick={() => toggleSort(field)}
      className={cn(
        "flex items-center gap-1 text-xs font-medium uppercase tracking-wider cursor-pointer transition-colors",
        sortField === field ? "text-primary" : "text-muted-foreground hover:text-foreground"
      )}
    >
      {label}
      <ArrowUpDown className="w-3 h-3" />
    </button>
  );

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
      <PageHeader icon={Database} title="Bóveda de Datos" subtitle="Todas las canciones del scanner" />

      {/* Search */}
      <GlassCard delay={0.1} hover={false} className="mb-6">
        <div className="flex items-center gap-3">
          <Search className="w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar por título, artista o género..."
            className="flex-1 bg-transparent border-none outline-none text-sm text-foreground placeholder:text-muted-foreground"
          />
          <span className="text-xs font-mono text-muted-foreground">{isLoading ? "cargando..." : `${filtered.length} canciones`}</span>
        </div>
      </GlassCard>

      {/* Data Grid */}
      <GlassCard delay={0.15} hover={false}>
        {analysisError && (
          <div className="mb-3 rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-300">
            {analysisError}
          </div>
        )}

        {analysisResult && (
          <>
            <div className="mb-3 rounded-md border border-border/50 bg-background/60 px-3 py-2 text-xs text-muted-foreground">
              Último análisis: <span className="text-foreground">{analysisResult.titulo}</span> · {analysisResult.nivel_global} ({analysisResult.puntuacion_global})
            </div>
            <div className="mb-3">
              <FeedbackBox
                storageKey={`feedback:analysis:${analysisResult.song_id}`}
                title={`Feedback del resultado (${analysisResult.titulo})`}
                placeholder="¿El resultado te pareció coherente? Déjanos comentarios."
              />
            </div>
          </>
        )}

        {error && (
          <div className="mb-3 rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-300">
            No se pudo cargar la bóveda desde Supabase.
          </div>
        )}

        {/* Header */}
        <div className="grid grid-cols-[40px_minmax(180px,1fr)_minmax(180px,1fr)_120px_80px_120px_240px] gap-3 px-3 py-2.5 border-b border-border/50 items-center">
          <span className="text-xs text-muted-foreground">#</span>
          <SortHeader field="title" label="Título" />
          <SortHeader field="artist" label="Artista" />
          <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">Género</span>
          <SortHeader field="year" label="Año" />
          <SortHeader field="streams" label="Streams" />
          <span className="text-xs text-muted-foreground text-right">Acciones</span>
        </div>

        {/* Rows */}
        <div className="divide-y divide-border/30">
          {isLoading && (
            <div className="px-3 py-6 text-sm text-muted-foreground">Cargando catálogo...</div>
          )}
          {visibleRows.map((song, i) => (
            <div key={song.id}>
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: Math.min(i * 0.005, 0.2) }}
                className={cn(
                  "grid grid-cols-[40px_minmax(180px,1fr)_minmax(180px,1fr)_120px_80px_120px_240px] gap-3 px-3 py-3 items-center hover:bg-muted/20 transition-colors"
                )}
              >
                <span className="text-xs font-mono text-muted-foreground">{i + 1}</span>
                <div className="min-w-0">
                  <p className="text-sm font-medium text-foreground truncate">{song.title}</p>
                  <p className="text-xs text-muted-foreground">{formatDuration(song.duration_seg)}</p>
                </div>
                <div className="flex items-center gap-2 min-w-0">
                  <div className="w-7 h-7 rounded-full bg-gradient-primary flex items-center justify-center text-[10px] font-bold text-primary-foreground flex-shrink-0">
                      {(song.artist || "?").charAt(0)}
                  </div>
                  <span className="text-sm text-foreground truncate">{song.artist}</span>
                </div>
                <GenreTag genre={song.genre || "Desconocido"} />
                <span className="text-sm font-mono text-muted-foreground">{song.year ?? "N/A"}</span>
                <span className="text-sm font-mono text-foreground">{parseStreams(song.streams).toLocaleString("es-CO")}</span>
                <div className="flex items-center justify-end gap-1.5 flex-wrap">
                  <button
                    onClick={() => openSongReference(song.title, song.artist)}
                    className="rounded-md border border-border/40 px-2 py-1 text-xs hover:border-primary/60"
                  >
                    <span className="inline-flex items-center gap-1"><PlayCircle className="h-3 w-3" />Escuchar</span>
                  </button>
                  <button
                    onClick={() => setFeedbackSongId((prev) => (prev === song.id ? null : song.id))}
                    className="rounded-md border border-border/40 px-2 py-1 text-xs hover:border-primary/60"
                  >
                    <span className="inline-flex items-center gap-1"><MessageSquare className="h-3 w-3" />Comentar</span>
                  </button>
                  <button
                    onClick={() => runAnalysisById(song.id)}
                    disabled={analyzingId === song.id}
                    className="rounded-md border border-border/40 px-2 py-1 text-xs hover:border-primary/60 disabled:opacity-50"
                  >
                    {analyzingId === song.id ? (
                      <span className="inline-flex items-center gap-1"><Loader2 className="h-3 w-3 animate-spin" />Analizando</span>
                    ) : (
                      <span className="inline-flex items-center gap-1"><Sparkles className="h-3 w-3" />Analizar</span>
                    )}
                  </button>
                </div>
              </motion.div>

              {feedbackSongId === song.id && (
                <div className="px-3 pb-3">
                  <FeedbackBox
                    storageKey={`feedback:song:${song.id}`}
                    title={`Feedback de canción: ${song.title}`}
                    placeholder="Escribe observaciones sobre esta canción o su clasificación."
                  />
                </div>
              )}
            </div>
          ))}

          {!isLoading && filtered.length === 0 && (
            <div className="px-3 py-6 text-sm text-muted-foreground">No hay canciones para mostrar con el filtro actual.</div>
          )}
        </div>

        {canShowMore && (
          <div className="mt-4 flex justify-center">
            <button
              onClick={() => setVisibleCount((current) => current + 100)}
              className="rounded-md border border-border/40 px-3 py-1.5 text-xs hover:border-primary/60"
            >
              Ver más canciones
            </button>
          </div>
        )}
      </GlassCard>
    </motion.div>
  );
}
