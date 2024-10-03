from photodiode import Keysight
from skyhunter import IoptronMount
from twmdb import TwilightMonitorDatabase

from config import port, USBSerial, databaseRoot

import datetime
import numpy as np
import time

class Scheduler:
    def __init__(self, expTime=1, nplc=5, rang0=20e-6, filter='Empty'):
        self.mount = IoptronMount(port)
        self.database = TwilightMonitorDatabase(path=databaseRoot)
        try:
            self.photodiode = Keysight(USBSerial)
            self.is_photodiode_on = True
        except:
            print("Keysight not connected.")
            self.is_photodiode_on = False
            # exit()

        self.filter = filter
        self.set_photodioe_params(expTime=expTime, nplc=nplc, rang0=rang0)

        # # self.photodiode.find_instrument()
    def set_photodioe_params(self, expTime=1, nplc=5, rang0=20e-6):
        self.expTime = expTime
        self.nplc = nplc
        self.nsamples = measure_nsamples(expTime, nplc, freq=50)
        self.rang0 = rang0

    def set_elevation_sweep_params(self, el_steps=6, el_slew_time=1):
        self.el_steps = el_steps
        self.el_slew_time = el_slew_time
    
    def set_azimuth_sweep_params(self, az_steps=6, az_slew_time=1):
        self.az_steps = az_steps
        self.az_slew_time = az_slew_time

    def reset_photodiode(self):
        if self.is_photodiode_on:
            # # set default photodiode values
            self.photodiode.write('SYST:REM')
            self.photodiode.set_mode("CURR")
            self.reset_exposure_time()
            self.photodiode.get_params()
        else:
            print("The photodiode is not connected.")
    
    def reset_exposure_time(self):
        if self.is_photodiode_on:
            self.set_exposure_time(self.expTime)

    def set_exposure_time(self, expTime):
        nsamples = measure_nsamples(expTime, self.nplc, freq=50)

        if self.is_photodiode_on:
            self.photodiode.set_nsamples(nsamples)
            self.photodiode.set_nplc(self.nplc)
        
        self.expTime = expTime

    def get_current_alt_az(self,verbose=False):
        self.mount.get_current_alt_az(verbose)
        return self.mount.altitude_deg, self.mount.azimuth_deg

    def auto_scale_photodiode(self, nplc=1, nsamples=5, verbose=False):
        if self.is_photodiode_on:
            # turn on the annmeter
            self.photodiode.on()

            # reduces nplc and nsamples to speed up the process
            self.photodiode.set_nplc(nplc)
            self.photodiode.set_nsamples(nsamples)

            # auto scale the photodiode
            self.photodiode.auto_scale(rang0=self.rang0, verbose=verbose)

            # set default exposure time
            self.reset_exposure_time()
            print(f"Photodiode Auto Scaled: {self.photodiode.params['rang']:00.0e}")

    def acquire(self, exposureTime=None, flag='false', alt_rank=0, az_rank=0):
        if exposureTime is None: 
            exposureTime = self.expTime
        else:
            self.photodiode.set_acquisition_time(exposureTime)

        keysight_data = self.photodiode.start_measurement()

        alt_current, az_current = self.get_current_alt_az()
        # print(f"Current Altitude: {alt_current}, Current Azimuth: {az_current}")
        print(f"Exposure Time: {exposureTime}")

        # Add exposure to the database
        timestamp = datetime.datetime.utcnow()
        self.database.add_exposure(
            timestamp=timestamp,
            alt=np.round(alt_current,5),
            az=np.round(az_current,5),
            exp_time_cmd = exposureTime,
            exp_time = keysight_data['teff'],
            filter_type=self.filter,  # Assuming filter is Empty
            current_mean=keysight_data['mean'],
            current_std=keysight_data['std'],
            alt_rank=int(alt_rank),
            az_rank=int(az_rank),
            flag=flag
        )
        self.database.save_electrometer_file(self.photodiode.datavector)
        self.database.save()
        print(f"Exposure added to the database at {timestamp}.")

    def acquire_while_slewing_elevation(self, exposureTime, direction='up', az_rank=0):
        # start slewing
        getattr(self.mount, f'slew_{direction}')(is_freerun=True)

        if self.is_photodiode_on:
            # set the scale
            self.photodiode.set_rang('AUTO')
        
            # take data
            self.acquire(exposureTime, flag=True, az_rank=az_rank)

        else:
            print("Photodiode not connected.")
            time.sleep(exposureTime)

        # stop slewing
        self.mount.stop_updown()
        
        # reset the exposure time
        self.reset_exposure_time()

        pass

    def sweep_elevation(self, slewTime, nsteps=6, direction='down', flag='false', az_rank=0):        
        test_start_time = time.time()

        self.mount.set_arrow_speed(9)
        self.mount.get_current_alt_az()
        posInitial = {'alt':self.mount.altitude_deg, 'az':self.mount.azimuth_deg}

        # set the scale
        self.auto_scale_photodiode()

        durations = []
        positions = [self.mount.altitude_deg]

        # corrections = [1.16128198, 0.98503225, 0.9976483, 1.0, 1.0, 1.0]+[1.0]*nsteps
        corrections = [1.0]*nsteps
        for i in range(nsteps):
            print(6*"---------")
            print(f"Step {i+1}/{nsteps}")
            start_time = time.time()

            # start slew
            getattr(self.mount, f'slew_{direction}')(slewTime*corrections[i])
            slew_duration = time.time() - start_time

            # take data
            if self.is_photodiode_on:
                self.acquire(flag=flag, alt_rank=i+1, az_rank=az_rank)
            else:
                time.sleep(self.expTime)

            self.mount.get_current_alt_az()

            if i>=nsteps-1:
                self.auto_scale_photodiode()
            
            duration = time.time() - start_time
            # print("Alt, Az: ", self.mount.altitude_deg, self.mount.azimuth_deg)
            print(f"Slew + Data Duration: {duration:0.2f} seconds")
            print(6*"---------")

            durations.append(slew_duration)
            positions.append(self.mount.altitude_deg)

        test_end_time = time.time()-test_start_time

        # Store Mount Information
        self.add_mount_info('AZ', self.mount.azimuth_deg)
        self.add_mount_info('EL', self.mount.altitude_deg)
        self.add_mount_info('slew_duration', durations)
        self.add_mount_info('slew_angle', positions)
        self.add_mount_info('slew_rate', np.diff(np.array(positions))/(np.array(durations)-self.mount.slew_pause))
        self.add_mount_info('test_duration', test_end_time)
        self.add_mount_info('test_slew_time', slewTime)
        self.add_mount_info('direction', direction)
        self.database.save_mount_file(self.mountDict)
        print(f"Swep completed in {test_end_time:0.02f} seconds")
        return self.mountDict
    
    def sweep_elevation_down_and_come_back(self, az_rank=1):
        """
        Sweep Elevation Down and Come Back

        1) Stop at alt=85.0
        2) Do a series of pointing in elevation for a fixed slew time
        3) Come back to the top while taking data

        """
        if getattr(self, 'el_steps', None) is None: 
            print("Error: set the elevation parameters first")
            return
        
        print("Go to Zero Elevation Point 85.0 degrees")
        self.mount.goto_elevation(85.0, tol=1.0, speed=8, niters=1)

        print("Sweeping Elevation")
        results = self.sweep_elevation(self.el_slew_time, nsteps=self.el_steps, direction='down',
                                        az_rank=az_rank)
        print("Alt Pointings Complted:", results['slew_angle'])            

        print("Slewing back up while taking data")
        duration_up = (85.0-self.mountDict['slew_angle'][-1])/np.median(np.abs(self.mountDict['slew_rate']))
        if self.is_photodiode_on: # there is a delay in the mount response that we subtract
            duration_up-= 2.0 # seconds
        self.acquire_while_slewing_elevation(duration_up, 'up', az_rank=az_rank)

        print("Sweep Elevation Down and Come Back Completed")
        pass

    def map_alt_az(self):
        """
        Map Altitude and Azimuth

        1) Prepare the mount and photodiode
        2) Forward Azimuth Sweep
        3) Go to -180 degree position
        4) Backward Azimuth Sweep
        5) Return to zero position

        The data is saved at each step by the database

        """
        header("Mapping the Altitude and Azimuth")
        # start the timer
        t0 = time.time()

        header("Preparing the Mount and Photodiode")
        self.prepare_map_alt_az()

        # Forward Azimuth Sweep
        header("Starting Forward Azimuth Sweep")
        self.forward_az_alt_swep()
        tforward = (time.time()-t0)/60.
        print(f"Azimuth Forward Sweep Completed in {tforward:2.0f} minutes")

        # Backward Azimuth Sweep
        header("Starting Backward Azimuth Sweep")
        tbacward_initial = time.time()
        self.backward_az_alt_swep()

        tbackward = (time.time()-tbacward_initial)/60.
        print(f"Azimuth Backward Sweep Completed in {tbackward:2.0f} minutes")
        
        # Report duration of the mapping
        ttotal = (time.time()-t0)/60.
        header("Printing Timing Information")
        print(f"Az Forward Sweep Duration: {tforward:0.2f} minute")
        print(f"Az Backward Sweep Duration: {tbackward:0.2f} minute")
        print(f"Total Script Time: {ttotal:0.2f} minute")
        print(6*"---------")

    def forward_az_alt_swep(self):
        """
        Forward Azimuth Sweep

        1) Start at the current position
        2) Sweep down in elevation
        3) Come back to the top while taking data
        4) Go to the next azimuth position (0 to -180)

        """
        # going forward in azimuth
        for i in range(self.az_steps):
            t0 = time.time()
            # print the az cycle header
            header(f"Starting Az Forward Cycle {i+1}/{self.az_steps}")

            self.sweep_elevation_down_and_come_back(i+1)

            # going forward in azimuth
            if i!=self.az_steps-1:
                self.going_forward_az(self.az_slew_time)
            else:
                print("Azimuth Forward Sweep Completed")
                break
            tfinal = time.time()-t0
            
            print(6*"---------")
            print(f"Azimuth Forward Cycle {i+1} completed within {tfinal:0.2f} seconds")
            print("")

    def backward_az_alt_swep(self):
        """
        Backward Azimuth Sweep

        1) Start at -180deg
        2) Sweep down in elevation
        3) Come back to the top while taking data
        4) Go to the previous azimuth position (-180 to 0)
        """
        if getattr(self, 'az_steps', None) is None:
            print("Error: set the azimuth parameters first")
            return
        
        # Make sure the azimuth position is -180 deg
        print("Returning to -180 degree position")
        self.mount.goto_azimuth(-180, tol=0.5, speed=8, niters=3)

        # going forward in bacward
        header("Starting Backward Azimuth Sweep")
        for i in range(self.az_steps):
            t0 = time.time()

            header(f"Starting Az Backward Cycle {i+1}/{self.az_steps}")

            # print the az cycle header
            self.header_map_alt_az(i)

            # Main Sweep Elevation Function
            # 1) stop at alt=85.0
            # 2) do a series of pointing in elevation for a fixed slew time
            # 3) come back to the top while taking data
            self.sweep_elevation_down_and_come_back(i+1)

            # going backward in azimuth
            if i==self.az_steps-1:
                print("Azimuth Backward Sweep Completed")
                print("Returning to zero position")
                self.mount.goto_zero_position()
                break
            else:
                self.going_backward_az(self.az_slew_time)

            tfinal = (time.time()-t0)/60.
            print(6*"---------")
            print(f"Azimuth Backward Cycle {i+1} completed within {tfinal:0.2f} seconds")
            print("")

    def going_forward_az(self, slewTime):
        self.mount.slew_left(slewTime)
        pass
    
    def going_backward_az(self, slewTime):
        self.mount.slew_right(slewTime)
        pass

    def header_map_alt_az(self, i):
        print("")
        print(6*"---------")
        print(f"Az Cycle: {i+1}/{self.az_steps}")
        print("")
        pass

    def prepare_map_alt_az(self):
        """
        Prepare the Mount and Photodiode for the Altitude and Azimuth Mapping

        1) Set the arrow speed to 9
        2) Reset the photodiode
        3) Go to the zero position
        4) Slew down to 1.25 degrees

        """
        self.mount.set_arrow_speed(9)
        self.reset_photodiode()
        self.mount.goto_zero_position()
        self.mount.slew_down(1.25)
        pass

    def add_mount_info(self, col, data):
        # if self.mountDict is not defined, create it
        if not hasattr(self, 'mountDict'): self.mountDict = {}
        self.mountDict[col] = data

def measure_nsamples(expTime, nplc, freq=50):
    return int(expTime*freq/nplc)

def header(text):
    print("")
    print("\t"+text)
    print("")


if __name__ == "__main__":
    scheduler = Scheduler()

    # Set the observation parameters
    scheduler.set_photodioe_params(expTime=1, nplc=5, rang0=20e-6)
    scheduler.set_azimuth_sweep_params(az_steps=6, az_slew_time=1)
    scheduler.set_elevation_sweep_params(el_steps=6, el_slew_time=1)
    
    # Starting the mapping
    scheduler.map_alt_az()
    pass
