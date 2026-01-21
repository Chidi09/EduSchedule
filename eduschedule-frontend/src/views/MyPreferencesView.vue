<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useAuthStore } from '@/stores/auth';

const authStore = useAuthStore();
const preferences = ref({
  prefers_morning: false,
  avoids_last_period: false,
});
const isLoading = ref(true);
const successMessage = ref('');
const errorMessage = ref('');

async function fetchPreferences() {
  isLoading.value = true;
  errorMessage.value = '';
  try {
    const token = authStore.session?.access_token;
    const response = await fetch('/api/teachers/me', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!response.ok) throw new Error('Could not fetch preferences.');
    const data = await response.json();
    if (data.preferences) {
      preferences.value = data.preferences;
    }
  } catch (error) {
    errorMessage.value = 'Failed to load your preferences.';
    console.error(error);
  } finally {
    isLoading.value = false;
  }
}

async function savePreferences() {
  successMessage.value = '';
  errorMessage.value = '';
  try {
    const token = authStore.session?.access_token;
    const response = await fetch('/api/teachers/me', {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(preferences.value)
    });
    if (!response.ok) throw new Error('Failed to save preferences.');
    successMessage.value = 'Your preferences have been saved successfully!';
  } catch (error) {
    errorMessage.value = 'An error occurred while saving.';
    console.error(error);
  } finally {
    setTimeout(() => {
      successMessage.value = '';
      errorMessage.value = '';
    }, 3000);
  }
}

onMounted(fetchPreferences);
</script>

<template>
  <div>
    <h2 class="text-3xl font-bold mb-6">My Preferences</h2>
    <div v-if="isLoading" class="text-brand-gray">Loading your preferences...</div>
    <div v-else class="bg-white p-6 rounded-lg shadow-md max-w-lg">
      <form @submit.prevent="savePreferences">
        <div class="space-y-4">
          <label class="flex items-center">
            <input type="checkbox" v-model="preferences.prefers_morning" class="h-4 w-4 rounded border-gray-300 text-brand-primary focus:ring-brand-secondary">
            <span class="ml-3 text-brand-dark">I prefer to teach in the morning (Periods 1-4)</span>
          </label>
          <label class="flex items-center">
            <input type="checkbox" v-model="preferences.avoids_last_period" class="h-4 w-4 rounded border-gray-300 text-brand-primary focus:ring-brand-secondary">
            <span class="ml-3 text-brand-dark">I prefer to avoid the last period of the day</span>
          </label>
        </div>
        <div class="mt-6">
          <button type="submit" class="bg-brand-primary text-white font-bold py-2 px-6 rounded-lg hover:bg-brand-secondary">
            Save Preferences
          </button>
        </div>
        <p v-if="successMessage" class="mt-4 text-green-600">{{ successMessage }}</p>
        <p v-if="errorMessage" class="mt-4 text-red-600">{{ errorMessage }}</p>
      </form>
    </div>
  </div>
</template>
