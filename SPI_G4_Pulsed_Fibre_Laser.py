import time
import serial


class Pulsed_Laser_Serial:
    def __init__(self, port, baudrate, stopbits, parity, databits, timeout):
        self.port = port
        self.baudrate = baudrate
        self.stopbits = stopbits
        self.parity = parity
        self.databits = databits
        self.timeout = timeout

    def open_connection(self):
        self.serial = serial.Serial(
                            port=self.port,
                            baudrate=self.baudrate,
                            parity=self.parity,
                            stopbits=self.stopbits,
                            bytesize=self.databits,
                            timeout=self.timeout
                        )

    def close_connection(self):
        self.serial.close()

    # Send a "set" command to the laser to change a parameter
    # On a success, will return "True".
    # Result will be empty, as there is no response from laser
    # On a failure, will return "False" and the error code
    def send_set_command(self, setcommand):
        self.serial.write(setcommand + '\r\n')
        time.sleep(0.01)
        result = self.serial.read_until(expected='\r\n')
        if result[0] == 'E':
            error = self.error_check(result)
            success = False
            return success, error
        else:
            success = True
            return success, result

    # Send a "get" command to the laser to read a parameter
    # On a success, will return "True" and the value
    # On a failure, will return "False" and the error code
    def send_get_command(self, getcommand):
        self.serial.write(getcommand + '\r\n')
        time.sleep(0.01)
        result = self.serial.read_until(expected='\r\n')
        if result[0] == 'E':
            error = self.error_check(result)
            success = False
            return success, error
        else:
            success = True
            return success, result

    # This dict stores the RS232 error codes and their meanings
    # It will return the error message associated with the code
    def error_check(self, errorcode):
        errordict = {'E5': "Illegal character",
                     'E6': "Too few characters",
                     'E7': "Illegal password character",
                     'E8': "Incorrect password",
                     'E9': "Insufficient privilege",
                     'E10': "Syntax error: command not recognised",
                     'E11': "'Set' method not available for this command",
                     'E12': "'Get' method not availble for this command",
                     'E13': "Parameter error: too many characters",
                     'E14': "Parameter error: not a number",
                     'E15': "Unsupported command in this laser",
                     'E16': "Command not available (e.g. password protected)",
                     'E17': "Too few parameters",
                     'E18': "Too many parameters",
                     'E20': "Parameter out of range",
                     'E21': "Command not executed because an alarm is active",
                     'E22': "Command not executed because of beam \
                                delivery alarm(1)",
                     'E23': "Command not executed because of \
                                temperature alarm",
                     'E24': "Command not executed because power supplies \
                                were not ready",
                     'E25': "Command not executed because Laser is not ready",
                     'E26': "Command not executed because it is not available \
                                in the active Laser Mode",
                     'E27': "Command not executed because Laser_Enavle input \
                                signal is active (high)",
                     'E28': "Command not executed - bit is already set",
                     'E29': "Command not executed - bit is already set",
                     'E30': "Command could not be executed because \
                                Laser is enabled",
                     'E31': "Command could not be executed because \
                                Laser is not enabled",
                     'E32': "Command could not be executed - parameter \
                                under hardware control",
                     'E33': "Command could not be executed - parameter \
                                under software control",
                     'E34': "Command could not be executed because \
                                pilot Laser is enabled",
                     'E35': "Command could not be executed because \
                                pulse repetition rate is out of range"
                     }
        return errordict[errorcode].value()


