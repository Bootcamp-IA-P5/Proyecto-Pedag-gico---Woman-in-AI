import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, Filter, BarChart3 } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from "recharts";
import { PageHeader } from "@/components/ui/PageHeader";
import { GlassCard } from "@/components/ui/GlassCard";
import { genreDistribution, yearlyTrends, songs, genres, years, genders } from "@/data/mockData";
import { cn } from "@/lib/utils";

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
  const [genre, setGenre] = useState("Todos");
  const [year, setYear] = useState("Todos");
  const [gender, setGender] = useState("Todos");
  const [chartType, setChartType] = useState<"bar" | "line" | "pie">("bar");

  const filteredSongs = useMemo(() => {
    return songs.filter((s) => {
      if (genre !== "Todos" && s.genre !== genre) return false;
      if (year !== "Todos" && s.year.toString() !== year) return false;
      if (gender !== "Todos") {
        const g = gender === "Masculino" ? "M" : "F";
        if (s.gender !== g) return false;
      }
      return true;
    });
  }, [genre, year, gender]);

  const genreStats = useMemo(() => {
    const counts: Record<string, number> = {};
    filteredSongs.forEach((s) => { counts[s.genre] = (counts[s.genre] || 0) + 1; });
    return Object.entries(counts).map(([name, value]) => ({
      name,
      value,
      fill: genreDistribution.find((g) => g.name === name)?.fill || "hsl(220, 15%, 40%)",
    }));
  }, [filteredSongs]);

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
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-muted-foreground">
          <span className="font-mono text-foreground">{filteredSongs.length}</span> resultados encontrados
        </p>
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
                    <Line type="monotone" dataKey="reggaeton" stroke={chartColors[0]} strokeWidth={2} dot={false} name="Reggaetón" />
                    <Line type="monotone" dataKey="vallenato" stroke={chartColors[2]} strokeWidth={2} dot={false} name="Vallenato" />
                    <Line type="monotone" dataKey="pop" stroke={chartColors[1]} strokeWidth={2} dot={false} name="Pop" />
                    <Line type="monotone" dataKey="rap" stroke={chartColors[3]} strokeWidth={2} dot={false} name="Rap" />
                  </LineChart>
                )}
              </ResponsiveContainer>
            </motion.div>
          </AnimatePresence>
        </GlassCard>

        {/* Filtered Songs List */}
        <GlassCard delay={0.25}>
          <h3 className="text-sm font-semibold text-foreground mb-4">Canciones Filtradas</h3>
          <div className="space-y-2 max-h-[300px] overflow-y-auto scrollbar-thin">
            {filteredSongs.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">No se encontraron resultados</p>
            ) : (
              filteredSongs.map((song, i) => (
                <motion.div
                  key={song.id}
                  initial={{ opacity: 0, x: 10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="flex items-center gap-3 p-2.5 rounded-lg hover:bg-muted/30 transition-colors"
                >
                  <div className="w-8 h-8 rounded-md bg-gradient-primary flex items-center justify-center text-xs font-bold text-primary-foreground">
                    {song.title[0]}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-foreground truncate">{song.title}</p>
                    <p className="text-xs text-muted-foreground">{song.artist} · {song.year}</p>
                  </div>
                  <span className="text-xs font-mono text-muted-foreground">{song.streams}</span>
                </motion.div>
              ))
            )}
          </div>
        </GlassCard>
      </div>
    </motion.div>
  );
}
