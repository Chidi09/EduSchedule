import { ref, onMounted } from 'vue';
import { defineStore } from 'pinia';
// Correct the import path if your file is named 'supabase.ts'
import { supabase } from '../supabase';
import type { User, Session, AuthChangeEvent, SignUpWithPasswordCredentials } from '@supabase/supabase-js';

// Define an interface for your custom profile data
interface Profile {
  id: string;
  name: string;
  school_id: string | null;
  role: 'admin' | 'teacher';
  // Add other profile fields here
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null);
  const session = ref<Session | null>(null);
  const profile = ref<Profile | null>(null); // Use the Profile interface
  const isAuthReady = ref(false);

  supabase.auth.onAuthStateChange(async (event: AuthChangeEvent, newSession: Session | null) => {
    session.value = newSession;
    user.value = newSession?.user ?? null;

    if (user.value) {
      // If the user is logged in, fetch their profile from our 'profiles' table
      const { data } = await supabase
        .from('profiles') // <-- Correct table name
        .select('*')
        .eq('id', user.value.id)
        .single();
      profile.value = data;
    } else {
      profile.value = null;
    }
    isAuthReady.value = true;
  });

  const signUp = async (credentials: SignUpWithPasswordCredentials) => {
    return await supabase.auth.signUp(credentials);
  };

  const signIn = async (credentials: SignUpWithPasswordCredentials) => {
    return await supabase.auth.signInWithPassword(credentials);
  };

  const logout = async () => {
    await supabase.auth.signOut();
  };

  onMounted(async () => {
    const { data } = await supabase.auth.getSession();
    session.value = data.session;
    user.value = data.session?.user ?? null;
    isAuthReady.value = true;
  });

  return { user, session, profile, isAuthReady, signUp, signIn, logout };
});

