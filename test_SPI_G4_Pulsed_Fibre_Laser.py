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

def test_error_check():
    port = '/dev/ttyUSB0'
    laser_serial = Pulsed_Laser_Serial(port=port, baudrate=115200,
                                        parity=serial.PARITY_NONE,
                                        stopbits=serial.STOPBITS_ONE,
                                        databits=serial.EIGHTBITS, timeout=1)
    result = laser_serial.error_check('E20')
    print(result)

def test_error_check_fail():
    port = '/dev/ttyUSB0'
    laser_serial = Pulsed_Laser_Serial(port=port, baudrate=115200,
                                        parity=serial.PARITY_NONE,
                                        stopbits=serial.STOPBITS_ONE,
                                        databits=serial.EIGHTBITS, timeout=1)
    
    with pytest.raises(KeyError, match=f'The error code fake_key is not in the list of errors'):
        laser_serial.error_check('fake_key')
    
def test_set_control_mode():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_set_command.return_value = (True, 'Success')

    result = laser.set_control_mode(3)

    assert result is None

def test_set_control_mode_fail():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_set_command.return_value = (False, 'Error')

    result = laser.set_control_mode(3)

    assert result == 'Error'

def test_get_control_mode():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_get_command.return_value = (True, '3')

    result = laser.get_control_mode()

    assert result == '3'

def test_get_control_mode_fail():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_get_command.return_value = (False, 'E9: Insufficient privilege')

    result = laser.get_control_mode()
    
    assert result == 'E9: Insufficient privilege'

def test_set_status_word():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_set_command.return_value = (True, 'Success')

    result = laser.set_status_word(0)
    assert result is None and laser.enable is True
    result = laser.set_status_word(1)
    assert result is None and laser.pulses is True
    result = laser.set_status_word(3)
    assert result is None and laser.mode is True
    result = laser.set_status_word(4)
    assert result is None and laser.extcurrentcontrol is True
    result = laser.set_status_word(8)
    assert result is None and laser.pilotlaser is True
    result = laser.set_status_word(9)
    assert result is None and laser.extpulsetrigger is True

def test_set_status_word_fail():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_set_command.return_value = (False, 'Error')

    result = laser.set_status_word(2)
    assert result  == "Error"


def test_clear_status_word():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_set_command.return_value = (True, 'Success')

    result = laser.clear_status_word(0)
    assert result is None and laser.enable is False
    result = laser.clear_status_word(1)
    assert result is None and laser.pulses is False
    result = laser.clear_status_word(3)
    assert result is None and laser.mode is False
    result = laser.clear_status_word(4)
    assert result is None and laser.extcurrentcontrol is False
    result = laser.clear_status_word(8)
    assert result is None and laser.pilotlaser is False
    result = laser.clear_status_word(9)
    assert result is None and laser.extpulsetrigger is False

def test_clear_status_word_fail():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_set_command.return_value = (False, 'Error')

    result = laser.clear_status_word(2)
    assert result  == "Error"

def test_get_status_word():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_get_command.return_value = (True, '0, 1, 0, 1, 0, 1')

    result = laser.get_status_word()

    assert result == '0, 1, 0, 1, 0, 1'
    assert laser.enable is False
    assert laser.pulses is True
    assert laser.mode is False
    assert laser.extcurrentcontrol is True
    assert laser.pilotlaser is False
    assert laser.extpulsetrigger is True

def test_get_status_word_fail():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_get_command.return_value = (False, 'E9: Insufficient privilege')

    result = laser.get_status_word()
    
    assert result == 'E9: Insufficient privilege'

def test_set_simmer_current():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_set_command.return_value = (True, 'Success')

    result = laser.set_simmer_current(90)

    assert result is None and laser.simmer == 90
    
def test_set_simmer_current_fail():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_set_command.return_value = (False, 'E20: Parameter out of range')

    result = laser.set_simmer_current(110)

    assert result == 'E20: Parameter out of range'

def test_get_simmer_current():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_get_command.return_value = (True, '100')

    result = laser.get_simmer_current()

    assert result == '100'
    assert laser.simmer == 100

def test_get_simmer_current_fail():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_get_command.return_value = (False, 'E9: Insufficient privilege')

    result = laser.get_simmer_current()
    
    assert result == 'E9: Insufficient privilege'

def test_set_active_current():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_set_command.return_value = (True, 'Success')

    result = laser.set_active_current(900)

    assert result is None and laser.activecurrent == 900
    
def test_set_active_current_fail():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_set_command.return_value = (False, 'E20: Parameter out of range')

    result = laser.set_active_current(1100)

    assert result == 'E20: Parameter out of range'

def test_get_active_current():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_get_command.return_value = (True, '1000')

    result = laser.get_active_current()

    assert result == '1000'
    assert laser.activecurrent == 1000

def test_get_active_current_fail():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_get_command.return_value = (False, 'E9: Insufficient privilege')

    result = laser.get_active_current()
    
    assert result == 'E9: Insufficient privilege'

