import matplotlib.pyplot as plt
import numpy as np
import time
import datetime

from scheduler import Scheduler

def going_forward_az(i):
    print("Go to next az position")
    if i == AZ_STEPS-1:
        return
    else:
        try:
            s.mount.slew_left(AZ_SLEW_TIME)
        except:
            s.mount.goto_azimuth(AZ_PRED[i], tol=1, speed=9, niters=5)

def going_backward_az(i):
    print("Go to next az position")
    if i == 0:
        print("Going to zero position")
        s.mount.goto_zero_position()
        time.sleep(EL_SLEW_TIME)
        timestamp = datetime.datetime.now().isoformat()
        print(f"Check the end of the zero position {timestamp}")

    if i == AZ_STEPS-1:
        return
    try:
        s.mount.slew_right(AZ_SLEW_TIME)
    except:
        s.mount.goto_azimuth(AZ_PRED[i], tol=1, speed=9, niters=5)

def trigger_sweep_elevation(i, is_forward=True):
    print(6*"-------")
    print("Cycle:", i+1)
    print(6*"-------")
    label  = 'forward' if is_forward else 'backward'
    name = f'cycle_{(i+1):04d}_{label}_test_mount'

    print("Go to Zero Elevation Point 85.0 degrees")
    s.mount.goto_elevation(85.0, tol=1.0, speed=8, niters=1)

    # Sweep Elevation for a number of pointings
    results = s.sweep_elevation(EL_SLEW_TIME, nsteps=EL_STEPS, az_rank=i+1, rang0=RANGE_INITIAL)
    print("Slewed to Alt:", results['slew_angle'])
    print("Slew Rate Result:", results['slew_rate'])

    # if not s.is_photodiode_on:
    np.savez(f'./tmp/{name}.npz', **results)

    # Come back to the top and take data
    duration_up = (85.0-results['slew_angle'][-1])/np.median(np.abs(results['slew_rate']))
    if s.is_photodiode_on:
        duration_up-= time_delay_photodiode
    print(f"Slew up for {duration_up:2.0f} seconds")
    ti = time.time()
    s.acquire_while_slewing_elevation(duration_up, 'up', az_rank=i+1)
    print("Acutal time to acquire data:", time.time()-ti, "seconds", "Expected time:", duration_up, "seconds")
    cTime = time.time() - t0
    print(6*"-----")
    print(f"Elapsed Cycle time: {cTime}")
    print(6*"-----")



if __name__ == "__main__":
    t0 = time.time()
    going_back = False

    ## SETUP 
    AZ_STEPS = 2
    AZ_SLEW_TIME = 7.46 # seconds
    AZ_PRED = np.linspace(0, 60, AZ_STEPS)
    EL_STEPS = 5 # steps
    EL_SLEW_TIME = 2.75 # seconds

    ## Photodiode Setup
    RANGE_INITIAL = 1e-5
    NPLC = 5
    EXPTIME = 1.0
    # Slewing while acquiring data, time correction 
    time_delay_photodiode = 2.05 # sec

    # Start Scheduler
    s = Scheduler(filter='SDSSg')
    s.mount.set_arrow_speed(9)

    # Reset Photodiode
    s.reset_photodiode()
    # nplc = 5, nsamples = 10, texp=1 sec

    # Exercising the mount
    s.mount.goto_zero_position()
    s.mount.slew_down(1.25)

    for i in range(AZ_STEPS):
        trigger_sweep_elevation(i)   
        going_forward_az(i)

    ## Going Back
    # s.mount.goto_azimuth(60, tol=0.5, speed=9, niters=3)
    s.mount.set_arrow_speed(9)

    # TO DEBUG
    # for i in range(AZ_STEPS):
    #     j = AZ_STEPS-i-1
    #     trigger_sweep_elevation(j+1, is_forward=False)
    #     going_backward_az(j)