"""
Loop a ramp on the Keysight/Agilent J7211C attenuator (10.1.1.137) over SCPI,
without the front-panel PROG limit of 200 loops.

Examples:
  python3 att_loop_control.py --start 0 --stop 60 --step 1 --dwell 1 --loops 1000
  python3 att_loop_control.py --start 0 --stop 60 --step 2 --dwell 0.5 --loops 0 --shape triangle   (0 = forever)
  python3 att_loop_control.py --levels 0,20,40,60 --dwell 5 --loops 500

Ctrl+C stops cleanly and sets the attenuation to --final (default: --start / first level).
"""
import argparse
import socket
import sys
import time

# global default host IP address of J7211C
host_ip = "192.168.1.100"
#port = 5025  # default SCPI port for J7211C
#timeout = 5  # seconds

class J7211:
    def __init__(self, host, port=5025, timeout=5):
        self.s = socket.create_connection((host, port), timeout=timeout)
        self.f = self.s.makefile("r", newline="\n")

    def write(self, cmd):
        self.s.sendall((cmd + "\n").encode())

    def query(self, cmd):
        self.write(cmd)
        return self.f.readline().strip()

    def set_att(self, db):
        self.write(f"ATT {db:g}")

    def close(self):
        self.s.close()


def frange(start, stop, step):
    step = abs(step) if stop >= start else -abs(step)
    vals, v = [], start
    while (step > 0 and v <= stop + 1e-9) or (step < 0 and v >= stop - 1e-9):
        vals.append(round(v, 3))
        v += step
    return vals


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--host", type=str, default=host_ip, help="IP address of J7211C")
    p.add_argument("--start", type=float, default=0)
    p.add_argument("--stop", type=float, default=60)
    p.add_argument("--step", type=float, default=1)
    p.add_argument("--levels", help="explicit comma-separated dB list (overrides start/stop/step)")
    p.add_argument("--shape", choices=["sawtooth", "triangle"], default="sawtooth",
                   help="sawtooth: start->stop then jump back; triangle: start->stop->start")
    p.add_argument("--dwell", type=float, default=1.0, help="seconds per step")
    p.add_argument("--loops", type=int, default=0, help="number of loops, 0 = forever")
    p.add_argument("--final", type=float, help="attenuation to leave set when done/stopped")
    a = p.parse_args()

    if a.levels:
        steps = [float(x) for x in a.levels.split(",")]
    else:
        steps = frange(a.start, a.stop, a.step)
        if a.shape == "triangle":
            steps = steps + steps[-2:0:-1]
    final = a.final if a.final is not None else steps[0]

    dev = J7211(a.host)
    print("Connected:", dev.query("*IDN?"))
    dev.write("*CLS")
    print(f"{len(steps)} steps/loop, dwell {a.dwell}s, loops {'forever' if a.loops == 0 else a.loops}")
    print("Levels:", steps)

    loop = 0
    try:
        while a.loops == 0 or loop < a.loops:
            loop += 1
            t0 = time.time()
            for i, db in enumerate(steps):
                dev.set_att(db)
                # schedule against absolute time so dwell doesn't drift
                target = t0 + (i + 1) * a.dwell
                time.sleep(max(0, target - time.time()))
            err = dev.query("SYST:ERR?")
            if not err.startswith("+0"):
                print(f"\nInstrument error: {err}")
            print(f"\rLoop {loop}{'' if a.loops == 0 else '/' + str(a.loops)} done  "
                  f"({time.strftime('%H:%M:%S')})", end="", flush=True)
    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        try:
            dev.set_att(final)
            print(f"\nAttenuation left at {dev.query('ATT?')} dB after {loop} loop(s).")
        finally:
            dev.close()


if __name__ == "__main__":
    sys.exit(main())
