<script setup lang="ts">
import { ref, watch } from 'vue';
import draggable from 'vuedraggable';
import { useAuthStore } from '@/stores/auth';

// Define the structure for an assignment item
interface Assignment {
  id: string;
  subject: string;
  teacher: string;
  room: string;
  // Store original position for validation
  original_day: number;
  original_period: number;
  // For optimistic UI
  isMoving?: boolean;
  moveError?: string;
}

interface RawAssignment {
  id: string;
  subject_id: string;
  teacher_id: string;
  room_id: string;
  day_of_week: number;
  period: number;
}

const props = defineProps<{
  assignmentsData: RawAssignment[]; // The raw assignments from the candidate
}>();

const authStore = useAuthStore();
const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
const periods = Array.from({ length: 8 }, (_, i) => `Period ${i + 1}`);

// A 3D array representing our grid: grid[dayIndex][periodIndex] = Assignment[]
const grid = ref<Assignment[][][]>([]);

// Store pending moves for rollback if validation fails
const pendingMoves = ref<Map<string, { from: [number, number], to: [number, number] }>>(new Map());

// Toast notifications for user feedback
const showToast = ref(false);
const toastMessage = ref('');
const toastType = ref<'success' | 'error'>('success');

// This function transforms the flat assignment list into our 3D grid
function initializeGrid() {
  const newGrid: Assignment[][][] = Array.from({ length: days.length }, () =>
    Array.from({ length: periods.length }, () => [])
  );

  props.assignmentsData.forEach(a => {
    const assignment: Assignment = {
      id: a.id,
      subject: `Sub ${a.subject_id.slice(0, 4)}`,
      teacher: `T ${a.teacher_id.slice(0, 4)}`,
      room: `R ${a.room_id.slice(0, 4)}`,
      original_day: a.day_of_week,
      original_period: a.period,
    };
    newGrid[a.day_of_week][a.period].push(assignment);
  });
  grid.value = newGrid;
}

// Show toast notification
function showToastMessage(message: string, type: 'success' | 'error') {
  toastMessage.value = message;
  toastType.value = type;
  showToast.value = true;

  setTimeout(() => {
    showToast.value = false;
  }, 3000);
}

async function validateMoveApi(assignmentId: string, newDay: number, newPeriod: number) {
  try {
    const token = authStore.session?.access_token;
    const response = await fetch('/api/assignments/validate-move', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        assignment_id: assignmentId,
        new_day: newDay,
        new_period: newPeriod,
      }),
    });

    if (!response.ok) return { valid: false, reason: 'Server error' };
    return await response.json();
  } catch (error) {
    return { valid: false, reason: 'Network error' };
  }
}

// Rollback a failed move
async function rollbackMove(assignment: Assignment) {
  const pendingMove = pendingMoves.value.get(assignment.id);
  if (!pendingMove) return;

  const [fromDay, fromPeriod] = pendingMove.from;
  const [toDay, toPeriod] = pendingMove.to;

  // Remove from current position
  const currentCell = grid.value[toDay][toPeriod];
  const index = currentCell.findIndex(a => a.id === assignment.id);
  if (index !== -1) {
    currentCell.splice(index, 1);
  }

  // Add back to original position
  grid.value[fromDay][fromPeriod].push({
    ...assignment,
    isMoving: false,
    moveError: 'Move not allowed - conflicts detected'
  });

  pendingMoves.value.delete(assignment.id);
  showToastMessage('Move not allowed - conflicts detected', 'error');

  // Clear error after 3 seconds
  setTimeout(() => {
    const dayCell = grid.value[fromDay][fromPeriod];
    const restoredAssignment = dayCell.find(a => a.id === assignment.id);
    if (restoredAssignment) {
      restoredAssignment.moveError = undefined;
    }
  }, 3000);
}

