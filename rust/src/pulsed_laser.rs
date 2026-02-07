//! Laser control library for SPI G4 pulsed lasers.
//!
//! This library provides high-level control over pulsed lasers via serial communication.
//! It handles command formatting, error checking, and state management.

use serialport::{Parity, SerialPort, StopBits};
use std::io::Write;
use std::time::Duration;

/// Low-level serial communication handler for pulsed lasers.
///
/// Manages the serial port connection and handles sending/receiving
/// commands with proper formatting and error checking.
pub struct PulsedLaserSerial {
    port: String,
    baud_rate: u32,
    stop_bits: StopBits,
    parity: Parity,
    timeout: Duration,
    connection: Option<Box<dyn SerialPort>>,
}

/// High-level interface for controlling a pulsed laser.
///
/// Maintains the current state of the laser and provides
/// methods for setting and querying laser parameters.
pub struct PulsedLaser {
    control_mode: i8,
    simmer_current: i32,
    active_current: i32,
    waveform: i8,
    prf_hz: i32,
    pulse_burst_length: i32,
    pump_duty: i32,

    alarms: Vec<String>,

    // Monitoring Word Vars
    monitor: bool,
    alarm_state_monitor: bool,
    laser_temp_monitor: bool,
    beam_delivery_temp_monitor: bool,
    system_fault_monitor: bool,
    deactivated_monitor: bool,
    emission_warning_monitor: bool,
    laser_on_monitor: bool,

    laser_temp: f32,
    beam_delivery_temp: f32,
    diode_currents: Vec<f32>,
    operating_hours: i32,
    external_prf: i32,
    extended_diode_currents: Vec<f32>,
    status_word_int: i16,

    serial_number: i16,
    part_number: String,
    vendor_info: String,

    // Status Word Vars
    external_pulse_trigger: bool,
    pilot_laser: bool,
    external_current_control: bool,
    mode: bool,
    pulses: bool,
    enable: bool,

    serial_conn: Option<PulsedLaserSerial>,
}

impl PulsedLaserSerial {
    /// Creates a new serial connection configuration.
    ///
    /// Note: This does not open the connection. Call [`open_connection`]
    /// to establish the connection.
    ///
    /// [`open_connection`]: PulsedLaserSerial::open_connection
    pub fn new(
        port: String,
        baud_rate: u32,
        stop_bits: StopBits,
        parity: Parity,
        timeout: Duration,
    ) -> Self {
        Self {
            port,
            baud_rate,
            stop_bits,
            parity,
            timeout,
            connection: None,
        }
    }

    fn error_check(&self, error_code: &str) -> String {
        match error_code {
            "E5" => "Illegal character",
            "E6" => "Too few characters",
            "E7" => "Illegal password character",
            "E8" => "Incorrect password",
            "E9" => "Insufficient privilege",
            "E10" => "Syntax error: command not recognised",
            "E11" => "'Set' method not available for this command",
            "E12" => "'Get' method not available for this command",
            "E13" => "Parameter error: too many characters",
            "E14" => "Parameter error: not a number",
            "E15" => "Unsupported command in this laser",
            "E16" => "Command not available (e.g. password protected)",
            "E17" => "Too few parameters",
            "E18" => "Too many parameters",
            "E20" => "Parameter out of range",
            "E21" => "Command not executed because an alarm is active",
            "E22" => "Command not executed because of beam delivery alarm(1)",
            "E23" => "Command not executed because of temperature alarm",
            "E24" => "Command not executed because power supplies were not ready",
            "E25" => "Command not executed because Laser is not ready",
            "E26" => "Command not executed because it is not available in the active Laser Mode",
            "E27" => "Command not executed because Laser_Enable input signal is active (high)",
            "E28" => "Command not executed - bit is already set",
            "E29" => "Command not executed - bit is already set",
            "E30" => "Command could not be executed because Laser is enabled",
            "E31" => "Command could not be executed because Laser is not enabled",
            "E32" => "Command could not be executed - parameter under hardware control",
            "E33" => "Command could not be executed - parameter under software control",
            "E34" => "Command could not be executed because pilot Laser is enabled",
            "E35" => "Command could not be executed because pulse repetition rate is out of range",
            _ => "Unknown error code",
        }
        .to_string()
    }

