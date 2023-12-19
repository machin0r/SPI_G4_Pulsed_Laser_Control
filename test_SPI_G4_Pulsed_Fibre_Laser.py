import pytest
from unittest.mock import Mock, patch
from SPI_G4_Pulsed_Fibre_Laser import Pulsed_Laser, Pulsed_Laser_Serial
import serial

@pytest.fixture
def mock_serial():
    with patch('SPI_G4_Pulsed_Fibre_Laser.serial.Serial') as mock_serial:
        yield mock_serial


def test_create_serial_connection(mock_serial):
    laser = Pulsed_Laser()
    port = '/dev/ttyUSB0'
    laser.create_serial_connection(port)

    mock_serial.assert_called_once_with(port=port, baudrate=115200,
                                        parity=serial.PARITY_NONE,
                                        stopbits=serial.STOPBITS_ONE,
                                        bytesize=serial.EIGHTBITS, timeout=1)
    
def test_close_serial():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.close_serial()

    laser.serialconn.close_connection.assert_called_once()

def test_set_control_mode():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_set_command.return_value = (True, 'Success')

    result = laser.set_control_mode(3)

    assert result is None

def test_set_control_mode_fail():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_set_command.return_value = (False, 'Fail')

    result = laser.set_control_mode(3)

    assert result == 'Fail'

def test_get_control_mode():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_get_command.return_value = (True, '3')

    result = laser.get_control_mode()

    assert result == '3'