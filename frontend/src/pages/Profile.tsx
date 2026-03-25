import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { User, Database, ShieldCheck, Activity, BookOpenText } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { GlassCard } from "@/components/ui/GlassCard";
import { fetchEvaluations, fetchSongs } from "@/lib/data";

export default function Profile() {
  const { data: songs = [], error: songsError } = useQuery({ queryKey: ["songs"], queryFn: fetchSongs });
  const { data: evaluations = [], error: evalsError } = useQuery({ queryKey: ["evaluations"], queryFn: fetchEvaluations });

  const profileError = songsError instanceof Error
    ? songsError.message
    : evalsError instanceof Error
      ? evalsError.message
      : null;

  const metrics = useMemo(() => {
    const totalSongs = songs.length;
    const validEvals = evaluations.filter((e) => e.total_score != null);
    const avgScore = validEvals.length
      ? Math.round((validEvals.reduce((acc, e) => acc + Number(e.total_score), 0) / validEvals.length) * 10) / 10
      : 0;
    const coverage = totalSongs > 0
      ? Math.round((validEvals.length * 100) / totalSongs)
      : 0;

    return {
      totalSongs,
      validEvaluations: validEvals.length,
      avgScore,
      coverage,
    };
  }, [songs, evaluations]);

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
      <PageHeader icon={User} title="Perfil del Proyecto" subtitle="Métricas reales del sistema y trazabilidad de la información" />

      {profileError && (
        <div className="mb-4 rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-300">
          {profileError}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
        <GlassCard delay={0.1}>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-primary flex items-center justify-center">
              <Database className="w-5 h-5 text-primary-foreground" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Canciones en catálogo</p>
              <p className="text-2xl font-semibold text-foreground">{metrics.totalSongs}</p>
            </div>
          </div>
        </GlassCard>

        <GlassCard delay={0.15}>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-primary flex items-center justify-center">
              <Activity className="w-5 h-5 text-primary-foreground" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Evaluaciones válidas</p>
              <p className="text-2xl font-semibold text-foreground">{metrics.validEvaluations}</p>
            </div>
          </div>
        </GlassCard>

        <GlassCard delay={0.2}>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-primary flex items-center justify-center">
              <ShieldCheck className="w-5 h-5 text-primary-foreground" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Cobertura de evaluación</p>
              <p className="text-2xl font-semibold text-foreground">{metrics.coverage}%</p>
            </div>
          </div>
        </GlassCard>

        <GlassCard delay={0.25}>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-primary flex items-center justify-center">
              <User className="w-5 h-5 text-primary-foreground" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Score global promedio</p>
              <p className="text-2xl font-semibold text-foreground">{metrics.avgScore}</p>
            </div>
          </div>
        </GlassCard>
      </div>

      <GlassCard delay={0.3} hover={false}>
        <div className="flex items-center gap-2 mb-3">
          <BookOpenText className="w-4 h-4 text-primary" />
          <h3 className="text-base font-semibold text-foreground">¿Qué representa esta vista?</h3>
        </div>
        <p className="text-sm text-muted-foreground">
          Esta vista ya no muestra logros, historial o datos de usuario simulados. Todas las métricas se calculan en tiempo real desde tablas de Supabase
          usadas por el proyecto (`songs` y `llm_evaluations`).
        </p>
        <p className="text-sm text-muted-foreground mt-2">
          Si no hay conexión a Supabase, se mostrará un error explícito y las cifras quedarán en cero para evitar mostrar información no verificable.
        </p>
      </GlassCard>
    </motion.div>
  );
}
