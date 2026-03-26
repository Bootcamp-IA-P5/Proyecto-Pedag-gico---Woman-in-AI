import { motion } from "framer-motion";
import { LucideIcon } from "lucide-react";

interface PageHeaderProps {
  title: string;
  subtitle: string;
  icon: LucideIcon;
}

export function PageHeader({ title, subtitle, icon: Icon }: PageHeaderProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="flex items-start sm:items-center gap-3 sm:gap-4 mb-6 sm:mb-8"
    >
      <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-xl bg-gradient-primary flex items-center justify-center glow-purple flex-shrink-0">
        <Icon className="w-5 h-5 sm:w-6 sm:h-6 text-primary-foreground" />
      </div>
      <div className="min-w-0">
        <h1 className="text-xl sm:text-3xl font-bold text-foreground leading-tight">{title}</h1>
        <p className="text-sm sm:text-base text-muted-foreground leading-snug">{subtitle}</p>
      </div>
    </motion.div>
  );
}
