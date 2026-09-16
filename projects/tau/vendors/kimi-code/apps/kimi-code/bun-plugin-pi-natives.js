export default {
  name: "skip-pi-natives",
  setup(build) {
    build.onLoad({ filter: /pi-natives/, namespace: "file" }, async (args) => {
      return { contents: "export default {};", loader: "js" };
    });
  }
};
