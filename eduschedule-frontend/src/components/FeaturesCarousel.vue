<script setup lang="ts">
import { ref } from 'vue';

const features = [
  { 
    title: 'AI-Powered Scheduling', 
    description: 'Our intelligent engine generates balanced, conflict-free timetables in minutes, not hours.',
    icon: '🧠' 
  },
  { 
    title: 'Drag & Drop Editing', 
    description: 'Easily make manual adjustments to your schedule with an intuitive interface and real-time conflict validation.',
    icon: '🖐️'
  },
  { 
    title: 'Teacher Preferences', 
    description: 'Create happier staff by allowing our solver to consider teacher availability and preferences.',
    icon: '❤️'
  },
];

const currentFeatureIndex = ref(0);

function nextFeature() {
  currentFeatureIndex.value = (currentFeatureIndex.value + 1) % features.length;
}
function prevFeature() {
  currentFeatureIndex.value = (currentFeatureIndex.value - 1 + features.length) % features.length;
}
</script>

<template>
  <div class="relative w-full max-w-2xl mx-auto text-center">
    <div class="overflow-hidden relative h-48">
      <Transition name="slide-fade">
        <div :key="currentFeatureIndex" class="absolute w-full">
          <p class="text-5xl">{{ features[currentFeatureIndex].icon }}</p>
          <h3 class="text-2xl font-bold mt-4">{{ features[currentFeatureIndex].title }}</h3>
          <p class="mt-2 text-brand-gray">{{ features[currentFeatureIndex].description }}</p>
        </div>
      </Transition>
    </div>

    <button @click="prevFeature" class="absolute left-0 top-1/2 -translate-y-1/2 p-2 rounded-full bg-gray-200 hover:bg-gray-300">
      &lt;
    </button>
    <button @click="nextFeature" class="absolute right-0 top-1/2 -translate-y-1/2 p-2 rounded-full bg-gray-200 hover:bg-gray-300">
      &gt;
    </button>
  </div>
</template>

<style scoped>
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.5s ease;
}
.slide-fade-enter-from {
  opacity: 0;
  transform: translateX(50px);
}
.slide-fade-leave-to {
  opacity: 0;
  transform: translateX(-50px);
}
</style>