    fn open_connection(&mut self) -> Result<(), serialport::Error> {
        let port = serialport::new(&self.port, self.baud_rate)
            .timeout(self.timeout)
            .stop_bits(self.stop_bits)
            .parity(self.parity)
            .open()?;
        self.connection = Some(port);
        Ok(())
    }

    pub fn close_connection(&mut self) {
        self.connection = None;
    }

    fn write(&mut self, data: &[u8]) -> Result<usize, std::io::Error> {
        match &mut self.connection {
            Some(port) => port.write(data),
            None => Err(std::io::Error::new(
                std::io::ErrorKind::NotConnected,
                "Port not open",
            )),
        }
    }

    fn read(&mut self, buf: &mut [u8]) -> Result<usize, std::io::Error> {
        match &mut self.connection {
            Some(port) => port.read(buf),
            None => Err(std::io::Error::new(
                std::io::ErrorKind::NotConnected,
                "Port not open",
            )),
        }
    }

    fn read_until_delimiter(&mut self) -> Result<String, std::io::Error> {
        let mut buffer = Vec::new();
        let mut byte = [0u8; 1];
        loop {
            self.read(&mut byte)?;

            if byte[0] == b'\n' {
                break;
            }
            if byte[0] != b'\r' {
                buffer.push(byte[0]);
            }
        }
        String::from_utf8(buffer)
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e))
    }

    /// Sends a command to the laser and returns the response.
    ///
    /// # Arguments
    ///
    /// * `command` - The command string (without CR/LF terminators)
    ///
    /// # Returns
    ///
    /// * `Ok(String)` - The laser's response
    /// * `Err(String)` - Error message from laser or I/O error
    ///
    /// # Errors
    ///
    /// Returns an error if:
    /// - Serial port is not open
    /// - Write/read operation fails
    /// - Laser returns an error code (E5-E35)
    pub fn send_command(&mut self, command: String) -> Result<String, String> {
        let command = format!("{}\r\n", command);
        self.write(command.as_bytes())
            .map_err(|e| format!("Write error: {}", e))?;
        let result = self
            .read_until_delimiter()
            .map_err(|e| format!("Read error {}", e))?;

        if result.starts_with('E') {
            Err(format!("{}: {}", result, self.error_check(&result)))
        } else {
            Ok(result)
        }
    }
}

impl PulsedLaser {
    pub fn new() -> Self {
        Self {
            control_mode: 0,
            simmer_current: 0,
            active_current: 0,
            waveform: 0,
            prf_hz: 0,
            pulse_burst_length: 0,
            pump_duty: 0,
            alarms: Vec::new(),
            monitor: false,
            alarm_state_monitor: false,
            laser_temp_monitor: false,
            beam_delivery_temp_monitor: false,
            system_fault_monitor: false,
            deactivated_monitor: false,
            emission_warning_monitor: false,
            laser_on_monitor: false,
            laser_temp: 0.0,
            beam_delivery_temp: 0.0,
            diode_currents: Vec::new(),
            operating_hours: 0,
            external_prf: 0,
            extended_diode_currents: Vec::new(),
            status_word_int: 0,
            serial_number: 0,
            part_number: String::new(),
            vendor_info: String::new(),
            external_pulse_trigger: false,
            pilot_laser: false,
            external_current_control: false,
            mode: false,
            pulses: false,
            enable: false,
            serial_conn: None,
        }
    }

    fn decode_alarms(&self, alarm_code: i32) -> String {
        match alarm_code {
            40..=49 => "System fault: diode driver current".to_string(),
            50..=53 => "System fault: seed laser".to_string(),
            65 => "System fault: beam delivery temperature sensor fault (1)".to_string(),
            66 => "Beam delivery temperature alarm (1)".to_string(),
            80 => "Base plate temperature alarm".to_string(),
            82 => "System fault: base plate temperature sensor fault".to_string(),
            93 => "Power supply alarm. When supply is restored the Laser returns to the STANDBY state".to_string(),
            95 => "Fan alarm. The Laser continues to operate if one fan stalls. The fan noise increases as the  remaining 3 fans increase their speed to compensate. Only cleared by cycling the power supply.".to_string(),
            99 => "Emergency stop alarm Triggered by the Laser_Disable signal".to_string(),
            100.. => "System fault: internal laser fault".to_string(),
            _ => format!("Unknown alarm: {}", alarm_code),
        }
    }

