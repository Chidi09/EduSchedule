<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

const email = ref('');
const password = ref('');
const errorMessage = ref('');
const isLoading = ref(false);

const router = useRouter();
const authStore = useAuthStore();

async function handleRegister() {
  isLoading.value = true;
  errorMessage.value = '';
  try {
    // Pass credentials as a single object
    const { error } = await authStore.signUp({ email: email.value, password: password.value });
    if (error) throw error;
    
    // Using a custom modal/alert is better than the browser's default alert
    alert('Registration successful! Please check your email to confirm your account.');
    router.push('/login');
  } catch (error) {
    if (error instanceof Error) {
      errorMessage.value = error.message;
    } else {
      errorMessage.value = 'An unexpected error occurred.';
    }
  } finally {
    isLoading.value = false;
  }
}
</script>

<template>
  <div class="flex items-center justify-center min-h-screen bg-brand-light">
    <div class="w-full max-w-sm p-8 space-y-6 bg-white rounded-lg shadow-md">
      <div>
        <h1 class="text-3xl font-bold text-center text-brand-primary">
          Create Your Admin Account
        </h1>
        <p class="mt-2 text-center text-brand-gray">
          Start your journey with EduSchedule
        </p>
      </div>
      <form @submit.prevent="handleRegister" class="space-y-4">
        <div>
          <label for="email" class="block text-sm font-medium text-brand-gray">Email Address</label>
          <input v-model="email" type="email" id="email" required class="w-full p-2 mt-1 border rounded-md">
        </div>
        <div>
          <label for="password" class="block text-sm font-medium text-brand-gray">Password</label>
          <input v-model="password" type="password" id="password" required class="w-full p-2 mt-1 border rounded-md">
        </div>
        <p v-if="errorMessage" class="text-red-500 text-sm">{{ errorMessage }}</p>
        <button type="submit" :disabled="isLoading" class="w-full bg-brand-accent text-brand-dark font-bold py-2 px-4 rounded-lg">
          {{ isLoading ? 'Registering...' : 'Register' }}
        </button>
      </form>
      <div class="text-center">
        <span class="text-sm text-brand-gray">Already have an account? </span>
        <router-link to="/login" class="text-sm font-semibold text-brand-primary hover:underline">
          Log In
        </router-link>
      </div>
    </div>
  </div>
</template>

