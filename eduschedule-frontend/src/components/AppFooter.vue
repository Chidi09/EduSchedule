<template>
  <footer class="bg-brand-dark text-white">
    <div class="container mx-auto px-6 py-12">
      <div class="md:flex md:justify-between">
        <div class="mb-6 md:mb-0">
          <h2 class="text-2xl font-bold text-brand-accent">EduSchedule</h2>
          <p class="mt-2 text-brand-gray">Intelligent Timetabling, Simplified.</p>
        </div>
        <div class="grid grid-cols-2 gap-8">
          <div>
            <h2 class="mb-4 text-sm font-semibold uppercase">Legal</h2>
            <ul class="text-brand-gray space-y-2">
              <li><a href="#" class="hover:underline">Privacy Policy</a></li>
              <li><a href="#" class="hover:underline">Terms & Conditions</a></li>
            </ul>
          </div>
          <div>
            <h2 class="mb-4 text-sm font-semibold uppercase">Follow us</h2>
            <div class="flex space-x-4">
              <a href="#" class="text-brand-gray hover:text-white">FB</a>
              <a href="#" class="text-brand-gray hover:text-white">TW</a>
              <a href="#" class="text-brand-gray hover:text-white">IG</a>
            </div>
          </div>
        </div>
      </div>
      <hr class="my-6 border-gray-600" />
      <div class="text-center text-brand-gray">
        © {{ new Date().getFullYear() }} EduSchedule™. All Rights Reserved.
      </div>
    </div>
  </footer>
</template>