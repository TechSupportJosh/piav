<template>
  <div class="container">
    <h1 class="mb-4">Task {{ taskId }}</h1>
    <h2>Input</h2>
    <hr />
    <h3>Setup Actions</h3>
    <div v-if="taskInput">
      <action-table :actions="taskInput.setup_actions"></action-table>
    </div>
    <h3>Main Actions</h3>
    <div v-if="taskInput">
      <action-table :actions="taskInput.actions"></action-table>
    </div>
    <div v-else>
      <h4>Loading...</h4>
    </div>
    <h2>Output</h2>
    <hr />
    <div v-if="taskOutput">
      <template v-if="taskOutput.same_as">
        <h4>
          Same as <router-link :to="`/task/${taskOutput.same_as}`">{{ taskOutput.same_as }}</router-link>
        </h4>
      </template>
      <template v-else>
        <h3>Window Enumeration</h3>
        <window-enumeration :data="taskOutput.window_enumeration"></window-enumeration>
        <hr />
        <h3>Network Traffic</h3>
        <network :network-events="taskOutput.kernel_events.net"></network>
        <hr />
        <h3>Registry Events</h3>
        <registry :registry-events="taskOutput.kernel_events.registry"></registry>
        <hr />
        <h3>File Events</h3>
        <file :file-events="taskOutput.kernel_events.file"></file>
        <hr />
      </template>
    </div>
    <div v-else>
      <h4>No task output. This page will update when the task finishes.</h4>
    </div>
  </div>
</template>

<script lang="ts">
import { computed, defineComponent, onBeforeUnmount, ref, watch } from "vue";
import { useRouter } from "../plugins/router";
import { TaskOutput } from "../models/types/TaskOutput";
import Network from "./Network.vue";
import Registry from "./Registry.vue";
import File from "./File.vue";
import WindowEnumeration from "./WindowEnumeration.vue";
import ActionTable from "./ActionTable.vue";
import API from "../utils/api";
import { TaskInput } from "../models/types/TaskInput";

export default defineComponent({
  components: {
    Network,
    WindowEnumeration,
    Registry,
    ActionTable,
    File,
  },
  setup: () => {
    const router = useRouter();

    let pollInterval: number | null = null;

    const taskInput = ref<TaskInput>();
    const taskOutput = ref<TaskOutput>();

    const taskId = computed(() => router.currentRoute.value.params.taskId.toString());

    const pollData = async () => {
      const response = await API.getTaskOutput(router.currentRoute.value.params.taskId.toString());

      // Once we get the output data, we can cancel the interval
      if (response) {
        taskOutput.value = response;
        if (pollInterval) clearInterval(pollInterval);
      }
    };

    watch(
      () => router.currentRoute.value.params,
      async () => {
        if (pollInterval) clearInterval(pollInterval);

        const response = await API.getTaskInput(router.currentRoute.value.params.taskId.toString());

        // If this task doesn't exist, redirect to home
        if (!response) return router.push("/");

        taskInput.value = response;
        taskOutput.value = undefined;

        pollData();
        pollInterval = setInterval(pollData, 5000);
      },
      { immediate: true }
    );

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
