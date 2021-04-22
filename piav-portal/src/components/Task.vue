<template>
  <div class="container">
    <h1 class="mb-4">Task {{ taskId }}</h1>
    <h2>Input</h2>
    <div v-if="taskInput">
      <precursors :precursors="taskInput.precursors"></precursors>
    </div>
    <div v-else>
      <h4>Loading...</h4>
    </div>
    <h2>Output</h2>
    <div v-if="taskOutput">
      <h3>Window Enumeration</h3>
      <window-enumeration :data="taskOutput.window_enumeration"></window-enumeration>
      <h3>Network Traffic</h3>
      <network :network-events="taskOutput.kernel_events.net"></network>
      <h3>Registry Events</h3>
      <registry :registry-events="taskOutput.kernel_events.registry"></registry>
    </div>
    <div v-else>
      <h4>No task output. This page will update when the task finishes.</h4>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, onBeforeUnmount, onMounted, ref } from "vue";
import { useRouter } from "../plugins/router";
import { TaskOutput } from "../models/types/TaskOutput";
import Network from "./Network.vue";
import Registry from "./Registry.vue";
import WindowEnumeration from "./WindowEnumeration.vue";
import Precursors from "./Precursors.vue";
import API from "../utils/api";
import { TaskInput } from "../models/types/TaskInput";

export default defineComponent({
  components: {
    Network,
    WindowEnumeration,
    Registry,
    Precursors,
  },
  setup: () => {
    const router = useRouter();

    const taskId = router.currentRoute.value.params.taskId.toString();

    let pollInterval: number | null = null;

    const taskInput = ref<TaskInput>();
    const taskOutput = ref<TaskOutput>();

    const pollData = async () => {
      const response = await API.getTaskOutput(taskId);

      // Once we get the output data, we can cancel the interval
      if (response) {
        taskOutput.value = response;
        if (pollInterval) clearInterval(pollInterval);
      }
    };

    onMounted(async () => {
      const response = await API.getTaskInput(taskId);

      // If this task doesn't exist, redirect to home
      if (!response) return router.push("/");

      taskInput.value = response;

      pollData();
      pollInterval = setInterval(pollData, 5000);
    });

    onBeforeUnmount(() => {
      if (pollInterval) clearInterval(pollInterval);
    });

    return {
      taskId,
      taskInput,
      taskOutput,
    };
  },
});
</script>
