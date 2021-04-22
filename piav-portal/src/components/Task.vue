<template>
  <div class="container">
    <h1 class="mb-4">Task {{ taskId }}</h1>

    <div v-if="taskOutput">
      <h2>Window Enumeration</h2>
      <window-enumeration :data="taskOutput.window_enumeration"></window-enumeration>
      <h2>Network Traffic</h2>
      <network :network-events="taskOutput.kernel_events.net"></network>
      <h2>Registry Events</h2>
      <registry :registry-events="taskOutput.kernel_events.registry"></registry>
    </div>
    {{ taskOutput }}
  </div>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { useRouter } from "../plugins/router";
import Network from "./Network.vue";
import Registry from "./Registry.vue";
import WindowEnumeration from "./WindowEnumeration.vue";

export default defineComponent({
  components: {
    Network,
    WindowEnumeration,
    Registry,
  },
  setup: () => {
    const router = useRouter();

    const taskId = router.currentRoute.value.params.taskId.toString();

    let pollInterval: number | null = null;

    /*
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
*/

    return {
      taskId,
      taskOutput,
    };
  },
});
</script>
