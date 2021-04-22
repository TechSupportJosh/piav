<template>
  <div class="container">
    <h1 class="mb-4">Queued Machines</h1>
    <table class="table">
      <thead>
        <tr>
          <th scope="col">Task ID</th>
          <th scope="col">Status</th>
        </tr>
      </thead>
      <tbody>
        <tr class="text-center" v-if="queueEntries === undefined">
          <td :colspan="2"><h4>Loading...</h4></td>
        </tr>
        <tr v-for="entry in queueEntries" :key="entry._id">
          <th scope="row">
            <router-link :to="`/task/${entry._id}`">{{ entry._id }}</router-link>
          </th>
          <td class="text-capitalize" :class="statusToBootstrapClass(entry.status)">{{ entry.status }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script lang="ts">
import { ref, defineComponent, onMounted, onBeforeUnmount } from "vue";
import { QueueEntry } from "../typings/Queue";
import API from "../utils/api";

export default defineComponent({
  setup: () => {
    const queueEntries = ref<QueueEntry[]>();

    let pollInterval: number | null = null;

    const pollData = async () => {
      const response = await API.getQueuedMachines();

      if (response) queueEntries.value = response;
    };

    const statusToBootstrapClass = (status: string) => {
      switch (status) {
        case "waiting":
          return "table-primary";
        case "started":
          return "table-success";
        case "finished":
          return "table-danger";
      }
      return "";
    };

    onMounted(() => {
      pollData();
      pollInterval = setInterval(pollData, 5000);
    });

    onBeforeUnmount(() => {
      if (pollInterval) clearInterval(pollInterval);
    });

    return {
      queueEntries,
      statusToBootstrapClass,
    };
  },
});
</script>
