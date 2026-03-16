import { useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Sparkles,
  FlaskConical,
  ShieldAlert,
  Activity,
  Users,
  BarChart3,
} from "lucide-react";

const AGENTS = [
  { name: "Celos / Control", description: "Detecta comportamiento posesivo, vigilancia y restricción de libertad.", color: "hsl(0, 70%, 55%)" },
  { name: "Insultos / Lenguaje Degradante", description: "Identifica insultos directos, descalificaciones y trato vejatorio.", color: "hsl(30, 80%, 55%)" },
  { name: "Sumisión / Roles de Género", description: "Analiza sumisión femenina, masculinidad tóxica y dinámicas de poder.", color: "hsl(50, 80%, 50%)" },
  { name: "Objetificación Sexual", description: "Detecta cosificación directa e indirecta y eliminación de agencia.", color: "hsl(265, 85%, 60%)" },
];

const COMING_SOON_FEATURES = [
  { icon: FlaskConical, label: "Análisis por letra", desc: "Pega cualquier letra y obtén la evaluación de sesgo por dimensión." },
  { icon: ShieldAlert, label: "Análisis por canción", desc: "Analiza directamente canciones del catálogo usando su ID." },
  { icon: Activity, label: "Comparativa de modelos", desc: "Groq vs OpenRouter: puntajes cruzados y detección de discrepancias." },
  { icon: BarChart3, label: "Historial de análisis", desc: "Consulta evaluaciones pasadas y tendencias por artista o género." },
  { icon: Users, label: "Revisión humana", desc: "Flagging automático de canciones que requieren revisión editorial." },
];

export default function Index() {
  const [hovered, setHovered] = useState<number | null>(null);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="pb-10"
    >
      {/* Header */}
      <div className="mb-8 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Analizador de Sesgos</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Motor de evaluación LLM para detección de sesgo de género en letras de canciones.
          </p>
        </div>
        <Link
          to="/dashboard"
          className="inline-flex items-center gap-2 self-start rounded-lg border border-border/60 bg-card/40 px-4 py-2 text-sm hover:border-primary/60"
        >
          <BarChart3 className="h-4 w-4" />
          Ver Dashboard
        </Link>
      </div>

      {/* Status banner */}
      <div className="mb-8 flex items-start gap-3 rounded-xl border border-amber-500/30 bg-amber-500/10 px-5 py-4">
        <FlaskConical className="mt-0.5 h-5 w-5 flex-shrink-0 text-amber-400" />
        <div>
          <p className="text-sm font-semibold text-amber-300">Motor de agentes en configuración</p>
          <p className="mt-0.5 text-xs text-amber-300/70">
            Los 9 agentes de análisis están siendo calibrados y conectados al pipeline. El analizador
            estará disponible en cuanto finalice esa integración.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Agents preview */}
        <section>
          <div className="mb-4 flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-primary" />
            <h2 className="text-base font-semibold text-foreground">Agentes de análisis</h2>
          </div>
          <div className="space-y-3">
            {AGENTS.map((agent, i) => (
              <motion.div
                key={agent.name}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.07 }}
                onMouseEnter={() => setHovered(i)}
                onMouseLeave={() => setHovered(null)}
                className="flex items-start gap-3 rounded-xl border border-border/50 bg-card/30 px-4 py-3 transition-colors hover:border-border/80 hover:bg-card/50"
              >
                <span
                  className="mt-0.5 h-2.5 w-2.5 flex-shrink-0 rounded-full"
                  style={{ backgroundColor: agent.color, boxShadow: hovered === i ? `0 0 8px ${agent.color}` : "none" }}
                />
                <div>
                  <p className="text-sm font-medium text-foreground">{agent.name}</p>
                  <p className="mt-0.5 text-xs text-muted-foreground">{agent.description}</p>
                </div>
                <span className="ml-auto self-start rounded-full border border-border/40 px-2 py-0.5 text-[10px] font-medium text-muted-foreground">
                  Escala 0–3
                </span>
              </motion.div>
            ))}
          </div>
        </section>

        {/* Features coming soon */}
        <section>
          <div className="mb-4 flex items-center gap-2">
            <FlaskConical className="h-4 w-4 text-primary" />
            <h2 className="text-base font-semibold text-foreground">Funcionalidades próximas</h2>
          </div>
          <div className="space-y-3">
            {COMING_SOON_FEATURES.map((feat, i) => (
              <motion.div
                key={feat.label}
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.07 }}
                className="flex items-start gap-3 rounded-xl border border-border/40 bg-card/20 px-4 py-3 opacity-70"
              >
                <feat.icon className="mt-0.5 h-4 w-4 flex-shrink-0 text-primary/70" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-foreground">{feat.label}</p>
                  <p className="mt-0.5 text-xs text-muted-foreground">{feat.desc}</p>
                </div>
                <span className="ml-auto self-start rounded-full border border-primary/30 bg-primary/10 px-2 py-0.5 text-[10px] font-medium text-primary/80">
                  Próximamente
                </span>
              </motion.div>
            ))}
          </div>
        </section>
      </div>

      {/* Score scale reference */}
      <div className="mt-8 rounded-xl border border-border/40 bg-card/20 px-5 py-4">
        <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Escala de puntuación</p>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {[
            { level: "0 — Sin sesgo", color: "text-emerald-400 border-emerald-500/30 bg-emerald-500/10", desc: "No se detectan indicadores" },
            { level: "1 — Leve", color: "text-yellow-400 border-yellow-500/30 bg-yellow-500/10", desc: "Insinuación o lenguaje ambiguo" },
            { level: "2 — Moderado", color: "text-orange-400 border-orange-500/30 bg-orange-500/10", desc: "Patrón claro pero no explícito" },
            { level: "3 — Grave", color: "text-red-400 border-red-500/30 bg-red-500/10", desc: "Explícito, reiterativo o normalizador" },
          ].map((s) => (
            <div key={s.level} className={`rounded-lg border px-3 py-2 ${s.color}`}>
              <p className="text-xs font-semibold">{s.level}</p>
              <p className="mt-0.5 text-[11px] opacity-80">{s.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  );
}
