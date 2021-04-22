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
      <tr v-for="(precursor, index) in precursors" :key="index">
        <td>{{ precursor.reference }}</td>
        <td>{{ precursor.wait_for_element_timeout }}</td>
        <td>{{ precursor.delay_after_action }}</td>
        <td>Method: {{ precursor.action.method }}<br />Parameters: {{ precursor.action.parameters }}</td>
      </tr>
    </tbody>
  </table>
</template>

<script lang="ts">
import { defineComponent, PropType } from "vue";
import { Precursor } from "../models/types/TaskInput";

export default defineComponent({
  props: {
    precursors: {
      type: Array as PropType<Precursor[]>,
      required: true,
    },
  },
  setup(props) {
    return {
      precursors: props.precursors,
    };
  },
});
</script>
