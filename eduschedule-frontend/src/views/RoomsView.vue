<script setup lang="ts">
import { ref, watch } from 'vue';
import LoadingSpinner from '@/components/LoadingSpinner.vue';
import { useAuthStore } from '@/stores/auth';
import HelperPopup from '@/components/HelperPopup.vue';

// Define the data structure for a Room
interface Room {
  id: string;
  name: string;
  capacity: number;
}

const rooms = ref<Room[]>([]);
const isLoading = ref(true);
const showAddModal = ref(false);
const newRoom = ref({ name: '', capacity: 30 });
const authStore = useAuthStore();

async function fetchData() {
  const token = authStore.session?.access_token;
  if (!token) {
    console.error("Authentication token not found.");
    return;
  }

  isLoading.value = true;
  try {
    const response = await fetch('/api/rooms', {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (!response.ok) throw new Error('Failed to fetch rooms');
    
    rooms.value = await response.json();
    
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

async function handleAddRoom() {
  const token = authStore.session?.access_token;
  if (!newRoom.value.name || !newRoom.value.capacity || !token) return;
  
  try {
    const response = await fetch('/api/rooms', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(newRoom.value),
    });

    if (!response.ok) throw new Error('Failed to add room');
    
    fetchData(); // Refresh the list of rooms
    showAddModal.value = false;
    newRoom.value = { name: '', capacity: 30 };

  } catch (error) {
    console.error(error);
  }
}
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <div class="flex items-center">
        <h2 class="text-3xl font-bold">Manage Rooms</h2>
        <HelperPopup text="Add, view, and manage all the rooms and halls available in your school." />
      </div>
      <button @click="showAddModal = true" class="bg-brand-primary text-white font-bold py-2 px-4 rounded-lg hover:bg-brand-secondary transition-transform hover:scale-105">
        + Add Room
      </button>
    </div>

    <LoadingSpinner v-if="isLoading" text="Fetching rooms..." />

    <div v-else class="bg-white rounded-lg shadow-md overflow-hidden">
      <table class="min-w-full">
        <thead class="bg-brand-light">
          <tr>
            <th class="py-3 px-4 text-left font-semibold text-brand-gray">Room Name</th>
            <th class="py-3 px-4 text-left font-semibold text-brand-gray">Capacity</th>
            <th class="py-3 px-4 text-left font-semibold text-brand-gray">Room ID</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="room in rooms" :key="room.id" class="border-t">
            <td class="py-3 px-4 font-medium">{{ room.name }}</td>
            <td class="py-3 px-4">{{ room.capacity }}</td>
            <td class="py-3 px-4 text-sm text-brand-gray">{{ room.id }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <Transition name="fade">
      <div v-if="showAddModal" class="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center">
        <div class="bg-white p-8 rounded-lg shadow-xl w-full max-w-md">
          <h3 class="text-2xl font-bold mb-6">Add New Room</h3>
          <form @submit.prevent="handleAddRoom">
            <div class="mb-4">
              <label class="block text-brand-gray mb-1" for="room-name">Room Name</label>
              <input v-model="newRoom.name" id="room-name" type="text" class="w-full p-2 border rounded-md" required placeholder="e.g., Science Lab 1">
            </div>
            <div class="mb-6">
              <label class="block text-brand-gray mb-1" for="room-capacity">Capacity</label>
              <input v-model.number="newRoom.capacity" id="room-capacity" type="number" class="w-full p-2 border rounded-md" required>
            </div>
            <div class="flex justify-end space-x-4">
              <button type="button" @click="showAddModal = false" class="bg-gray-200 px-4 py-2 rounded-lg">Cancel</button>
              <button type="submit" class="bg-brand-accent text-brand-dark font-bold px-4 py-2 rounded-lg">Add Room</button>
            </div>
          </form>
        </div>
      </div>
    </Transition>
  </div>
</template>