class Pulsed_Laser:
    def __init__(self):
        self.controlmode = 0
        self.simmer = 0
        self.activecurrent = 0
        self.waveform = 0
        self.prf = 0
        self.pulseburstlength = 0
        self.pumpduty = 0

        self.alarms = []

        self.monitoringsignals
        self.monitor = False  # bit0, 0=No alarm, 1=Alarm condition
        self.alarmstatemonitor = False  # bit1, 0=No alarm, 1=Alarm condition
        self.lasertempmonitor = False  # bit2, 0=No temp alarm, 1=Temp alarm
        self.beamdeliverytempmon = False  # bit3, 0=No deliv. alarm, 1=Alarm
        self.systemfaultmonitor = False  # bit4, 0=No sys. fault, 1=Sys fault
        self.deactivatedmonitor = False  # bit5, 0=Not deactiv., 1=Deactivated
        self.emissionwarningmon = False  # bit6, 0=PSU not in range, 1=In range
        self.laseronmonitor = False  # bit7, 0=Laser Off, 1=Laser On

        self.lasertemp = 0
        self.beamdeliverytemp = 0
        self.diodecurrents = ""
        self.operatinghours = 0
        self.extprf = 0
        self.extendeddiodecurrent = ""
        self.statuswordint = 0

        self.serialno = 0
        self.partno = ""
        self.vendorinfo = ""

        self.errorcode = ""

        # Status Word Vars
        self.extpulsetrigger = False  # bit9, 0=Internal pulses, 1=External
        self.pilotlaser = False  # bit8, 0=Pilot off, 1=Pilot on
        self.extcurrentcontrol = False  # bit4, 0=Internal current, 1=External
        self.mode = False  # bit3, 0=Pulsed, 1=CW
        self.pulses = False  # bit1, 0=Off, 1=Inernal Pulse On
        self.enable = False  # bit0, 0=Laser off, 1=Laser on

    # Create an instance of the Pulsed_Laser_Serial class to talk to laser
    # Default serial settings are those detailed in the G4 manual
    def create_serial_connection(self, port, baudrate=115200,
                                 stopbits=serial.STOPBITS_ONE,
                                 parity=serial.PARITY_NONE,
                                 databits=serial.EIGHTBITS, timeout=1):
        self.serialconn = Pulsed_Laser_Serial(port, baudrate, stopbits,
                                              parity, databits, timeout)

    # Close the connection with the laser
    def close_serial(self):
        self.serialconn.close_connection()

    # Set the control mode of the laser
    # mode = 0-7
    # To understand the different control modes, refer to laser documentation
    def set_control_mode(self, mode):
        setcommand = f'SM {mode}'
        success, result = self.serialconn.send_set_command(setcommand)
        if success is True:
            self.controlmode = mode
            return
        elif success is False:
            return result

    # Get the current control mode
    # On success return a single digit 0-7
    def get_control_mode(self):
        command = 'GM'
        success, result = (self.serialconn.send_get_command(command))
        if success is True:
            self.controlmode = int(result)
            return result
        elif success is False:
            return result

    # Set the value of the status word bit to 1
    # Only writable bits (0, 1, 3, 4, 8, 9)
    def set_status_word(self, bit):
        command = f'SS {bit}'
        success, result = self.serialconn.send_set_command(command)
        if success is True:
            match bit:
                case 0:
                    self.enable = True
                case 1:
                    self.pulses = True
                case 3:
                    self.mode = True
                case 4:
                    self.extcurrentcontrol = True
                case 8:
                    self.pilotlaser = True
                case 9:
                    self.extpulsetrigger = True
            return
        elif success is False:
            return result

    # Set the value of the status word bit to 0
    # Only writable bits (0, 1, 3, 4, 8, 9)
    def clear_status_word(self, bit):
        command = f'SC {bit}'
        success, result = self.serialconn.send_set_command(command)
        if success is True:
            match bit:
                case 0:
                    self.enable = False
                case 1:
                    self.pulses = False
                case 3:
                    self.mode = False
                case 4:
                    self.extcurrentcontrol = False
                case 8:
                    self.pilotlaser = False
                case 9:
                    self.extpulsetrigger = False
            return
        elif success is False:
            return result

    # Get the current value of each status word bit
    # Result is in the format "n, n, n,"
    # Convert the "n" part of the result to a bool for each parameter
    def get_status_word(self):
        command = f'GS'
        success, result = self.serialconn.send_get_command(command)
        if success is True:
            self.extpulsetrigger = bool(int(result[15]))
            self.pilotlaser = bool(int(result[12]))
            self.extcurrentcontrol = bool(int(result[9]))
            self.mode = bool(int(result[6]))
            self.pulses = bool(int(result[3]))
            self.enable = bool(int(result[0]))
            return
        elif success is False:
            return result

    # Set the simmer current of the laser
    # current can be 000-100
    def set_simmer_current(self, current):
        setcommand = f'SH {current}'
        success, result = self.serialconn.send_set_command(setcommand)
        if success is True:
            self.simmer = current
            return
        elif success is False:
            return result

    # Get the current simmer current
    # On success return "nnn"
    def get_simmer_current(self):
        command = 'GH'
        success, result = (self.serialconn.send_get_command(command))
        if success is True:
            self.simmer = int(result)
            return result
        elif success is False:
            return result

    # Set the active current of the laser
    # current can be 0000-1000
    # Active current is proportional to power
    def set_active_current(self, current):
        setcommand = f'SI {current}'
        success, result = self.serialconn.send_set_command(setcommand)
        if success is True:
            self.activecurrent = current
            return
        elif success is False:
            return result

    # Get the current active current
    # On success return "nnnn"
    # Active current is proportional to power
    def get_active_current(self):
        command = 'GI'
        success, result = (self.serialconn.send_get_command(command))
        if success is True:
            self.activecurrent = int(result)
            return result
        elif success is False:
            return result

    # Set the waveform of the laser
    # waveform can be 00-31
    # Change is implimented when pulses start (SS1)
    def set_waveform(self, waveform):
        setcommand = f'SW {waveform}'
        success, result = self.serialconn.send_set_command(setcommand)
        if success is True:
            self.waveform = waveform
            return
        elif success is False:
            return result

    # Get the waveform of the laser
    # waveformc an be 00-31
    def get_waveform(self):
        command = 'GW'
        success, result = (self.serialconn.send_get_command(command))
        if success is True:
            self.waveform = int(result)
            return result
        elif success is False:
            return result

    # Set the pulse repetition frequency (PRF) of the laser
    # PRF can be 0010000-1000000 Hz in pulsed mode
    # PRF can be 0000100-0100000 Hz in CW mode
    # Change is implimented when pulses start (SS1)
    def set_prf(self, PRF):
        setcommand = f'SR {PRF}'
        success, result = self.serialconn.send_set_command(setcommand)
        if success is True:
            self.prf = PRF
            return
        elif success is False:
            return result

    # Get the pulse repetition frequency (PRF) of the laser
    # PRF can be 0010000-1000000 Hz in pulsed mode
    # PRF can be 0000100-0100000 Hz in CW mode
    def get_prf(self):
        command = 'GR'
        success, result = (self.serialconn.send_get_command(command))
        if success is True:
            self.prf = int(result)
            return result
        elif success is False:
            return result

    # Set the pulse burst length, number of pulses produced
    # When Laser_Emission_Gate input = High
    # Pulse burst length can be 0000000-10000000
    # =0 is continuous pulsing
    # Change is implimented when pulses start (SS1)
    def set_pulse_burst_length(self, pulseburst):
        setcommand = f'SL {pulseburst}'
        success, result = self.serialconn.send_set_command(setcommand)
        if success is True:
            self.pulseburstlength = pulseburst
            return
        elif success is False:
            return result

    # Set the pulse burst length, number of pulses produced
    # When Laser_Emission_Gate input = High
    # Pulse burst length can be 0000000-10000000
    # =0 is continuous pulsing
    def get_pulse_burst_length(self):
        command = 'GL'
        success, result = (self.serialconn.send_get_command(command))
        if success is True:
            self.pulseburstlength = int(result)
            return result
        elif success is False:
            return result

    # Set the pump duty factor
    # pump duty can be 0000-1000
    # Pump modulation duty factor when laser in CWM mode
    # Change is implimented when pulses start (SS1)
    def set_pump_duty(self, pumpduty):
        setcommand = f'SF {pumpduty}'
        success, result = self.serialconn.send_set_command(setcommand)
        if success is True:
            self.pumpduty = pumpduty
            return
        elif success is False:
            return result

    # Set the pump duty factor
    # pump duty can be 0000-1000
    # Response is "nnnnnn"
    # Pump modulation duty factor when laser in CWM mode
    def get_pump_duty(self):
        command = 'GF'
        success, result = (self.serialconn.send_get_command(command))
        if success is True:
            self.pumpduty = int(result)
            return result
        elif success is False:
            return result

    # Query the alarms active
    # Response is "nn, nn, nn..."
    # No response if no alarms
    # The return string is split using ', ' as the deliminator
    # Each alarm is passed to read_alarms(), and the returned error message
    # is appended to the alarms array
    def query_alarms(self):
        command = 'QA'
        success, result = (self.serialconn.send_get_command(command))
        if success is True:
            alarmarray = result.split(', ')
            for alarm in alarmarray:
                self.alarms.append(self.decode_alarms(int(alarm)))
            return result
        elif success is False:
            return result

    def decode_alarms(self, alarmcode):
        alarm = int(alarmcode)
        if 40 <= alarm <= 49:
            return "System fault: diode driver current"
        elif 50 <= alarm <= 53:
            return "System fault: seed laser"
        elif alarm >= 100:
            return "System fault: internal laser fault"
        elif alarm == 65:
            return "System fault: beam delivery temperature sensor fault (1)"
        elif alarm == 82:
            return "System fault: base plate temperature sensor fault"
        elif alarm == 66:
            return "Beam delivery temperature alarm (1)"
        elif alarm == 80:
            return "Base plate temperature alarm"
        elif alarm == 93:
            return "Power supply alarm. When supply is restored the Laser \
                    returns to the STANDBY state"
        elif alarm == 95:
            return "Fan alarm. The Laser continues to operate if one fan \
                    stalls. The fan noise increases as the  remaining 3 fans \
                    increase their speed to compensate. Only cleared by \
                    cycling the power supply."
        elif alarm == 99:
            return "Emergency stop alarm Triggered by the Laser_Disable signal"

    # Query the monitoring group signal states
    # Response is "bbbbbbbb", 00000000-11111111
    def query_monitoring_states(self):
        command = 'QD'
        success, result = self.serialconn.send_get_command(command)
        if success is True:
            self.monitor = bool(result[0])
            self.alarmstatemonitor = bool(result[1])
            self.lasertempmonitor = bool(result[2])
            self.beamdeliverytempmon = bool(result[3])
            self.systemfaultmonitor = bool(result[4])
            self.deactivatedmonitor = bool(result[5])
            self.emissionwarningmon = bool(result[6])
            self.laseronmonitor = bool(result[7])
            return
        elif success is False:
            return result

    # Query the laser temperature
    # Response is "nn.n" from 00.0-85.0 C
    def query_laser_temp(self):
        command = 'QT'
        success, result = (self.serialconn.send_get_command(command))
        if success is True:
            self.lasertemp = int(result)
            return result
        elif success is False:
            return result

    # Query the beam delivery temperature
    # Response is "nn.n" from 00.0-85.0 C
    def query_beam_delivery_temp(self):
        command = 'QU'
        success, result = (self.serialconn.send_get_command(command))
        if success is True:
            self.beamdeliverytemp = int(result)
            return result
        elif success is False:
            return result

    # Query the diode current of the pump laser driver stages (mA)
    # Response is "nnnnn, nnnnn" from 00000-20000
    def query_active_diode_currents(self):
        command = 'QI'
        success, result = (self.serialconn.send_get_command(command))
        if success is True:
            self.diodecurrents = result
            return result
        elif success is False:
            return result

    # Query the operating time of the laser
    # Time for whcih the 24V Logic supply has been applied
    # Response is "nnnnnn" in hours
    def query_operating_hours(self):
        command = 'QH'
        success, result = (self.serialconn.send_get_command(command))
        if success is True:
            self.operatinghours = int(result)
            return result
        elif success is False:
            return result

    # Query the external PRF signal
    # Rising edge to rising edge of the external trigger signal
    # Response is "nnnnnnn", 0000000-1000000 Hz
    def query_ext_prf(self):
        command = 'QR'
        success, result = (self.serialconn.send_get_command(command))
        if success is True:
            self.extprf = int(result)
            return result
        elif success is False:
            return result

    # Query the extended diode currents
    # CUrrent of pump laser diode driver stages in high power lasers
    # Response is "nnnnn, nnnnn, nnnnn, (nnnnn)"
    # 00000-20000 mA
    def query_extended_diode_currents(self):
        command = 'QJ'
        success, result = (self.serialconn.send_get_command(command))
        if success is True:
            self.extendeddiodecurrent = result
            return result
        elif success is False:
            return result

    # Query the status word as a 16-bit integer
    # Response is "nnnnnn", 00000-65535
    def query_status_word_int(self):
        command = 'QS'
        success, result = (self.serialconn.send_get_command(command))
        if success is True:
            self.statuswordint = int(result)
            return result
        elif success is False:
            return result

    # Read the laser serial number
    # Response is "nnnnnn", numerical
    def read_serial_number(self):
        command = 'RSN'
        success, result = (self.serialconn.send_get_command(command))
        if success is True:
            self.serialno = int(result)
            return result
        elif success is False:
            return result

    # Read the part number of the laser
    # Response is "XX-XXXP-X-XX-X-X-X(XX)"
    def read_part_number(self):
        command = 'RPN'
        success, result = (self.serialconn.send_get_command(command))
        if success is True:
            self.partno = result
            return result
        elif success is False:
            return result

    # Query Vendor Information on the laser
    # Response is:
    # FPGA HW Rev: 8.x.x
    # NIOS-II FW Rev: 8.x.x
    # Stellaris FW Rev: 0.0.x.x
    # IP Config: xxx.xxx.xxx.xxx DHCP
    # Driver FW Rev: x.x
    #
    # 'DCHP' may be 'STATIC' depending on IP config
    # x.x.x specifies versions
    def query_vendor_info(self):
        command = 'RQV'
        success, result = (self.serialconn.send_get_command(command))
        if success is True:
            self.vendorinfo = result
            return result
        elif success is False:
            return result

    def initialise_laser(self):
        self.get_control_mode()
        self.get_status_word()
        self.get_simmer_current()
        self.get_active_current()
        self.get_waveform()
        self.get_prf()
        self.get_pulse_burst_length()
        self.get_pump_duty()
        self.query_monitoring_states()
        self.query_laser_temp()
        self.query_beam_delivery_temp()
        self.query_active_diode_currents()
        self.query_operating_hours()
        self.query_ext_prf()
        self.query_extended_diode_currents()
        self.query_status_word_int()
        self.read_serial_number()
        self.read_part_number()
        self.query_vendor_info()

        self.query_alarms()
