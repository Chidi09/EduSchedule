<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useAuthStore } from '@/stores/auth';

const authStore = useAuthStore();
const stats = ref({ teachers: 0, classes: 0, subjects: 0, rooms: 0 });
const isLoading = ref(true);

// This is a simplified fetch function. In a real app, you might have a single
// endpoint to get all dashboard stats at once.
onMounted(async () => {
  try {
    const token = authStore.session?.access_token;
    const headers = { 'Authorization': `Bearer ${token}` };
    
    const [teachersRes, classesRes, subjectsRes, roomsRes] = await Promise.all([
      fetch('/api/teachers/', { headers }),
      fetch('/api/classes/', { headers }),
      fetch('/api/subjects/', { headers }),
      fetch('/api/rooms/', { headers }),
    ]);

    stats.value = {
      teachers: (await teachersRes.json()).length,
      classes: (await classesRes.json()).length,
      subjects: (await subjectsRes.json()).length,
      rooms: (await roomsRes.json()).length,
    };
  } catch (error) {
    console.error("Failed to load dashboard stats", error);
  } finally {
    isLoading.value = false;
  }
});
</script>

<template>
  <div>
    <h2 class="text-3xl font-bold mb-6">
      Welcome, {{ authStore.profile?.name || 'Admin' }}!
    </h2>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <div class="bg-white p-6 rounded-lg shadow-md">
        <h3 class="text-brand-gray">Teachers</h3>
        <p class="text-3xl font-bold">{{ stats.teachers }}</p>
      </div>
      <div class="bg-white p-6 rounded-lg shadow-md">
        <h3 class="text-brand-gray">Classes</h3>
        <p class="text-3xl font-bold">{{ stats.classes }}</p>
      </div>
      <div class="bg-white p-6 rounded-lg shadow-md">
        <h3 class="text-brand-gray">Subjects</h3>
        <p class="text-3xl font-bold">{{ stats.subjects }}</p>
      </div>
      <div class="bg-white p-6 rounded-lg shadow-md">
        <h3 class="text-brand-gray">Rooms</h3>
        <p class="text-3xl font-bold">{{ stats.rooms }}</p>
      </div>
    </div>

    <div class="bg-white p-6 rounded-lg shadow-md">
      <h3 class="text-xl font-bold mb-4">Getting Started Checklist</h3>
      <ul class="space-y-4">
        <li class="flex items-center">
          <span :class="['w-6 h-6 rounded-full mr-4 flex items-center justify-center text-white', stats.rooms > 0 ? 'bg-green-500' : 'bg-gray-300']">✓</span>
          <router-link to="/rooms" class="text-brand-primary hover:underline">Step 1: Add your school's rooms</router-link>
        </li>
        <li class="flex items-center">
          <span :class="['w-6 h-6 rounded-full mr-4 flex items-center justify-center text-white', stats.subjects > 0 ? 'bg-green-500' : 'bg-gray-300']">✓</span>
          <router-link to="/subjects" class="text-brand-primary hover:underline">Step 2: Add your subjects</router-link>
        </li>
        <li class="flex items-center">
          <span :class="['w-6 h-6 rounded-full mr-4 flex items-center justify-center text-white', stats.classes > 0 ? 'bg-green-500' : 'bg-gray-300']">✓</span>
          <router-link to="/classes" class="text-brand-primary hover:underline">Step 3: Add your classes</router-link>
        </li>
        <li class="flex items-center">
          <span :class="['w-6 h-6 rounded-full mr-4 flex items-center justify-center text-white', stats.teachers > 0 ? 'bg-green-500' : 'bg-gray-300']">✓</span>
          <router-link to="/teachers" class="text-brand-primary hover:underline">Step 4: Add your teachers</router-link>
        </li>
      </ul>
      <div class="mt-6 text-center">
        <button class="bg-brand-accent text-brand-dark font-bold py-3 px-8 rounded-lg text-lg">
          Generate New Timetable
        </button>
      </div>
    </div>
  </div>
</template>