    pub fn create_serial_connection(
        &mut self,
        port: String,
        baud_rate: u32,
        stop_bits: StopBits,
        parity: Parity,
        timeout: Duration,
    ) -> Result<(), serialport::Error> {
        let mut serial = PulsedLaserSerial::new(port, baud_rate, stop_bits, parity, timeout);
        serial.open_connection()?;
        self.serial_conn = Some(serial);
        Ok(())
    }

    pub fn close_serial(&mut self) {
        self.serial_conn = None;
    }

    /// Sets the current control mode of the laser.
    ///
    /// Sets the passed control mode on the laser and updates
    /// the internal state. Modes are 0-7
    ///
    /// # Returns
    ///
    /// # Arguments
    /// * `mode` - The mode to put the laser in
    ///
    /// # Errors
    ///
    /// Returns an error if the serial connection is not established
    /// or if the set command fails.
    pub fn set_control_mode(&mut self, mode: i8) -> Result<(), String> {
        let serial = self
            .serial_conn
            .as_mut()
            .ok_or("Serial connection not established")?;

        let set_command = format!("SM {}", mode);
        serial.send_command(set_command)?;

        self.control_mode = mode;
        Ok(())
    }

    /// Gets the current control mode from the laser.
    ///
    /// Queries the laser for its current control mode and updates
    /// the internal state.
    ///
    /// # Returns
    ///
    /// The current control mode (0-255)
    ///
    /// # Errors
    ///
    /// Returns an error if the serial connection is not established
    /// or if the laser's response cannot be parsed.
    pub fn get_control_mode(&mut self) -> Result<i8, String> {
        let serial = self
            .serial_conn
            .as_mut()
            .ok_or("Serial connection not established")?;

        let result = serial.send_command("GM".to_string())?;

        let mode = result
            .trim()
            .parse::<i8>()
            .map_err(|e| format!("Failed to parse mode: {}", e))?;

        self.control_mode = mode;
        Ok(mode)
    }

    /// Sets a bit in the laser's status word.
    ///
    /// Only bits 0, 1, 3, 4, 8, 9 are writable.
    ///
    /// Updates the internal state.
    ///
    ///
    /// # Returns
    ///
    /// # Arguments
    /// * `bit` - The bit to set
    ///
    /// # Errors
    ///
    /// Returns an error if the serial connection is not established
    /// or if the set command fails.
    pub fn set_status_word(&mut self, bit: u8) -> Result<(), String> {
        if ![0, 1, 3, 4, 8, 9].contains(&bit) {
            return Err(format!("Bit {} is not writable", bit));
        }

        let serial = self
            .serial_conn
            .as_mut()
            .ok_or("Serial connection not established")?;

        let set_command = format!("SS {}", bit);
        serial.send_command(set_command)?;

        match bit {
            0 => self.enable = true,
            1 => self.pulses = true,
            3 => self.mode = true,
            4 => self.external_current_control = true,
            8 => self.pilot_laser = true,
            9 => self.external_pulse_trigger = true,
            _ => unreachable!(),
        }
        Ok(())
    }

    /// Clears a bit in the laser's status word.
    ///
    /// Only bits 0, 1, 3, 4, 8, 9 are writable.
    ///
    /// Updates the internal state.
    ///
    /// # Returns
    ///
    /// # Arguments
    /// * `bit` - The bit to cleat
    ///
    /// # Errors
    ///
    /// Returns an error if the serial connection is not established
    /// or if the set command fails.
    pub fn clear_status_word(&mut self, bit: u8) -> Result<(), String> {
        if ![0, 1, 3, 4, 8, 9].contains(&bit) {
            return Err(format!("Bit {} is not writable", bit));
        }

        let serial = self
            .serial_conn
            .as_mut()
            .ok_or("Serial connection not established")?;

        let set_command = format!("SC {}", bit);
        serial.send_command(set_command)?;

        match bit {
            0 => self.enable = false,
            1 => self.pulses = false,
            3 => self.mode = false,
            4 => self.external_current_control = false,
            8 => self.pilot_laser = false,
            9 => self.external_pulse_trigger = false,
            _ => unreachable!(),
        }
        Ok(())
    }

