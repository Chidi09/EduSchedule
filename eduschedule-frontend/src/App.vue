<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRoute, RouterView, RouterLink } from 'vue-router';
import { useAuthStore } from './stores/auth';

const route = useRoute();
const authStore = useAuthStore();
const isSidebarOpen = ref(false);

const isAppRoute = computed(() => route.meta.requiresAuth);
const userRole = computed(() => authStore.profile?.role);

async function logout() {
  await authStore.logout();
  // The router guard will automatically redirect to the login page
}
</script>

<template>
  <div v-if="isAppRoute" class="relative flex h-screen font-sans overflow-hidden">
    <aside 
      @mouseenter="isSidebarOpen = true" 
      @mouseleave="isSidebarOpen = false"
      :class="[
        'absolute lg:relative inset-y-0 left-0 bg-brand-primary text-white p-6 flex flex-col z-20 transition-all duration-300 ease-in-out',
        isSidebarOpen ? 'w-64' : 'w-20'
      ]"
    >
      <h1 :class="['text-2xl font-bold text-brand-accent mb-10 transition-opacity', !isSidebarOpen && 'opacity-0']">EduSchedule</h1>
      
      <nav class="flex flex-col space-y-2">
        <template v-if="userRole === 'admin'">
          <RouterLink to="/dashboard" class="flex items-center p-2 rounded-md hover:bg-brand-secondary transition-colors">
            <span class="text-2xl">📊</span> <span v-if="isSidebarOpen" class="ml-4">Dashboard</span>
          </RouterLink>
          <RouterLink to="/teachers" class="flex items-center p-2 rounded-md hover:bg-brand-secondary transition-colors">
            <span class="text-2xl">👩‍🏫</span> <span v-if="isSidebarOpen" class="ml-4">Teachers</span>
          </RouterLink>
          <RouterLink to="/rooms" class="flex items-center p-2 rounded-md hover:bg-brand-secondary transition-colors">
            <span class="text-2xl">🚪</span> <span v-if="isSidebarOpen" class="ml-4">Rooms</span>
          </RouterLink>
           <RouterLink to="/subjects" class="flex items-center p-2 rounded-md hover:bg-brand-secondary transition-colors">
            <span class="text-2xl">📚</span> <span v-if="isSidebarOpen" class="ml-4">Subjects</span>
          </RouterLink>
          <RouterLink to="/classes" class="flex items-center p-2 rounded-md hover:bg-brand-secondary transition-colors">
            <span class="text-2xl">🏫</span> <span v-if="isSidebarOpen" class="ml-4">Classes</span>
          </RouterLink>
        </template>

        <template v-if="userRole === 'teacher'">
          <RouterLink to="/my-schedule" class="flex items-center p-2 rounded-md hover:bg-brand-secondary transition-colors">
            <span class="text-2xl">🗓️</span> <span v-if="isSidebarOpen" class="ml-4">My Schedule</span>
          </RouterLink>
          <RouterLink to="/my-preferences" class="flex items-center p-2 rounded-md hover:bg-brand-secondary transition-colors">
            <span class="text-2xl">⚙️</span> <span v-if="isSidebarOpen" class="ml-4">My Preferences</span>
          </RouterLink>
        </template>
        
        <RouterLink to="/pricing" class="flex items-center p-2 rounded-md hover:bg-brand-secondary transition-colors">
          <span class="text-2xl">💳</span> <span v-if="isSidebarOpen" class="ml-4">Pricing</span>
        </RouterLink>
      </nav>
      
      <div class="mt-auto">
        <button @click="logout" class="w-full text-left flex items-center p-2 rounded-md hover:bg-brand-secondary transition-colors">
          <span class="text-2xl">➡️</span> <span v-if="isSidebarOpen" class="ml-4">Log Out</span>
        </button>
      </div>
    </aside>

    <button @click="isSidebarOpen = !isSidebarOpen" class="lg:hidden fixed bottom-4 right-4 z-30 w-12 h-12 bg-brand-primary text-white rounded-full shadow-lg">
      <span v-if="isSidebarOpen">&lt;</span>
      <span v-else>&gt;</span>
    </button>

    <main :class="['flex-1 p-8 overflow-y-auto bg-brand-light transition-all duration-300 ease-in-out', isSidebarOpen ? 'lg:ml-0' : 'lg:ml-[-192px]']">
      <RouterView v-slot="{ Component }">
        <Transition name="fade" mode="out-in">
          <component :is="Component" />
        </Transition>
      </RouterView>
    </main>
  </div>

  <div v-else>
    <RouterView />
  </div>
</template>

<style lang="postcss">
.router-link-exact-active {
  @apply bg-brand-secondary font-semibold;
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>

