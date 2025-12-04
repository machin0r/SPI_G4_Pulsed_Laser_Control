# SPI_G4_Pulsed_Laser_Control

This is a library to interface with an SPI G4 pulsed laser.

This library uses RS232 communication with the laser.

#### To fire the laser, an emission gate signal must be provided. This is a 5V signal applied to either Pin 39 on the 62 way D-sub or J3:2 on the breakout board.
#### This should be connected to a safety interlock to ensure that the laser emission is controlled and in a safe environment

# RS-232 Connection

The RS232 interface on the SPI G4 laser is a simplix interface, therefore the read command must finish before another write command is sent.

The RS232 connection can either be made using the SPI G4 Break-out Board accessory (PT-E01628), or by using the following pins on the 64 way D-sub connector:

RS232_TX - Pin 25

RS232_RX - Pin 26

GND_D - Pins 59, 60
