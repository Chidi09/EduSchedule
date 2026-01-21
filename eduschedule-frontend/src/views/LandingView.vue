<script setup lang="ts">
import FeaturesCarousel from '@/components/FeaturesCarousel.vue';
import HowItWorks from '@/components/HowItWorks.vue';
import TestimonialSection from '@/components/TestimonialSection.vue';
import FAQ from '@/components/FAQ.vue';
import AppFooter from '@/components/AppFooter.vue';
</script>

<template>
  <div class="bg-white">
    <header class="absolute inset-x-0 top-0 z-50">
      <nav class="flex items-center justify-between p-6 lg:px-8">
        <div class="flex lg:flex-1">
          <a href="#" class="-m-1.5 p-1.5">
            <h1 class="text-xl font-bold text-brand-primary">EduSchedule</h1>
          </a>
        </div>
        <div class="flex lg:flex-1 lg:justify-end">
          <router-link to="/login" class="text-sm font-semibold leading-6 text-brand-dark">
            Log in / Register <span aria-hidden="true">&rarr;</span>
          </router-link>
        </div>
      </nav>
    </header>

    <div class="relative isolate px-6 pt-14 lg:px-8">
      <div class="mx-auto max-w-2xl py-32 sm:py-48 lg:py-56 text-center">
        <h1 class="text-4xl font-bold tracking-tight text-brand-dark sm:text-6xl">
          Intelligent Timetabling, Simplified
        </h1>
        <p class="mt-6 text-lg leading-8 text-brand-gray">
          Effortlessly create balanced, conflict-free academic schedules with the power of AI.
        </p>
        <div class="mt-10 flex items-center justify-center gap-x-6">
          <router-link to="/login" class="rounded-md bg-brand-primary px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-brand-secondary">
            Get Started
          </router-link>
        </div>
      </div>
    </div>

    <HowItWorks />

    <div class="py-24 bg-brand-light">
      <h2 class="text-3xl font-bold text-center mb-12">Why Choose EduSchedule?</h2>
      <FeaturesCarousel />
    </div>

    <TestimonialSection />

    <div class="bg-brand-accent">
      <div class="container mx-auto px-6 py-16 text-center">
        <h2 class="text-3xl font-bold text-brand-dark">A Chance Deal Could Be Yours!</h2>
        <p class="mt-4 text-lg text-brand-dark opacity-90">
          Register today for a chance to get a limited-time discount on our premium plans. This lucky offer is only available for 24 hours after you sign up!
        </p>
        <div class="mt-8">
          <router-link to="/login" class="rounded-md bg-brand-dark px-6 py-3 text-sm font-semibold text-white shadow-sm hover:opacity-90">
            Sign Up and Try Your Luck
          </router-link>
        </div>
      </div>
    </div>

    <FAQ />

    <AppFooter />
  </div>
</template>