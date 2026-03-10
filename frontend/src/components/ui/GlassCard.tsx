import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { ReactNode } from "react";

interface GlassCardProps {
  children: ReactNode;
  className?: string;
  delay?: number;
  hover?: boolean;
  glow?: "purple" | "blue" | "cyan" | "none";
}

export function GlassCard({ children, className, delay = 0, hover = true, glow = "none" }: GlassCardProps) {
  const glowClass = {
    purple: "glow-purple",
    blue: "glow-blue",
    cyan: "glow-cyan",
    none: "",
  }[glow];

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay, ease: [0.4, 0, 0.2, 1] }}
      whileHover={hover ? { y: -2, transition: { duration: 0.2 } } : undefined}
      className={cn(
        "glass rounded-xl p-5 transition-all duration-300",
        hover && "hover:border-primary/30",
        glowClass,
        className
      )}
    >
      {children}
    </motion.div>
  );
}