    fn parse_bit(&self, result: &str, position: usize) -> Result<bool, String> {
        result
            .chars()
            .nth(position)
            .ok_or_else(|| format!("Invalid status word format at position {}", position))?
            .to_digit(10)
            .ok_or_else(|| format!("Invalid digit at position {}", position))
            .map(|digit| digit == 1)
    }

    /// Get the value of the laser's status word.
    ///
    /// Updates the internal state with the different bit meanings
    ///
    /// # Returns
    /// The status bit as a string
    ///
    /// # Errors
    ///
    /// Returns an error if the serial connection is not established
    /// or if the get command fails.
    pub fn get_status_word(&mut self) -> Result<String, String> {
        let serial = self
            .serial_conn
            .as_mut()
            .ok_or("Serial connection not established")?;

        let result = serial.send_command("GS".to_string())?;

        self.enable = self.parse_bit(&result, 0)?;
        self.pulses = self.parse_bit(&result, 3)?;
        self.mode = self.parse_bit(&result, 6)?;
        self.external_current_control = self.parse_bit(&result, 9)?;
        self.pilot_laser = self.parse_bit(&result, 12)?;
        self.external_pulse_trigger = self.parse_bit(&result, 15)?;

        Ok(result)
    }

    /// Set the current control mode on the laser.
    ///
    /// The current is limited from 0-100.
    ///
    /// # Returns
    ///
    /// # Arguments
    /// * `current` - The simmer current value to set in A
    ///
    /// # Errors
    ///
    /// Returns an error if the serial connection is not established
    /// or if the laser's response cannot be parsed.
    pub fn set_simmer_current(&mut self, current: i32) -> Result<(), String> {
        let serial = self
            .serial_conn
            .as_mut()
            .ok_or("Serial connection not established")?;

        let set_command = format!("SH {}", current);
        serial.send_command(set_command)?;

        self.simmer_current = current;

        Ok(())
    }

    /// Gets the simmer current from the laser.
    ///
    /// The current is limited from 0-100.
    ///
    /// # Returns
    ///
    /// The simmer current value.
    ///
    /// # Errors
    ///
    /// Returns an error if the serial connection is not established
    /// or if the set command fails.
    pub fn get_simmer_current(&mut self) -> Result<i32, String> {
        let serial = self
            .serial_conn
            .as_mut()
            .ok_or("Serial connection not established")?;

        let result = serial.send_command("GH".to_string())?;

        let current = result
            .trim()
            .parse::<i32>()
            .map_err(|e| format!("Failed to parse simmer current: {}", e))?;

        self.simmer_current = current;
        Ok(current)
    }

    /// Set the active current for the laser.
    ///
    /// The current is limited from 0-1000.
    /// Active current is proportional to power
    ///
    /// # Returns
    ///
    /// # Arguments
    /// * `current` - The active current value to set
    ///
    /// # Errors
    ///
    /// Returns an error if the serial connection is not established
    /// or if the laser's response cannot be parsed.
    pub fn set_active_current(&mut self, current: i32) -> Result<(), String> {
        let serial = self
            .serial_conn
            .as_mut()
            .ok_or("Serial connection not established")?;

        let set_command = format!("SI {}", current);
        serial.send_command(set_command)?;

        self.active_current = current;

        Ok(())
    }

    /// Gets the active current from the laser.
    ///
    /// The current is limited from 0-1000.
    /// Active current is proportional to power
    ///
    /// # Returns
    ///
    /// The active current value.
    ///
    /// # Errors
    ///
    /// Returns an error if the serial connection is not established
    /// or if the set command fails.
    pub fn get_active_current(&mut self) -> Result<i32, String> {
        let serial = self
            .serial_conn
            .as_mut()
            .ok_or("Serial connection not established")?;

        let result = serial.send_command("GI".to_string())?;

        let current = result
            .trim()
            .parse::<i32>()
            .map_err(|e| format!("Failed to parse active current: {}", e))?;

        self.active_current = current;
        Ok(current)
    }

