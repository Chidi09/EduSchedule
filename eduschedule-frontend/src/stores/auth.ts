import { defineStore } from 'pinia';
import { supabase } from '../supabase';
import type { Session, User } from '@supabase/supabase-js';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    session: null as Session | null,
    user: null as User | null,
    profile: null as any | null,
    loading: true,
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
      }

      // Listen for auth changes
      supabase.auth.onAuthStateChange((_event, session) => {
        this.session = session;
        this.user = session?.user || null;
        if (this.user) this.fetchProfile();
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

    async signOut() {
      await supabase.auth.signOut();
      this.session = null;
      this.user = null;
      this.profile = null;
    }
  }
});
