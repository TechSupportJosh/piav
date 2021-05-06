<template>
  <table class="table">
    <thead>
      <tr>
        <th scope="col">Control Reference</th>
        <th scope="col">Wait for Element Timeout</th>
        <th scope="col">Delay After Action</th>
        <th scope="col">Action</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="(precursor, index) in actions" :key="index">
        <td>{{ precursor.reference }}</td>
        <td>{{ precursor.wait_for_element_timeout }}</td>
        <td>{{ precursor.delay_after_action }}</td>
        <td>Method: {{ precursor.method }}<br />Parameters: {{ precursor.method_params }}</td>
      </tr>
    </tbody>
  </table>
</template>

<script lang="ts">
import { defineComponent, PropType } from "vue";
import { Action } from "../models/types/TaskInput";

export default defineComponent({
  props: {
    actions: {
      type: Array as PropType<Action[]>,
      required: true,
    },
  },
  setup(props) {
    return {
      actions: props.actions,
    };
  },
});
</script>
