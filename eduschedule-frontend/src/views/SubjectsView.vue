<script setup lang="ts">
import { ref, onMounted } from 'vue';
import LoadingSpinner from '@/components/LoadingSpinner.vue';
import { useAuthStore } from '@/stores/auth';
import HelperPopup from '@/components/HelperPopup.vue';

interface Subject {
  id: string;
  name: string;
  periods_per_week: number;
}

const subjects = ref<Subject[]>([]);
const isLoading = ref(true);
const showAddModal = ref(false);
const newSubject = ref({ name: '', periods_per_week: 4 });
const authStore = useAuthStore();

async function fetchSubjects() {
  isLoading.value = true;
  try {
    // FIXED: Use Supabase session token instead of Firebase getIdToken()
    const token = authStore.session?.access_token;
    if (!token) return;

    const response = await fetch('/api/subjects', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!response.ok) throw new Error('Failed to fetch subjects');
    subjects.value = await response.json();
  } catch (error) {
    console.error(error);
  } finally {
    isLoading.value = false;
  }
}

async function handleAddSubject() {
  try {
    // FIXED: Use Supabase session token instead of Firebase getIdToken()
    const token = authStore.session?.access_token;
    if (!token) return;

    const response = await fetch('/api/subjects', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(newSubject.value),
    });
    if (!response.ok) throw new Error('Failed to add subject');

    await fetchSubjects();
    showAddModal.value = false;
    newSubject.value = { name: '', periods_per_week: 4 };
  } catch (error) {
    console.error(error);
  }
}

onMounted(fetchSubjects);
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <div class="flex items-center">
        <h2 class="text-3xl font-bold">Manage Subjects</h2>
        <HelperPopup text="List all the subjects taught at your institution and specify how many periods per week each subject requires." />
      </div>
      <button @click="showAddModal = true" class="bg-brand-primary text-white font-bold py-2 px-4 rounded-lg">
        + Add Subject
      </button>
    </div>

    <LoadingSpinner v-if="isLoading" text="Fetching subjects..." />

    <div v-else class="bg-white rounded-lg shadow-md overflow-hidden">
      <table class="min-w-full">
        <thead class="bg-brand-light">
          <tr>
            <th class="py-3 px-4 text-left font-semibold text-brand-gray">Subject Name</th>
            <th class="py-3 px-4 text-left font-semibold text-brand-gray">Periods Per Week</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="subject in subjects" :key="subject.id" class="border-t hover:bg-gray-50">
            <td class="py-3 px-4 font-medium">{{ subject.name }}</td>
            <td class="py-3 px-4">{{ subject.periods_per_week }}</td>
          </tr>
          <tr v-if="subjects.length === 0">
            <td colspan="2" class="py-8 text-center text-gray-500 italic">No subjects added yet.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <Transition name="fade">
      <div v-if="showAddModal" class="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50">
        <div class="bg-white p-8 rounded-lg shadow-xl w-full max-w-md">
          <h3 class="text-2xl font-bold mb-6">Add New Subject</h3>
          <form @submit.prevent="handleAddSubject">
            <div class="mb-4">
              <label class="block text-brand-gray mb-1" for="name">Subject Name</label>
              <input
                v-model="newSubject.name"
                type="text"
                id="name"
                class="w-full p-2 border rounded-md focus:ring-brand-primary focus:border-brand-primary"
                required
              >
            </div>
            <div class="mb-6">
              <label class="block text-brand-gray mb-1" for="periods">Periods per Week</label>
              <input
                v-model.number="newSubject.periods_per_week"
                type="number"
                id="periods"
                class="w-full p-2 border rounded-md focus:ring-brand-primary focus:border-brand-primary"
                required
                min="1"
              >
            </div>
            <div class="flex justify-end space-x-4">
              <button
                type="button"
                @click="showAddModal = false"
                class="bg-gray-200 hover:bg-gray-300 px-4 py-2 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                class="bg-brand-accent text-brand-dark font-bold px-4 py-2 rounded-lg hover:opacity-90 transition-opacity"
              >
                Save Subject
              </button>
            </div>
          </form>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
