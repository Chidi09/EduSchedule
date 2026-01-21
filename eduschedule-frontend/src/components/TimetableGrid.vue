<script setup lang="ts">
import { ref, computed, watch } from 'vue';
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

// This function transforms the flat assignment list into our 2D grid
function initializeGrid() {
  const newGrid: Assignment[][] = Array.from({ length: days.length }, () => 
    Array.from({ length: periods.length }, () => null)
  );
  
  props.assignmentsData.forEach(a => {
    // Each cell will now hold an array to make it a draggable list
    newGrid[a.day_of_week][a.period] = [{
      id: a.id,
      subject: `Sub ${a.subject_id.slice(0,4)}`,
      teacher: `T ${a.teacher_id.slice(0,4)}`,
      room: `R ${a.room_id.slice(0,4)}`,
      original_day: a.day_of_week,
      original_period: a.period,
    }];
  });
  grid.value = newGrid;
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
    <div class="grid grid-cols-6 gap-1 text-center font-bold text-brand-gray">
      <div class="p-2">Time</div>
      <div v-for="day in days" :key="day" class="p-2">{{ day }}</div>
    </div>
    <div v-for="(period, periodIndex) in periods" :key="period" class="grid grid-cols-6 gap-1">
      <div class="p-2 text-center font-bold text-brand-gray">{{ period }}</div>
      
      <div v-for="(day, dayIndex) in days" :key="day" class="border rounded-md min-h-[90px] bg-brand-light">
        <draggable
          :list="grid[dayIndex] ? grid[dayIndex][periodIndex] : []"
          group="assignments"
          @end="onDragEnd"
          item-key="id"
          class="h-full w-full"
          :data-day="dayIndex"
          :data-period="periodIndex"
        >
          <template #item="{ element }">
            <div class="bg-brand-secondary text-white rounded-md p-2 text-xs flex flex-col h-full cursor-grab">
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