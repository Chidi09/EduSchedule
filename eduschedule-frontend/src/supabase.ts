import { createClient, SupabaseClient } from '@supabase/supabase-js'

// Use Vite's special import.meta.env object to access the variables
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

// Create a mock client for development when env vars are missing
const createMockSupabaseClient = (): SupabaseClient => {
  console.warn('Supabase environment variables not configured. Using mock client for development.')
  
  const mockAuth = {
    getSession: () => Promise.resolve({ data: { session: null }, error: null }),
    signUp: () => Promise.resolve({ data: { user: null, session: null }, error: { message: 'Supabase not configured' } }),
    signInWithPassword: () => Promise.resolve({ data: { user: null, session: null }, error: { message: 'Supabase not configured' } }),
    signOut: () => Promise.resolve({ error: null }),
    onAuthStateChange: () => ({ data: { subscription: {} }, unsubscribe: () => {} })
  }
  
  const mockFrom = () => ({
    select: () => ({ eq: () => ({ single: () => Promise.resolve({ data: null, error: { message: 'Supabase not configured' } }) }) })
  })
  
  return { auth: mockAuth, from: mockFrom } as any
}

// Export the Supabase client with fallback
export const supabase: SupabaseClient = 
  supabaseUrl && supabaseAnonKey 
    ? createClient(supabaseUrl, supabaseAnonKey)
    : createMockSupabaseClient()

// Export a helper to check if Supabase is properly configured
export const isSupabaseConfigured = Boolean(supabaseUrl && supabaseAnonKey)
