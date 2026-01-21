<template>
  <div class="flex flex-col items-center justify-center space-y-2">
    <div class="spinner"></div>
    <span v-if="text" class="text-brand-gray">{{ text }}</span>
  </div>
</template>

<script setup lang="ts">
defineProps<{ text?: string }>();
</script>

<style scoped>
.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #FFF;
  border-bottom-color: #EE9B00; /* brand-accent */
  border-radius: 50%;
  display: inline-block;
  box-sizing: border-box;
  animation: rotation 1s linear infinite;
}

@keyframes rotation {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>