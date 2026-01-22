<script setup lang="ts">
import { ref } from 'vue';

const faqs = [
  {
    q: "Can I handle double periods (block classes)?",
    a: "Yes! You can specify subjects that require consecutive periods (e.g., a 2-hour Physics Lab), and our algorithm will force them to stay together."
  },
  {
    q: "What happens if no timetable is possible?",
    a: "The system will identify exactly which constraints are conflicting (e.g., 'Not enough Math teachers for Grade 10') so you can fix them."
  },
  {
    q: "Is my school's data secure?",
    a: "Absolutely. We use enterprise-grade encryption and strict Role-Based Access Control (RBAC) to ensure only authorized admins can access data."
  },
  {
    q: "Can I export the timetable?",
    a: "Yes, you can export schedules as PDF, Excel, or directly email them to teachers and students from the dashboard."
  }
];

const activeIndex = ref<number | null>(0);
</script>

<template>
  <section class="py-24 bg-white">
    <div class="max-w-3xl mx-auto px-6">
      <h2 class="text-3xl font-bold font-heading text-brand-primary text-center mb-12">Frequently Asked Questions</h2>

      <div class="space-y-4">
        <div
          v-for="(faq, i) in faqs"
          :key="i"
          class="border border-slate-200 rounded-2xl overflow-hidden transition-all duration-300"
          :class="activeIndex === i ? 'bg-brand-bg border-brand-accent/30 shadow-sm' : 'bg-white hover:border-slate-300'"
        >
          <button
            @click="activeIndex = activeIndex === i ? null : i"
            class="w-full flex justify-between items-center p-6 text-left focus:outline-none"
          >
            <span class="font-bold text-brand-primary text-lg">{{ faq.q }}</span>
            <span
              class="transform transition-transform duration-300 text-brand-accent text-xl font-bold"
              :class="activeIndex === i ? 'rotate-180' : ''"
            >
              ⌄
            </span>
          </button>

          <div
            v-show="activeIndex === i"
            class="px-6 pb-6 text-brand-secondary leading-relaxed animate-fade-in-up"
          >
            {{ faq.a }}
          </div>
        </div>
      </div>
    </div>
  </section>
</template>
