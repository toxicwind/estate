  containers = {
    shell = {
      name = "sovereign-shell";
      copyToRoot = [ configToml secretspecToml prometheusYml ];
    };
    processes = {
      name = "sovereign-stack";
      copyToRoot = [ configToml secretspecToml prometheusYml ];
    };
  };