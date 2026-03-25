import { useState, useMemo, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { Search, Filter, BarChart3, Sparkles, Loader2, MessageSquare } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from "recharts";
import { PageHeader } from "@/components/ui/PageHeader";
import { GlassCard } from "@/components/ui/GlassCard";
import { FeedbackBox } from "@/components/feedback/FeedbackBox";
import { cn } from "@/lib/utils";
import { fetchSongs, normalizeArtistGender, normalizeGenre, parseStreams } from "@/lib/data";
import { analyzeSongById, AnalysisResult } from "@/lib/analysisApi";

const chartColors = [
  "hsl(330, 85%, 60%)", "hsl(265, 90%, 65%)", "hsl(155, 80%, 50%)",
  "hsl(220, 85%, 60%)", "hsl(195, 95%, 55%)",
];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload) return null;
  return (
    <div className="glass-strong rounded-lg px-3 py-2 text-xs shadow-lg">
      <p className="font-semibold text-foreground">{label}</p>
      {payload.map((p: any, i: number) => (
        <p key={i} style={{ color: p.color }} className="capitalize">
          {p.name}: <span className="font-mono">{p.value}%</span>
        </p>
      ))}
    </div>
  );
};

function FilterSelect({ label, options, value, onChange }: { label: string; options: string[]; value: string; onChange: (v: string) => void }) {
  return (
    <div className="space-y-1.5">
      <label className="text-xs font-medium uppercase tracking-wider text-muted-foreground">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full bg-muted/50 border border-border/50 rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:border-primary/50 transition-colors appearance-none cursor-pointer"
      >
        {options.map((opt) => (
          <option key={opt} value={opt} className="bg-card text-foreground">{opt}</option>
        ))}
      </select>
    </div>
  );
}