def test_set_waveform():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_set_command.return_value = (True, 'Success')

    result = laser.set_waveform(1)

    assert result is None and laser.waveform == 1
    
def test_set_waveform_fail():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_set_command.return_value = (False, 'E20: Parameter out of range')

    result = laser.set_waveform(200)

    assert result == 'E20: Parameter out of range'

def test_get_waveform():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_get_command.return_value = (True, '1')

    result = laser.get_waveform()

    assert result == '1'
    assert laser.waveform == 1

def test_get_waveform_fail():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_get_command.return_value = (False, 'E9: Insufficient privilege')

    result = laser.get_waveform()
    
    assert result == 'E9: Insufficient privilege'

def test_set_prf():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_set_command.return_value = (True, 'Success')

    result = laser.set_prf(1000)

    assert result is None and laser.prf == 1000
    
def test_set_prf_fail():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_set_command.return_value = (False, 'E35: Command could not be executed because \
                                pulse repetition rate is out of range')

    result = laser.set_prf(2000000)

    assert result == 'E35: Command could not be executed because \
                                pulse repetition rate is out of range'

def test_get_prf():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_get_command.return_value = (True, '10000')

    result = laser.get_prf()

    assert result == '10000'
    assert laser.prf == 10000

def test_get_prf_fail():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_get_command.return_value = (False, 'E9: Insufficient privilege')

    result = laser.get_prf()
    
    assert result == 'E9: Insufficient privilege'

def test_set_pulse_burst_length():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_set_command.return_value = (True, 'Success')

    result = laser.set_pulse_burst_length(1000)

    assert result is None and laser.pulseburstlength == 1000
    
def test_set_pulse_burst_length_fail():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_set_command.return_value = (False, 'E20: Parameter out of range')

    result = laser.set_pulse_burst_length(20000000)

    assert result == 'E20: Parameter out of range'

def test_get_pulse_burst_length():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_get_command.return_value = (True, '10000')

    result = laser.get_pulse_burst_length()

    assert result == '10000'
    assert laser.pulseburstlength == 10000

def test_get_pulse_burst_length_fail():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_get_command.return_value = (False, 'E9: Insufficient privilege')

    result = laser.get_pulse_burst_length()
    
    assert result == 'E9: Insufficient privilege'

def test_set_pump_duty():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_set_command.return_value = (True, 'Success')

    result = laser.set_pump_duty(500)

    assert result is None and laser.pumpduty == 500
    
def test_set_pump_duty_fail():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_set_command.return_value = (False, 'E20: Parameter out of range')

    result = laser.set_pump_duty(2000)

    assert result == 'E20: Parameter out of range'

def test_get_pump_duty():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_get_command.return_value = (True, '200')

    result = laser.get_pump_duty()

    assert result == '200'
    assert laser.pumpduty == 200

def test_get_pump_duty_fail():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_get_command.return_value = (False, 'E9: Insufficient privilege')

    result = laser.get_pump_duty()
    
    assert result == 'E9: Insufficient privilege'

def test_query_alarms():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_get_command.return_value = (True, '40, 50, 65, 66, 80, 82, 93, 95, 99, 105')

    result = laser.query_alarms()

    assert result == '40, 50, 65, 66, 80, 82, 93, 95, 99, 105'
    assert laser.alarms == ["System fault: diode driver current",
                            "System fault: seed laser",
                            "System fault: beam delivery temperature sensor fault (1)",
                            "Beam delivery temperature alarm (1)",
                            "Base plate temperature alarm",
                            "System fault: base plate temperature sensor fault",
                            "Power supply alarm. When supply is restored the Laser returns to the STANDBY state",
                            "Fan alarm. The Laser continues to operate if one fan stalls. The fan noise increases as the  remaining 3 fans increase their speed to compensate. Only cleared by cycling the power supply.",
                            "Emergency stop alarm Triggered by the Laser_Disable signal",
                            "System fault: internal laser fault"]
    
def test_query_all_alarms():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_get_command.return_value = (True, '40, 50, 80')

    result = laser.query_alarms()

    assert result == '40, 50, 80'
    assert laser.alarms == ['System fault: diode driver current',
                            'System fault: seed laser',
                            'Base plate temperature alarm']
    
def test_query_alarms_fail():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_get_command.return_value = (False, 'E9: Insufficient privilege')

    result = laser.query_alarms()
    
    assert result == 'E9: Insufficient privilege'
    
def test_query_monitoring_states():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_get_command.return_value = (True, '01010101')

    result = laser.query_monitoring_states()

    assert result is None
    assert laser.monitor is False
    assert laser.alarmstatemonitor is True
    assert laser.lasertempmonitor is False
    assert laser.beamdeliverytempmon is True
    assert laser.systemfaultmonitor is False
    assert laser.deactivatedmonitor is True
    assert laser.emissionwarningmon is False
    assert laser.laseronmonitor is True

def test_query_monitoring_states_fail():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_get_command.return_value = (False, 'E9: Insufficient privilege')

    result = laser.query_monitoring_states()
    
    assert result == 'E9: Insufficient privilege'

