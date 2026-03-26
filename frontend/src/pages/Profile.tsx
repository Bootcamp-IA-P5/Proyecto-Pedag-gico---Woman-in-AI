import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { User, Clock3, ShieldAlert, Trash2, Sparkles, Compass } from "lucide-react";
import { Link } from "react-router-dom";
import { PageHeader } from "@/components/ui/PageHeader";
import { GlassCard } from "@/components/ui/GlassCard";
import {
  clearProfileActivity,
  onProfileActivityUpdate,
  readProfileActivity,
  type ProfileActivity,
} from "@/lib/profileActivity";

function sourceLabel(source: ProfileActivity["source"]) {
  if (source === "manual") return "Analizar";
  if (source === "explorer") return "Explorador";
  return "Bóveda";
}

function formatDate(value: string) {
  const date = new Date(value);
  return new Intl.DateTimeFormat("es-ES", {
    hour: "2-digit",
    minute: "2-digit",
    day: "2-digit",
    month: "short",
  }).format(date);
}

export default function Profile() {
  const [activity, setActivity] = useState<ProfileActivity[]>(() => readProfileActivity());

  useEffect(() => {
    const sync = () => setActivity(readProfileActivity());
    const unsubscribe = onProfileActivityUpdate(sync);
    return unsubscribe;
  }, []);

  const stats = useMemo(() => {
    const total = activity.length;
    const highRisk = activity.filter((entry) => entry.score >= 2).length;
    const averageScore = total
      ? Math.round((activity.reduce((acc, entry) => acc + entry.score, 0) / total) * 10) / 10
      : 0;
    const latest = activity[0] ?? null;

    return { total, highRisk, averageScore, latest };
  }, [activity]);

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
      <PageHeader
        icon={User}
        title="Mi Perfil"
        subtitle="Actividad real de tu sesión y accesos rápidos de análisis"
      />

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 mb-6">
        <GlassCard delay={0.1} className="xl:col-span-2">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-gradient-primary flex items-center justify-center">
                <User className="w-6 h-6 text-primary-foreground" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Perfil de analista</p>
                <p className="text-xl font-semibold text-foreground">Sesión activa en Vértice</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Link
                to="/analizar"
                className="inline-flex items-center gap-1.5 rounded-md border border-border/50 px-3 py-1.5 text-sm hover:border-primary/60"
              >
                <Sparkles className="w-4 h-4" />
                Nueva prueba
              </Link>
              <button
                onClick={() => clearProfileActivity()}
                className="inline-flex items-center gap-1.5 rounded-md border border-border/50 px-3 py-1.5 text-sm hover:border-red-500/60"
              >
                <Trash2 className="w-4 h-4" />
                Limpiar sesión
              </button>
            </div>
          </div>
        </GlassCard>

        <GlassCard delay={0.15}>
          <p className="text-sm text-muted-foreground">Última actividad</p>
          {stats.latest ? (
            <div className="mt-2 space-y-1">
              <p className="text-sm font-semibold text-foreground truncate">{stats.latest.title}</p>
              <p className="text-xs text-muted-foreground truncate">{stats.latest.artist}</p>
              <p className="text-xs text-muted-foreground">
                {sourceLabel(stats.latest.source)} · {formatDate(stats.latest.analyzedAt)}
              </p>
            </div>
          ) : (
            <p className="mt-2 text-sm text-muted-foreground">Aún no has analizado canciones en esta sesión.</p>
          )}
        </GlassCard>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <GlassCard delay={0.2}>
          <div className="flex items-center gap-3">
            <Clock3 className="w-5 h-5 text-primary" />
            <div>
              <p className="text-sm text-muted-foreground">Analizadas en sesión</p>
              <p className="text-2xl font-semibold text-foreground">{stats.total}</p>
            </div>
          </div>
        </GlassCard>

        <GlassCard delay={0.25}>
          <div className="flex items-center gap-3">
            <Compass className="w-5 h-5 text-primary" />
            <div>
              <p className="text-sm text-muted-foreground">Score promedio sesión</p>
              <p className="text-2xl font-semibold text-foreground">{stats.averageScore}</p>
            </div>
          </div>
        </GlassCard>

        <GlassCard delay={0.3}>
          <div className="flex items-center gap-3">
            <ShieldAlert className="w-5 h-5 text-primary" />
            <div>
              <p className="text-sm text-muted-foreground">Alertas de riesgo (&gt;=2)</p>
              <p className="text-2xl font-semibold text-foreground">{stats.highRisk}</p>
            </div>
          </div>
        </GlassCard>
      </div>

      <GlassCard delay={0.35} hover={false}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base font-semibold text-foreground">Historial reciente de análisis</h3>
          <span className="text-xs text-muted-foreground">{activity.length} registros</span>
        </div>

        {activity.length === 0 ? (
          <p className="text-sm text-muted-foreground">No hay historial aún. Ejecuta un análisis en Analizar, Explorador o Bóveda.</p>
        ) : (
          <div className="space-y-2">
            {activity.slice(0, 12).map((entry) => (
              <div
                key={entry.id}
                className="rounded-lg border border-border/40 bg-background/40 px-3 py-2 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2"
              >
                <div className="min-w-0">
                  <p className="text-sm font-medium text-foreground truncate">{entry.title}</p>
                  <p className="text-xs text-muted-foreground truncate">{entry.artist}</p>
                </div>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <span>{sourceLabel(entry.source)}</span>
                  <span className="rounded-md border border-border/50 px-2 py-0.5 text-foreground">
                    {entry.level} ({entry.score})
                  </span>
                  <span>{formatDate(entry.analyzedAt)}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </GlassCard>
    </motion.div>
  );
}
