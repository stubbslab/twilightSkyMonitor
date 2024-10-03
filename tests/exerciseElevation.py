import matplotlib.pyplot as plt
import numpy as np
import time

from scheduler import Scheduler

PAUSE = 0.5 # sec

def elevation_sweep(i):
    print(6*"-------")
    print("Cycle:", i+1)
    print(6*"-------")
    name = f'cycle_{(i+1):04d}'

    print("Go to Zero Elevation Point 85.0 degrees")
    time.sleep(PAUSE)
    s.mount.goto_elevation(85.0, tol=1.0, speed=8, niters=1)
    s.mount.get_current_alt_az()

    # Sweep Elevation for a number of pointings
    results = s.sweep_elevation(EL_SLEW_TIME, nsteps=EL_STEPS, az_rank=i+1, rang0=RANGE_INITIAL)
    print("Slewed to Alt:", results['slew_angle'])
    print("Slew Rate Result:", results['slew_rate'])

    if not s.is_photodiode_on:
        np.savez(f'./tmp/{name}_forward.npz', **results)

    # Come back to the top and take data
    duration_up = (90.-results['slew_angle'][-1])/np.median(np.abs(results['slew_rate']))
    print(f"Slew up for {duration_up:2.0f} seconds")
    # s.acquire_while_slewing_elevation(duration_up, 'up', az_rank=i+1)
    s.mount.set_arrow_speed(9)
    s.mount.slew_up(duration_up)

    cTime = time.time() - t0
    print(6*"-----")
    print(f"Elapsed Cycle time: {cTime}")
    print(6*"-----")
    return results
   
if __name__ == "__main__":
    t0 = time.time()
    going_back = False

    ## SETUP 
    AZ_STEPS = 10 # steps
    AZ_SLEW_TIME = 7.46 # seconds
    AZ_PRED = np.linspace(0, 180, AZ_STEPS)
    EL_STEPS = 5 # steps
    EL_SLEW_TIME = 2.75 # seconds

    ## Photodiode Setup
    RANGE_INITIAL = 2e-7
    NPLC = 5
    EXPTIME = 2.5

    # Start Scheduler
    s = Scheduler(filter='Empty', expTime=EXPTIME, nplc=NPLC)
    s.mount.set_arrow_speed(9)

    # Reset Photodiode
    s.reset_photodiode()
    # nplc = 5, nsamples = 10, texp=1 sec

    # Exercising the mount
    s.mount.goto_zero_position()
    s.mount.slew_down(0.75)

    maps = []
    for i in range(AZ_STEPS):
        res = elevation_sweep(i)
        maps.append(res)

    maps = []
    for i in range(AZ_STEPS):
        name = f'cycle_{(i+1):04d}'
        d = np.load(f'./tmp/{name}_forward.npz')
        maps.append(d)

    # Plot the results
    fig, ax = plt.subplots()
    evals = []
    evals2 = []
    for i in range(AZ_STEPS):
        evals.append(maps[i]['slew_angle'])
        evals2.append(maps[i]['slew_rate'])

    print("Corrections")
    print(np.median(evals2)/np.array(evals2).mean(axis=0))
    plt.scatter(np.mean(evals, axis=0)[1:], np.median(evals2)/np.array(evals2).mean(axis=0))
    print("Results:", np.array(evals).mean(axis=0))
    print("Standard Deviation: ", np.array(evals).std(axis=0))
    plt.show()