def test_query_laser_temp():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_get_command.return_value = (True, '76.4')

    result = laser.query_laser_temp()

    assert result is '76.4'
    assert laser.lasertemp == 76.4

def test_query_laser_temp_fail():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_get_command.return_value = (False, 'E9: Insufficient privilege')

    result = laser.query_laser_temp()
    
    assert result == 'E9: Insufficient privilege'

def test_query_beam_delivery_temp():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_get_command.return_value = (True, '56.4')

    result = laser.query_beam_delivery_temp()

    assert result is '56.4'
    assert laser.beamdeliverytemp == 56.4

def test_query_beam_delivery_fail():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_get_command.return_value = (False, 'E9: Insufficient privilege')

    result = laser.query_beam_delivery_temp()
    
    assert result == 'E9: Insufficient privilege'

def test_query_active_diode_currents():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_get_command.return_value = (True, '10000, 15000')

    result = laser.query_active_diode_currents()

    assert result is '10000, 15000'
    assert laser.diodecurrents == '10000, 15000'

def test_query_active_diode_fail():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_get_command.return_value = (False, 'E9: Insufficient privilege')

    result = laser.query_active_diode_currents()
    
    assert result == 'E9: Insufficient privilege'

def test_query_operating_hours():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_get_command.return_value = (True, '000100')

    result = laser.query_operating_hours()

    assert result is '000100'
    assert laser.operatinghours == 100

def test_query_operating_hours_fail():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_get_command.return_value = (False, 'E9: Insufficient privilege')

    result = laser.query_operating_hours()
    
    assert result == 'E9: Insufficient privilege'

def test_query_ext_prf():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_get_command.return_value = (True, '0034567')

    result = laser.query_ext_prf()

    assert result is '0034567'
    assert laser.extprf == 34567

def test_query_ext_prf_fail():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_get_command.return_value = (False, 'E9: Insufficient privilege')

    result = laser.query_ext_prf()
    
    assert result == 'E9: Insufficient privilege'

def test_query_extended_diode_currents():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_get_command.return_value = (True, '01000, 20000, 00030, (12032)')

    result = laser.query_extended_diode_currents()

    assert result is '01000, 20000, 00030, (12032)'
    assert laser.extendeddiodecurrent == '01000, 20000, 00030, (12032)'

def test_query_extended_diode_currents_fail():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_get_command.return_value = (False, 'E9: Insufficient privilege')

    result = laser.query_extended_diode_currents()
    
    assert result == 'E9: Insufficient privilege'

def test_query_status_word_int():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_get_command.return_value = (True, '65535')

    result = laser.query_status_word_int()

    assert result is '65535'
    assert laser.statuswordint == 65535

def test_query_status_word_int_fail():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_get_command.return_value = (False, 'E9: Insufficient privilege')

    result = laser.query_status_word_int()
    
    assert result == 'E9: Insufficient privilege'

def test_read_serial_number():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_get_command.return_value = (True, '123213')

    result = laser.read_serial_number()

    assert result is '123213'
    assert laser.serialno == 123213

def test_read_serial_number_fail():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_get_command.return_value = (False, 'E9: Insufficient privilege')

    result = laser.read_serial_number()
    
    assert result == 'E9: Insufficient privilege'

def test_read_part_number():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_get_command.return_value = (True, 'XX-XXXP-X-XX-X-X-X(XX)')

    result = laser.read_part_number()

    assert result is 'XX-XXXP-X-XX-X-X-X(XX)'
    assert laser.partno == 'XX-XXXP-X-XX-X-X-X(XX)'

def test_read_part_number_fail():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_get_command.return_value = (False, 'E9: Insufficient privilege')

    result = laser.read_part_number()
    
    assert result == 'E9: Insufficient privilege'

def test_query_vendor_info():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_get_command.return_value = (True,
                                                     '''FPGA HW Rev: 8.x.x
    NIOS-II FW Rev: 8.x.x
    Stellaris FW Rev: 0.0.x.x
    IP Config: xxx.xxx.xxx.xxx DHCP
    Driver FW Rev: x.x''')

    result = laser.query_vendor_info()

    assert result is '''FPGA HW Rev: 8.x.x
    NIOS-II FW Rev: 8.x.x
    Stellaris FW Rev: 0.0.x.x
    IP Config: xxx.xxx.xxx.xxx DHCP
    Driver FW Rev: x.x'''
    assert laser.vendorinfo == '''FPGA HW Rev: 8.x.x
    NIOS-II FW Rev: 8.x.x
    Stellaris FW Rev: 0.0.x.x
    IP Config: xxx.xxx.xxx.xxx DHCP
    Driver FW Rev: x.x'''

def test_query_vendor_info_fail():
    laser = Pulsed_Laser()
    laser.serialconn = Mock()
    laser.serialconn.send_get_command.return_value = (False, 'E9: Insufficient privilege')

    result = laser.query_vendor_info()
    
    assert result == 'E9: Insufficient privilege'