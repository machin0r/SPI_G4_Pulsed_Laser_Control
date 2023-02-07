# SPI_G4_Pulsed_Laser_Control

This is a Python library to interface with an SPI G4 pulsed laser.

This library uses RS232 communication with the laser.

# Dependencies

This program requires the use of [pySerial](https://github.com/pyserial/pyserial)

# Usage

1) Create a ``Pulsed_Laser`` object
``` python
import SPI_G4_Pulsed_Fibre_Laser

laser = SPI_G4_Pulsed_Fibre_Laser.Pulsed_Laser()
```
2) The ``Pulsed_Laser`` object opens communications by calling the ``create_serial_connection(port)`` function with the port name as an argument. Baud rate, etc. can also be passed as arguments, but are set at the laser default. This function creates a ``Pulsed_Laser_Serial`` object tied to the ``Pulsed_Laser`` object.

``` python
laser.create_serial_connection('/dev/ttyUSB0')

# The default settings are used as arguments below
laser.create_serial_connection('/dev/ttyUSB0', baudrate=115200,
                                 stopbits=serial.STOPBITS_ONE,
                                 parity=serial.PARITY_NONE,
                                 databits=serial.EIGHTBITS, timeout=2):
```
3) The current laser parameters are requested using ``initialise_laser()``, this should be called after the connection has been made
``` python
laser.initialise_laser()
```

# Example

``` python
import SPI_G4_Pulsed_Fibre_Laser

# Create a Pulsed_Laser object called "laser"
laser = SPI_G4_Pulsed_Fibre_Laser.Pulsed_Laser()

# Open a connection to the G4 pulsed laser connected to port '/dev/ttyUSB0'
laser.create_serial_connection('/dev/ttyUSB0')

# Populate the properties of the Pulsed_Laser object
laser.initialise_laser()

# Set the laser to use waveform 1, PRF 50 kHz, power 50%
laser.set_waveform(1)
laser.set_prf(50000)
laser.set_active_current(500)

# Enable the "Laser is On" bit (bit 0) and go into a simmer state
laser.set_status_word(0)

# Start firing the laser by setting the "Start Pulses" bit to 1
laser.set_status_word(1)

# Changes to laser waveform, PRF, and number of pulses can be queued
# This queues a change to waveform 0, PRF 100 kHz, and will fire 10,000 pulses
laser.set_waveform(0)
laser.set_prf(100000)
laser.set_pulse_burst_length(10000)

# To make the change, se the "Start Pulses" bit to 1 again
laser.set_status_word(1)

# To stop the laser clear the "Laser is On" bit
laser.clear_status_word(0)
```

# RS-232 Connection

The RS232 interface on the SPI G4 laser is a simplix interface, therefore the read command must finish before another write command is sent.

The RS232 connection can either be made using the SPI G4 Break-out Board accessory (PT-E01628), or by using the following pins on the 64 way D-sub connector:

RS232_TX - Pin 25

RS232_RX - Pin 26

GND_D - Pins 59, 60
