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
      <tr v-for="(action, index) in actions" :key="index">
        <td>Type: {{ action.control.type }}<br />Reference: {{ action.control.reference }}<br />Meta: {{ action.control.meta }}</td>
        <td>{{ action.wait_for_element_timeout }}</td>
        <td>{{ action.delay_after_action }}</td>
        <td>Method: {{ action.method }}<br />Parameters: {{ action.method_params }}</td>
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
