import { useState } from "react";
import { motion } from "framer-motion";
import { User, Pin, Clock, Star, BarChart3, TrendingUp, Music } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { GlassCard } from "@/components/ui/GlassCard";
import { GenreTag } from "@/components/ui/GenreTag";
import { cn } from "@/lib/utils";

const searchHistory = [
  { query: "Tendencia vallenato 2024", timestamp: "Hace 2h", results: 45 },
  { query: "Artistas femeninas reggaetón", timestamp: "Hace 5h", results: 128 },
  { query: "Top streams 2023 vs 2024", timestamp: "Ayer", results: 89 },
  { query: "Nuevos artistas colombianos", timestamp: "Hace 2 días", results: 67 },
  { query: "Evolución del rap latino", timestamp: "Hace 3 días", results: 156 },
];

const pinnedCharts = [
  { title: "Distribución de Géneros 2024", type: "Pie Chart", genre: "Reggaetón", pinned: "Hace 1 día" },
  { title: "Streams Mensuales Q4", type: "Area Chart", genre: "Pop", pinned: "Hace 3 días" },
  { title: "Top 10 Artistas Femeninas", type: "Bar Chart", genre: "Vallenato", pinned: "Hace 1 semana" },
];

const achievements = [
  { icon: BarChart3, title: "Explorador", desc: "100 consultas realizadas", progress: 72 },
  { icon: TrendingUp, title: "Analista", desc: "50 gráficos generados", progress: 45 },
  { icon: Star, title: "Curador", desc: "25 gráficos guardados", progress: 60 },
  { icon: Music, title: "Melómano", desc: "Explorar 10 géneros", progress: 80 },
];

export default function Profile() {
  const [activeTab, setActiveTab] = useState<"history" | "pinned">("history");

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
      <PageHeader icon={User} title="Mi Perfil" subtitle="Tu espacio personal de análisis" />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profile Card */}
        <GlassCard delay={0.1} className="lg:row-span-2" glow="purple">
          <div className="flex flex-col items-center text-center">
            <div className="w-20 h-20 rounded-2xl bg-gradient-primary flex items-center justify-center mb-4 glow-purple animate-float">
              <User className="w-10 h-10 text-primary-foreground" />
            </div>
            <h2 className="text-lg font-bold text-foreground">Analista</h2>
            <p className="text-sm text-muted-foreground mb-4">Explorador de datos musicales</p>
            <div className="w-full space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Consultas</span>
                <span className="font-mono text-foreground">247</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Gráficos Guardados</span>
                <span className="font-mono text-foreground">15</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Nivel</span>
                <span className="font-mono text-gradient-primary font-semibold">Pro</span>
              </div>
            </div>
          </div>

          {/* Achievements */}
          <div className="mt-6 pt-6 border-t border-border/50">
            <h3 className="text-sm font-semibold text-foreground mb-3">Logros</h3>
            <div className="space-y-3">
              {achievements.map((a, i) => (
                <div key={i} className="space-y-1.5">
                  <div className="flex items-center gap-2">
                    <a.icon className="w-3.5 h-3.5 text-primary" />
                    <span className="text-xs font-medium text-foreground">{a.title}</span>
                    <span className="ml-auto text-[10px] font-mono text-muted-foreground">{a.progress}%</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-muted/50 overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${a.progress}%` }}
                      transition={{ duration: 1, delay: 0.5 + i * 0.1 }}
                      className="h-full rounded-full bg-gradient-primary"
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </GlassCard>

        {/* Tabs */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex gap-1 p-1 rounded-lg bg-muted/30 w-fit">
            {(["history", "pinned"] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={cn(
                  "flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all cursor-pointer",
                  activeTab === tab ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"
                )}
              >
                {tab === "history" ? <Clock className="w-4 h-4" /> : <Pin className="w-4 h-4" />}
                {tab === "history" ? "Historial" : "Guardados"}
              </button>
            ))}
          </div>

          {activeTab === "history" ? (
            <GlassCard delay={0.15} hover={false}>
              <h3 className="text-sm font-semibold text-foreground mb-4">Búsquedas Recientes</h3>
              <div className="space-y-2">
                {searchHistory.map((item, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 + i * 0.06 }}
                    className="flex items-center gap-3 p-3 rounded-lg hover:bg-muted/30 transition-colors cursor-pointer group"
                  >
                    <div className="w-8 h-8 rounded-lg bg-muted/50 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                      <Clock className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-foreground truncate">{item.query}</p>
                      <p className="text-xs text-muted-foreground">{item.timestamp} · {item.results} resultados</p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </GlassCard>
          ) : (
            <GlassCard delay={0.15} hover={false}>
              <h3 className="text-sm font-semibold text-foreground mb-4">Gráficos Guardados</h3>
              <div className="space-y-2">
                {pinnedCharts.map((chart, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 + i * 0.06 }}
                    className="flex items-center gap-3 p-3 rounded-lg hover:bg-muted/30 transition-colors cursor-pointer"
                  >
                    <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                      <Pin className="w-4 h-4 text-primary" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-foreground truncate">{chart.title}</p>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-muted-foreground">{chart.type}</span>
                        <GenreTag genre={chart.genre} />
                      </div>
                    </div>
                    <span className="text-xs text-muted-foreground">{chart.pinned}</span>
                  </motion.div>
                ))}
              </div>
            </GlassCard>
          )}
        </div>
      </div>
    </motion.div>
  );
}
