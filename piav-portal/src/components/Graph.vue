<template>
  <div id="cy" style="width: 100%; height: 1200px"></div>
</template>

<script lang="ts">
import { defineComponent, onMounted } from "vue";
import cytoscape from "cytoscape";
import api from "../utils/api";

export default defineComponent({
  setup() {
    onMounted(async () => {
      const response = await api.getTaskInputs();

      if (!response) return;

      const elements: cytoscape.ElementDefinition[] = [];
      response.forEach((taskInput) => {
        elements.push({
          data: {
            id: taskInput._id,
            name: taskInput._id,
          },
        });
        if (taskInput.parent_task)
          elements.push({
            data: {
              id: taskInput._id + taskInput.parent_task,
              source: taskInput.parent_task,
              target: taskInput._id,
            },
          });
      });

      const cy = cytoscape({
        container: document.getElementById("cy"), // container to render in
        elements: elements,
        style: [
          {
            selector: "node[name]",
            style: {
              content: "data(name)",
            },
          },

          {
            selector: "edge",
            style: {
              "curve-style": "bezier",
              "target-arrow-shape": "triangle",
            },
          },
        ],
      });
    });
    return {};
  },
});
</script>
