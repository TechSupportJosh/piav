<template>
  <div id="cy" style="width: 100%; height: 1200px"></div>
</template>

<script lang="ts">
import { defineComponent, onMounted } from "vue";
import cytoscape, { ElementDefinition } from "cytoscape";
import api from "../utils/api";
import dagre from "cytoscape-dagre";
import { Action, TaskInput } from "../models/types/TaskInput";

export default defineComponent({
  setup() {
    const taskActionsToString = (taskInput: TaskInput) => {
      const actions = taskInput.actions;
      return actions
        .map((action) => `${methodToHumanMethod(action.method, action.method_params)} "${action.control.meta.text}"`)
        .join("\n");
    };

    const methodToHumanMethod = (method: string, params: Record<string, any>) => {
      switch (method) {
        case "click":
        case "click_input":
          return "Click";
        case "set_toggle_state":
          return params.state ? "Toggle" : "Untoggle";
        default:
          return method;
      }
    };

    onMounted(async () => {
      const taskInputs = await api.getTaskInputs();
      const taskOutputs = await api.getTaskOutputs(true, false);

      if (!taskInputs || !taskOutputs) return;

      let rootId = "";
      const parents: Record<string, string> = {};

      const elements: cytoscape.ElementDefinition[] = [];
      taskInputs.forEach((taskInput) => {
        // We don't draw same_as outputs as a new node
        const taskOutput = taskOutputs.find((output) => output._id === taskInput._id);
        if (taskOutput && taskOutput.same_as) return;

        const node: ElementDefinition = {
          data: {
            id: taskInput._id,
            name: taskInput._id,
          },
          style: {},
        };

        if (taskOutput && !taskOutput.window_enumeration.application_alive) node.style.backgroundColor = "red";

        if (taskOutput && taskOutput.window_enumeration.program_installed) node.style.backgroundColor = "green";

        elements.push(node);
        if (taskInput.parent_task) {
          parents[taskInput._id] = taskInput.parent_task;

          elements.push({
            data: {
              id: taskInput._id + taskInput.parent_task,
              source: taskInput.parent_task,
              target: taskInput._id,
              label: taskActionsToString(taskInput),
              color: "blue",
            },
          });
        } else {
          rootId = taskInput._id;
        }
      });

      taskOutputs.forEach((taskOutput) => {
        if (!taskOutput.same_as) return;
        const taskInput = taskInputs.find((input) => input._id === taskOutput._id);
        console.log(taskInput);
        console.log(taskOutput);
        if (taskInput)
          elements.push({
            data: {
              source: taskInput.parent_task,
              target: taskOutput.same_as,
              label: taskActionsToString(taskInput),
              color: "red",
            },
          });
      });

      let options: cytoscape.LayoutOptions = {
        name: "dagre",

        fit: true, // whether to fit the viewport to the graph
        directed: false, // whether the tree is directed downwards (or edges can point in any direction if false)
        padding: 30, // padding on fit
        circle: false, // put depths in concentric circles if true, put depths top down if false
        //grid: false, // whether to create an even grid into which the DAG is placed (circle:false only)
        spacingFactor: 1.75, // positive spacing factor, larger => more space between nodes (N.B. n/a if causes overlap)
        boundingBox: undefined, // constrain layout bounds; { x1, y1, x2, y2 } or { x1, y1, w, h }
        avoidOverlap: true, // prevents node overlap, may overflow boundingBox if not enough space
        nodeDimensionsIncludeLabels: true, // Excludes the label when calculating node bounding boxes for the layout algorithm
        roots: [rootId], // the roots of the trees
        //maximal: false, // whether to shift nodes down their natural BFS depths in order to avoid upwards edges (DAGS only)
        animate: false, // whether to transition the node positions
        animationDuration: 500, // duration of animation in ms if enabled
        animationEasing: undefined, // easing of animation if enabled,
        ready: undefined, // callback on layoutready
        stop: undefined, // callback on layoutstop
      };

      cytoscape.use(dagre);
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
              "target-arrow-color": "data(color)",
              "arrow-scale": 1.5,
              "text-wrap": "wrap",
              "control-point-step-size": 120,
              "line-color": "data(color)",
              width: 5,
              label: "data(label)",
            },
          },
        ],
        layout: options,
      });
    });
    return {};
  },
});
</script>
