<template>
  <div class="container">
    <h1 class="mb-4">Task {{ taskId }}</h1>
    {{ taskOutput }}
  </div>
</template>

<script lang="ts">
import { defineComponent, onMounted, onBeforeUnmount, ref } from "vue";
import { useRouter } from "../plugins/router";
import { TaskOutput } from "../typings/TaskOutput";
import API from "../utils/api";

export default defineComponent({
  setup: () => {
    const router = useRouter();

    const taskId = router.currentRoute.value.params.taskId.toString();

    let pollInterval: number | null = null;

    const taskOutput = ref<TaskOutput>();

    const pollData = async () => {
      const response = await API.getTaskOutput(taskId);

      if (response) taskOutput.value = response;
    };

    onMounted(() => {
      pollData();
      pollInterval = setInterval(pollData, 5000);
    });

    onBeforeUnmount(() => {
      if (pollInterval) clearInterval(pollInterval);
    });

    return {
      taskId,
      taskOutput,
    };
  },
});
</script>
