import { useEffect, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { AppSidebar } from "./AppSidebar";
import { VerticeSpotlight } from "../vertice/VerticeSpotlight";
import { motion, AnimatePresence } from "framer-motion";
import { Menu, Moon, Sparkles, Sun } from "lucide-react";

export function AppLayout() {
  const [spotlightOpen, setSpotlightOpen] = useState(false);
  const [isLightMode, setIsLightMode] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const savedTheme = localStorage.getItem("vertice-theme");
    const prefersLight = window.matchMedia("(prefers-color-scheme: light)").matches;
    const useLight = savedTheme ? savedTheme === "light" : prefersLight;
    setIsLightMode(useLight);
    document.documentElement.classList.toggle("light", useLight);
  }, []);

  const toggleTheme = () => {
    const next = !isLightMode;
    setIsLightMode(next);
    document.documentElement.classList.toggle("light", next);
    localStorage.setItem("vertice-theme", next ? "light" : "dark");
  };

  useEffect(() => {
    document.body.style.overflow = mobileMenuOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileMenuOpen]);

  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

  return (
    <div className="flex min-h-screen bg-background bg-grid-pattern">
      {/* Ambient background effects */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-0 left-1/4 w-[600px] h-[600px] rounded-full bg-neon-purple/5 blur-[120px]" />
        <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] rounded-full bg-neon-blue/5 blur-[100px]" />
        <div className="absolute top-1/2 right-0 w-[400px] h-[400px] rounded-full bg-neon-cyan/3 blur-[80px]" />
      </div>

      <AppSidebar mobileOpen={mobileMenuOpen} onMobileClose={() => setMobileMenuOpen(false)} />

      <div className="flex-1 flex flex-col min-h-screen relative">
        {/* Top Bar */}
        <header className="sticky top-0 z-30 h-14 flex items-center justify-between px-3 sm:px-6 glass border-b border-border/50">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileMenuOpen(true)}
              className="md:hidden p-2 rounded-lg border border-border/60 bg-background/40 text-muted-foreground hover:text-foreground"
              aria-label="Abrir menú"
            >
              <Menu className="w-4 h-4" />
            </button>
            <span className="text-xs sm:text-sm text-muted-foreground font-mono">v0.1.0</span>
          </div>

          <div className="flex items-center gap-1.5 sm:gap-2">
            <button
              onClick={toggleTheme}
              className="flex items-center gap-2 px-2.5 sm:px-3 py-2 rounded-lg border border-border/60 bg-background/40 text-sm font-medium hover:border-primary/50 transition-colors"
            >
              {isLightMode ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
              <span className="hidden sm:inline">{isLightMode ? "Modo oscuro" : "Modo claro"}</span>
            </button>

            <button
              onClick={() => setSpotlightOpen(true)}
              className="flex items-center gap-2 px-2.5 sm:px-3 py-2 rounded-lg bg-gradient-primary text-primary-foreground text-sm font-medium hover:opacity-90 transition-opacity cursor-pointer"
            >
              <Sparkles className="w-4 h-4" />
              <span className="hidden sm:inline">Vértice AI</span>
            </button>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 p-3 sm:p-6 overflow-x-hidden">
          <AnimatePresence mode="wait">
            <Outlet />
          </AnimatePresence>
        </main>

        <footer className="border-t border-border/50 bg-card/60 backdrop-blur px-3 sm:px-6 py-3">
          <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
            <div className="space-y-0.5">
              <p className="text-xs font-medium text-foreground">
                Vértice · Factoría F5 · Women in AI
              </p>
              <p className="hidden sm:block text-[11px] text-muted-foreground">
                Stakeholder: Patricia (Dirección Madrid, Women in AI)
              </p>
            </div>
            <div className="flex items-center gap-3">
              <img
                src="/logo-wowen-ia.jpeg"
                alt="Women in AI Spain"
                className="h-8 w-auto rounded-sm border border-border/60 object-contain"
              />
              <span className="hidden md:inline text-[11px] font-medium text-foreground">
                Comunidad internacional de IA con foco en liderazgo femenino
              </span>
            </div>
          </div>
        </footer>
      </div>

      <VerticeSpotlight open={spotlightOpen} onClose={() => setSpotlightOpen(false)} />
    </div>
  );
}