    /// Sets the pulse waveform to use.
    ///
    /// Waveforms available are 0-31
    ///
    /// # Returns
    ///
    /// # Arguments
    /// * `waveform` - The pulsed waveform
    ///
    /// # Errors
    ///
    /// Returns an error if the serial connection is not established
    /// or if the laser's response cannot be parsed.
    pub fn set_waveform(&mut self, waveform: i8) -> Result<(), String> {
        let serial = self
            .serial_conn
            .as_mut()
            .ok_or("Serial connection not established")?;

        let set_command = format!("SW {}", waveform);
        serial.send_command(set_command)?;

        self.waveform = waveform;

        Ok(())
    }

    /// Gets the active pulse waveform from the laser.
    ///
    /// Waveforms are 0-31
    ///
    /// # Returns
    ///
    /// The active pulse waveform.
    ///
    /// # Errors
    ///
    /// Returns an error if the serial connection is not established
    /// or if the set command fails.
    pub fn get_waveform(&mut self) -> Result<i8, String> {
        let serial = self
            .serial_conn
            .as_mut()
            .ok_or("Serial connection not established")?;

        let result = serial.send_command("GW".to_string())?;

        let waveform = result
            .trim()
            .parse::<i8>()
            .map_err(|e| format!("Failed to parse waveform: {}", e))?;

        self.waveform = waveform;
        Ok(waveform)
    }

    /// Set the Pulse Repetition Frequency (PRF) of the laser.
    ///
    /// The PRF is limited from 1000-1000000 in pulsed mode,
    /// and 100 to 100000 in modulated CW mode.
    ///
    /// Change is implemented when pulses start ('SS 1' sent)
    /// Every time a change is made, 'SS 1' still needs to be sent to update
    ///
    /// # Returns
    ///
    /// # Arguments
    /// * `prf_hz` - The Pulse Repetition Frequency to set
    ///
    /// # Errors
    ///
    /// Returns an error if the serial connection is not established
    /// or if the laser's response cannot be parsed.
    pub fn set_prf(&mut self, prf_hz: i32) -> Result<(), String> {
        let serial = self
            .serial_conn
            .as_mut()
            .ok_or("Serial connection not established")?;

        let set_command = format!("SR {}", prf_hz);
        serial.send_command(set_command)?;

        self.prf_hz = prf_hz;

        Ok(())
    }

    /// Get the Pulse Repetition Frequency (PRF) from the laser.
    ///
    /// The PRF is limited from 1000-1000000 in pulsed mode,
    /// and 100 to 100000 in modulated CW mode.
    ///
    /// # Returns
    ///
    /// # Errors
    ///
    /// Returns an error if the serial connection is not established
    /// or if the laser's response cannot be parsed.
    pub fn get_prf(&mut self) -> Result<i32, String> {
        let serial = self
            .serial_conn
            .as_mut()
            .ok_or("Serial connection not established")?;

        let result = serial.send_command("GR".to_string())?;

        let prf = result
            .trim()
            .parse::<i32>()
            .map_err(|e| format!("Failed to parse PRF: {}", e))?;

        self.prf_hz = prf;
        Ok(prf)
    }

    /// Set the pulse burst length of the laser.
    ///
    /// This is the number of pulses produced
    /// when the Laser_Emission_Gate input = High
    /// The pulse burst length can be 0000000-10000000
    /// =0 is continuous pulsing
    ///
    /// Change is implemented when pulses start ('SS 1' sent)
    /// Every time a change is made, 'SS 1' still needs to be sent to update
    ///
    /// # Returns
    ///
    /// # Arguments
    /// * `pulse_burst` - The pulse burst length to use
    ///
    /// # Errors
    ///
    /// Returns an error if the serial connection is not established
    /// or if the laser's response cannot be parsed.
    pub fn set_pulse_burst_length(&mut self, pulse_burst: i32) -> Result<(), String> {
        let serial = self
            .serial_conn
            .as_mut()
            .ok_or("Serial connection not established")?;

        let set_command = format!("SL {}", pulse_burst);
        serial.send_command(set_command)?;

        self.pulse_burst_length = pulse_burst;

        Ok(())
    }

