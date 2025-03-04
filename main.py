import time
import subprocess
import os
import json
import argparse
from threading import Thread, Event, Lock
from src.aip1640_driver import AIP1640
from src.__version__ import __version__, __author__, __copyright__

BANNER = f"""
LEDCAVA-AIP1640
Version {__version__}
{__copyright__}
"""

class ConfigurableLEDDisplay:
    def __init__(self, settings_path='settings.json'):
        with open(settings_path, 'r') as f:
            self.settings = json.load(f)
        
        self.stop_event = Event()
        self.display = None
        self.cava_data = [0] * self.settings['cava']['bars']
        self.cava_lock = Lock()
        self.cava_process = None
        self.reverse_bits_table = [int(f'{i:08b}'[::-1], 2) for i in range(256)]
        self.column_cache = [
            self.reverse_bits_table[sum(1 << i for i in range(value)) & 0xFF]
            for value in range(9)  # 0-8 são os valores possíveis
        ]

    def create_cava_config(self):
        cava_cfg = self.settings['cava']
        config = f"""
[general]
bars = {cava_cfg['bars']}
framerate = {cava_cfg['framerate']}

[input]
method = {cava_cfg['input']['method']}
source = {cava_cfg['input']['source']}
channels = {cava_cfg['input']['channels']}

[output]
method = {cava_cfg['output']['method']}
raw_target = {cava_cfg['output']['raw_target']}
data_format = {cava_cfg['output']['data_format']}
ascii_max_range = {cava_cfg['output']['ascii_max_range']}

[smoothing]
noise_reduction = {cava_cfg['smoothing']['noise_reduction']}
monstercat = {cava_cfg['smoothing']['monstercat']}
waves = {cava_cfg['smoothing']['waves']}
gravity = {cava_cfg['smoothing']['gravity']}
ignore = {cava_cfg['smoothing']['ignore']}

[eq]
{self.generate_eq_config()}
"""
        config_path = "/tmp/cava_config"
        with open(config_path, 'w') as f:
            f.write(config)
        return config_path

    def generate_eq_config(self):
        eq_bands = self.settings['cava']['eq']
        return '\n'.join([f"{band} = {value}" for band, value in eq_bands.items()])

    def start_cava(self):
        config_path = self.create_cava_config()
        try:
            self.cava_process = subprocess.Popen(
                ['cava', '-p', config_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=1,
                universal_newlines=True
            )
            print("[INFO] CAVA started")
        except Exception as e:
            print(f"[ERROR] CAVA start failed: {e}")
            self.stop_event.set()

    def read_cava_output(self):
        while not self.stop_event.is_set():
            try:
                line = self.cava_process.stdout.readline().strip()
                if line:
                    values = [int(v) for v in line.split(';') if v]
                    if len(values) == self.settings['cava']['bars']:
                        with self.cava_lock:
                            self.cava_data = values
                else:
                    time.sleep(0.01)
            except Exception as e:
                print(f"[ERROR] CAVA read error: {e}")
                time.sleep(0.1)

    def transform_to_bitmap(self, data):
        def create_column(value):
            column = sum(1 << i for i in range(value))
            return self.reverse_bits_table[column & 0xFF]
        
        left_data = data[:8]
        right_data = data[8:]
        
        if self.settings['display'].get('mirror', False):
            left_data, right_data = right_data, left_data
        
        left_bitmap = [self.column_cache[value] for value in left_data]
        right_bitmap = [self.column_cache[value] for value in right_data]
        
        if self.settings['display'].get('orientation', 'normal') == 'reversed':
            left_bitmap.reverse()
            right_bitmap.reverse()
        
        left_rotated = [
            sum((1 << (7 - j)) for j in range(8) if left_bitmap[j] & (1 << i))
            for i in range(8)
        ]
        right_rotated = [
            sum((1 << j) for j in range(8) if right_bitmap[j] & (1 << (7 - i)))
            for i in range(8)
        ]
        
        return left_rotated + right_rotated

    def update_display(self):
        try:
            with self.cava_lock:
                bitmap = self.transform_to_bitmap(self.cava_data)
            self.display.write(bitmap)
        except Exception as e:
            print(f"[ERROR] Display update failed: {e}")

    def run(self):
        print(BANNER)
        print("[INFO] Starting system...")
        
        try:
            self.display = AIP1640(
                clk_pin=self.settings['display']['clock_pin'],
                dio_pin=self.settings['display']['data_pin']
            )
            self.display.set_brightness(self.settings['display']['brightness'])
            self.display.clear()
            print("[INFO] AiP1640 matrix initialized")
        except Exception as e:
            print(f"[ERROR] Display initialization failed: {e}")
            self.stop_event.set()
            return

        self.start_cava()
        cava_thread = Thread(target=self.read_cava_output)
        cava_thread.daemon = True
        cava_thread.start()
        print("[INFO] System ready - Press Ctrl+C to exit")

        try:
            frame_interval = 1.0 / self.settings['cava']['framerate']
            next_frame_time = time.time()
            
            while not self.stop_event.is_set():
                current_time = time.time()
                
                if current_time >= next_frame_time:
                    self.update_display()
                    next_frame_time = current_time + frame_interval
                
                time.sleep(0.001)
                
        except KeyboardInterrupt:
            print("\n[INFO] Shutdown requested")
        finally:
            print("[INFO] Cleaning up...")
            self.stop_event.set()
            if self.cava_process:
                self.cava_process.terminate()
            self.display.clear()
            if os.path.exists("/tmp/cava_config"):
                os.remove("/tmp/cava_config")
            print("[INFO] Shutdown complete")

def main():
    parser = argparse.ArgumentParser(description='LED matrix audio visualizer')
    parser.add_argument('--version', '-v', action='version', version=f'LEDCAVA-AIP1640 {__version__}')
    args = parser.parse_args()
    
    display = ConfigurableLEDDisplay()
    display.run()

if __name__ == '__main__':
    main() 