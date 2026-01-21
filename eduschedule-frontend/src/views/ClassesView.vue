<script setup lang="ts">
import { ref, onMounted } from 'vue';
import LoadingSpinner from '@/components/LoadingSpinner.vue';
import { useAuthStore } from '@/stores/auth';
import HelperPopup from '@/components/HelperPopup.vue';

interface Class {
  id: string;
  name: string;
  student_count: number;
}

const classes = ref<Class[]>([]);
const isLoading = ref(true);
const showAddModal = ref(false);
const newClass = ref({ name: '', student_count: 30 });
const authStore = useAuthStore();

async function fetchClasses() {
  isLoading.value = true;
  try {
    const token = authStore.session?.access_token;
    const response = await fetch('/api/classes', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!response.ok) throw new Error('Failed to fetch classes');
    classes.value = await response.json();
  } catch (error) {
    console.error(error);
  } finally {
    isLoading.value = false;
  }
}

async function handleAddClass() {
  try {
    const token = authStore.session?.access_token;
    await fetch('/api/classes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify(newClass.value),
    });
    fetchClasses();
    showAddModal.value = false;
    newClass.value = { name: '', student_count: 30 };
  } catch (error) {
    console.error(error);
  }
}

onMounted(fetchClasses);
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <div class="flex items-center">
        <h2 class="text-3xl font-bold">Manage Classes</h2>
        <HelperPopup text="Add each class or group of students. The student count is used to ensure classes are not scheduled in rooms that are too small." />
      </div>
      <button @click="showAddModal = true" class="bg-brand-primary text-white font-bold py-2 px-4 rounded-lg">
        + Add Class
      </button>
    </div>

    <LoadingSpinner v-if="isLoading" text="Fetching classes..." />

    <div v-else class="bg-white rounded-lg shadow-md overflow-hidden">
      <table class="min-w-full">
        <thead class="bg-brand-light">
          <tr>
            <th class="py-3 px-4 text-left font-semibold text-brand-gray">Class Name</th>
            <th class="py-3 px-4 text-left font-semibold text-brand-gray">Student Count</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="cls in classes" :key="cls.id" class="border-t">
            <td class="py-3 px-4 font-medium">{{ cls.name }}</td>
            <td class="py-3 px-4">{{ cls.student_count }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <Transition name="fade">
      <div v-if="showAddModal" class="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center">
        <div class="bg-white p-8 rounded-lg shadow-xl w-full max-w-md">
          <h3 class="text-2xl font-bold mb-6">Add New Class</h3>
          <form @submit.prevent="handleAddClass">
            <div class="mb-4">
              <label class="block text-brand-gray mb-1" for="name">Class Name</label>
              <input v-model="newClass.name" type="text" id="name" class="w-full p-2 border rounded-md" required>
            </div>
            <div class="mb-6">
              <label class="block text-brand-gray mb-1" for="student_count">Student Count</label>
              <input v-model.number="newClass.student_count" type="number" id="student_count" class="w-full p-2 border rounded-md" required>
            </div>
            <div class="flex justify-end space-x-4">
              <button type="button" @click="showAddModal = false" class="bg-gray-200 px-4 py-2 rounded-lg">Cancel</button>
              <button type="submit" class="bg-brand-accent text-brand-dark font-bold px-4 py-2 rounded-lg">Save Class</button>
            </div>
          </form>
        </div>
      </div>
    </Transition>
  </div>
</template>