    /// Get the pulse burst length from the laser.
    ///
    /// This is the number of pulses produced
    /// when the Laser_Emission_Gate input = High
    /// The pulse burst length can be 0000000-10000000
    /// =0 is continuous pulsing
    ///
    /// # Returns
    ///
    /// # Errors
    ///
    /// Returns an error if the serial connection is not established
    /// or if the laser's response cannot be parsed.
    pub fn get_pulse_burst_length(&mut self) -> Result<i32, String> {
        let serial = self
            .serial_conn
            .as_mut()
            .ok_or("Serial connection not established")?;

        let result = serial.send_command("GL".to_string())?;

        let pulse_burst_length = result
            .trim()
            .parse::<i32>()
            .map_err(|e| format!("Failed to parse pulse burst length: {}", e))?;

        self.pulse_burst_length = pulse_burst_length;
        Ok(pulse_burst_length)
    }

    /// Set the pump modulation duty factor when laser in CWM mode
    ///
    /// Pump duty can be 0000-1000
    ///
    /// Change is implemented when pulses start ('SS 1' sent)
    /// Every time a change is made, 'SS 1' still needs to be sent to update
    ///
    /// # Returns
    ///
    /// # Arguments
    /// * `pump_duty` - The pump modulation duy factor
    ///
    /// # Errors
    ///
    /// Returns an error if the serial connection is not established
    /// or if the laser's response cannot be parsed.
    pub fn set_pump_duty(&mut self, pump_duty: i32) -> Result<(), String> {
        let serial = self
            .serial_conn
            .as_mut()
            .ok_or("Serial connection not established")?;

        let set_command = format!("SF {}", pump_duty);
        serial.send_command(set_command)?;

        self.pump_duty = pump_duty;

        Ok(())
    }

    /// Get the pump modulation duty factor when laser in CWM mode
    ///
    /// Pump duty can be 0000-1000
    ///
    /// # Returns
    ///
    /// # Errors
    ///
    /// Returns an error if the serial connection is not established
    /// or if the laser's response cannot be parsed.
    pub fn get_pump_duty(&mut self) -> Result<i32, String> {
        let serial = self
            .serial_conn
            .as_mut()
            .ok_or("Serial connection not established")?;

        let result = serial.send_command("GF".to_string())?;

        let pump_duty = result
            .trim()
            .parse::<i32>()
            .map_err(|e| format!("Failed to parse pump duty: {}", e))?;

        self.pump_duty = pump_duty;
        Ok(pump_duty)
    }

    /// Query the alarms active
    ///
    /// Each alarm is passed to decode_alarms, and the returned error message
    /// is appended to the alarms array
    ///
    /// # Returns
    ///
    /// # Errors
    ///
    /// Returns an error if the serial connection is not established
    /// or if the laser's response cannot be parsed.
    pub fn query_alarms(&mut self) -> Result<(), String> {
        let serial = self
            .serial_conn
            .as_mut()
            .ok_or("Serial connection not established")?;

        let result = serial.send_command("QA".to_string())?;

        self.alarms.clear();

        let new_alarms: Vec<String> = result
            .split(", ")
            .filter(|s| !s.is_empty()) // Handles trailing commas
            .map(|s| {
                s.parse::<i32>()
                    .map(|code| self.decode_alarms(code))
                    .map_err(|e| format!("Failed to parse alarm '{}': {}", s, e))
            })
            .collect::<Result<Vec<_>, _>>()?;

        self.alarms.extend(new_alarms);

        Ok(())
    }

    /// Query the monitoring signals
    ///
    /// Response is a status byte
    ///
    /// # Returns
    ///
    /// # Errors
    ///
    /// Returns an error if the serial connection is not established
    /// or if the laser's response cannot be parsed.
    pub fn query_monitoring_states(&mut self) -> Result<(), String> {
        let serial = self
            .serial_conn
            .as_mut()
            .ok_or("Serial connection not established")?;

        let result = serial.send_command("QD".to_string())?;

        self.monitor = self.parse_bit(&result, 0)?;
        self.alarm_state_monitor = self.parse_bit(&result, 1)?;
        self.laser_temp_monitor = self.parse_bit(&result, 2)?;
        self.beam_delivery_temp_monitor = self.parse_bit(&result, 3)?;
        self.system_fault_monitor = self.parse_bit(&result, 4)?;
        self.deactivated_monitor = self.parse_bit(&result, 5)?;
        self.emission_warning_monitor = self.parse_bit(&result, 6)?;
        self.laser_on_monitor = self.parse_bit(&result, 7)?;

        Ok(())
    }

