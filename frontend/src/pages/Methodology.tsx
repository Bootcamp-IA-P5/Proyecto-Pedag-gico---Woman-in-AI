import { motion } from "framer-motion";
import { BookOpenText, Eye, Lock, Theater, MessageSquareWarning, Scale, ShieldCheck, Workflow } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { GlassCard } from "@/components/ui/GlassCard";

const dimensions = [
  {
    title: "Objetificación",
    icon: Eye,
    description:
      "Reducción de una persona a su cuerpo o apariencia física, tratándola como objeto de deseo sin considerar agencia o identidad.",
  },
  {
    title: "Posesión y Control",
    icon: Lock,
    description:
      "Expresiones que implican dominio, propiedad o control sobre otra persona, limitando su autonomía y capacidad de decisión.",
  },
  {
    title: "Roles y Estereotipos",
    icon: Theater,
    description:
      "Refuerzo de roles de género rígidos que condicionan expectativas según género: por ejemplo, mujer sumisa u hombre dominante.",
  },
  {
    title: "Lenguaje Degradante",
    icon: MessageSquareWarning,
    description:
      "Uso de insultos, expresiones despectivas o generalizaciones negativas dirigidas a un género o a personas en relación de poder.",
  },
];

const scoring = [
  { score: "0", level: "No presente", details: "No se detecta sesgo en la dimensión analizada." },
  { score: "1", level: "Leve", details: "Indicios sutiles o implícitos de sesgo." },
  { score: "2", level: "Explícito", details: "Sesgo claro y directamente observable." },
  { score: "3", level: "Crítico", details: "Sesgo reiterado, intenso o normalizado en la narrativa." },
];

export default function Methodology() {
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
      <PageHeader
        icon={BookOpenText}
        title="Metodología"
        subtitle="Cómo funciona el análisis de sesgo en Vértice"
      />

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5 mb-6">
        <GlassCard className="xl:col-span-2" delay={0.05} hover={false} glow="blue">
          <h2 className="text-base font-semibold text-foreground mb-2">¿Qué es Vértice?</h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Vértice es una herramienta de análisis lingüístico asistido por IA para detectar y cuantificar
            sesgos de género en letras de canciones en español. El sistema evalúa cuatro dimensiones y
            construye una puntuación comparable entre obras, artistas y géneros.
          </p>
          <p className="text-sm text-muted-foreground leading-relaxed mt-3">
            El objetivo no es censurar ni emitir juicios morales sobre autores, sino abrir lectura crítica
            sobre patrones narrativos que consumimos de forma cotidiana.
          </p>
        </GlassCard>

        <GlassCard delay={0.08} hover={false} glow="cyan">
          <div className="flex items-center gap-2 mb-2">
            <Workflow className="h-4 w-4 text-primary" />
            <h3 className="text-sm font-semibold text-foreground">Pipeline de análisis</h3>
          </div>
          <ol className="space-y-2 text-sm text-muted-foreground list-decimal pl-4">
            <li>Normalización y validación del texto.</li>
            <li>Análisis por dimensión con modelos LLM.</li>
            <li>Revisión crítica y resolución de discrepancias.</li>
            <li>Consolidación de score y evidencia trazable.</li>
          </ol>
        </GlassCard>
      </div>

      <GlassCard className="mb-6" delay={0.1} hover={false}>
        <h2 className="text-base font-semibold text-foreground mb-4">Dimensiones de análisis</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {dimensions.map((item, idx) => (
            <motion.div
              key={item.title}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.12 + idx * 0.06 }}
              className="rounded-lg border border-border/50 bg-background/40 p-4"
            >
              <div className="flex items-center gap-2 mb-2">
                <item.icon className="h-4 w-4 text-primary" />
                <h3 className="text-sm font-semibold text-foreground">{item.title}</h3>
              </div>
              <p className="text-sm text-muted-foreground leading-relaxed">{item.description}</p>
            </motion.div>
          ))}
        </div>
      </GlassCard>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <GlassCard delay={0.16} hover={false} glow="purple">
          <div className="flex items-center gap-2 mb-3">
            <Scale className="h-4 w-4 text-primary" />
            <h2 className="text-base font-semibold text-foreground">Escala de puntuación</h2>
          </div>
          <div className="space-y-2">
            {scoring.map((item) => (
              <div key={item.score} className="rounded-lg border border-border/50 bg-background/40 p-3">
                <p className="text-sm font-semibold text-foreground">
                  {item.score} · {item.level}
                </p>
                <p className="text-sm text-muted-foreground">{item.details}</p>
              </div>
            ))}
          </div>
          <p className="text-xs text-muted-foreground mt-3">
            La suma de las 4 dimensiones permite comparar intensidad de sesgo entre canciones.
          </p>
        </GlassCard>

        <GlassCard delay={0.2} hover={false} glow="none">
          <div className="flex items-center gap-2 mb-3">
            <ShieldCheck className="h-4 w-4 text-primary" />
            <h2 className="text-base font-semibold text-foreground">Nota ética</h2>
          </div>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Este sistema analiza lenguaje y patrones textuales, no intenciones personales. Los resultados
            representan señales de sesgo en la letra y no equivalen a una sentencia sobre artistas o audiencias.
          </p>
          <p className="text-sm text-muted-foreground leading-relaxed mt-3">
            Vértice se desarrolla en colaboración con Women in AI como comunidad internacional, con el equipo
            de Vértice y Factoría F5, incorporando acompañamiento estratégico desde la dirección de Madrid.
          </p>
          <div className="mt-4 rounded-lg border border-border/50 bg-background/40 p-3">
            <p className="text-xs text-muted-foreground">Créditos</p>
            <p className="text-sm text-foreground font-medium">Vértice · Factoría F5 · Women in AI · Patricia (Madrid)</p>
          </div>
        </GlassCard>
      </div>
    </motion.div>
  );
}
