/// <reference types="vite/client" />

interface VerticeRuntimeEnv {
	VITE_API_BASE_URL?: string;
	VITE_SUPABASE_URL?: string;
	VITE_SUPABASE_ANON_KEY?: string;
}

interface Window {
	__VERTICE_ENV?: VerticeRuntimeEnv;
}