    /// Query the laser temperature
    ///
    /// Response is "nn.n" from 00.0-85.0 C
    ///
    /// # Returns
    ///
    /// The current laser temperature
    ///
    /// # Errors
    ///
    /// Returns an error if the serial connection is not established
    /// or if the laser's response cannot be parsed.
    pub fn query_laser_temp(&mut self) -> Result<f32, String> {
        let serial = self
            .serial_conn
            .as_mut()
            .ok_or("Serial connection not established")?;

        let result = serial.send_command("QT".to_string())?;

        let laser_temp = result
            .trim()
            .parse::<f32>()
            .map_err(|e| format!("Failed to parse laser temperature: {}", e))?;

        self.laser_temp = laser_temp;
        Ok(laser_temp)
    }

    /// Query the beam delivery temperature
    ///
    /// Response is "nn.n" from 00.0-85.0 C
    ///
    /// # Returns
    ///
    /// The current beam delivery temperature
    ///
    /// # Errors
    ///
    /// Returns an error if the serial connection is not established
    /// or if the laser's response cannot be parsed.
    pub fn query_beam_delivery_temp(&mut self) -> Result<f32, String> {
        let serial = self
            .serial_conn
            .as_mut()
            .ok_or("Serial connection not established")?;

        let result = serial.send_command("QU".to_string())?;

        let beam_delivery_temp = result
            .trim()
            .parse::<f32>()
            .map_err(|e| format!("Failed to parse beam delivery temperature: {}", e))?;

        self.beam_delivery_temp = beam_delivery_temp;
        Ok(beam_delivery_temp)
    }

    /// Query the diode currents of the pump laser driven stages
    ///
    /// Response is 0-20000 mA, there are two values returned.
    ///
    /// # Returns
    ///
    /// The active diode currents
    ///
    /// # Errors
    ///
    /// Returns an error if the serial connection is not established
    /// or if the laser's response cannot be parsed.
    pub fn query_active_diode_currents(&mut self) -> Result<Vec<f32>, String> {
        let serial = self
            .serial_conn
            .as_mut()
            .ok_or("Serial connection not established")?;

        let result = serial.send_command("QI".to_string())?;

        let diode_currents = result
            .split(", ")
            .map(|s| s.trim().parse::<f32>())
            .collect::<Result<Vec<_>, _>>()
            .map_err(|e| format!("Failed to parse the active diode current: {}", e))?;

        self.diode_currents = diode_currents.clone();
        Ok(diode_currents)
    }

    /// Query the operating time of the laser
    ///
    /// Time for which the 24V Logic supply has been applied
    ///
    /// # Returns
    ///
    /// The time the laser has been operating for
    ///
    /// # Errors
    ///
    /// Returns an error if the serial connection is not established
    /// or if the laser's response cannot be parsed.
    pub fn query_operating_hours(&mut self) -> Result<i32, String> {
        let serial = self
            .serial_conn
            .as_mut()
            .ok_or("Serial connection not established")?;

        let result = serial.send_command("QH".to_string())?;

        let operating_hours = result
            .trim()
            .parse::<i32>()
            .map_err(|e| format!("Failed to parse operating hours: {}", e))?;

        self.operating_hours = operating_hours;
        Ok(operating_hours)
    }

    /// Query the external Pulse Repetition Frequency of the laser
    ///
    /// Returns the measured repetition rate in Hz of the external
    /// pulse trigger signal (rising edge to rising edge
    ///
    /// 0-1000000 Hz
    ///
    /// # Returns
    ///
    /// The externally applied PRF
    ///
    /// # Errors
    ///
    /// Returns an error if the serial connection is not established
    /// or if the laser's response cannot be parsed.
    pub fn query_ext_prf(&mut self) -> Result<i32, String> {
        let serial = self
            .serial_conn
            .as_mut()
            .ok_or("Serial connection not established")?;

        let result = serial.send_command("QR".to_string())?;

        let external_prf = result
            .trim()
            .parse::<i32>()
            .map_err(|e| format!("Failed to parse external PRF: {}", e))?;

        self.external_prf = external_prf;
        Ok(external_prf)
    }

