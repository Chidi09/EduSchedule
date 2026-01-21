<template>
  <div class="flex items-center justify-center min-h-screen bg-brand-light">
    <div class="w-full max-w-md p-8 space-y-8 bg-white rounded-lg shadow-md">
      <div>
        <h1 class="text-3xl font-bold text-center text-brand-primary">
          Welcome to EduSchedule!
        </h1>
        <p class="mt-2 text-center text-brand-gray">
          Let's set up your school to get started.
        </p>
      </div>
      <form @submit.prevent="handleCreateSchool">
        <div class="mb-6">
          <label class="block text-brand-gray mb-1" for="schoolName">What is the name of your school?</label>
          <input v-model="schoolName" type="text" id="schoolName" class="w-full p-2 border rounded-md" required placeholder="e.g. Greenwood High">
        </div>
        <button type="submit" :disabled="isLoading" class="w-full bg-brand-accent text-brand-dark font-bold py-2 px-4 rounded-lg hover:opacity-90 disabled:opacity-50">
          <span v-if="isLoading">Creating...</span>
          <span v-else>Continue</span>
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

const schoolName = ref('');
const isLoading = ref(false);
const authStore = useAuthStore();
const router = useRouter();

async function handleCreateSchool() {
  const token = authStore.session?.access_token;
  if (!schoolName.value || !token) {
    alert("Authentication error. Please wait a moment and try again.");
    return;
  }

  isLoading.value = true;

  try {
    const response = await fetch('/api/schools/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ name: schoolName.value })
    });

    if (!response.ok) throw new Error('Failed to create school');

    const newSchool = await response.json();
    if (authStore.profile) {
        authStore.profile.school_id = newSchool.id;
    }

    router.push('/dashboard');

  } catch (error) {
    console.error(error);
  } finally {
    isLoading.value = false;
  }
}
</script>

