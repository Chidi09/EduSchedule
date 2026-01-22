<script setup lang="ts">
import AppFooter from '@/components/AppFooter.vue';

const team = [
  { name: "Chidi N.", role: "Lead Engineer", img: "https://api.dicebear.com/7.x/avataaars/svg?seed=Chidi" },
  { name: "Sarah J.", role: "Product Manager", img: "https://api.dicebear.com/7.x/avataaars/svg?seed=Sarah" },
  { name: "David K.", role: "Algorithm Specialist", img: "https://api.dicebear.com/7.x/avataaars/svg?seed=David" },
];
</script>

<template>
  <div class="min-h-screen bg-white">
    <nav class="p-6 border-b border-slate-100">
       <div class="max-w-7xl mx-auto font-heading font-bold text-2xl text-brand-primary">EduSchedule</div>
    </nav>

    <div class="max-w-4xl mx-auto px-6 py-20">
      <h1 class="text-4xl md:text-5xl font-bold font-heading text-brand-primary mb-8 text-center">Reimagining Education Logistics</h1>
      <p class="text-xl text-brand-secondary text-center leading-relaxed mb-16">
        We believe school administrators should focus on education, not spreadsheets.
        Our mission is to automate the administrative burden of running a school using state-of-the-art AI.
      </p>

      <div class="grid md:grid-cols-2 gap-8 mb-24">
        <div class="p-8 bg-brand-bg rounded-2xl">
          <h3 class="text-xl font-bold text-brand-primary mb-3">Efficiency First</h3>
          <p class="text-brand-secondary">We optimize for the most compact, efficient schedules possible, saving time for everyone.</p>
        </div>
        <div class="p-8 bg-brand-bg rounded-2xl">
          <h3 class="text-xl font-bold text-brand-primary mb-3">Transparency</h3>
          <p class="text-brand-secondary">No black boxes. We explain exactly why a schedule was generated the way it was.</p>
        </div>
      </div>

      <h2 class="text-3xl font-bold font-heading text-brand-primary text-center mb-12">Meet the Team</h2>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-8">
        <div v-for="member in team" :key="member.name" class="text-center">
          <img :src="member.img" alt="Team member" class="w-32 h-32 rounded-full mx-auto mb-4 bg-slate-100" />
          <h3 class="font-bold text-lg text-brand-primary">{{ member.name }}</h3>
          <p class="text-brand-secondary text-sm">{{ member.role }}</p>
        </div>
      </div>
    </div>

    <AppFooter />
  </div>
</template>