// Optimistic UI: Apply move immediately, then validate
// evt is the change event from vuedraggable
async function handleMove(evt: any, dayIndex: number, periodIndex: number) {
  if (!evt.added) return;

  const assignment = evt.added.element as Assignment;
  const fromDay = assignment.original_day;
  const fromPeriod = assignment.original_period;

  // Mark as moving for visual feedback
  assignment.isMoving = true;
  assignment.moveError = undefined;

  // Store the move for potential rollback
  pendingMoves.value.set(assignment.id, {
    from: [fromDay, fromPeriod],
    to: [dayIndex, periodIndex]
  });

  const result = await validateMoveApi(assignment.id, dayIndex, periodIndex);

  if (result.valid) {
    // Success - update original position and clear moving state
    assignment.original_day = dayIndex;
    assignment.original_period = periodIndex;
    assignment.isMoving = false;
    pendingMoves.value.delete(assignment.id);
    showToastMessage('Move successful!', 'success');
  } else {
    // Failed validation - rollback the move
    await rollbackMove(assignment);
  }
}

// Re-initialize the grid whenever the input data changes
watch(() => props.assignmentsData, initializeGrid, { immediate: true });

</script>

<template>
  <div class="bg-white rounded-lg shadow-md p-4">
    <!-- Toast Notification -->
    <div v-if="showToast"
         :class="[
           'fixed top-4 right-4 z-50 px-4 py-2 rounded-lg shadow-lg transition-all duration-300',
           toastType === 'success' ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
         ]">
      {{ toastMessage }}
    </div>

    <div class="grid grid-cols-6 gap-1 text-center font-bold text-brand-gray">
      <div class="p-2">Time</div>
      <div v-for="day in days" :key="day" class="p-2">{{ day }}</div>
    </div>
    <div v-for="(period, periodIndex) in periods" :key="period" class="grid grid-cols-6 gap-1">
      <div class="p-2 text-center font-bold text-brand-gray">{{ period }}</div>

      <div v-for="(day, dayIndex) in days" :key="day"
           class="border rounded-md min-h-[90px] bg-brand-light touch-manipulation">
        <draggable
          :list="grid[dayIndex][periodIndex]"
          group="assignments"
          @change="(evt: any) => handleMove(evt, dayIndex, periodIndex)"
          item-key="id"
          class="h-full w-full min-h-[90px] touch-manipulation"
          :data-day="dayIndex"
          :data-period="periodIndex"
          :animation="200"
          :delay="100"
          :delayOnTouchStart="true"
          :touchStartThreshold="10"
        >
          <template #item="{ element }">
            <div :class="[
              'text-white rounded-md p-3 text-xs flex flex-col h-full min-h-[44px] transition-all duration-200 relative',
              'touch-manipulation select-none',
              element.isMoving ? 'bg-yellow-500 animate-pulse' : 'bg-brand-secondary',
              element.moveError ? 'bg-red-500' : '',
              'cursor-grab active:cursor-grabbing'
            ]">
              <span class="font-bold text-sm">{{ element.subject }}</span>
              <span class="text-xs opacity-90">{{ element.teacher }}</span>
              <span class="mt-auto text-xs opacity-70">{{ element.room }}</span>

              <!-- Loading indicator for moving items -->
              <div v-if="element.isMoving" class="absolute top-1 right-1">
                <div class="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              </div>

              <!-- Error indicator -->
              <div v-if="element.moveError" class="mt-1 text-xs text-red-200">
                {{ element.moveError }}
              </div>
            </div>
          </template>
        </draggable>
      </div>
    </div>
  </div>
</template>

<style scoped>
.touch-manipulation {
  touch-action: manipulation;
}

/* Enhanced touch targets for mobile */
@media (max-width: 768px) {
  .min-h-\[44px\] {
    min-height: 44px;
  }

  .p-3 {
    padding: 12px;
  }
}

/* Smooth drag animations */
.sortable-ghost {
  opacity: 0.5;
}

.sortable-chosen {
  transform: scale(1.05);
  z-index: 999;
}

.sortable-drag {
  transform: rotate(5deg);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
}
</style>
