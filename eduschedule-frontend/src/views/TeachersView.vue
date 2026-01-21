<script setup lang="ts">
import { ref, watch } from 'vue';
import LoadingSpinner from '@/components/LoadingSpinner.vue';
import { useAuthStore } from '@/stores/auth';
import HelperPopup from '@/components/HelperPopup.vue';

// Define the data structures
interface User {
  id: string;
  name: string;
  email: string;
}
interface Teacher {
  id: string;
  user_id: string;
  user_name?: string;
  user_email?: string;
}

const teachers = ref<Teacher[]>([]);
const users = ref<User[]>([]);
const isLoading = ref(true);
const showAddModal = ref(false);
const newTeacher = ref({ name: '', email: '' }); // New state for the form
const authStore = useAuthStore();

async function fetchData() {
  const token = authStore.session?.access_token;
  if (!token) return;

  isLoading.value = true;
  try {
    const headers = { 'Authorization': `Bearer ${token}` };

    const usersResponse = await fetch('/api/users', { headers }); 
    const teachersResponse = await fetch('/api/teachers', { headers });

    if (!usersResponse.ok || !teachersResponse.ok) throw new Error('Failed to fetch data');
    
    const usersData: User[] = await usersResponse.json();
    const teachersData: Teacher[] = await teachersResponse.json();
    
    const usersById = new Map(usersData.map((u) => [u.id, u]));
    
    teachers.value = teachersData.map((t: Teacher) => {
      const user = usersById.get(t.user_id);
      return {
        ...t,
        user_name: user ? user.name : 'N/A',
        user_email: user ? user.email : 'N/A',
      };
    });

    users.value = usersData;
    
  } catch (error) {
    console.error(error);
  } finally {
    isLoading.value = false;
  }
}

watch(() => authStore.session, (newSession) => {
  if (newSession) {
    fetchData();
  }
}, { immediate: true });

async function handleAddTeacher() {
  const token = authStore.session?.access_token;
  if (!newTeacher.value.name || !newTeacher.value.email || !token) return;
  
  try {
    const response = await fetch('/api/teachers/add', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(newTeacher.value),
    });

    if (!response.ok) throw new Error('Failed to add teacher');
    
    fetchData(); // Refresh the list
    showAddModal.value = false;
    newTeacher.value = { name: '', email: '' };

  } catch (error) {
    console.error(error);
  }
}
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <div class="flex items-center">
        <h2 class="text-3xl font-bold">Manage Teachers</h2>
        <HelperPopup text="Add new teachers to your school. This will create a user account for them and send an email to set up their password." />
      </div>
      <button @click="showAddModal = true" class="bg-brand-primary text-white font-bold py-2 px-4 rounded-lg hover:bg-brand-secondary transition-transform hover:scale-105">
        + Add Teacher
      </button>
    </div>

    <LoadingSpinner v-if="isLoading" text="Fetching data..." />

    <div v-else class="bg-white rounded-lg shadow-md overflow-hidden">
      <table class="min-w-full">
        <thead class="bg-brand-light">
          <tr>
            <th class="py-3 px-4 text-left font-semibold text-brand-gray">Name</th>
            <th class="py-3 px-4 text-left font-semibold text-brand-gray">Email</th>
            <th class="py-3 px-4 text-left font-semibold text-brand-gray">User ID</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="teacher in teachers" :key="teacher.id" class="border-t">
            <td class="py-3 px-4 font-medium">{{ teacher.user_name || 'N/A' }}</td>
            <td class="py-3 px-4">{{ teacher.user_email || 'N/A' }}</td>
            <td class="py-3 px-4 text-sm text-brand-gray">{{ teacher.user_id }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <Transition name="fade">
      <div v-if="showAddModal" class="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center">
        <div class="bg-white p-8 rounded-lg shadow-xl w-full max-w-md">
          <h3 class="text-2xl font-bold mb-6">Add New Teacher</h3>
          <form @submit.prevent="handleAddTeacher">
            <div class="mb-4">
              <label class="block text-brand-gray mb-1" for="teacher-name">Full Name</label>
              <input v-model="newTeacher.name" id="teacher-name" type="text" class="w-full p-2 border rounded-md" required>
            </div>
            <div class="mb-6">
              <label class="block text-brand-gray mb-1" for="teacher-email">School Email</label>
              <input v-model="newTeacher.email" id="teacher-email" type="email" class="w-full p-2 border rounded-md" required>
            </div>
            <div class="flex justify-end space-x-4">
              <button type="button" @click="showAddModal = false" class="bg-gray-200 px-4 py-2 rounded-lg">Cancel</button>
              <button type="submit" class="bg-brand-accent text-brand-dark font-bold px-4 py-2 rounded-lg">Add Teacher</button>
            </div>
          </form>
        </div>
      </div>
    </Transition>
  </div>
</template>

