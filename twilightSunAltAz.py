"""
This script calculates the AltAz position of the Sun at Cerro Pachon

It prints the following information:
- The current UTC date
- The local time of the next civic/nautical/astronomical twilight
- The Sun alt and az at the time of the civic/nautical/astronomical twilight

"""
import ephem
import datetime
import numpy as np
from datetime import timedelta
import pytz

# Cerro Pachon coordinates
latitude = '-30:15:06.37'
longitude = '-70:44:17.50'
elevation = 2552.0
utc_date = datetime.datetime.utcnow()
chile_tz = pytz.timezone('America/Santiago')

# Determine altitude and azimuth of the target
def get_sun_alt_az(telescope, verbose=False):
    sun = ephem.Sun()
    sun.compute(telescope)
    alt_target = float(repr(sun.alt)) * (360/(2*np.pi))
    az_target = float(repr(sun.az)) * (360/(2*np.pi))
    if verbose:
        print("Altitude / Azimuth of target: %.5f / %.5f"%(alt_target,az_target))
    return alt_target, az_target

# Convert UTC to Chilean time
def convert_to_chile_time(utc_time):
    utc_zone = pytz.utc
    utc_time = utc_zone.localize(utc_time)
    chile_time = utc_time.astimezone(chile_tz)
    return chile_time

def setPachon(date):
    telescope = ephem.Observer()
    telescope.lat = latitude
    telescope.long = longitude
    telescope.elevation = elevation
    telescope.date = date
    return telescope

# Establish the location of the telescope
telescope = setPachon(utc_date)

# Determine the position of the Sun
sun = ephem.Sun()
sun.compute()
# print("RA / DEC of the Sun: %.5f / %.5f"%(sun.ra,sun.dec))
twilight_date =  telescope.next_setting(sun).datetime()
twilight_date_local = convert_to_chile_time(twilight_date)

# print("Civic Twilight Local Time: ",twilight_date_local)
# get_sun_alt_az(setPachon(twilight_date), verbose=True)

# Find the azimuth and altitude of the Sun over time
nsteps = 120
dt = 1 # minutes
times = np.linspace(0, nsteps*dt, nsteps) - 20
timeSun = np.array([twilight_date+timedelta(minutes=t) for t in times])

# Initialize arrays to store the Sun's position
altSun = np.zeros(nsteps)
azSun = np.zeros(nsteps)
for i in range(nsteps):
    # Set the new date in ephem format
    _telescope = setPachon(timeSun[i])
    
    # Get Sun's position
    alt, az = get_sun_alt_az(_telescope)
    altSun[i] = alt
    azSun[i] = az

from scipy.interpolate import interp1d
func = interp1d(altSun, times)
astronomical_twilight = twilight_date+ timedelta(minutes=float(func(-15.0)))
astronomical_twilight_local = convert_to_chile_time(astronomical_twilight)

astronomical_twilight_10 = twilight_date+ timedelta(minutes=float(func(-10.0)))
astronomical_twilight_10_local = convert_to_chile_time(astronomical_twilight_10)

astronomical_twilight_12 = twilight_date+ timedelta(minutes=float(func(-12.0)))
astronomical_twilight_12_local = convert_to_chile_time(astronomical_twilight_12)

civic_twilight = twilight_date+timedelta(minutes=float(func(0)))
civic_twilight_local = convert_to_chile_time(civic_twilight)

print(5*"-------")
print("Finding the position of the Sun")
print("UTC Date Now: ",utc_date)

print('Civic Twilight Local Time: ', civic_twilight_local)
alt_as, az_as = get_sun_alt_az(setPachon(civic_twilight_local), verbose=True)

print('Nautical Twilight -10 Local Time: ', astronomical_twilight_10_local)
alt_10, az_10 = get_sun_alt_az(setPachon(astronomical_twilight_10), verbose=True)

print('Nautical Twilight -12 Local Time: ', astronomical_twilight_12_local)
alt_12, az_12 = get_sun_alt_az(setPachon(astronomical_twilight_12), verbose=True)

print('Astronomical Twilight Local Time: ', astronomical_twilight_local)
alt, az = get_sun_alt_az(setPachon(astronomical_twilight), verbose=True)

print(5*"-------")