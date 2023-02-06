# SPI_G4_Pulsed_Laser_Control

This is a Python library to interface with an SPI G4 pulsed laser.

This library uses RS232 communication with the laser.

# Dependencies

This program requires the use of [pySerial](https://github.com/pyserial/pyserial)

# Usage

1) A ``Pulsed_Laser`` object is created
2) The ``Pulsed_Laser`` object opens communications by calling the ``create_serial_connection(port)`` function with the port name as an argument. Baud rate, etc. can also be passed as arguments, but are set at the laser default. This function creates a ``Pulsed_Laser_Serial`` object tied to the ``Pulsed_Laser`` object.
3) The current laser parameters are requested using ``initialise_laser()``, this should be called after the connection has been made

# RS-232 Connection

The RS232 interface on the SPI G4 laser is a simplix interface, therefore the read command must finish before another write command is sent.

The RS232 connection can either be made using the SPI G4 Break-out Board accessory (PT-E01628), or by using the following pins on the 64 way D-sub connector:

RS232_TX - Pin 25

RS232_RX - Pin 26

GND_D - Pins 59, 60
