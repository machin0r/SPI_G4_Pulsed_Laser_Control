import asyncio
from concurrent.futures import ThreadPoolExecutor
import serial
from SPI_G4_Pulsed_Fibre_Laser import Pulsed_Laser


class AsyncPulsedLaser:
    """An asynchronous wrapper for the Pulsed_Laser class.

    This class provides an async interface to the synchronous Pulsed_Laser,
    allowing it to be used in asyncio applications without blocking the event loop.
    """

    def __init__(self):
        self._laser = Pulsed_Laser()
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._loop = asyncio.get_event_loop()

    # Connection methods
    async def create_serial_connection(
        self,
        port: str,
        baudrate: int = 115200,
        stopbits: int = serial.STOPBITS_ONE,
        parity: str = serial.PARITY_NONE,
        databits: int = serial.EIGHTBITS,
        timeout: int = 1,
    ) -> None:
        """Asynchronously create an instance of the Pulsed_Laser_Serial class to talk to laser
        Default serial settings are those detailed in the G4 manual"""
        return await self._loop.run_in_executor(
            self._executor,
            self._laser.create_serial_connection,
            port,
            baudrate,
            stopbits,
            parity,
            databits,
            timeout,
        )

    async def close_serial(self) -> None:
        """Asynchronously close the connection with the laser"""
        return await self._loop.run_in_executor(
            self._executor, self._laser.close_serial
        )

    # Set/Get methods
    async def set_control_mode(self, mode: int) -> None | str:
        """Asynchronously set the control mode of the laser
        mode = 0-7
        To understand the different control modes, refer to laser documentation"""
        return await self._loop.run_in_executor(
            self._executor, self._laser.set_control_mode, mode
        )

    async def get_control_mode(self) -> None | str:
        """Asynchronously get the current control mode
        On success return a single digit 0-7"""
        return await self._loop.run_in_executor(
            self._executor, self._laser.get_control_mode
        )

    async def set_status_word(self, bit: int) -> None | str:
        """Asynchronously set the value of the status word bit to 1
        Only writable bits (0, 1, 3, 4, 8, 9)"""
        return await self._loop.run_in_executor(
            self._executor, self._laser.set_status_word, bit
        )

    async def clear_status_word(self, bit: int) -> None | str:
        """Asynchronously set the value of the status word bit to 0
        Only writable bits (0, 1, 3, 4, 8, 9)"""
        return await self._loop.run_in_executor(
            self._executor, self._laser.clear_status_word, bit
        )

    async def get_status_word(self) -> None | str:
        """Asynchronously get the current value of each status word bit
        Result is in the format "n, n, n,"
        Convert the "n" part of the result to a bool for each parameter"""
        return await self._loop.run_in_executor(
            self._executor, self._laser.get_status_word
        )

    async def set_simmer_current(self, current: int) -> None | str:
        """Asynchronously set the simmer current of the laser
        current can be 000-100"""
        return await self._loop.run_in_executor(
            self._executor, self._laser.set_simmer_current, current
        )

    async def get_simmer_current(self) -> None | str:
        """Asynchronously get the current simmer current
        On success return "nnn" where nnn is the current"""
        return await self._loop.run_in_executor(
            self._executor, self._laser.get_simmer_current
        )

    async def set_active_current(self, current: int) -> None | str:
        """Asynchronously set the active current of the laser
        current can be 0000-1000
        Active current is proportional to power"""
        return await self._loop.run_in_executor(
            self._executor, self._laser.set_active_current, current
        )

    async def get_active_current(self) -> None | str:
        """Asynchronously get the current active current
        On success return "nnnn" where nnnn is the current
        Active current is proportional to power"""
        return await self._loop.run_in_executor(
            self._executor, self._laser.get_active_current
        )

    async def set_waveform(self, waveform: int) -> None | str:
        """Asynchronously set the waveform of the laser
        waveform can be 00-31
        Change is implimented when pulses start ('SS 1' sent)
        Every time a change is made, 'SS 1' still needs to be sent to update"""
        return await self._loop.run_in_executor(
            self._executor, self._laser.set_waveform, waveform
        )

    async def get_waveform(self) -> None | str:
        """Asynchronously get the waveform of the laser
        waveform can be 00-31"""
        return await self._loop.run_in_executor(
            self._executor, self._laser.get_waveform
        )

    async def set_prf(self, prf: int) -> None | str:
        """Asynchronously set the pulse repetition frequency (PRF) of the laser
        PRF can be 0010000-1000000 Hz in pulsed mode
        PRF can be 0000100-0100000 Hz in CW mode
        Change is implimented when pulses start ('SS 1' sent)
        Every time a change is made, 'SS 1' still needs to be sent to update"""
        return await self._loop.run_in_executor(
            self._executor, self._laser.set_prf, prf
        )

    async def get_prf(self) -> None | str:
        """Asynchronously get the pulse repetition frequency (PRF) of the laser
        PRF can be 0010000-1000000 Hz in pulsed mode
        PRF can be 0000100-0100000 Hz in CW mode"""
        return await self._loop.run_in_executor(self._executor, self._laser.get_prf)

    async def set_pulse_burst_length(self, pulseburst: int) -> None | str:
        """Asynchronously set the pulse burst length, number of pulses produced
        When Laser_Emission_Gate input = High
        Pulse burst length can be 0000000-10000000
        =0 is continuous pulsing
        Change is implimented when pulses start ('SS 1' sent)
        Every time a change is made, 'SS 1' still needs to be sent to update"""
        return await self._loop.run_in_executor(
            self._executor, self._laser.set_pulse_burst_length, pulseburst
        )

    async def get_pulse_burst_length(self) -> None | str:
        """Asynchronously set the pulse burst length, number of pulses produced
        When Laser_Emission_Gate input = High
        Pulse burst length can be 0000000-10000000
        =0 is continuous pulsing"""
        return await self._loop.run_in_executor(
            self._executor, self._laser.get_pulse_burst_length
        )

    async def set_pump_duty(self, pumpduty: int) -> None | str:
        """Asynchronously set the pump duty factor
        pump duty can be 0000-1000
        Pump modulation duty factor when laser in CWM mode
        Change is implimented when pulses start ('SS 1' sent)
        Every time a change is made, 'SS 1' still needs to be sent to update"""
        return await self._loop.run_in_executor(
            self._executor, self._laser.set_pump_duty, pumpduty
        )

    async def get_pump_duty(self) -> None | str:
        """Asynchronously set the pump duty factor
        pump duty can be 0000-1000
        Response is "nnnnnn"
        Pump modulation duty factor when laser in CWM mode"""
        return await self._loop.run_in_executor(
            self._executor, self._laser.get_pump_duty
        )

    # Query methods
    async def query_alarms(self) -> None | str:
        """Asynchronously query the alarms active
        Response is "nn, nn, nn..."
        No response if no alarms
        The return string is split using ', ' as the deliminator
        Each alarm is passed to read_alarms(), and the returned error message
        is appended to the alarms array"""
        return await self._loop.run_in_executor(
            self._executor, self._laser.query_alarms
        )

    async def query_monitoring_states(self) -> None | str:
        """Asynchronously query the monitoring group signal states
        Response is "bbbbbbbb", 00000000-11111111"""
        return await self._loop.run_in_executor(
            self._executor, self._laser.query_monitoring_states
        )

    async def query_laser_temp(self) -> None | str:
        """Asynchronously query the laser temperature
        Response is "nn.n" from 00.0-85.0 C"""
        return await self._loop.run_in_executor(
            self._executor, self._laser.query_laser_temp
        )

    async def query_beam_delivery_temp(self) -> None | str:
        """Asynchronously query the beam delivery temperature
        Response is "nn.n" from 00.0-85.0 C"""
        return await self._loop.run_in_executor(
            self._executor, self._laser.query_beam_delivery_temp
        )

    async def query_active_diode_currents(self) -> None | str:
        """Asynchronously query the diode current of the pump laser driver stages (mA)
        Response is "nnnnn, nnnnn" from 00000-20000"""
        return await self._loop.run_in_executor(
            self._executor, self._laser.query_active_diode_currents
        )

    async def query_operating_hours(self) -> None | str:
        """Asynchronously query the operating time of the laser
        Time for which the 24V Logic supply has been applied
        Response is "nnnnnn" in hours"""
        return await self._loop.run_in_executor(
            self._executor, self._laser.query_operating_hours
        )

    async def query_ext_prf(self) -> None | str:
        """Asynchronously query the external PRF signal
        Rising edge to rising edge of the external trigger signal
        Response is "nnnnnnn", 0000000-1000000 Hz"""
        return await self._loop.run_in_executor(
            self._executor, self._laser.query_ext_prf
        )

    async def query_extended_diode_currents(self) -> None | str:
        """Asynchronously query the extended diode currents
        Current of pump laser diode driver stages in high power lasers
        Response is "nnnnn, nnnnn, nnnnn, (nnnnn)"
        00000-20000 mA"""
        return await self._loop.run_in_executor(
            self._executor, self._laser.query_extended_diode_currents
        )

    async def query_status_word_int(self) -> None | str:
        """Asynchronously query the status word as a 16-bit integer
        Response is "nnnnnn", 00000-65535"""
        return await self._loop.run_in_executor(
            self._executor, self._laser.query_status_word_int
        )

    # Read methods
    async def read_serial_number(self) -> None | str:
        """Asynchronously read the laser serial number
        Response is "nnnnnn", numerical"""
        return await self._loop.run_in_executor(
            self._executor, self._laser.read_serial_number
        )

    async def read_part_number(self) -> None | str:
        """Asynchronously read the part number of the laser
        Response is "XX-XXXP-X-XX-X-X-X(XX)"""
        return await self._loop.run_in_executor(
            self._executor, self._laser.read_part_number
        )

    async def query_vendor_info(self) -> None | str:
        """Asynchronously query Vendor Information on the laser
        Response is:
        FPGA HW Rev: 8.x.x
        NIOS-II FW Rev: 8.x.x
        Stellaris FW Rev: 0.0.x.x
        IP Config: xxx.xxx.xxx.xxx DHCP
        Driver FW Rev: x.x

        'DCHP' may be 'STATIC' depending on IP config
        x.x.x specifies versions"""
        return await self._loop.run_in_executor(
            self._executor, self._laser.query_vendor_info
        )

    # Initialisation
    async def initialise_laser(self) -> None:
        """Asynchronously runs through all the functions that request information off the laser
        to populate the information about it"""
        return await self._loop.run_in_executor(
            self._executor, self._laser.initialise_laser
        )
