<template>
  <div class="container">
    <div class="row mb-4">
      <div class="col-10">
        <h1 class="mb-0">Setup New Executable</h1>
      </div>
      <div class="col-2 d-flex align-items-center">
        <router-link to="/executables" class="btn btn-primary w-100">Back</router-link>
      </div>
    </div>
    <form @submit.prevent="submitForm">
      <div class="form-group">
        <label>Application Name</label>
        <input type="text" class="form-control" v-model="formData.applicationName" />
      </div>
      <div class="form-group">
        <label>Full Installation Name</label>
        <input type="text" class="form-control" v-model="formData.fullInstallationName" />
      </div>
      <div class="form-group">
        <label>Installer File</label>
        <input type="file" class="form-control-file" v-on:change="handleFileUpload" accept=".msi,.exe" />
      </div>
      <button
        type="submit"
        class="btn btn-primary"
        :disabled="formData.applicationName === '' || formData.fullInstallationName === '' || !formData.installer"
      >
        Submit
      </button>
    </form>
  </div>
</template>

<script lang="ts">
import { defineComponent, reactive } from "vue";
import router from "../plugins/router";
import API from "../utils/api";

interface FormData {
  applicationName: string;
  fullInstallationName: string;
  installer: string;
  installerName: string;
}

export default defineComponent({
  setup() {
    const formData = reactive<FormData>({
      applicationName: "",
      fullInstallationName: "",
      installer: "",
      installerName: "",
    });

    const handleFileUpload = (event: Event) => {
      if (!event.target) return;

      const input = event.target as HTMLInputElement;

      if (!input.files?.length) return;

      formData.installerName = input.files[0].name;

      const reader = new FileReader();
      reader.readAsDataURL(input.files[0]);
      reader.onload = () => {
        formData.installer = (reader.result?.toString() ?? ",").split(",")[1];
      };
    };

    const submitForm = async () => {
      const response = await API.setupExecutable(
        formData.applicationName,
        formData.fullInstallationName,
        formData.installer,
        formData.installerName
      );

      if (response) return router.push("/executables");
    };

    return {
      formData,
      handleFileUpload,
      submitForm,
    };
  },
});
</script>
