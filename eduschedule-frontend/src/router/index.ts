import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth';
import { watch } from 'vue';

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    // Public routes
    { path: '/', name: 'landing', component: () => import('../views/LandingView.vue') },
    { path: '/login', name: 'login', component: () => import('../views/LoginView.vue') },
    { 
      path: '/register', 
      name: 'register', 
      component: () => import('../views/RegisterView.vue') 
    },
    { path: '/view', name: 'student-view', component: () => import('../views/StudentView.vue') },

    // Protected application routes
    { path: '/dashboard', name: 'dashboard', component: () => import('../views/DashboardView.vue'), meta: { requiresAuth: true, requiresPremium: true } },
    { path: '/teachers', name: 'teachers', component: () => import('../views/TeachersView.vue'), meta: { requiresAuth: true, requiresPremium: true }},
    { path: '/rooms', name: 'rooms', component: () => import('../views/RoomsView.vue'), meta: { requiresAuth: true, requiresPremium: true }},
    { path: '/subjects', name: 'subjects', component: () => import('../views/SubjectsView.vue'), meta: { requiresAuth: true, requiresPremium: true }},
    { path: '/classes', name: 'classes', component: () => import('../views/ClassesView.vue'), meta: { requiresAuth: true, requiresPremium: true }},
    { path: '/my-preferences', name: 'my-preferences', component: () => import('../views/MyPreferencesView.vue'), meta: { requiresAuth: true }},
    { path: '/pricing', name: 'pricing', component: () => import('../views/PricingView.vue'), meta: { requiresAuth: true }},
    
    // Protected onboarding/utility routes
    { path: '/setup-school', name: 'school-setup', component: () => import('../views/SchoolSetupView.vue'), meta: { requiresAuth: true } },
    { path: '/payment-success', name: 'payment-success', component: () => import('../views/PaymentSuccessView.vue'), meta: { requiresAuth: true } },
  ]
})

// Helper to wait for the auth store to be fully ready
const waitForAuthInit = async () => {
  const authStore = useAuthStore();
  if (authStore.isAuthReady) {
    return;
  }
  // Create a promise that resolves when isAuthReady becomes true
  return new Promise(resolve => {
    const unwatch = watch(() => authStore.isAuthReady, (isReady) => {
      if (isReady) {
        unwatch(); // Clean up the watcher
        resolve(true);
      }
    });
  });
};


router.beforeEach(async (to, from, next) => {
  // Always wait for authentication to be fully initialized first
  await waitForAuthInit();

  const authStore = useAuthStore();
  const isAuthenticated = !!authStore.user;
  const hasSchool = !!authStore.profile?.school_id;

  const requiresAuth = to.matched.some(record => record.meta.requiresAuth);
  const isSetupRoute = to.name === 'school-setup';

  if (requiresAuth && !isAuthenticated) {
    // If a protected page is accessed and user is not logged in, go to login.
    return next({ name: 'login' });
  }

  if (isAuthenticated) {
    if (!hasSchool && !isSetupRoute) {
      // If user is logged in but has no school, force them to the setup page.
      return next({ name: 'school-setup' });
    }
    if (hasSchool && (to.name === 'login' || to.name === 'landing')) {
      // If a user with a school tries to visit login/landing, send to dashboard.
      return next({ name: 'dashboard' });
    }
  }

  // Otherwise, allow navigation.
  return next();
});

export default router;