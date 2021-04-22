<template>
  <table class="table table-bordered">
    <thead>
      <tr>
        <th scope="col">Registry Function</th>
        <th scope="col">Key</th>
        <th scope="col">Status</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="(event, index) in registryEvents" :key="index">
        <td style="width: 20%">{{ event.event_name }}</td>
        <td class="text-break">{{ event.params.key_name }}</td>
        <td>{{ event.params.status }}</td>
      </tr>
    </tbody>
  </table>
</template>

<script lang="ts">
import { defineComponent, PropType } from "vue";
import { RegistryEvent } from "../typings/TaskOutput";

export default defineComponent({
  props: {
    registryEvents: {
      type: Array as PropType<RegistryEvent[]>,
      required: true,
    },
  },
  setup(props) {
    return {
      registryEvents: props.registryEvents,
    };
  },
});
</script>
