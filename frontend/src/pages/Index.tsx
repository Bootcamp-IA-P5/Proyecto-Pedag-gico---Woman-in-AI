import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Sparkles, Loader2, AlertTriangle, CheckCircle2 } from "lucide-react";
import { GlassCard } from "@/components/ui/GlassCard";
import { PageHeader } from "@/components/ui/PageHeader";
import { FeedbackBox } from "@/components/feedback/FeedbackBox";
import { analyzeLyrics, type AnalysisResult } from "@/lib/analysisApi";
import { recordProfileActivity } from "@/lib/profileActivity";

const SCORE_STYLES: Record<string, string> = {
  "0": "text-emerald-300 border-emerald-500/30 bg-emerald-500/10",
  "1": "text-yellow-300 border-yellow-500/30 bg-yellow-500/10",
  "2": "text-orange-300 border-orange-500/30 bg-orange-500/10",
  "3": "text-rose-300 border-rose-500/30 bg-rose-500/10",
};

type FormState = {
  titulo: string;
  artista: string;
  genero_musical: string;
  letra: string;
};

const INITIAL_FORM: FormState = {
  titulo: "",
  artista: "",
  genero_musical: "Reggaeton",
  letra: "",
};

type ProviderDimension = {
  name: "Groq" | "OpenRouter";
  score?: number;
  fragments: string[];
};

function round1(value: number) {
  return Math.round(value * 10) / 10;
}

function getDimensionProviders(d: AnalysisResult["dimensiones"][number]): ProviderDimension[] {
  return [
    {
      name: "Groq",
      score: typeof d.puntuacion_groq === "number" ? d.puntuacion_groq : undefined,
      fragments: Array.isArray(d.fragmentos_groq) ? d.fragmentos_groq.filter(Boolean) : [],
    },
    {
      name: "OpenRouter",
      score: typeof d.puntuacion_openrouter === "number" ? d.puntuacion_openrouter : undefined,
      fragments: Array.isArray(d.fragmentos_openrouter) ? d.fragmentos_openrouter.filter(Boolean) : [],
    },
  ];
}

function computeEvidenceAwareScore(providers: ProviderDimension[]): number | null {
  const scored = providers.filter((p) => typeof p.score === "number") as Array<ProviderDimension & { score: number }>;
  if (!scored.length) return null;

  // If at least one provider returns textual evidence, weight scores by evidence volume.
  const withEvidence = scored.filter((p) => p.fragments.length > 0);
  if (withEvidence.length) {
    const weightedTotal = withEvidence.reduce((acc, p) => acc + p.score * p.fragments.length, 0);
    const weight = withEvidence.reduce((acc, p) => acc + p.fragments.length, 0);
    if (weight > 0) return round1(weightedTotal / weight);
  }

  return round1(scored.reduce((acc, p) => acc + p.score, 0) / scored.length);
}

function getMergedEvidence(providers: ProviderDimension[]): string[] {
  return Array.from(
    new Set(
      providers
        .flatMap((p) => p.fragments)
        .map((f) => f.trim())
        .filter((f) => f.length > 0),
    ),
  );
}

