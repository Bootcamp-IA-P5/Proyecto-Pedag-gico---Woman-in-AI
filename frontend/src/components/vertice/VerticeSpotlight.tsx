import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, Send, X, Bot, User } from "lucide-react";

interface Message {
  role: "user" | "ai";
  content: string;
}

const sampleResponses: Record<string, string> = {
  default: "¡Hola! Soy **Vértice AI** 🧠. Puedo analizar tendencias musicales, géneros, artistas y mucho más. ¿Qué quieres descubrir hoy?",
  vallenato: "📊 **Tendencia del Vallenato (2024)**\n\nEl vallenato ha experimentado un crecimiento del **23%** en streams durante 2024. Los artistas más destacados incluyen a Carlos Vives y Silvestre Dangond, con una presencia femenina creciente del **18%** en el género.",
  reggaeton: "🔥 **Reggaetón - Datos Clave**\n\nDomina el **34%** de los streams totales en Latinoamérica. Bad Bunny sigue liderando con 2.1B reproducciones, seguido por Karol G con 1.8B.",
  tendencia: "📈 **Top Tendencias 2024**\n\n1. Corridos Tumbados: +45% crecimiento\n2. Afrobeats Fusión: +38%\n3. K-Pop Latino: +29%\n4. Vallenato Urbano: +23%",
};

function getResponse(query: string): string {
  const q = query.toLowerCase();
  if (q.includes("vallenato")) return sampleResponses.vallenato;
  if (q.includes("reggaeton") || q.includes("reguetón")) return sampleResponses.reggaeton;
  if (q.includes("tendencia") || q.includes("trend")) return sampleResponses.tendencia;
  return sampleResponses.default;
}

interface Props {
  open: boolean;
  onClose: () => void;
}

export function VerticeSpotlight({ open, onClose }: Props) {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 100);
      if (messages.length === 0) {
        setMessages([{ role: "ai", content: sampleResponses.default }]);
      }
    }
  }, [open]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        open ? onClose() : null;
      }
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, onClose]);

  const handleSend = () => {
    if (!query.trim()) return;
    const userMsg = query.trim();
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    setQuery("");
    setIsTyping(true);
    setTimeout(() => {
      setMessages((prev) => [...prev, { role: "ai", content: getResponse(userMsg) }]);
      setIsTyping(false);
    }, 1200);
  };

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50"
            onClick={onClose}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -20 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="fixed top-[10%] left-1/2 -translate-x-1/2 w-full max-w-2xl z-50"
          >
            <div className="glass-strong rounded-2xl shadow-2xl overflow-hidden glow-purple">
              {/* Header */}
              <div className="flex items-center justify-between px-5 py-3 border-b border-border/50">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-md bg-gradient-primary flex items-center justify-center">
                    <Sparkles className="w-3 h-3 text-primary-foreground" />
                  </div>
                  <span className="text-sm font-semibold text-gradient-primary">Vértice AI</span>
                </div>
                <button onClick={onClose} className="p-1 rounded-md hover:bg-muted/50 transition-colors cursor-pointer">
                  <X className="w-4 h-4 text-muted-foreground" />
                </button>
              </div>

              {/* Messages */}
              <div className="max-h-[400px] overflow-y-auto p-4 space-y-3 scrollbar-thin">
                {messages.map((msg, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.05 }}
                    className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}
                  >
                    {msg.role === "ai" && (
                      <div className="w-7 h-7 rounded-lg bg-gradient-primary flex items-center justify-center flex-shrink-0 mt-0.5">
                        <Bot className="w-3.5 h-3.5 text-primary-foreground" />
                      </div>
                    )}
                    <div
                      className={`max-w-[80%] rounded-xl px-4 py-2.5 text-sm leading-relaxed ${
                        msg.role === "user"
                          ? "bg-primary/20 text-foreground"
                          : "bg-muted/50 text-foreground"
                      }`}
                    >
                      <div className="whitespace-pre-wrap">{msg.content}</div>
                    </div>
                    {msg.role === "user" && (
                      <div className="w-7 h-7 rounded-lg bg-muted flex items-center justify-center flex-shrink-0 mt-0.5">
                        <User className="w-3.5 h-3.5 text-muted-foreground" />
                      </div>
                    )}
                  </motion.div>
                ))}
                {isTyping && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="flex gap-3"
                  >
                    <div className="w-7 h-7 rounded-lg bg-gradient-primary flex items-center justify-center flex-shrink-0">
                      <Bot className="w-3.5 h-3.5 text-primary-foreground" />
                    </div>
                    <div className="bg-muted/50 rounded-xl px-4 py-3 flex gap-1">
                      <span className="w-2 h-2 rounded-full bg-primary/60 animate-bounce" style={{ animationDelay: "0ms" }} />
                      <span className="w-2 h-2 rounded-full bg-primary/60 animate-bounce" style={{ animationDelay: "150ms" }} />
                      <span className="w-2 h-2 rounded-full bg-primary/60 animate-bounce" style={{ animationDelay: "300ms" }} />
                    </div>
                  </motion.div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Input */}
              <div className="p-3 border-t border-border/50">
                <div className="flex items-center gap-2">
                  <input
                    ref={inputRef}
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSend()}
                    placeholder="¿Cuál es la tendencia del vallenato en 2024?"
                    className="flex-1 bg-transparent border-none outline-none text-sm text-foreground placeholder:text-muted-foreground"
                  />
                  <button
                    onClick={handleSend}
                    disabled={!query.trim()}
                    className="p-2 rounded-lg bg-gradient-primary text-primary-foreground disabled:opacity-30 hover:opacity-90 transition-opacity cursor-pointer"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
