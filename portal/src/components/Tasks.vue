<template>
  <div class="container">
    <h1 class="mb-4">Task Queue</h1>
    <table class="table">
      <thead>
        <tr>
          <th scope="col">Task ID</th>
          <th scope="col">Status</th>
          <th scope="col">Restart</th>
        </tr>
      </thead>
      <tbody>
        <tr class="text-center" v-if="taskInputs === undefined">
          <td :colspan="2"><h4>Loading...</h4></td>
        </tr>
        <tr v-else v-for="task in taskInputs" :key="task._id">
          <th scope="row">
            <router-link :to="`/task/${task._id}`">{{ task._id }}</router-link>
          </th>
          <td class="text-capitalize" :class="statusToBootstrapClass(task.status)">{{ task.status }}</td>
          <td>
            <button class="w-100 btn btn-primary" :disabled="task.status !== 'failed'" @click="restartTask(task._id)">Restart Task</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script lang="ts">
import { ref, defineComponent, onMounted, onBeforeUnmount } from "vue";
import { TaskInput } from "../models/types/TaskInput";
import API from "../utils/api";

export default defineComponent({
  setup: () => {
    const taskInputs = ref<TaskInput[]>();

    let pollInterval: number | null = null;

    const pollData = async () => {
      const response = await API.getTaskInputs();

      if (response) taskInputs.value = response;
    };

    const statusToBootstrapClass = (status: string) => {
      switch (status) {
        case "waiting":
          return "table-secondary";
        case "running":
          return "table-primary";
        case "finished":
          return "table-success";
        case "failed":
          return "table-danger";
      }
      return "";
    };

    const restartTask = async (taskId: string) => {
      const response = await API.restartTask(taskId);

      if (response) pollData();
    };

    onMounted(() => {
      pollData();
      pollInterval = setInterval(pollData, 5000);
    });

    onBeforeUnmount(() => {
      if (pollInterval) clearInterval(pollInterval);
    });

    return {
      taskInputs,
      statusToBootstrapClass,
      restartTask,
    };
  },
});
</script>
