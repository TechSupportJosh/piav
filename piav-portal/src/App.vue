<template>
  <nav class="navbar navbar-expand navbar-dark bg-primary mb-4">
    <!-- Navbar content -->
    <a class="navbar-brand" href="#"><strong>PIAV</strong></a>
    <div class="collapse navbar-collapse">
      <ul class="navbar-nav">
        <li class="nav-item" v-for="route in routes" :key="route.path">
          <router-link class="nav-link" active-class="active" :to="route.path">{{ route.meta?.navigationLabel }}</router-link>
        </li>
      </ul>
    </div>
  </nav>
  <router-view class="mt-4"></router-view>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { useRouter } from "./plugins/router";

export default defineComponent({
  name: "App",
  setup() {
    const router = useRouter();
    console.log(router.getRoutes());
    return {
      routes: router.getRoutes().filter((route) => route.meta.navigationLabel),
    };
  },
});
</script>

<style></style>
