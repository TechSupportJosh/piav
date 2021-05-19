<template>
  <div v-for="filePath in sortedKeys">
    <strong>{{ filePath }}</strong
    ><br />
    <span v-for="(count, eventName) in grouped[filePath]">{{ eventName }}: {{ count }}<br /></span>
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType } from "vue";
import { FileEvent } from "../models/types/TaskOutput";

export default defineComponent({
  props: {
    fileEvents: {
      type: Array as PropType<FileEvent[]>,
      required: true,
    },
  },
  setup(props) {
    const grouped: Record<string, Record<string, number>> = {};

    props.fileEvents.forEach((event) => {
      if (!(event.params.file_name in grouped)) grouped[event.params.file_name] = {};

      grouped[event.params.file_name][event.event_name] = (grouped[event.params.file_name][event.event_name] ?? 0) + 1;
    });

    const sortedKeys = Object.keys(grouped).sort();

    return {
      fileEvents: props.fileEvents,
      grouped,
      sortedKeys,
    };
  },
});
</script>
