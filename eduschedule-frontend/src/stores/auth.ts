import { defineStore } from 'pinia';
import { supabase } from '../supabase';
import type { Session, User, SignUpWithPasswordCredentials } from '@supabase/supabase-js';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    session: null as Session | null,
    user: null as User | null,
    profile: null as any | null,
    loading: true,
    isAuthReady: false,
  }),
  
  actions: {
    async initialize() {
      try {
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
      if (!this.user) return;
      
      const { data, error } = await supabase
        .from('profiles')
        .select('*')
        .eq('id', this.user.id)
        .single();
        
      if (!error && data) {
        this.profile = data;
      }
    },

    async signUp(credentials: SignUpWithPasswordCredentials) {
      return await supabase.auth.signUp(credentials);
    },

    async signIn(credentials: SignUpWithPasswordCredentials) {
      return await supabase.auth.signInWithPassword(credentials);
    },

    async signOut() {
      await supabase.auth.signOut();
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
