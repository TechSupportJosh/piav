<template>
  <table class="table">
    <thead>
      <tr>
        <th scope="col">Protocol</th>
        <th scope="col">Source</th>
        <th scope="col"></th>
        <th scope="col">Destination</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="(event, index) in networkEvents" :key="index">
        <template v-if="['Send', 'Recv'].includes(event.event_name)">
          <td>{{ event.params.l4_proto }}</td>
          <td>{{ event.params.sip }}:{{ event.params.sport }} {{ event.params.sport_name ? `(${event.params.sport_name})` : "" }}</td>
          <td>{{ event.event_name === "Send" ? "----->" : "<-----" }}<br />{{ event.params.size }}</td>
          <td>{{ event.params.dip }}:{{ event.params.dport }} {{ event.params.dport_name ? `(${event.params.dport_name})` : "" }}</td>
        </template>
        <template v-else>
          <td :colspan="4">
            {{ event.event_name }}
          </td>
        </template>
      </tr>
    </tbody>
  </table>
</template>

<script lang="ts">
import { defineComponent, PropType } from "vue";
import { NetworkEvent } from "../models/types/TaskOutput";

export default defineComponent({
  props: {
    networkEvents: {
      type: Array as PropType<NetworkEvent[]>,
      required: true,
    },
  },
  setup(props) {
    return {
      networkEvents: props.networkEvents,
    };
  },
});
</script>
