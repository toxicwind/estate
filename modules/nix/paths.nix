{ config, ... }:
let
  SOV = config.env.DEVENV_ROOT or ".";
in
{
  _module.args = rec {
    SOV_HOME = "${SOV}";
    MODELS = "${SOV_HOME}/models";
    STATE = "${SOV_HOME}/.state";
    LOGS = "${SOV_HOME}/logs";
    PROMETHEUS_DATA = "${SOV_HOME}/.prometheus";
  };
}
