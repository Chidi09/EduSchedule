import { defineStore } from 'pinia';
import { supabase, isSupabaseConfigured } from '../supabase';
import type { Session, User, SignUpWithPasswordCredentials } from '@supabase/supabase-js';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    session: null as Session | null,
    user: null as User | null,
    profile: null as any | null,
    loading: true,
    isAuthReady: false,
    isConfigured: isSupabaseConfigured,
  }),
  
  actions: {
    async initialize() {
      try {
        if (!this.isConfigured) {
          console.warn('Supabase is not configured. Authentication will not work.');
          this.loading = false;
          this.isAuthReady = true;
          return;
        }

        const { data } = await supabase.auth.getSession();
        this.session = data.session;
        this.user = data.session?.user || null;
        
        if (this.user) {
          await this.fetchProfile();
        }
      } catch (error) {
        console.error("Auth init error:", error);
      } finally {
        this.loading = false;
        this.isAuthReady = true;
      }

      // Listen for auth changes
      supabase.auth.onAuthStateChange(async (_event, session) => {
        this.session = session;
        this.user = session?.user || null;
        if (this.user) {
          await this.fetchProfile();
        } else {
          this.profile = null;
        }
        this.isAuthReady = true;
      });
    },

    async fetchProfile() {
      if (!this.user || !this.isConfigured) return;
      
      try {
        const { data, error } = await supabase
          .from('profiles')
          .select('*')
          .eq('id', this.user.id)
          .single();
          
        if (!error && data) {
          this.profile = data;
        }
      } catch (error) {
        console.error('Failed to fetch profile:', error);
      }
    },

    async signUp(credentials: SignUpWithPasswordCredentials) {
      if (!this.isConfigured) {
        return { data: { user: null, session: null }, error: { message: 'Supabase not configured' } };
      }
      return await supabase.auth.signUp(credentials);
    },

    async signIn(credentials: SignUpWithPasswordCredentials) {
      if (!this.isConfigured) {
        return { data: { user: null, session: null }, error: { message: 'Supabase not configured' } };
      }
      return await supabase.auth.signInWithPassword(credentials);
    },

    async signOut() {
      if (this.isConfigured) {
        await supabase.auth.signOut();
      }
      this.session = null;
      this.user = null;
      this.profile = null;
    },

    // Legacy method name for compatibility
    async logout() {
      return await this.signOut();
    }
  }
});
