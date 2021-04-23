<template>
  <JsonTreeView :data="testObj" :maxDepth="1" />
  <!--
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
  </table>-->
</template>

<script lang="ts">
import { defineComponent, PropType } from "vue";
import { RegistryEvent } from "../models/types/TaskOutput";
import { JsonTreeView, JsonTreeViewItem } from "json-tree-view-vue3";

export default defineComponent({
  components: { JsonTreeView },
  props: {
    registryEvents: {
      type: Array as PropType<RegistryEvent[]>,
      required: true,
    },
  },
  setup(props) {
    const treeObj: Record<string, any> = {};

    props.registryEvents.forEach((event) => {
      const split = event.params.key_name.split("\\").filter((i) => i);
      let parent = treeObj;
      split.forEach((leaf, index) => {
        if (!(leaf in parent)) parent[leaf] = {};

        if (split.length - 1 === index) {
          if (!(event.event_name in parent[leaf])) parent[leaf]["Event: " + event.event_name] = {};

          parent[leaf]["Event: " + event.event_name][event.params.status] =
            (parent[leaf]["Event: " + event.event_name][event.params.status] ?? 0) + 1;
        }

        parent = parent[leaf];
      });
    });

    return {
      registryEvents: props.registryEvents,
      testObj: JSON.stringify(treeObj, null, 1),
    };
  },
});
</script>