export default function Index() {
  const [form, setForm] = useState<FormState>(INITIAL_FORM);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);

  const canSubmit = useMemo(() => {
    return form.titulo.trim().length > 0 &&
      form.artista.trim().length > 0 &&
      form.genero_musical.trim().length > 0 &&
      form.letra.trim().length >= 30;
  }, [form]);

  const onChange = (field: keyof FormState, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const runAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setResult(null);

    if (!canSubmit) {
      setError("Completa todos los campos. La letra debe tener al menos 30 caracteres.");
      return;
    }

    setIsLoading(true);
    try {
      const response = await analyzeLyrics({
        titulo: form.titulo.trim(),
        artista: form.artista.trim(),
        genero_musical: form.genero_musical.trim(),
        letra: form.letra.trim(),
      });
      setResult(response);
      recordProfileActivity({
        songId: String(response.song_id ?? `${form.titulo.trim()}-${form.artista.trim()}`),
        title: response.titulo,
        artist: response.artista,
        score: Number(response.puntuacion_global ?? 0),
        level: response.nivel_global ?? "Sin nivel",
        source: "manual",
      });
    } catch (err: any) {
      setError(err?.message || "No fue posible analizar la canción en este momento.");
    } finally {
      setIsLoading(false);
    }
  };

  const scoreClass = SCORE_STYLES[String(result?.puntuacion_global ?? "")] || "text-muted-foreground border-border/40 bg-background/30";

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
      <PageHeader
        icon={Sparkles}
        title="Analizador de Canciones"
        subtitle="Ingresa título, artista, género y letra para obtener evaluación de sesgo"
      />

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <GlassCard delay={0.1} hover={false}>
          <form onSubmit={runAnalyze} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-medium uppercase tracking-wider text-muted-foreground">Título</label>
                <input
                  value={form.titulo}
                  onChange={(e) => onChange("titulo", e.target.value)}
                  placeholder="Ej: Mi canción"
                  className="w-full rounded-lg border border-border/50 bg-muted/30 px-3 py-2 text-sm outline-none focus:border-primary/60"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-medium uppercase tracking-wider text-muted-foreground">Artista</label>
                <input
                  value={form.artista}
                  onChange={(e) => onChange("artista", e.target.value)}
                  placeholder="Ej: Artista X"
                  className="w-full rounded-lg border border-border/50 bg-muted/30 px-3 py-2 text-sm outline-none focus:border-primary/60"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium uppercase tracking-wider text-muted-foreground">Género musical</label>
              <select
                value={form.genero_musical}
                onChange={(e) => onChange("genero_musical", e.target.value)}
                className="w-full rounded-lg border border-border/50 bg-muted/30 px-3 py-2 text-sm outline-none focus:border-primary/60"
              >
                <option>Reggaeton</option>
                <option>Pop</option>
                <option>Rap</option>
                <option>Vallenato</option>
                <option>Otro</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium uppercase tracking-wider text-muted-foreground">Letra</label>
              <textarea
                value={form.letra}
                onChange={(e) => onChange("letra", e.target.value)}
                placeholder="Pega aquí la letra completa de la canción..."
                rows={11}
                className="w-full rounded-lg border border-border/50 bg-muted/30 px-3 py-2 text-sm outline-none focus:border-primary/60"
              />
              <p className="text-xs text-muted-foreground">{form.letra.trim().length} caracteres</p>
            </div>

            <button
              type="submit"
              disabled={!canSubmit || isLoading}
              className="inline-flex items-center gap-2 rounded-lg border border-border/50 px-4 py-2 text-sm font-medium hover:border-primary/60 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
              {isLoading ? "Analizando..." : "Analizar canción"}
            </button>
          </form>
        </GlassCard>

        <GlassCard delay={0.15} hover={false}>
          {!result && !error && (
            <div className="flex min-h-[300px] items-center justify-center text-sm text-muted-foreground">
              Completa el formulario para ver el resultado del análisis.
            </div>
          )}

          {error && (
            <div className="rounded-md border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-sm text-rose-300 inline-flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" />
              {error}
            </div>
          )}

          {result && (
            <div className="space-y-4">
              <div className="rounded-lg border border-border/50 bg-background/40 p-3">
                <p className="text-sm text-muted-foreground">Resultado global</p>
                <div className="mt-2 flex items-center gap-3">
                  <span className={`rounded-md border px-2 py-1 text-sm font-semibold ${scoreClass}`}>
                    Score {result.puntuacion_global}
                  </span>
                  <span className="text-sm font-medium text-foreground">{result.nivel_global}</span>
                  {result.requiere_revision_humana ? (
                    <span className="text-xs text-orange-300">Requiere revisión humana</span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-xs text-emerald-300"><CheckCircle2 className="h-3 w-3" />Sin revisión humana</span>
                  )}
                </div>
              </div>

              <div className="space-y-2 max-h-[260px] overflow-y-auto pr-1">
                {result.dimensiones.map((d) => {
                  const providers = getDimensionProviders(d);
                  const evidenceAware = computeEvidenceAwareScore(providers);
                  const mergedEvidence = getMergedEvidence(providers);
                  return (
                    <div key={d.dimension} className="rounded-md border border-border/40 bg-background/30 p-3">
                      <p className="text-sm font-medium text-foreground">{d.dimension}</p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {providers.map((p) => `${p.name}: ${typeof p.score === "number" ? p.score : "N/D"}`).join(" · ")}
                        {` · Score con evidencia: ${evidenceAware ?? "N/D"}`}
                      </p>

                      {mergedEvidence.length > 0 ? (
                        <div className="mt-2 rounded-md border border-border/40 bg-background/40 p-2">
                          <p className="text-[11px] uppercase tracking-wider text-muted-foreground">Dónde y por qué se detectó sesgo</p>
                          <ul className="mt-1 space-y-1">
                            {mergedEvidence.slice(0, 4).map((fragment, idx) => (
                              <li key={`${d.dimension}-${idx}`} className="text-xs text-foreground/90">"{fragment}"</li>
                            ))}
                          </ul>
                        </div>
                      ) : (
                        <p className="mt-2 text-xs text-muted-foreground">Sin fragmentos de evidencia textual para esta dimensión.</p>
                      )}
                    </div>
                  );
                })}
              </div>

              <FeedbackBox
                storageKey={`feedback:analysis:${result.song_id || `${form.titulo}:${form.artista}`}`}
                title="¿Qué opinas del resultado?"
                placeholder="Escribe observaciones sobre precisión, sesgos o aspectos a mejorar."
              />
            </div>
          )}
        </GlassCard>
      </div>
    </motion.div>
  );
}
