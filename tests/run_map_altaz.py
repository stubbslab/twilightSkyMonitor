import matplotlib.pyplot as plt
import numpy as np
import time
import datetime

from scheduler import Scheduler

def going_forward_az(i):
    print(6*"-------")
    print("Cycle:", i+1)
    print(6*"-------")
    name = f'cycle_{(i+1):04d}'

    print("Go to Zero Elevation Point 85.0 degrees")
    s.mount.goto_elevation(85.0, tol=1.0, speed=8, niters=1)
    s.mount.get_current_alt_az()

    # Sweep Elevation for a number of pointings
    results = s.sweep_elevation(EL_SLEW_TIME, nsteps=EL_STEPS, az_rank=i+1, rang0=RANGE_INITIAL)
    print("Slewed to Alt:", results['slew_angle'])
    print("Slew Rate Result:", results['slew_rate'])

    if not s.is_photodiode_on:
        np.savez(f'./tmp/{name}_forward.npz', **results)

    # Come back to the top and take data
    duration_up = (90.-results['slew_angle'][-1])/np.median(1.1*np.abs(results['slew_rate']))
    print(f"Slew up for {duration_up:2.0f} seconds")
    s.acquire_while_slewing_elevation(duration_up, 'up', az_rank=i+1)

    cTime = time.time() - t0
    print(6*"-----")
    print(f"Elapsed Cycle time: {cTime}")
    print(6*"-----")

    print("Go to next az position")
    if i == AZ_STEPS-1:
        return
    else:
        try:
            s.mount.slew_left(AZ_SLEW_TIME)
        except:
            s.mount.goto_azimuth(AZ_PRED[i], tol=1, speed=9, niters=5)

        # print("Go to initial el position")
        # s.mount.slew_down(2.0)

def going_backward_az(i):
    print(6*"-------")
    print("Cycle:", i+1)
    print(6*"-------")
    name = f'cycle_{(i+1):04d}'

    # Sweep Elevation for a number of pointings
    results = s.sweep_elevation(EL_SLEW_TIME, nsteps=EL_STEPS, az_rank=i+1, rang0=RANGE_INITIAL)
    print("Slewed to Alt:", results['slew_angle'])
    print("Slew Rate Result:", results['slew_rate'])
    if not s.is_photodiode_on:
        np.savez(f'./tmp/{name}_backward.npz', **results)

    # Come back to the top and take data
    duration_up = (90.-results['slew_angle'][-1])/np.median(1.1*np.abs(results['slew_rate']))
    print(f"Slew up for {duration_up} seconds")
    s.acquire_while_slewing_elevation(duration_up, 'up', az_rank=i+1)

    cTime = time.time() - t0
    print(6*"-----")
    print(f"Elapsed Cycle time: {cTime}")
    print(6*"-----")

    print("Go to next az position")
    if i == AZ_STEPS-1:
        return
    try:
        s.mount.slew_right(AZ_SLEW_TIME)
    except:
        s.mount.goto_azimuth(AZ_PRED[i], tol=1, speed=9, niters=5)


    # print("Go to initial el position")
    # s.mount.slew_down(2.0)

if __name__ == "__main__":
    t0 = time.time()
    going_back = False

    ## SETUP 
    AZ_STEPS = 7
    AZ_SLEW_TIME = 7.46 # seconds
    AZ_PRED = np.linspace(0, 180, AZ_STEPS)
    EL_STEPS = 6 # steps
    EL_SLEW_TIME = 2.5 # seconds

    ## Photodiode Setup
    RANGE_INITIAL = 2e-6
    NPLC = 5
    EXPTIME = 1.0

    # Start Scheduler
    s = Scheduler(filter='Empty', expTime=EXPTIME, nplc=NPLC)
    s.mount.set_arrow_speed(9)

    # Reset Photodiode
    s.reset_photodiode()
    # nplc = 5, nsamples = 10, texp=1 sec

    # Exercising the mount
    s.mount.goto_zero_position()

    for i in range(AZ_STEPS):
        going_forward_az(i)
    
    ## Going Back
    s.mount.goto_azimuth(-179.99, tol=0.5, speed=9, niters=5)
    s.mount.set_arrow_speed(9)

    for i in range(AZ_STEPS):
        if i == AZ_STEPS-1:
            print("Going to zero position")
            s.mount.goto_zero_position()
            time.sleep(AZ_SLEW_TIME)
            timestamp = datetime.datetime.now().isoformat()
            print(f"Check the end of the slew {timestamp}")
        going_backward_az(AZ_STEPS-i-1)