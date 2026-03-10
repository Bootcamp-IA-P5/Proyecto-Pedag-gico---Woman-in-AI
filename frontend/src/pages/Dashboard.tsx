import { motion } from "framer-motion";
import { LayoutDashboard, Music, TrendingUp, Users, Headphones, BarChart3 } from "lucide-react";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/ui/StatCard";
import { GlassCard } from "@/components/ui/GlassCard";
import { GenreTag } from "@/components/ui/GenreTag";
import { genreDistribution, monthlyStreams, topArtists, genderDistribution } from "@/data/mockData";

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload) return null;
  return (
    <div className="glass-strong rounded-lg px-3 py-2 text-xs shadow-lg">
      <p className="font-semibold text-foreground">{label}</p>
      {payload.map((p: any, i: number) => (
        <p key={i} className="text-muted-foreground">
          {p.name}: <span className="text-foreground font-mono">{p.value.toLocaleString()}</span>
        </p>
      ))}
    </div>
  );
};

export default function Dashboard() {
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
      <PageHeader icon={LayoutDashboard} title="Centro de Mando" subtitle="Visión general del ecosistema musical" />

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard icon={Music} title="Género Dominante" value="Reggaetón" subtitle="34% de los streams" gradient="primary" delay={0.1} trend={{ value: 5, label: "vs mes anterior" }} />
        <StatCard icon={TrendingUp} title="Top Streamed Year" value="2024" subtitle="9.2B reproducciones" gradient="accent" delay={0.15} trend={{ value: 12, label: "crecimiento anual" }} />
        <StatCard icon={Users} title="Artistas F/M" value="31% / 62%" subtitle="7% grupos" gradient="warm" delay={0.2} trend={{ value: 8, label: "mujeres +YoY" }} />
        <StatCard icon={Headphones} title="Canciones Analizadas" value="12,847" subtitle="Últimos 30 días" gradient="primary" delay={0.25} trend={{ value: 23, label: "vs periodo anterior" }} />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
        {/* Area Chart */}
        <GlassCard delay={0.3} className="lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-foreground">Streams Mensuales</h3>
              <p className="text-xs text-muted-foreground">Evolución 2024</p>
            </div>
            <BarChart3 className="w-4 h-4 text-muted-foreground" />
          </div>
          <ResponsiveContainer width="100%" height={240}>
            <AreaChart data={monthlyStreams}>
              <defs>
                <linearGradient id="streamGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="hsl(265, 90%, 65%)" stopOpacity={0.4} />
                  <stop offset="100%" stopColor="hsl(265, 90%, 65%)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="month" axisLine={false} tickLine={false} />
              <YAxis axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="streams" stroke="hsl(265, 90%, 65%)" strokeWidth={2} fill="url(#streamGradient)" name="Streams" />
            </AreaChart>
          </ResponsiveContainer>
        </GlassCard>

        {/* Pie Chart */}
        <GlassCard delay={0.35}>
          <div className="mb-4">
            <h3 className="text-sm font-semibold text-foreground">Distribución por Género</h3>
            <p className="text-xs text-muted-foreground">Artistas activos</p>
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

      {/* Top Artists */}
      <GlassCard delay={0.4}>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-semibold text-foreground">Top Artistas</h3>
            <p className="text-xs text-muted-foreground">Por reproducciones totales</p>
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
              <span className="w-6 text-center text-sm font-mono font-bold text-muted-foreground">
                {i + 1}
              </span>
              <div className="w-9 h-9 rounded-full bg-gradient-primary flex items-center justify-center text-sm font-bold text-primary-foreground">
                {artist.name[0]}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground truncate">{artist.name}</p>
                <div className="flex items-center gap-2">
                  <GenreTag genre={artist.genre} />
                  <span className="text-xs text-muted-foreground">{artist.gender === "F" ? "♀" : "♂"}</span>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm font-mono font-semibold text-foreground">{artist.streams}</p>
                <p className={`text-xs font-mono ${artist.change > 0 ? "text-neon-green" : "text-destructive"}`}>
                  {artist.change > 0 ? "+" : ""}{artist.change}%
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      </GlassCard>
    </motion.div>
  );
}
