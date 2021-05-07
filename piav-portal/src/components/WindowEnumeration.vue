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
  <h3>Screenshot</h3>
  <div class="mb-4">
    <img :src="`data:image/jpeg;charset=utf-8;base64,${data.base64_images[currentImageIndex]}`" class="mb-4" />
    <nav class="d-flex justify-content-center">
      <ul class="pagination">
        <li class="page-item" :class="{ active: index === currentImageIndex }" v-for="(image, index) in data.base64_images" :key="index">
          <a class="page-link" href="#" @click.prevent="currentImageIndex = index">{{ convertImageIndexToLabel(index) }}</a>
        </li>
      </ul>
    </nav>
  </div>
  <template v-if="data.top_window_texts && data.found_controls">
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
          <td>{{ control.type }}</td>
          <td>{{ control.reference }}</td>
          <td>{{ control.meta }}</td>
        </tr>
      </tbody>
    </table>
  </template>
</template>

<script lang="ts">
import { defineComponent, PropType, ref } from "vue";
import { WindowEnumeration } from "../models/types/TaskOutput";

export default defineComponent({
  props: {
    data: {
      type: Object as PropType<WindowEnumeration>,
      required: true,
    },
  },
  setup(props) {
    const currentImageIndex = ref(0);

    const convertImageIndexToLabel = (index: number) => {
      switch (index) {
        case 0:
          return "Loaded";
        case props.data.base64_images!.length - 1:
          return "Enumeration";
        default:
          return index.toString();
      }
    };

    return {
      data: props.data,
      currentImageIndex,
      convertImageIndexToLabel,
    };
  },
});
</script>
