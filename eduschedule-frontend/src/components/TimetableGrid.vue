<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue';
import draggable from 'vuedraggable';

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

const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
const periods = Array.from({ length: 8 }, (_, i) => `Period ${i + 1}`);

// A 2D array representing our grid, e.g., grid[dayIndex][periodIndex]
const grid = ref<Assignment[][]>([]);

// Store pending moves for rollback if validation fails
const pendingMoves = ref<Map<string, { from: [number, number], to: [number, number] }>>(new Map());

// Toast notifications for user feedback
const showToast = ref(false);
const toastMessage = ref('');
const toastType = ref<'success' | 'error'>('success');

// This function transforms the flat assignment list into our 2D grid
function initializeGrid() {
  const newGrid: Assignment[][] = Array.from({ length: days.length }, () =>
    Array.from({ length: periods.length }, () => [])
  );

  props.assignmentsData.forEach(a => {
    // Each cell will now hold an array to make it a draggable list
    const assignment: Assignment = {
      id: a.id,
      subject: `Sub ${a.subject_id.slice(0,4)}`,
      teacher: `T ${a.teacher_id.slice(0,4)}`,
      room: `R ${a.room_id.slice(0,4)}`,
      original_day: a.day_of_week,
      original_period: a.period,
    };
    newGrid[a.day_of_week][a.period].push(assignment);
  });
  grid.value = newGrid;
}

// Optimistic UI: Apply move immediately, then validate
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

  try {
    // Simulate server validation (replace with actual API call)
    const isValid = await validateMove(assignment.id, dayIndex, periodIndex);

    if (isValid) {
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
  } catch (error) {
    console.error('Move validation error:', error);
    await rollbackMove(assignment);
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
    const restoredAssignment = grid.value[fromDay][fromPeriod].find(a => a.id === assignment.id);
    if (restoredAssignment) {
      restoredAssignment.moveError = undefined;
    }
  }, 3000);
}

// Mock validation function - replace with actual API call
async function validateMove(assignmentId: string, newDay: number, newPeriod: number): Promise<boolean> {
  // Simulate network delay
  await new Promise(resolve => setTimeout(resolve, 500));

  // Mock validation logic - replace with actual server validation
  // For demo: randomly succeed/fail (80% success rate)
  return Math.random() > 0.2;
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

// Re-initialize the grid whenever the input data changes
watch(() => props.assignmentsData, initializeGrid, { immediate: true });

// This function is called when a user finishes a drag-and-drop action
async function onDragEnd(event: any) {
  const { to, from, oldIndex, newIndex, item } = event;

  // Extract day and period from the element's dataset
  const toDay = parseInt(to.dataset.day);
  const toPeriod = parseInt(to.dataset.period);
  const fromDay = parseInt(from.dataset.day);
  const fromPeriod = parseInt(from.dataset.period);

  // The assignment that was moved
  const movedAssignment = grid.value[fromDay][fromPeriod][0];

  // Call our backend to validate the move
  const validationResponse = await validateMove(movedAssignment, toDay, toPeriod);

  if (!validationResponse.valid) {
    alert(`Invalid Move: ${validationResponse.reason}`);

    // Move is invalid, so we snap it back to its original position
    // This requires a bit of a trick: move it to the new spot, then back to the old one.
    const itemToMoveBack = grid.value[toDay][toPeriod].splice(0, 1)[0];
    grid.value[fromDay][fromPeriod].push(itemToMoveBack);

  } else {
    // Move is valid, the UI is already updated by the draggable library.
    // Optionally, you can show a success message.
    console.log("Move successful!");
  }
}

async function validateMove(assignment: Assignment, newDay: number, newPeriod: number) {
  // This would use the authStore to get the token
  // const token = ...;
  const response = await fetch('/api/assignments/validate-move', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      // 'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      assignment_id: assignment.id,
      new_day: newDay,
      new_period: newPeriod,
    }),
  });
  return response.json();
}
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
          :list="grid[dayIndex] ? grid[dayIndex][periodIndex] : []"
          group="assignments"
          @add="(evt) => handleMove(evt, dayIndex, periodIndex)"
          @end="onDragEnd"
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
              'text-white rounded-md p-3 text-xs flex flex-col h-full min-h-[44px] transition-all duration-200',
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
