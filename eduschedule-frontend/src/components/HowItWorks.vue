<script setup lang="ts">
const steps = [
  {
    num: "01",
    title: "Define Your Constraints",
    desc: "Input your teachers, classes, rooms, and subjects. Tell us who is unavailable on Fridays or which classes need double periods.",
    icon: "📝"
  },
  {
    num: "02",
    title: "AI Generation",
    desc: "Our CP-SAT solver analyzes millions of possibilities in seconds, ensuring no room is double-booked and every teacher gets a break.",
    icon: "🧠"
  },
  {
    num: "03",
    title: "Review & Publish",
    desc: "Drag and drop to make final tweaks if needed (we'll warn you if you break a rule), then export to PDF or email to staff.",
    icon: "🚀"
  }
];
</script>

<template>
  <section id="how-it-works" class="py-24 bg-brand-bg relative overflow-hidden">
    <div class="absolute left-1/2 top-0 bottom-0 w-px bg-gradient-to-b from-transparent via-brand-secondary/20 to-transparent hidden md:block"></div>

    <div class="max-w-7xl mx-auto px-6 relative z-10">
      <div class="text-center mb-16">
        <h2 class="text-3xl md:text-4xl font-bold font-heading text-brand-primary mb-4">How It Works</h2>
        <p class="text-brand-secondary max-w-2xl mx-auto">Three simple steps to move from chaos to clarity.</p>
      </div>

      <div class="space-y-12 md:space-y-0 md:grid md:grid-cols-3 md:gap-12">
        <div v-for="(step, index) in steps" :key="index" class="relative group">
          <div class="bg-white p-8 rounded-2xl shadow-sm border border-slate-100 relative z-10 hover:shadow-xl hover:-translate-y-1 transition-all duration-300">
            <div class="text-5xl font-bold text-brand-bg/50 absolute top-4 right-4">{{ step.num }}</div>
            <div class="w-14 h-14 bg-brand-accent/10 rounded-xl flex items-center justify-center text-3xl mb-6 text-brand-accent">
              {{ step.icon }}
            </div>
            <h3 class="text-xl font-bold text-brand-primary mb-3">{{ step.title }}</h3>
            <p class="text-brand-secondary leading-relaxed text-sm">{{ step.desc }}</p>
          </div>

          <div v-if="index !== steps.length - 1" class="absolute left-1/2 -bottom-12 w-px h-12 bg-slate-200 md:hidden"></div>
        </div>
      </div>
    </div>
  </section>
</template>
