<template>
  <div class="flex items-center justify-center min-h-screen bg-brand-light">
    <div class="w-full max-w-md p-8 text-center bg-white rounded-lg shadow-md">
      <h1 class="text-3xl font-bold text-green-600">Payment Successful!</h1>
      <p class="mt-4 text-brand-gray">
        Thank you for subscribing. Your premium features are now active.
      </p>
      <div class="mt-8">
        <router-link to="/dashboard" class="rounded-md bg-brand-primary px-6 py-3 text-sm font-semibold text-white shadow-sm hover:bg-brand-secondary">
          Go to Dashboard
        </router-link>
      </div>
    </div>
  </div>
</template>