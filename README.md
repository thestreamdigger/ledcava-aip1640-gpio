# LEDCAVA-AIP1640

## Overview

Real-time music visualization system for AiP1640-based displays using CAVA audio visualizer data.

## Key Features

- Frequency amplitude-based audio visualization
- Display on AiP1640 with up to 16 columns
- Mirror effects and reverse orientation support
- Customizable JSON configuration
- Simplified integration with moOde audio player

## Technical Challenges with AiP1640

The AiP1640 chip requires:
- Manual GPIO signal manipulation ("bit banging")
- Precise timing requirements
- Incompatibility with standard hardware peripherals

Despite these challenges, we achieved:
- Real-time audio column updates
- Fluid visual effects
- Stable music-synchronized operation

## Hardware Requirements

- Raspberry Pi (tested on Pi 3 and 4)
- AiP1640 driver-based display
- Adequate power supply

### Connections

| AiP1640 | Raspberry Pi |
|---------|--------------|
| VCC     | 5V           |
| GND     | GND (pin 6)  |
| DIO     | GPIO2 (pin 3)|
| CLK     | GPIO3 (pin 5)|

## Installation

1. Install system dependencies:
   ```bash
   sudo apt update
   sudo apt install cava
   ```

2. Clone repository:
   ```bash
   git clone https://github.com/thestreamdigger/ledcava-aip1640.git
   cd ledcava-aip1640
   ```

3. Install Python dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```

## Configuration

Edit `settings.json` to adjust:
- Display brightness
- CAVA bar count
- Refresh rate
- Display orientation

### Display Configuration Options

- **orientation**: Controls the direction of frequency bars
  - `"normal"`: Default order (low frequencies on left, high on right)
  - `"reversed"`: Inverted order (high frequencies on left, low on right)

- **mirror**: Controls the swapping of left/right sides of the display
  - `false`: Default display (no swapping)
  - `true`: Swaps left and right channels of the visualization

## Usage

Start the project:
```bash
python3 main.py
```

## Version Information

- Current version: 0.1.0
- Tested on:
  - moOde 9.2
  - CAVA 0.10.2
  - Raspberry Pi 4 Model B

## License

GNU General Public License v3.0