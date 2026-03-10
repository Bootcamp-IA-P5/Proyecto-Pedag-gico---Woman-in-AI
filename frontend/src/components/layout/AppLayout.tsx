import { useState } from "react";
import { Outlet } from "react-router-dom";
import { AppSidebar } from "./AppSidebar";
import { VerticeSpotlight } from "../vertice/VerticeSpotlight";
import { motion, AnimatePresence } from "framer-motion";
import { Search, Sparkles } from "lucide-react";

export function AppLayout() {
  const [spotlightOpen, setSpotlightOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-background bg-grid-pattern">
      {/* Ambient background effects */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-0 left-1/4 w-[600px] h-[600px] rounded-full bg-neon-purple/5 blur-[120px]" />
        <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] rounded-full bg-neon-blue/5 blur-[100px]" />
        <div className="absolute top-1/2 right-0 w-[400px] h-[400px] rounded-full bg-neon-cyan/3 blur-[80px]" />
      </div>

      <AppSidebar />

      <div className="flex-1 flex flex-col min-h-screen relative">
        {/* Top Bar */}
        <header className="sticky top-0 z-40 h-14 flex items-center justify-between px-6 glass border-b border-border/50">
          <div className="flex items-center gap-3">
            <span className="text-sm text-muted-foreground font-mono">v0.1.0</span>
          </div>

          <button
            onClick={() => setSpotlightOpen(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-lg glass border border-border/50 hover:border-primary/50 transition-all group cursor-pointer"
          >
            <Search className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors" />
            <span className="text-sm text-muted-foreground group-hover:text-foreground transition-colors">
              Pregúntale a Vértice AI...
            </span>
            <kbd className="hidden sm:inline-flex items-center gap-1 px-2 py-0.5 rounded bg-muted text-[10px] font-mono text-muted-foreground">
              ⌘K
            </kbd>
          </button>

          <button
            onClick={() => setSpotlightOpen(true)}
            className="flex items-center gap-2 px-3 py-2 rounded-lg bg-gradient-primary text-primary-foreground text-sm font-medium hover:opacity-90 transition-opacity cursor-pointer"
          >
            <Sparkles className="w-4 h-4" />
            <span className="hidden sm:inline">Vértice AI</span>
          </button>
        </header>

        {/* Page Content */}
        <main className="flex-1 p-6">
          <AnimatePresence mode="wait">
            <Outlet />
          </AnimatePresence>
        </main>
      </div>

      <VerticeSpotlight open={spotlightOpen} onClose={() => setSpotlightOpen(false)} />
    </div>
  );
}
