"""

This script is used to check the connection to a Keysight instrument.
The script will try to connect to the instrument three times before giving up.
The script will print the error message if the connection fails.

"""
import pyvisa as visa

rm = visa.ResourceManager()
instrument_address = 'USB0::10893::47361::MY61390721::0::INSTR'

for i in range(3):
    try:
        print(f"Attempt {i+1}: Opening the resource.")
        instrument = rm.open_resource(instrument_address)
        print(f"Connected to {instrument.query('*IDN?')}")
        instrument.close()
        print(f"Resource closed on attempt {i+1}.")
    except visa.VisaIOError as e:
        print(f"VISA IO Error on attempt {i+1}: {e}")
    except Exception as e:
        print(f"Error on attempt {i+1}: {e}")
