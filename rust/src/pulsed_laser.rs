use serialport::{Parity, SerialPort, StopBits};
use std::io::Write;
use std::time::Duration;

struct PulsedLaserSerial {
    port: String,
    baud_rate: u32,
    stop_bits: StopBits,
    parity: Parity,
    timeout: Duration,
    connection: Option<Box<dyn SerialPort>>,
}

struct PulsedLaser {
    control_mode: i8,
    simmer_current: i32,
    active_current: i32,
    waveform: i8,
    prf: i32,
    pulse_burst_length: i32,
    pump_duty: i32,

    alarms: Vec<String>,

    monitoring_signals: Vec<String>,

    // Monitoring Word Vars
    monitor: bool,
    alarm_state_monitor: bool,
    laser_temp_monitor: bool,
    beam_delivery_temp_monitor: bool,
    system_fault_monitor: bool,
    deactivated_monitor: bool,
    emission_warning_monitor: bool,
    laser_on_monitor: bool,

    laser_temp: i16,
    beam_delivery_temp: i16,
    diode_currents: String,
    operating_hours: i32,
    external_prf: i32,
    extended_diode_current: String,
    status_word_int: i8,

    serial_number: i16,
    part_numbers: String,
    vendor_info: String,

    error_code: String,

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
    fn new(
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

    fn close_connection(&mut self) {
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

    fn send_command(&mut self, command: String) -> Result<String, String> {
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
    fn new() -> Self {
        Self {
            control_mode: 0,
            simmer_current: 0,
            active_current: 0,
            waveform: 0,
            prf: 0,
            pulse_burst_length: 0,
            pump_duty: 0,
            alarms: Vec::new(),
            monitoring_signals: Vec::new(),
            monitor: false,
            alarm_state_monitor: false,
            laser_temp_monitor: false,
            beam_delivery_temp_monitor: false,
            system_fault_monitor: false,
            deactivated_monitor: false,
            emission_warning_monitor: false,
            laser_on_monitor: false,
            laser_temp: 0,
            beam_delivery_temp: 0,
            diode_currents: String::new(),
            operating_hours: 0,
            external_prf: 0,
            extended_diode_current: String::new(),
            status_word_int: 0,
            serial_number: 0,
            part_numbers: String::new(),
            vendor_info: String::new(),
            error_code: String::new(),
            external_pulse_trigger: false,
            pilot_laser: false,
            external_current_control: false,
            mode: false,
            pulses: false,
            enable: false,
            serial_conn: None,
        }
    }

    fn create_serial_connection(
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

    fn close_serial(&mut self) {
        self.serial_conn = None;
    }

    fn set_control_mode(&mut self, mode: i8) -> Result<(), String> {
        let serial = self
            .serial_conn
            .as_mut()
            .ok_or("Serial connection not established")?;

        let set_command = format!("SM {}", mode);
        serial.send_command(set_command)?;

        self.control_mode = mode;
        Ok(())
    }

    fn get_control_mode(&mut self) -> Result<i8, String> {
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

    fn set_status_word(&mut self, bit: u8) -> Result<(), String> {
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

    fn clear_status_word(&mut self, bit: u8) -> Result<(), String> {
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

    fn get_status_word(&mut self) -> Result<String, String> {
        let serial = self
            .serial_conn
            .as_mut()
            .ok_or("Serial connection not established")?;

        let get_command = format!("GS");
        let result = serial.send_command(get_command)?;

        self.enable = self.parse_bit(&result, 0)?;
        self.pulses = self.parse_bit(&result, 3)?;
        self.mode = self.parse_bit(&result, 6)?;
        self.external_current_control = self.parse_bit(&result, 9)?;
        self.pilot_laser = self.parse_bit(&result, 12)?;
        self.external_pulse_trigger = self.parse_bit(&result, 15)?;

        Ok(result)
    }
}
