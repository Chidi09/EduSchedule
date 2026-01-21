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

// FIXED: Defined as 3D array (Day -> Period -> List of Assignments)
const grid = ref<Assignment[][][]>([]);

// This function transforms the flat assignment list into our 3D grid
function initializeGrid() {
  // Initialize with empty arrays instead of null
  const newGrid: Assignment[][][] = Array.from({ length: days.length }, () =>
    Array.from({ length: periods.length }, () => [])
  );

  props.assignmentsData.forEach(a => {
    // Ensure the target cell exists before pushing
    if (newGrid[a.day_of_week] && newGrid[a.day_of_week][a.period]) {
      newGrid[a.day_of_week][a.period].push({
        id: a.id,
        subject: `Sub ${a.subject_id.slice(0,4)}`,
        teacher: `T ${a.teacher_id.slice(0,4)}`,
        room: `R ${a.room_id.slice(0,4)}`,
        original_day: a.day_of_week,
        original_period: a.period,
      });
    }
  });
  grid.value = newGrid;
}

// Re-initialize the grid whenever the input data changes
watch(() => props.assignmentsData, initializeGrid, { immediate: true });

// This function is called when a user finishes a drag-and-drop action
async function onDragEnd(event: any) {
  const { to, from } = event;

  // Extract day and period from the element's dataset
  const toDay = parseInt(to.dataset.day);
  const toPeriod = parseInt(to.dataset.period);
  const fromDay = parseInt(from.dataset.day);
  const fromPeriod = parseInt(from.dataset.period);

  // The assignment that was moved is now in the 'to' location
  const cellAssignments = grid.value[toDay][toPeriod];
  const movedAssignment = cellAssignments[event.newIndex];

  if (!movedAssignment) return;

  // Call our backend to validate the move
  const validationResponse = await validateMove(movedAssignment, toDay, toPeriod);

  if (!validationResponse.valid) {
    alert(`Invalid Move: ${validationResponse.reason}`);

    // Move is invalid, so we snap it back to its original position
    // Manually manipulate the array to move it back
    // 1. Remove from new position
    grid.value[toDay][toPeriod].splice(event.newIndex, 1);
    // 2. Add back to old position
    grid.value[fromDay][fromPeriod].splice(event.oldIndex, 0, movedAssignment);

  } else {
    // Move is valid, update the assignment's internal coordinates if necessary
    movedAssignment.original_day = toDay;
    movedAssignment.original_period = toPeriod;
    console.log("Move successful!");
  }
}

async function validateMove(assignment: Assignment, newDay: number, newPeriod: number) {
  try {
    const token = authStore.session?.access_token;
    if (!token) return { valid: false, reason: "Not authenticated" };

    const response = await fetch('/api/assignments/validate-move', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        assignment_id: assignment.id,
        new_day: newDay,
        new_period: newPeriod,
      }),
    });
    return await response.json();
  } catch (error) {
    console.error("Validation error", error);
    return { valid: false, reason: "Network error" };
  }
}
</script>

<template>
  <div class="bg-white rounded-lg shadow-md p-4">
    <div class="grid grid-cols-6 gap-1 text-center font-bold text-brand-gray">
      <div class="p-2">Time</div>
      <div v-for="day in days" :key="day" class="p-2">{{ day }}</div>
    </div>
    <div v-for="(period, periodIndex) in periods" :key="period" class="grid grid-cols-6 gap-1">
      <div class="p-2 text-center font-bold text-brand-gray">{{ period }}</div>

      <div v-for="(_, dayIndex) in days" :key="dayIndex" class="border rounded-md min-h-[90px] bg-brand-light">
        <draggable
          v-if="grid[dayIndex]"
          :list="grid[dayIndex][periodIndex]"
          group="assignments"
          @end="onDragEnd"
          item-key="id"
          class="h-full w-full"
          :data-day="dayIndex"
          :data-period="periodIndex"
        >
          <template #item="{ element }">
            <div class="bg-brand-secondary text-white rounded-md p-2 text-xs flex flex-col h-full cursor-grab hover:opacity-90">
              <span class="font-bold">{{ element.subject }}</span>
              <span>{{ element.teacher }}</span>
              <span class="mt-auto opacity-70">{{ element.room }}</span>
            </div>
          </template>
        </draggable>
      </div>
    </div>
  </div>
</template>
