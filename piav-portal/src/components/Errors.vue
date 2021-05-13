<template>
  <div class="container">
    <h1 class="mb-4">Errors</h1>
    <ul class="list-group">
      <li class="list-group-item" v-for="error in errors">
        <h4>{{ error.task_id }}</h4>
        <pre><code>{{error.stack_trace}}</code></pre>
      </li>
    </ul>
    {{ errors }}
  </div>
</template>

<script lang="ts">
import { ref, defineComponent, onMounted, onBeforeUnmount } from "vue";
import { Error } from "../models/types/Error";
import API from "../utils/api";

export default defineComponent({
  setup: () => {
    const errors = ref<Error[]>();

    let pollInterval: number | null = null;

    const pollData = async () => {
      const response = await API.getErrors();

      if (response) errors.value = response;
    };

    onMounted(() => {
      pollData();
      pollInterval = setInterval(pollData, 5000);
    });

    onBeforeUnmount(() => {
      if (pollInterval) clearInterval(pollInterval);
    });

    return {
      errors,
    };
  },
});
</script>
