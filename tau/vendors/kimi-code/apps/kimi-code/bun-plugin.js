export default {
  name: "kimi-resolve",
  setup(build) {
    // Resolve #/ imports to ./src/*
    build.onResolve({ filter: /^#\//, namespace: "file" }, async (args) => {
      const path = args.path;
      const resolved = args.resolveDir + "/src/" + path.slice(2);
      return { path: resolved, external: true };
    });
    // Skip pi-natives native modules
    build.onLoad({ filter: /pi-natives/, namespace: "file" }, async (args) => {
      return { contents: "export default {};", loader: "js" };
    });
  }
};
