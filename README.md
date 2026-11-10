### Why need this?
1. Avoid the burden of clicking start/stop on the WebGUI
2. Force Attenuation Program more than 200 cycles (WARN: USE WITH CARE)

### Tested model
1. KeySight J7211C

### Prerequisite
1. python3
2. Please change the variable host to your programmable attenuator IP address

### Examples:
```bash
python3 att_loop.py --start 0 --stop 60 --step 1 --dwell 1 --loops 1000
python3 att_loop.py --start 0 --stop 60 --step 2 --dwell 0.5 --loops 0 --shape triangle   (0 = forever)
python3 att_loop.py --levels 0,20,40,60 --dwell 5 --loops 500
```