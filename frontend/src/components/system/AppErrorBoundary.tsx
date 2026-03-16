import { Component, type ErrorInfo, type ReactNode } from "react";

type Props = {
  children: ReactNode;
};

type State = {
  hasError: boolean;
  message: string;
};

export class AppErrorBoundary extends Component<Props, State> {
  state: State = {
    hasError: false,
    message: "",
  };

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      message: error?.message || "Error inesperado en la aplicación.",
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("AppErrorBoundary:", error, errorInfo);
  }

  private handleReload = () => {
    window.location.reload();
  };

  render() {
    if (!this.state.hasError) {
      return this.props.children;
    }

    return (
      <div className="min-h-screen bg-background text-foreground flex items-center justify-center p-6">
        <div className="max-w-md w-full rounded-xl border border-border/50 bg-card/70 p-6">
          <h1 className="text-lg font-semibold mb-2">Ocurrió un error al renderizar esta vista</h1>
          <p className="text-sm text-muted-foreground mb-4">{this.state.message}</p>
          <button
            onClick={this.handleReload}
            className="rounded-md border border-border/60 px-3 py-2 text-sm hover:border-primary/60"
          >
            Recargar aplicación
          </button>
        </div>
      </div>
    );
  }
}
