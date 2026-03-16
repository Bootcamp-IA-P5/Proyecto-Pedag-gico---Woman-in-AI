import { useEffect, useMemo, useState } from "react";
import { ThumbsDown, ThumbsUp, Send } from "lucide-react";
import { cn } from "@/lib/utils";

type Reaction = "like" | "dislike" | null;

type StoredFeedback = {
  reaction: Reaction;
  comment: string;
  updatedAt: string;
};

type FeedbackBoxProps = {
  storageKey: string;
  title: string;
  placeholder?: string;
};

export function FeedbackBox({ storageKey, title, placeholder }: FeedbackBoxProps) {
  const [reaction, setReaction] = useState<Reaction>(null);
  const [comment, setComment] = useState("");
  const [status, setStatus] = useState<string | null>(null);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(storageKey);
      if (!raw) return;
      const parsed = JSON.parse(raw) as StoredFeedback;
      setReaction(parsed.reaction ?? null);
      setComment(parsed.comment ?? "");
    } catch {
      // Ignore malformed local state and let user write feedback again.
    }
  }, [storageKey]);

  const commentLength = comment.trim().length;

  const canSave = useMemo(() => {
    return Boolean(reaction || commentLength > 0) && commentLength <= 500;
  }, [reaction, commentLength]);

  const handleSave = () => {
    if (!reaction && commentLength === 0) {
      setStatus("Selecciona 👍 o 👎, o escribe un comentario para guardar.");
      return;
    }

    if (commentLength > 500) {
      setStatus("El comentario no puede superar 500 caracteres.");
      return;
    }

    const payload: StoredFeedback = {
      reaction,
      comment: comment.trim(),
      updatedAt: new Date().toISOString(),
    };

    localStorage.setItem(storageKey, JSON.stringify(payload));
    setStatus("Feedback guardado localmente.");
  };

  return (
    <div className="rounded-lg border border-border/40 bg-background/50 p-3">
      <p className="mb-2 text-xs font-medium text-foreground">{title}</p>

      <div className="mb-3 flex items-center gap-2">
        <button
          type="button"
          onClick={() => setReaction((prev) => (prev === "like" ? null : "like"))}
          className={cn(
            "inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs transition-colors",
            reaction === "like"
              ? "border-emerald-400/70 bg-emerald-500/10 text-emerald-300"
              : "border-border/50 text-muted-foreground hover:border-emerald-400/50 hover:text-emerald-300"
          )}
        >
          <ThumbsUp className="h-3.5 w-3.5" />
          👍 Me gustó
        </button>

        <button
          type="button"
          onClick={() => setReaction((prev) => (prev === "dislike" ? null : "dislike"))}
          className={cn(
            "inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs transition-colors",
            reaction === "dislike"
              ? "border-rose-400/70 bg-rose-500/10 text-rose-300"
              : "border-border/50 text-muted-foreground hover:border-rose-400/50 hover:text-rose-300"
          )}
        >
          <ThumbsDown className="h-3.5 w-3.5" />
          👎 No me gustó
        </button>
      </div>

      <textarea
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        rows={3}
        maxLength={550}
        placeholder={placeholder ?? "Escribe aquí tu comentario sobre el resultado o la canción..."}
        className="w-full resize-y rounded-md border border-border/50 bg-background/70 px-3 py-2 text-sm text-foreground outline-none transition-colors focus:border-primary/60"
      />

      <div className="mt-2 flex items-center justify-between gap-3">
        <span className={cn("text-xs", commentLength > 500 ? "text-rose-300" : "text-muted-foreground")}>
          {commentLength}/500
        </span>

        <button
          type="button"
          onClick={handleSave}
          disabled={!canSave}
          className="inline-flex items-center gap-1 rounded-md border border-border/50 px-2.5 py-1.5 text-xs text-foreground transition-colors hover:border-primary/60 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Send className="h-3.5 w-3.5" />
          Guardar comentario
        </button>
      </div>

      {status && <p className="mt-2 text-xs text-muted-foreground">{status}</p>}
    </div>
  );
}