"""
Twilight Monitor Scheduler


Standard Scheduler Script to map the twilight sky brightness at Cerro Pachon, Chile.

Below you have the description of the main functions of the Scheduler class.

Map Altitude and Azimuth (`map_alt_az`) has the following steps:

1) Prepare the mount and photodiode
2) Forward Azimuth Sweep
3) Go to -180 degree position
4) Backward Azimuth Sweep
5) Return to zero position

The data is saved at each step by the database. 

The Forward Azimuth Sweep (`forward_az_alt_swep`) is done by the following steps:

1) Start at the zero position
2) Sweep down in elevation for a number of elevation pointings
3) Come back to the top while taking data
4) Go to the next azimuth position (0 to -180) for a fixed slew time

The Backward Azimuth Sweep (`backward_az_alt_swep`) is done by the following steps:

1) Start at -180deg azimuth position
2) Sweep down in elevation for a number of elevation pointings
3) Come back to the top while taking data
4) Go to the next azimuth position (-180 to 0) for a fixed slew time

Sweep Elevation Down and Come Back (`sweep_elevation_and_come_back`) is done by the following steps:

1) Stop at alt=85.0
2) Do a series of pointing in elevation for a fixed slew time
3) Come back to the top while taking data

The database is saved in the `DATA` folder with the following format, "YYYYMMDD.csv"

To change the photodiode parameters, use the `set_photodiode_params` method.
To change the azimuth sweep parameters, use the `set_azimuth_sweep_params` method.
To change the elevation sweep parameters, use the `set_elevation_sweep_params` method.

The photodiode connection information needs to be setup in the config.py file
The mount connection information needs to be setup in the config.py file
The database root path is set in the config.py file

"""
from scheduler import Scheduler

s = Scheduler(filter='SDSSg')

# Set the observation parameters
s.set_photodioe_params(expTime=1, nplc=5, rang0=20e-6)
s.set_azimuth_sweep_params(az_steps=7, az_slew_time=7.5)
s.set_elevation_sweep_params(el_steps=5, el_slew_time=2.75)

# Starting the mapping
s.map_alt_az()