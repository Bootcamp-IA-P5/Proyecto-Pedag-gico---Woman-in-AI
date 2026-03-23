import { cn } from "@/lib/utils";

const genreColors: Record<string, string> = {
  "Reggaetón": "bg-neon-pink/20 text-neon-pink border-neon-pink/30",
  "Vallenato": "bg-neon-green/20 text-neon-green border-neon-green/30",
  "Pop": "bg-neon-purple/20 text-neon-purple border-neon-purple/30",
  "Rap": "bg-neon-blue/20 text-neon-blue border-neon-blue/30",
  "Rock": "bg-neon-cyan/20 text-neon-cyan border-neon-cyan/30",
  "Salsa": "bg-accent/20 text-accent border-accent/30",
  "Bachata": "bg-neon-pink/20 text-neon-pink border-neon-pink/30",
  "Electrónica": "bg-neon-cyan/20 text-neon-cyan border-neon-cyan/30",
};

interface GenreTagProps {
  genre: string;
  className?: string;
}

export function GenreTag({ genre, className }: GenreTagProps) {
  const colorClass = genreColors[genre] || "bg-muted text-muted-foreground border-border";
  return (
    <span className={cn("inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-medium border", colorClass, className)}>
      {genre}
    </span>
  );
}
