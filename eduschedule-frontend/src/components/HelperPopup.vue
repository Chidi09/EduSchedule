<script setup lang="ts">
import { ref } from 'vue';

defineProps<{
  text: string;
}>();

const show = ref(false);
</script>

<template>
  <div class="relative inline-block ml-2">
    <button @click="show = !show" @blur="show = false" class="w-5 h-5 flex items-center justify-center bg-gray-300 text-gray-600 rounded-full text-xs font-bold">
      ?
    </button>
    <Transition name="fade">
      <div v-if="show" class="absolute bottom-full mb-2 w-64 p-3 bg-brand-dark text-white text-sm rounded-lg shadow-lg z-10">
        {{ text }}
      </div>
    </Transition>
  </div>
</template>