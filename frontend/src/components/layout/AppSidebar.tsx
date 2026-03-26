import { NavLink, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  Search,
  Database,
  User,
  Sparkles,
  ChevronLeft,
  ChevronRight,
  BookOpenText,
  X,
} from "lucide-react";
import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { cn } from "@/lib/utils";

const navItems = [
  { title: "Metodología", path: "/", icon: BookOpenText },
  { title: "Analizar", path: "/analizar", icon: Sparkles },
  { title: "Dashboard", path: "/dashboard", icon: LayoutDashboard },
  { title: "Explorador", path: "/explorer", icon: Search },
  { title: "Bóveda", path: "/vault", icon: Database },
  { title: "Perfil", path: "/profile", icon: User },
];

interface AppSidebarProps {
  mobileOpen: boolean;
  onMobileClose: () => void;
}

export function AppSidebar({ mobileOpen, onMobileClose }: AppSidebarProps) {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();

  const navContent = (isMobile = false) => (
    <nav className="flex-1 py-4 px-3 space-y-1">
      {navItems.map((item) => {
        const isMethodologyItem = item.path === "/";
        const isActive = isMethodologyItem
          ? location.pathname === "/" || location.pathname === "/metodologia"
          : location.pathname === item.path;
        return (
          <NavLink
            key={item.path}
            to={item.path}
            onClick={isMobile ? onMobileClose : undefined}
            className={cn(
              "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200",
              isActive
                ? "bg-primary/10 text-primary glow-purple"
                : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
            )}
          >
            <item.icon className={cn("w-5 h-5 flex-shrink-0", isActive && "text-primary")} />
            {(isMobile || !collapsed) && <span>{item.title}</span>}
            {isActive && (isMobile || !collapsed) && (
              <motion.div
                layoutId={isMobile ? "activeIndicatorMobile" : "activeIndicatorDesktop"}
                className="ml-auto w-1.5 h-1.5 rounded-full bg-primary"
              />
            )}
          </NavLink>
        );
      })}
    </nav>
  );

  return (
    <>
      <motion.aside
        animate={{ width: collapsed ? 72 : 240 }}
        transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
        className="relative hidden md:flex flex-col h-screen border-r border-border/50 bg-sidebar overflow-hidden z-50"
      >
        <div className="h-14 flex items-center px-4 border-b border-border/50">
          <div className="flex items-center gap-3">
            <img src="/vertice-logo.png" alt="Vértice Logo" className="w-8 h-8 object-contain rounded-md" />
            {!collapsed && (
              <motion.span
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-lg font-bold text-gradient-primary"
              >
                Vértice
              </motion.span>
            )}
          </div>
        </div>
        {navContent(false)}

        <div className="p-3 border-t border-border/50">
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="w-full flex items-center justify-center p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors cursor-pointer"
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>
      </motion.aside>

      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.button
              aria-label="Cerrar menú"
              onClick={onMobileClose}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-40 bg-black/50 md:hidden"
            />

            <motion.aside
              initial={{ x: -320 }}
              animate={{ x: 0 }}
              exit={{ x: -320 }}
              transition={{ duration: 0.2, ease: [0.4, 0, 0.2, 1] }}
              className="fixed left-0 top-0 bottom-0 z-50 w-[85vw] max-w-[300px] bg-sidebar border-r border-border/50 md:hidden flex flex-col"
            >
              <div className="h-14 flex items-center justify-between px-4 border-b border-border/50">
                <div className="flex items-center gap-3">
                  <img src="/vertice-logo.png" alt="Vértice Logo" className="w-8 h-8 object-contain rounded-md" />
                  <span className="text-lg font-bold text-gradient-primary">Vértice</span>
                </div>
                <button
                  onClick={onMobileClose}
                  className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted/50"
                  aria-label="Cerrar menú"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
              {navContent(true)}
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
