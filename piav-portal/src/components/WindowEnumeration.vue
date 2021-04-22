<template>
  <table class="table table-bordered">
    <tbody>
      <tr>
        <td>Application Alive</td>
        <td :class="data.application_alive ? 'table-success' : 'table-danger'">{{ data.application_alive ? "Alive" : "Dead" }}</td>
      </tr>
      <tr>
        <td>Program Installed</td>
        <td :class="data.program_installed ? 'table-success' : 'table-danger'">{{ data.program_installed ? "Yes" : "No" }}</td>
      </tr>
    </tbody>
  </table>
  <h3>Window Text</h3>
  <ul>
    <li v-for="(text, index) in data.top_window_texts" :key="index">{{ text }}</li>
  </ul>
  <h3>Found Controls</h3>
  <table class="table">
    <thead>
      <tr>
        <th scope="col">Control Type</th>
        <th scope="col">Reference</th>
        <th scope="col">Debug Info</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="(control, index) in data.found_controls" :key="index">
        <td>{{ control.control_type }}</td>
        <td>{{ control.reference }}</td>
        <td></td>
      </tr>
    </tbody>
  </table>
</template>

<script lang="ts">
import { defineComponent, PropType } from "vue";
import { WindowEnumeration } from "../typings/TaskOutput";

export default defineComponent({
  props: {
    data: {
      type: Object as PropType<WindowEnumeration>,
      required: true,
    },
  },
  setup(props) {
    return {
      data: props.data,
    };
  },
});
</script>
