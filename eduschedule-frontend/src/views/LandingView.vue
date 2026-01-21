<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { RouterLink } from 'vue-router';

const isScrolled = ref(false);

onMounted(() => {
  window.addEventListener('scroll', () => {
    isScrolled.value = window.scrollY > 20;
  });
});

const features = [
  {
    title: "AI-Powered Solving",
    desc: "Our constraints solver checks millions of combinations in seconds to find the perfect conflict-free schedule.",
    icon: "⚡"
  },
  {
    title: "Fair Distribution",
    desc: "Algorithmically ensures teachers have balanced workloads and students get optimal learning gaps.",
    icon: "⚖️"
  },
  {
    title: "Real-time Conflicts",
    desc: "Instant feedback when you manually adjust the schedule. Never double-book a room again.",
    icon: "🛡️"
  }
];
</script>

<template>
  <div class="min-h-screen flex flex-col overflow-x-hidden">

    <nav
      class="fixed w-full z-50 transition-all duration-300"
      :class="isScrolled ? 'bg-white/80 backdrop-blur-md shadow-sm py-4' : 'bg-transparent py-6'"
    >
      <div class="max-w-7xl mx-auto px-6 flex justify-between items-center">
        <div class="text-2xl font-heading font-bold text-brand-primary tracking-tight">
          Edu<span class="text-brand-accent">Schedule</span>
        </div>
        <div class="space-x-8 hidden md:flex items-center">
          <a href="#features" class="text-sm font-medium text-brand-secondary hover:text-brand-primary transition">Features</a>
          <a href="#how-it-works" class="text-sm font-medium text-brand-secondary hover:text-brand-primary transition">How it Works</a>
          <RouterLink to="/login" class="text-sm font-medium text-brand-primary hover:text-brand-accent transition">Sign In</RouterLink>
          <RouterLink
            to="/register"
            class="px-5 py-2.5 rounded-full bg-brand-primary text-white text-sm font-semibold shadow-lg hover:shadow-xl hover:-translate-y-0.5 transition-all duration-300"
          >
            Get Started
          </RouterLink>
        </div>
      </div>
    </nav>

    <section class="pt-40 pb-20 px-6 relative">
      <div class="absolute top-0 right-0 -z-10 w-[600px] h-[600px] bg-brand-accent/10 rounded-full blur-3xl animate-pulse"></div>
      <div class="absolute bottom-0 left-0 -z-10 w-[400px] h-[400px] bg-purple-500/10 rounded-full blur-3xl"></div>

      <div class="max-w-7xl mx-auto grid lg:grid-cols-2 gap-12 items-center">
        <div class="space-y-8 animate-fade-in-up">
          <div class="inline-flex items-center px-3 py-1 rounded-full border border-brand-accent/30 bg-brand-accent/5 text-brand-accent text-xs font-bold uppercase tracking-wide">
            🚀 Version 2.0 Now Live
          </div>
          <h1 class="text-5xl lg:text-7xl font-bold font-heading text-brand-primary leading-[1.1]">
            School Timetables,<br>
            <span class="text-transparent bg-clip-text bg-gradient-to-r from-brand-accent to-purple-600">
              Solved in Seconds.
            </span>
          </h1>
          <p class="text-xl text-brand-secondary max-w-lg leading-relaxed">
            Stop using spreadsheets. EduSchedule uses advanced constraint programming to generate conflict-free schedules for your entire school automatically.
          </p>
          <div class="flex flex-col sm:flex-row gap-4 pt-4">
            <RouterLink
              to="/register"
              class="px-8 py-4 rounded-xl bg-brand-accent text-white font-bold text-lg shadow-blue-500/30 shadow-lg hover:bg-blue-600 hover:scale-105 transition-all duration-300 text-center"
            >
              Start Free Trial
            </RouterLink>
            <a
              href="#demo"
              class="px-8 py-4 rounded-xl border-2 border-slate-200 text-brand-primary font-bold text-lg hover:border-brand-primary/30 hover:bg-white transition-all duration-300 text-center"
            >
              Watch Demo
            </a>
          </div>

          <div class="pt-8 flex items-center gap-4 text-sm text-brand-secondary font-medium">
            <div class="flex -space-x-2">
              <div class="w-8 h-8 rounded-full bg-gray-300 border-2 border-white"></div>
              <div class="w-8 h-8 rounded-full bg-gray-400 border-2 border-white"></div>
              <div class="w-8 h-8 rounded-full bg-gray-500 border-2 border-white"></div>
            </div>
            <p>Trusted by 500+ School Admins</p>
          </div>
        </div>

        <div class="relative hidden lg:block animate-float">
          <div class="absolute inset-0 bg-gradient-to-tr from-blue-500 to-purple-600 rounded-[2rem] rotate-3 opacity-20 blur-xl"></div>
          <div class="relative bg-white border border-slate-100 p-6 rounded-[2rem] shadow-2xl">
            <div class="flex items-center justify-between mb-8">
              <div class="w-20 h-6 bg-slate-200 rounded animate-pulse"></div>
              <div class="w-8 h-8 bg-blue-100 rounded-full text-blue-600 flex items-center justify-center font-bold">A</div>
            </div>
            <div class="space-y-4">
              <div class="grid grid-cols-5 gap-4">
                <div v-for="i in 5" :key="i" class="h-24 rounded-xl bg-slate-50 border border-slate-100 p-2 flex flex-col justify-between hover:border-brand-accent/50 transition-colors cursor-default">
                  <div class="w-8 h-2 bg-slate-200 rounded"></div>
                  <div class="w-16 h-2 bg-blue-100 rounded self-end"></div>
                </div>
              </div>
              <div class="grid grid-cols-5 gap-4">
                 <div v-for="i in 5" :key="`row2-${i}`" class="h-24 rounded-xl bg-slate-50 border border-slate-100 p-2 flex flex-col justify-between">
                  <div class="w-10 h-2 bg-purple-100 rounded"></div>
                </div>
              </div>
            </div>

            <div class="absolute -right-8 top-1/2 bg-white p-4 rounded-xl shadow-xl border border-slate-50 flex items-center gap-3 animate-bounce" style="animation-duration: 3s;">
              <div class="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center text-green-600 text-xl">✅</div>
              <div>
                <p class="text-xs text-brand-secondary font-bold uppercase">Status</p>
                <p class="font-bold text-brand-primary">Conflict Free</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section id="features" class="py-24 bg-white relative">
      <div class="max-w-7xl mx-auto px-6">
        <div class="text-center max-w-2xl mx-auto mb-16">
          <h2 class="text-3xl font-bold text-brand-primary mb-4">Everything needed to run a modern school.</h2>
          <p class="text-brand-secondary">We stripped away the complexity. You define the teachers, rooms, and classes. We handle the math.</p>
        </div>

        <div class="grid md:grid-cols-3 gap-8">
          <div
            v-for="feature in features"
            :key="feature.title"
            class="p-8 rounded-2xl bg-slate-50 hover:bg-white hover:shadow-xl border border-slate-100 transition-all duration-300 group"
          >
            <div class="w-14 h-14 rounded-xl bg-white shadow-sm border border-slate-100 flex items-center justify-center text-3xl mb-6 group-hover:scale-110 transition-transform">
              {{ feature.icon }}
            </div>
            <h3 class="text-xl font-bold text-brand-primary mb-3">{{ feature.title }}</h3>
            <p class="text-brand-secondary leading-relaxed">{{ feature.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <section class="py-20 px-6">
      <div class="max-w-5xl mx-auto bg-brand-primary rounded-[2.5rem] p-12 md:p-20 text-center relative overflow-hidden">
        <div class="absolute top-0 left-0 w-full h-full opacity-10 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')]"></div>

        <div class="relative z-10">
          <h2 class="text-3xl md:text-5xl font-bold text-white mb-6">Ready to reclaim your weekends?</h2>
          <p class="text-slate-400 max-w-xl mx-auto mb-10 text-lg">Join forward-thinking administrators who have automated their scheduling process.</p>
          <RouterLink
            to="/register"
            class="inline-block px-10 py-5 rounded-xl bg-white text-brand-primary font-bold text-lg hover:bg-brand-accent hover:text-white transition-all duration-300"
          >
            Get Started for Free
          </RouterLink>
          <p class="mt-6 text-sm text-slate-500">No credit card required • Cancel anytime</p>
        </div>
      </div>
    </section>

    <footer class="bg-white border-t border-slate-100 pt-16 pb-8">
      <div class="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-6">
        <div class="text-brand-primary font-bold text-xl">EduSchedule</div>
        <div class="text-brand-secondary text-sm">
          &copy; {{ new Date().getFullYear() }} EduSchedule. All rights reserved.
        </div>
        <div class="flex gap-6 text-brand-secondary">
          <a href="#" class="hover:text-brand-primary">Privacy</a>
          <a href="#" class="hover:text-brand-primary">Terms</a>
          <a href="#" class="hover:text-brand-primary">Contact</a>
        </div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
/* Gradient Text Utility */
.text-gradient {
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
</style>
