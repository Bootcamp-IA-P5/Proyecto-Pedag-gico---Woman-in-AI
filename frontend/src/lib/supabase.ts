import { createClient } from '@supabase/supabase-js';

const runtimeSupabaseUrl = window.__VERTICE_ENV?.VITE_SUPABASE_URL;
const runtimeSupabaseAnonKey = window.__VERTICE_ENV?.VITE_SUPABASE_ANON_KEY;

const supabaseUrl = (runtimeSupabaseUrl || import.meta.env.VITE_SUPABASE_URL)?.trim();
const supabaseAnonKey = (runtimeSupabaseAnonKey || import.meta.env.VITE_SUPABASE_ANON_KEY)?.trim();

export const hasSupabaseEnv = Boolean(supabaseUrl && supabaseAnonKey);

export const supabase = hasSupabaseEnv
  ? createClient(supabaseUrl as string, supabaseAnonKey as string)
  : null;
