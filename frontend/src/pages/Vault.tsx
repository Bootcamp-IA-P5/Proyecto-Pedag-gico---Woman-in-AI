import { useState } from "react";
import { motion } from "framer-motion";
import { Database, Play, Search, ArrowUpDown } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { GlassCard } from "@/components/ui/GlassCard";
import { GenreTag } from "@/components/ui/GenreTag";
import { songs } from "@/data/mockData";
import { cn } from "@/lib/utils";

type SortField = "title" | "artist" | "streams" | "year";

export default function Vault() {
  const [search, setSearch] = useState("");
  const [sortField, setSortField] = useState<SortField>("streams");
  const [sortAsc, setSortAsc] = useState(false);
  const [playing, setPlaying] = useState<number | null>(null);

  const filtered = songs
    .filter((s) => {
      const q = search.toLowerCase();
      return s.title.toLowerCase().includes(q) || s.artist.toLowerCase().includes(q) || s.genre.toLowerCase().includes(q);
    })
    .sort((a, b) => {
      let cmp = 0;
      if (sortField === "title") cmp = a.title.localeCompare(b.title);
      else if (sortField === "artist") cmp = a.artist.localeCompare(b.artist);
      else if (sortField === "year") cmp = a.year - b.year;
      else cmp = 0; // streams is string, keep original order
      return sortAsc ? cmp : -cmp;
    });

  const toggleSort = (field: SortField) => {
    if (sortField === field) setSortAsc(!sortAsc);
    else { setSortField(field); setSortAsc(false); }
  };

  const SortHeader = ({ field, label }: { field: SortField; label: string }) => (
    <button
      onClick={() => toggleSort(field)}
      className={cn(
        "flex items-center gap-1 text-xs font-medium uppercase tracking-wider cursor-pointer transition-colors",
        sortField === field ? "text-primary" : "text-muted-foreground hover:text-foreground"
      )}
    >
      {label}
      <ArrowUpDown className="w-3 h-3" />
    </button>
  );

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
      <PageHeader icon={Database} title="Bóveda de Datos" subtitle="Todas las canciones del scanner" />

      {/* Search */}
      <GlassCard delay={0.1} hover={false} className="mb-6">
        <div className="flex items-center gap-3">
          <Search className="w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar por título, artista o género..."
            className="flex-1 bg-transparent border-none outline-none text-sm text-foreground placeholder:text-muted-foreground"
          />
          <span className="text-xs font-mono text-muted-foreground">{filtered.length} canciones</span>
        </div>
      </GlassCard>

      {/* Data Grid */}
      <GlassCard delay={0.15} hover={false}>
        {/* Header */}
        <div className="grid grid-cols-[40px_1fr_1fr_100px_80px_80px_60px] gap-3 px-3 py-2.5 border-b border-border/50 items-center">
          <span className="text-xs text-muted-foreground">#</span>
          <SortHeader field="title" label="Título" />
          <SortHeader field="artist" label="Artista" />
          <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">Género</span>
          <SortHeader field="year" label="Año" />
          <SortHeader field="streams" label="Streams" />
          <span className="text-xs text-muted-foreground text-center">▶</span>
        </div>

        {/* Rows */}
        <div className="divide-y divide-border/30">
          {filtered.map((song, i) => (
            <motion.div
              key={song.id}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: i * 0.03 }}
              className={cn(
                "grid grid-cols-[40px_1fr_1fr_100px_80px_80px_60px] gap-3 px-3 py-3 items-center hover:bg-muted/20 transition-colors group",
                playing === song.id && "bg-primary/5"
              )}
            >
              <span className="text-xs font-mono text-muted-foreground">{i + 1}</span>
              <div className="min-w-0">
                <p className="text-sm font-medium text-foreground truncate">{song.title}</p>
                <p className="text-xs text-muted-foreground">{song.duration}</p>
              </div>
              <div className="flex items-center gap-2 min-w-0">
                <div className="w-7 h-7 rounded-full bg-gradient-primary flex items-center justify-center text-[10px] font-bold text-primary-foreground flex-shrink-0">
                  {song.artist[0]}
                </div>
                <span className="text-sm text-foreground truncate">{song.artist}</span>
              </div>
              <GenreTag genre={song.genre} />
              <span className="text-sm font-mono text-muted-foreground">{song.year}</span>
              <span className="text-sm font-mono text-foreground">{song.streams}</span>
              <div className="flex justify-center">
                <button
                  onClick={() => setPlaying(playing === song.id ? null : song.id)}
                  className={cn(
                    "w-8 h-8 rounded-full flex items-center justify-center transition-all cursor-pointer",
                    playing === song.id
                      ? "bg-primary text-primary-foreground glow-purple"
                      : "bg-muted/50 text-muted-foreground opacity-0 group-hover:opacity-100 hover:bg-primary/20 hover:text-primary"
                  )}
                >
                  <Play className="w-3.5 h-3.5" fill={playing === song.id ? "currentColor" : "none"} />
                </button>
              </div>
            </motion.div>
          ))}
        </div>
      </GlassCard>
    </motion.div>
  );
}
