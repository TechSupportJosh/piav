<template>
  <div class="container">
    <div class="row mb-4">
      <div class="col-10">
        <h1 class="mb-0">Executables</h1>
      </div>
      <div class="col-2 d-flex align-items-center">
        <router-link to="/setup_exe" class="btn btn-primary w-100">Setup Executable</router-link>
      </div>
    </div>
    <table class="table">
      <thead>
        <tr>
          <th scope="col">ID</th>
          <th scope="col">Application Name</th>
          <th scope="col">Full Installation Name</th>
          <th scope="col">Installer</th>
        </tr>
      </thead>
      <tbody>
        <tr class="text-center" v-if="executables === undefined">
          <td :colspan="2"><h4>Loading...</h4></td>
        </tr>
        <tr v-else v-for="executable in executables" :key="executable._id">
          <td>{{ executable._id }}</td>
          <td>{{ executable.application_name }}</td>
          <td>{{ executable.full_installation_name }}</td>
          <td>
            <a :href="`${API_BASE}/executables/${executable.file_name}`" download>{{ executable.file_name }}</a
            ><br />{{ executable.file_sha256sum }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script lang="ts">
import { defineComponent, onMounted, ref } from "vue";
import { Executable } from "../models/types/Executable";
import API, { API_BASE } from "../utils/api";

export default defineComponent({
  setup: () => {
    const executables = ref<Executable[]>();

    onMounted(async () => {
      const response = await API.getExecutables();

      if (response) executables.value = response;
    });

    return {
      executables,
      API_BASE,
    };
  },
});
</script>
