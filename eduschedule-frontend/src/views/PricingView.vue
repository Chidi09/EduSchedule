<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useAuthStore } from '@/stores/auth';
import LoadingSpinner from '@/components/LoadingSpinner.vue';

// 1. Define the interface for a plan
interface Plan {
  id: string;
  amount: number;
  label: string;
}

const authStore = useAuthStore();
const isLoading = ref(false);
const deal = ref({ isActive: false, expiresIn: 0 });

// Dummy data using the Plan interface
const currentPrices = ref<{ [key: number]: Plan }>({ 
  12: { id: 'price_12_month', amount: 99, label: 'Premium Plan' } 
});

function startCountdown(seconds: number) {
  console.log(`Countdown started for ${seconds} seconds.`);
  deal.value.expiresIn = seconds;
  // In a real app, you would set an interval here to tick the countdown down.
}

// 2. Use the new 'Plan' interface in the function signature
async function handleUpgrade(plan: Plan) {
  isLoading.value = true;
  try {
    const token = authStore.session?.access_token;
    const response = await fetch('/api/payments/subscribe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify({ planId: plan.id, amount: plan.amount * 100 })
    });
    const data = await response.json();
    if (data.authorization_url) {
      window.location.href = data.authorization_url;
    }
  } finally {
    isLoading.value = false;
  }
}

onMounted(async () => {
  const token = authStore.session?.access_token;
  if (token) {
    try {
      const response = await fetch('/api/users/me/deal-status', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      deal.value = data;
      if (data.isActive) {
        startCountdown(data.expiresIn);
      }
    } catch (error) {
      console.error("Failed to fetch deal status:", error);
    }
  }
});
</script>

<template>
  <div>
    <h1 class="text-3xl font-bold mb-4">Pricing Plans</h1>
    <p class="text-brand-gray mb-8">Choose the plan that's right for your institution.</p>
    
    <div class="mt-8 bg-white p-8 rounded-lg shadow-md max-w-sm mx-auto flex flex-col" style="height: 400px;">
        <h2 class="text-2xl font-bold text-center">Premium Plan</h2>
        <p class="text-center text-brand-gray mt-2">All features, unlimited access, priority support.</p>
        <div class="text-center text-4xl font-bold my-8">
            ${{ currentPrices[12].amount }} <span class="text-lg font-normal">/ month</span>
        </div>
        
        <div v-if="deal.isActive" class="my-4 text-center text-green-600 font-semibold p-2 bg-green-100 rounded-md">
            🎉 Special Offer Active! Expires in {{ deal.expiresIn }} seconds.
        </div>

        <button @click="handleUpgrade(currentPrices[12])" :disabled="isLoading" class="w-full mt-auto py-3 px-4 rounded-lg bg-brand-accent text-brand-dark font-bold hover:opacity-90 disabled:opacity-50 transition-colors flex justify-center items-center">
            <LoadingSpinner v-if="isLoading" />
            <span v-else>Choose Plan</span>
        </button>
    </div>
  </div>
</template>

