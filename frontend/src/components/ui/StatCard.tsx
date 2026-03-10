import { GlassCard } from "./GlassCard";
import { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface StatCardProps {
  title: string;
  value: string;
  subtitle?: string;
  icon: LucideIcon;
  trend?: { value: number; label: string };
  gradient?: "primary" | "accent" | "warm";
  delay?: number;
}

export function StatCard({ title, value, subtitle, icon: Icon, trend, gradient = "primary", delay = 0 }: StatCardProps) {
  const gradientClass = {
    primary: "bg-gradient-primary",
    accent: "bg-gradient-accent",
    warm: "bg-gradient-warm",
  }[gradient];

  return (
    <GlassCard delay={delay} glow="purple">
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">{title}</p>
          <p className="text-2xl font-bold text-foreground">{value}</p>
          {subtitle && <p className="text-sm text-muted-foreground">{subtitle}</p>}
          {trend && (
            <div className="flex items-center gap-1.5">
              <span className={cn("text-xs font-mono font-semibold", trend.value > 0 ? "text-neon-green" : "text-destructive")}>
                {trend.value > 0 ? "+" : ""}{trend.value}%
              </span>
              <span className="text-xs text-muted-foreground">{trend.label}</span>
            </div>
          )}
        </div>
        <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center", gradientClass)}>
          <Icon className="w-5 h-5 text-primary-foreground" />
        </div>
      </div>
    </GlassCard>
  );
}
