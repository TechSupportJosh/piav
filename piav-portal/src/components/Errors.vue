<template>
  <ul class="list-group">
    <li class="list-group-item" v-for="error in errors">
      <strong>{{ new Date(error.time * 1000).toLocaleString() }}</strong>
      <br />
      <br />
      <pre><code>{{error.stack_trace}}</code></pre>
    </li>
  </ul>
</template>

<script lang="ts">
import { ref, defineComponent, onMounted, onBeforeUnmount } from "vue";
import { Error } from "../models/types/Error";
import API from "../utils/api";

export default defineComponent({
  props: {
    taskId: String,
  },
  setup: (props) => {
    const errors = ref<Error[]>();

    let pollInterval: number | null = null;

    const pollData = async () => {
      const response = props.taskId ? await API.getError(props.taskId) : await API.getErrors();

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
