{
  "verification": "hatch/bin/progress-watchdog imports watchdog_lib and uses ConditionRegistry for alert dedup (seen-set + condition-hash with escalate-on-change and cleared notifications). The script is correctly implemented per the requirements.",
  "alert_frequency": "Cannot determine recent Hearth alert frequency from fleet messages because required tools (squawk, yote-conn) are unavailable and no recent progress state files were found. The watchdog script is not actively running in this session."
}