    /// Query the extended diode currents of the pump laser driven stages in high power lasers
    ///
    /// Response is 0-20000 mA, there are three or four  values returned.
    ///
    /// # Returns
    ///
    /// The extended diode currents
    ///
    /// # Errors
    ///
    /// Returns an error if the serial connection is not established
    /// or if the laser's response cannot be parsed.
    pub fn query_extended_diode_currents(&mut self) -> Result<Vec<f32>, String> {
        let serial = self
            .serial_conn
            .as_mut()
            .ok_or("Serial connection not established")?;

        let result = serial.send_command("QJ".to_string())?;

        let extended_diode_current = result
            .split(", ")
            .map(|s| s.trim().parse::<f32>())
            .collect::<Result<Vec<_>, _>>()
            .map_err(|e| format!("Failed to parse the extended diode current: {}", e))?;

        self.extended_diode_currents = extended_diode_current.clone();
        Ok(extended_diode_current)
    }

    /// Query the status word as a 16-bit integer
    ///
    /// # Returns
    ///
    /// The status word
    ///
    /// # Errors
    ///
    /// Returns an error if the serial connection is not established
    /// or if the laser's response cannot be parsed.
    pub fn query_status_word_int(&mut self) -> Result<i16, String> {
        let serial = self
            .serial_conn
            .as_mut()
            .ok_or("Serial connection not established")?;

        let result = serial.send_command("QS".to_string())?;

        let status_word_int = result
            .trim()
            .parse::<i16>()
            .map_err(|e| format!("Failed to parse status word: {}", e))?;

        self.status_word_int = status_word_int;
        Ok(status_word_int)
    }

    /// Query the laser serial number
    ///
    /// # Returns
    ///
    /// The serial number
    ///
    /// # Errors
    ///
    /// Returns an error if the serial connection is not established
    /// or if the laser's response cannot be parsed.
    pub fn read_serial_number(&mut self) -> Result<i16, String> {
        let serial = self
            .serial_conn
            .as_mut()
            .ok_or("Serial connection not established")?;

        let result = serial.send_command("RSN".to_string())?;

        let serial_number = result
            .trim()
            .parse::<i16>()
            .map_err(|e| format!("Failed to parse serial number: {}", e))?;

        self.serial_number = serial_number;
        Ok(serial_number)
    }

    /// Query the laser part number
    ///
    /// # Returns
    ///
    /// The part number
    ///
    /// # Errors
    ///
    /// Returns an error if the serial connection is not established
    /// or if the laser's response cannot be parsed.
    pub fn read_part_number(&mut self) -> Result<String, String> {
        let serial = self
            .serial_conn
            .as_mut()
            .ok_or("Serial connection not established")?;

        let part_number = serial.send_command("RPN".to_string())?;

        self.part_number = part_number.clone();
        Ok(part_number)
    }

    /// Query the vendor information
    ///
    /// # Returns
    ///
    /// The vendor information in the form:
    /// FPGA HW Rev: 8.x.x
    /// NIOS-II FW Rev: 8.x.x
    /// Stellaris FW Rev: 0.0.x.x
    /// IP Config: xxx.xxx.xxx.xxx DHCP
    /// Driver FW Rev: x.x
    ///
    /// # Errors
    ///
    /// Returns an error if the serial connection is not established
    /// or if the laser's response cannot be parsed.
    pub fn query_vendor_info(&mut self) -> Result<String, String> {
        let serial = self
            .serial_conn
            .as_mut()
            .ok_or("Serial connection not established")?;

        let vendor_info = serial.send_command("RQC".to_string())?;

        self.vendor_info = vendor_info.clone();
        Ok(vendor_info)
    }

    pub fn initialise_laser(&mut self) -> Result<(), String> {
        self.get_control_mode()?;
        self.get_status_word()?;
        self.get_simmer_current()?;
        self.get_active_current()?;
        self.get_waveform()?;
        self.get_prf()?;
        self.get_pulse_burst_length()?;
        self.get_pump_duty()?;
        self.query_monitoring_states()?;
        self.query_laser_temp()?;
        self.query_beam_delivery_temp()?;
        self.query_active_diode_currents()?;
        self.query_operating_hours()?;
        self.query_ext_prf()?;
        self.query_extended_diode_currents()?;
        self.query_status_word_int()?;
        self.read_serial_number()?;
        self.read_part_number()?;
        self.query_vendor_info()?;
        self.query_alarms()?;

        Ok(())
    }
}

impl Default for PulsedLaser {
    fn default() -> Self {
        Self::new()
    }
}
