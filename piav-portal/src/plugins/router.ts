import { createRouter, createWebHistory, RouteRecordRaw } from "vue-router";

import Task from "../components/Task.vue";
import TaskQueue from "../components/TaskQueue.vue";
import Executable from "../components/Executable.vue";
import SetupExecutable from "../components/SetupExecutable.vue";

const routes: RouteRecordRaw[] = [
  {
    path: "/executables",
    component: Executable,
    meta: {
      navigationLabel: "Executables",
    },
  },
  {
    path: "/setup_exe",
    component: SetupExecutable,
  },
  {
    path: "/",
    component: TaskQueue,
    meta: {
      navigationLabel: "Queued Tasks",
    },
  },
  {
    path: "/task/:taskId",
    component: Task,
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes: routes,
});

export const useRouter = () => {
  return router;
};

export default router;
