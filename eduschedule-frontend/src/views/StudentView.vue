<template>
  <div>
    <h1>Student Timetable</h1>
    <div v-if="timetable">
      <h2>{{ timetable.term }} - {{ timetable.type }}</h2>
      <!-- Render timetable assignments here -->
    </div>
    <div v-else>
      <p>Loading timetable...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useAuthStore } from '@/stores/auth';

interface Assignment {
  id: string;
  teacher_id: string;
  room_id: string;
  class_id: string;
  subject_id: string;
  day_of_week: number;
  period: number;
}

interface Timetable {
  id: string;
  term: string;
  type: string;
  assignments: Assignment[];
}

const timetable = ref<Timetable | null>(null);
const authStore = useAuthStore();

onMounted(async () => {
  const token = authStore.session?.access_token;
  if (token) {
    try {
      const response = await fetch('/api/timetables/student', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        timetable.value = await response.json();
      }
    } catch (error) {
      console.error('Failed to fetch timetable:', error);
    }
  }
});
</script>

