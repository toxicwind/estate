#!/usr/bin/env python3
import pynvml, time, signal, sys, logging

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("nvidia-fan")

FAN_CURVE = [
    (30, 25), (40, 30), (50, 40), (60, 55),
    (65, 65), (70, 75), (75, 85), (80, 95), (85, 100),
]
POLL = 3

class FanController:
    def __init__(self):
        self.running = True
        self.handle = None
        self.fan_count = 0

    def init(self):
        pynvml.nvmlInit()
        self.handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        name = pynvml.nvmlDeviceGetName(self.handle)
        self.fan_count = pynvml.nvmlDeviceGetNumFans(self.handle)
        log.info(f"GPU 0: {name} ({self.fan_count} fans)")
        pynvml.nvmlDeviceSetFanControlPolicy(self.handle, 0, pynvml.NVML_FAN_POLICY_MANUAL)

    def speed_for_temp(self, temp):
        curve = self.curve
        if temp <= curve[0][0]: return curve[0][1]
        if temp >= curve[-1][0]: return curve[-1][1]
        for i in range(len(curve) - 1):
            t1, s1 = curve[i]
            t2, s2 = curve[i + 1]
            if t1 <= temp < t2:
                return int(s1 + (s2 - s1) * (temp - t1) / (t2 - t1))
        return curve[-1][1]

    def run(self):
        self.curve = FAN_CURVE
        log.info(f"Curve: {self.curve}  Poll: {POLL}s")
        while self.running:
            try:
                temp = pynvml.nvmlDeviceGetTemperature(self.handle, pynvml.NVML_TEMPERATURE_GPU)
            except:
                time.sleep(POLL)
                continue
            target = self.speed_for_temp(temp)
            for i in range(self.fan_count):
                pynvml.nvmlDeviceSetFanSpeed_v2(self.handle, i, target)
            time.sleep(POLL)

    def shutdown(self):
        self.running = False
        try:
            for i in range(self.fan_count):
                pynvml.nvmlDeviceSetFanControlPolicy(self.handle, i, pynvml.NVML_FAN_POLICY_TEMPERATURE_CONTINOUS_SW)
        except: pass
        try: pynvml.nvmlShutdown()
        except: pass

def main():
    ctrl = FanController()
    signal.signal(signal.SIGINT, lambda *a: setattr(ctrl, "running", False))
    signal.signal(signal.SIGTERM, lambda *a: setattr(ctrl, "running", False))
    try:
        ctrl.init()
        ctrl.run()
    finally:
        ctrl.shutdown()

if __name__ == "__main__":
    main()
