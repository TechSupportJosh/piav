import { RouteMeta } from "vue-router";

declare module "vue-router" {
  // Add a custom parameter to RouteRecordRaw
  interface RouteMeta {
    navigationLabel?: string;
  }
}