export default function Explorer() {
  const { data: songs = [], isLoading, error } = useQuery({ queryKey: ["songs"], queryFn: fetchSongs });

  const genres = useMemo(() => {
    const unique = Array.from(new Set(songs.map((s) => normalizeGenre(s.genre)))).sort();
    return ["Todos", ...unique];
  }, [songs]);

  const years = useMemo(() => {
    const unique = Array.from(new Set(songs.map((s) => String(s.year ?? "Desconocido")))).sort();
    return ["Todos", ...unique];
  }, [songs]);

  const genders = ["Todos", "Masculino", "Femenino", "Grupo", "No definido"];

  const [genre, setGenre] = useState("Todos");
  const [year, setYear] = useState("Todos");
  const [gender, setGender] = useState("Todos");
  const [chartType, setChartType] = useState<"bar" | "line" | "pie">("bar");
  const [analyzingId, setAnalyzingId] = useState<number | null>(null);
  const [feedbackSongId, setFeedbackSongId] = useState<number | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [visibleCount, setVisibleCount] = useState(100);

  const filteredSongs = useMemo(() => {
    return songs.filter((s) => {
      const sGenre = s.genre || "Desconocido";
      const sYear = String(s.year ?? "Desconocido");
      const sGender = normalizeArtistGender(s.artist_gender);

      if (genre !== "Todos" && normalizeGenre(sGenre) !== genre) return false;
      if (year !== "Todos" && sYear !== year) return false;
      if (gender !== "Todos") {
        if (sGender !== gender) return false;
      }
      return true;
    });
  }, [genre, year, gender]);

  const genreStats = useMemo(() => {
    const counts: Record<string, number> = {};
    const colorByIndex = [
      "hsl(330, 85%, 60%)",
      "hsl(265, 90%, 65%)",
      "hsl(155, 80%, 50%)",
      "hsl(220, 85%, 60%)",
      "hsl(195, 95%, 55%)",
    ];

    filteredSongs.forEach((s) => {
      const g = normalizeGenre(s.genre);
      counts[g] = (counts[g] || 0) + 1;
    });

    return Object.entries(counts).map(([name, value]) => ({
      name,
      value,
      fill: colorByIndex[Math.abs(name.length) % colorByIndex.length],
    }));
  }, [filteredSongs]);

  const yearlyTrends = useMemo(() => {
    const map = new Map<string, any>();
    songs.forEach((s) => {
      const yearLabel = String(s.year ?? "N/A");
      if (!map.has(yearLabel)) {
        map.set(yearLabel, { year: yearLabel, total: 0, Reggaeton: 0, Vallenato: 0, Pop: 0, Rap: 0 });
      }
      const row = map.get(yearLabel);
      row.total += 1;
      const genreName = normalizeGenre(s.genre).toLowerCase();
      if (genreName.includes("regga")) row.Reggaeton += 1;
      else if (genreName.includes("vallen")) row.Vallenato += 1;
      else if (genreName.includes("pop")) row.Pop += 1;
      else if (genreName.includes("rap")) row.Rap += 1;
    });
    return [...map.values()].sort((a, b) => Number(a.year) - Number(b.year));
  }, [songs]);

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

  const visibleSongs = useMemo(() => filteredSongs.slice(0, visibleCount), [filteredSongs, visibleCount]);

  const canShowMore = filteredSongs.length > visibleCount;

  useEffect(() => {
    setVisibleCount(100);
  }, [genre, year, gender]);

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
      <PageHeader icon={Search} title="Explorador Profundo" subtitle="Análisis dinámico con filtros cruzados" />

      {/* Filters */}
      <GlassCard delay={0.1} hover={false} className="mb-6">
        <div className="flex items-center gap-2 mb-4">
          <Filter className="w-4 h-4 text-primary" />
          <h3 className="text-sm font-semibold text-foreground">Filtros de Exploración</h3>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <FilterSelect label="Género Musical" options={genres} value={genre} onChange={setGenre} />
          <FilterSelect label="Año" options={years} value={year} onChange={setYear} />
          <FilterSelect label="Género Artista" options={genders} value={gender} onChange={setGender} />
        </div>
      </GlassCard>

      {/* Chart Type Selector + Results */}
      <div className="flex items-center justify-end mb-4">
        <div className="flex gap-1 p-1 rounded-lg bg-muted/50">
          {(["bar", "line", "pie"] as const).map((type) => (
            <button
              key={type}
              onClick={() => setChartType(type)}
              className={cn(
                "px-3 py-1.5 rounded-md text-xs font-medium transition-all cursor-pointer capitalize",
                chartType === type ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"
              )}
            >
              {type === "bar" ? "Barras" : type === "line" ? "Líneas" : "Circular"}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Dynamic Chart */}
        <GlassCard delay={0.2}>
          <h3 className="text-sm font-semibold text-foreground mb-4">Distribución de Resultados</h3>
          <AnimatePresence mode="wait">
            <motion.div key={chartType + genre + year + gender} initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }} transition={{ duration: 0.3 }}>
              <ResponsiveContainer width="100%" height={280}>
                {chartType === "bar" ? (
                  <BarChart data={genreStats}>
                    <XAxis dataKey="name" axisLine={false} tickLine={false} />
                    <YAxis axisLine={false} tickLine={false} />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="value" radius={[6, 6, 0, 0]} name="Canciones">
                      {genreStats.map((entry, i) => (
                        <Cell key={i} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                ) : chartType === "pie" ? (
                  <PieChart>
                    <Pie data={genreStats} cx="50%" cy="50%" innerRadius={60} outerRadius={100} dataKey="value" strokeWidth={0}>
                      {genreStats.map((entry, i) => (
                        <Cell key={i} fill={entry.fill} />
                      ))}
                    </Pie>
                    <Tooltip content={<CustomTooltip />} />
                  </PieChart>
                ) : (
                  <LineChart data={yearlyTrends}>
                    <XAxis dataKey="year" axisLine={false} tickLine={false} />
                    <YAxis axisLine={false} tickLine={false} />
                    <Tooltip content={<CustomTooltip />} />
                    <Line type="monotone" dataKey="Reggaeton" stroke={chartColors[0]} strokeWidth={2} dot={false} name="Reggaetón" />
                    <Line type="monotone" dataKey="Vallenato" stroke={chartColors[2]} strokeWidth={2} dot={false} name="Vallenato" />
                    <Line type="monotone" dataKey="Pop" stroke={chartColors[1]} strokeWidth={2} dot={false} name="Pop" />
                    <Line type="monotone" dataKey="Rap" stroke={chartColors[3]} strokeWidth={2} dot={false} name="Rap" />
                  </LineChart>
                )}
              </ResponsiveContainer>
            </motion.div>
          </AnimatePresence>
        </GlassCard>

        {/* Filtered Songs List */}
        <GlassCard delay={0.25}>
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-foreground">Canciones Filtradas</h3>
            {analysisResult && (
              <span className="text-xs text-muted-foreground">Último análisis: {analysisResult.nivel_global} ({analysisResult.puntuacion_global})</span>
            )}
          </div>

          {isLoading && (
            <div className="mb-3 rounded-md border border-border/40 bg-background/60 px-3 py-2 text-xs text-muted-foreground">
              Cargando canciones desde Supabase...
            </div>
          )}

          {error && (
            <div className="mb-3 rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-300">
              No se pudieron cargar las canciones para el explorador.
            </div>
          )}

          {analysisError && (
            <div className="mb-3 rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-300">
              {analysisError}
            </div>
          )}

          {analysisResult && (
            <div className="mb-3">
              <FeedbackBox
                storageKey={`feedback:analysis:${analysisResult.song_id}`}
                title={`Feedback del resultado (${analysisResult.titulo})`}
                placeholder="¿Qué tan útil fue este resultado? ¿Qué cambiarías?"
              />
            </div>
          )}

          <div className="space-y-2 max-h-[300px] overflow-y-auto scrollbar-thin">
            {filteredSongs.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">No se encontraron resultados</p>
            ) : (
              visibleSongs.map((song, i) => (
                <div key={song.id} className="space-y-2 rounded-lg">
                  <motion.div
                    initial={{ opacity: 0, x: 10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: Math.min(i * 0.01, 0.2) }}
                    className="flex items-center gap-3 p-2.5 rounded-lg hover:bg-muted/30 transition-colors"
                  >
                    <div className="w-8 h-8 rounded-md bg-gradient-primary flex items-center justify-center text-xs font-bold text-primary-foreground">
                      {(song.title || "?").charAt(0)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-foreground truncate">{song.title}</p>
                      <p className="text-xs text-muted-foreground">{song.artist} · {song.year ?? "N/A"}</p>
                    </div>
                    <span className="text-xs font-mono text-muted-foreground">{parseStreams(song.streams).toLocaleString("es-CO")}</span>

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
                  </motion.div>

                  {feedbackSongId === song.id && (
                    <div className="px-2">
                      <FeedbackBox
                        storageKey={`feedback:song:${song.id}`}
                        title={`Feedback de canción: ${song.title}`}
                        placeholder="Escribe observaciones sobre esta canción o su contexto."
                      />
                    </div>
                  )}
                </div>
              ))
            )}
          </div>

          {canShowMore && (
            <div className="mt-3 flex justify-center">
              <button
                onClick={() => setVisibleCount((current) => current + 100)}
                className="rounded-md border border-border/40 px-3 py-1.5 text-xs hover:border-primary/60"
              >
                Ver más
              </button>
            </div>
          )}
        </GlassCard>
      </div>
    </motion.div>
  );
}
