<script setup lang="ts">
// Modern SaaS "Bento Grid" style features
</script>

<template>
  <section class="py-24 bg-slate-50">
    <div class="max-w-7xl mx-auto px-6">
      <div class="text-center mb-16">
        <h2 class="text-3xl md:text-4xl font-bold font-heading text-brand-primary mb-4">Powerful Features</h2>
        <p class="text-brand-secondary">Everything you need to run a modern academic institution.</p>
      </div>

      <div class="grid md:grid-cols-4 md:grid-rows-2 gap-6 h-auto md:h-[600px]">
        <div class="md:col-span-2 md:row-span-2 bg-brand-primary rounded-3xl p-8 md:p-12 relative overflow-hidden group text-white">
          <div class="relative z-10">
            <h3 class="text-2xl font-bold mb-4">Conflict-Free Guarantee</h3>
            <p class="text-slate-300 leading-relaxed">Our core algorithm mathematically proves that no teacher or room is double booked. If a schedule exists, we will find it.</p>
            <button class="mt-8 px-6 py-2 bg-white/10 backdrop-blur-sm rounded-full text-sm font-semibold hover:bg-white/20 transition">Learn about the Solver &rarr;</button>
          </div>
          <div class="absolute -bottom-10 -right-10 w-64 h-64 bg-brand-accent rounded-full blur-[80px] opacity-50 group-hover:opacity-70 transition duration-700"></div>
        </div>

        <div class="md:col-span-2 bg-white rounded-3xl p-8 border border-slate-100 shadow-sm hover:shadow-md transition">
          <div class="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center text-2xl mb-4">📱</div>
          <h3 class="text-xl font-bold text-brand-primary mb-2">Mobile First</h3>
          <p class="text-brand-secondary text-sm">Teachers can check their upcoming classes on their phones. PWA support included.</p>
        </div>

        <div class="md:col-span-1 bg-white rounded-3xl p-8 border border-slate-100 shadow-sm hover:shadow-md transition">
          <div class="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center text-2xl mb-4">⚡</div>
          <h3 class="text-lg font-bold text-brand-primary mb-2">Instant</h3>
          <p class="text-brand-secondary text-sm">Generate full term schedules in under 60 seconds.</p>
        </div>

        <div class="md:col-span-1 bg-white rounded-3xl p-8 border border-slate-100 shadow-sm hover:shadow-md transition">
          <div class="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center text-2xl mb-4">📊</div>
          <h3 class="text-lg font-bold text-brand-primary mb-2">Reports</h3>
          <p class="text-brand-secondary text-sm">Export teacher workload and room utilization stats.</p>
        </div>
      </div>
    </div>
  </section>
</template>
