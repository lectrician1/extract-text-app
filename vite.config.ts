import { sveltekit } from "@sveltejs/kit/vite";
import houdini from "houdini/vite";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [houdini(), sveltekit()],
  define: {
    "process.env.VITE_GRAPHQL_ENDPOINT_HOST": JSON.stringify(
      process.env.VITE_GRAPHQL_ENDPOINT_HOST
    ),
    "process.env.VITE_BASE_URL": JSON.stringify(process.env.VITE_BASE_URL),
  },
  base: process.env.VITE_BASE_URL || "",
});
