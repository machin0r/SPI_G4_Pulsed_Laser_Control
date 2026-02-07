# `spi_g4_pulsed_laser_rs`

This repository contains a Rust library for controlling an SPI G4 pulsed laser via a serial (RS232) connection. This project is a rewrite and port of an existing Python library, aiming to leverage Rust's performance, safety, and concurrency features for robust hardware interaction.

## Features

* **Serial Communication:** Establishes and manages RS232 serial communication with the SPI G4 pulsed laser.
* **Commands:** Sends "set" and "get" commands to configure and query laser parameters.
* **Laser State Management:** Maintains an internal representation of the laser's current operating parameters and status.

## Usage

To use this library in your Rust project, add it as a dependency in your `Cargo.toml`:

```toml
[dependencies]
spi_g4_pulsed_laser_rs = { path = "../rust" } # Adjust path as necessary
```

Then, you can interact with the laser:

```rust
use spi_g4_pulsed_laser_rs::{PulsedLaser, PulsedLaserSerial};
use serialport::{Parity, StopBits};
use std::time::Duration;

fn main() -> Result<(), String> {
    let mut laser = PulsedLaser::new();

    // Configure serial connection parameters
    let port_name = "COM1".to_string(); // Replace with your actual serial port
    let baud_rate = 115200;
    let stop_bits = StopBits::One;
    let parity = Parity::None;
    let timeout = Duration::from_secs(1);

    laser.create_serial_connection(
        port_name,
        baud_rate,
        stop_bits,
        parity,
        timeout,
    ).map_err(|e| format!("Failed to open serial connection: {}", e))?;

    println!("Serial connection established.");

    // Set control mode
    laser.set_control_mode(1)?;
    println!("Control mode set to 1.");

    // Get control mode
    let current_mode = laser.get_control_mode()?;
    println!("Current control mode: {}", current_mode);

    // Query alarms
    laser.query_alarms()?;
    if !laser.alarms().is_empty() {
        println!("Active alarms: {:?}", laser.alarms());
    } else {
        println!("No active alarms.");
    }

    laser.close_serial();
    println!("Serial connection closed.");

    Ok(())
}
```

## Project Structure

*   `Cargo.toml`: Project manifest and dependencies.
*   `src/pulsed_laser.rs`: Contains the core logic for `PulsedLaserSerial` (low-level serial handling) and `PulsedLaser` (high-level laser control).

## Dependencies

*   `serialport = "4.8.1"`: For cross-platform serial port access.
