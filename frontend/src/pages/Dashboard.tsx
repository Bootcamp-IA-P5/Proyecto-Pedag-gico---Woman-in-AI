import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { LayoutDashboard, Music, TrendingUp, Users, Headphones, BarChart3 } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, CartesianGrid } from "recharts";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/ui/StatCard";
import { GlassCard } from "@/components/ui/GlassCard";
import { GenreTag } from "@/components/ui/GenreTag";
import { fetchEvaluations, fetchSongs, formatStreams, normalizeArtistGender, normalizeGenre, parseStreams } from "@/lib/data";

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload) return null;
  return (
    <div className="glass-strong rounded-lg px-3 py-2 text-xs shadow-lg">
      <p className="font-semibold text-foreground">{label}</p>
      {payload.map((p: any, i: number) => (
        <p key={i} className="text-muted-foreground">
          {p.name}: <span className="text-foreground font-mono">{Math.round(p.value).toLocaleString()}</span>
        </p>
      ))}
    </div>
  );
};

export default function Dashboard() {
  const { data: songs = [], error: songsError } = useQuery({ queryKey: ["songs"], queryFn: fetchSongs });
  const { data: evaluations = [], error: evalsError } = useQuery({ queryKey: ["evaluations"], queryFn: fetchEvaluations });
  const dashboardError = songsError instanceof Error
    ? songsError.message
    : evalsError instanceof Error
      ? evalsError.message
      : null;

  const dominantGenre = useMemo(() => {
    const byGenre = new Map<string, number>();
    songs.forEach((s) => {
      const genre = normalizeGenre(s.genre);
      byGenre.set(genre, (byGenre.get(genre) || 0) + 1);
    });
    const top = [...byGenre.entries()].sort((a, b) => b[1] - a[1])[0];
    return top
      ? { genre: top[0], count: top[1], pct: songs.length ? Math.round((top[1] * 100) / songs.length) : 0 }
      : { genre: "N/A", count: 0, pct: 0 };
  }, [songs]);

  const genderDistribution = useMemo(() => {
    const male = songs.filter((s) => normalizeArtistGender(s.artist_gender) === "Masculino").length;
    const female = songs.filter((s) => normalizeArtistGender(s.artist_gender) === "Femenino").length;
    const group = songs.filter((s) => normalizeArtistGender(s.artist_gender) === "Grupo").length;
    const unknown = Math.max(0, songs.length - male - female - group);
    const total = Math.max(1, songs.length);
    return [
      { name: "Masculino", value: Math.round((male * 100) / total), fill: "hsl(220, 85%, 60%)" },
      { name: "Femenino", value: Math.round((female * 100) / total), fill: "hsl(330, 85%, 60%)" },
      { name: "Grupo", value: Math.round((group * 100) / total), fill: "hsl(195, 95%, 55%)" },
      { name: "No definido", value: Math.round((unknown * 100) / total), fill: "hsl(30, 80%, 55%)" },
    ];
  }, [songs]);

  const topSongsByStreams = useMemo(() => {
    return songs
      .map((s) => ({
        title: s.title,
        artist: s.artist,
        streams: parseStreams(s.streams),
      }))
      .sort((a, b) => b.streams - a.streams)
      .slice(0, 10)
      .reverse()
      .map((row) => ({
        label: `${row.title} · ${row.artist}`,
        streams: row.streams,
      }));
  }, [songs]);

  const topArtists = useMemo(() => {
    const acc = new Map<string, { name: string; streams: number; genre: string; gender: string }>();
    songs.forEach((s) => {
      const key = s.artist || "Artista desconocido";
      if (!acc.has(key)) {
        acc.set(key, {
          name: key,
          streams: 0,
          genre: normalizeGenre(s.genre),
          gender: normalizeArtistGender(s.artist_gender),
        });
      }
      const row = acc.get(key)!;
      row.streams += parseStreams(s.streams);
    });

    return [...acc.values()]
      .sort((a, b) => b.streams - a.streams)
      .slice(0, 5)
      .map((a) => ({ ...a, streamsLabel: formatStreams(a.streams) }));
  }, [songs]);

  const latestEvalBySong = useMemo(() => {
    const map = new Map<number, number>();
    evaluations.forEach((e) => {
      if (e.total_score == null) return;
      if (!map.has(e.song_id)) {
        map.set(e.song_id, Number(e.total_score));
      }
    });
    return map;
  }, [evaluations]);

  const riskByGenre = useMemo(() => {
    const sums = new Map<string, { total: number; count: number }>();
    songs.forEach((s) => {
      const score = latestEvalBySong.get(s.id);
      if (score == null) return;
      const genre = normalizeGenre(s.genre);
      const row = sums.get(genre) || { total: 0, count: 0 };
      row.total += score;
      row.count += 1;
      sums.set(genre, row);
    });
    const avg = [...sums.entries()].map(([genre, row]) => ({ genre, avg: row.total / Math.max(1, row.count) }));
    return avg.sort((a, b) => b.avg - a.avg)[0] || { genre: "N/A", avg: 0 };
  }, [songs, latestEvalBySong]);

  const riskByArtist = useMemo(() => {
    const sums = new Map<string, { total: number; count: number }>();
    songs.forEach((s) => {
      const score = latestEvalBySong.get(s.id);
      if (score == null) return;
      const artist = s.artist || "Artista desconocido";
      const row = sums.get(artist) || { total: 0, count: 0 };
      row.total += score;
      row.count += 1;
      sums.set(artist, row);
    });
    const avg = [...sums.entries()].map(([artist, row]) => ({ artist, avg: row.total / Math.max(1, row.count) }));
    return avg.sort((a, b) => b.avg - a.avg)[0] || { artist: "N/A", avg: 0 };
  }, [songs, latestEvalBySong]);

  const globalRiskAvg = useMemo(() => {
    const valid = evaluations.filter((e) => e.total_score != null);
    if (!valid.length) return 0;
    const total = valid.reduce((sum, e) => sum + Number(e.total_score), 0);
    return Math.round((total / valid.length) * 10) / 10;
  }, [evaluations]);

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
      <PageHeader icon={LayoutDashboard} title="Centro de Mando" subtitle="Visión general del ecosistema musical" />

      {dashboardError && (
        <div className="mb-4 rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-300">
          {dashboardError}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard
          icon={Music}
          title="Género Dominante"
          value={dominantGenre.genre}
          subtitle={`${dominantGenre.pct}% del catálogo`}
          gradient="primary"
          delay={0.1}
        />
        <StatCard
          icon={TrendingUp}
          title="Riesgo Promedio LLM"
          value={String(globalRiskAvg)}
          subtitle={`${evaluations.filter((e) => e.total_score != null).length} evaluaciones válidas`}
          gradient="accent"
          delay={0.15}
        />
        <StatCard
          icon={Users}
          title="Género con Mayor Score"
          value={riskByGenre.genre}
          subtitle={`score promedio ${Math.round(riskByGenre.avg * 10) / 10}`}
          gradient="warm"
          delay={0.2}
        />
        <StatCard
          icon={Headphones}
          title="Artista con Mayor Score"
          value={riskByArtist.artist}
          subtitle={`score promedio ${Math.round(riskByArtist.avg * 10) / 10}`}
          gradient="primary"
          delay={0.25}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
        <GlassCard delay={0.3} className="lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-foreground">Top 10 canciones por streams</h3>
              <p className="text-xs text-muted-foreground">Ranking directo por `songs.streams`</p>
            </div>
            <BarChart3 className="w-4 h-4 text-muted-foreground" />
          </div>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={topSongsByStreams} layout="vertical" margin={{ left: 40, right: 10 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis type="number" axisLine={false} tickLine={false} />
              <YAxis dataKey="label" type="category" width={220} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="streams" fill="hsl(46 100% 50%)" radius={[0, 6, 6, 0]} name="Streams" />
            </BarChart>
          </ResponsiveContainer>
        </GlassCard>

        <GlassCard delay={0.35}>
          <div className="mb-4">
            <h3 className="text-sm font-semibold text-foreground">Distribución por Tipo de Artista</h3>
            <p className="text-xs text-muted-foreground">Basado en artist_gender</p>
          </div>
          <ResponsiveContainer width="100%" height={180}>
            <PieChart>
              <Pie data={genderDistribution} cx="50%" cy="50%" innerRadius={50} outerRadius={75} dataKey="value" strokeWidth={0}>
                {genderDistribution.map((entry, i) => (
                  <Cell key={i} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex justify-center gap-4 mt-2">
            {genderDistribution.map((g) => (
              <div key={g.name} className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: g.fill }} />
                {g.name} ({g.value}%)
              </div>
            ))}
          </div>
        </GlassCard>
      </div>

      <GlassCard delay={0.4}>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-semibold text-foreground">Top Artistas</h3>
            <p className="text-xs text-muted-foreground">Por streams acumulados</p>
          </div>
        </div>
        <div className="space-y-3">
          {topArtists.map((artist, i) => (
            <motion.div
              key={artist.name}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.5 + i * 0.08 }}
              className="flex items-center gap-4 p-3 rounded-lg hover:bg-muted/30 transition-colors"
            >
              <span className="w-6 text-center text-sm font-mono font-bold text-muted-foreground">{i + 1}</span>
              <div className="w-9 h-9 rounded-full bg-gradient-primary flex items-center justify-center text-sm font-bold text-primary-foreground">
                {artist.name[0]}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground truncate">{artist.name}</p>
                <div className="flex items-center gap-2">
                  <GenreTag genre={artist.genre} />
                  <span className="text-xs text-muted-foreground">
                    {artist.gender === "Femenino" ? "♀" : artist.gender === "Masculino" ? "♂" : artist.gender === "Grupo" ? "◉" : "∎"}
                  </span>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm font-mono font-semibold text-foreground">{artist.streamsLabel}</p>
                <p className="text-xs font-mono text-muted-foreground">acumulado</p>
              </div>
            </motion.div>
          ))}
        </div>
      </GlassCard>
    </motion.div>
  );
}
