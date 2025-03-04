from gpiozero import LEDBoard
from time import sleep
from threading import Lock

class AIP1640:
    DATA_COMMAND = 0x40
    FIXED_ADDRESS = 0x44
    ADDRESS_COMMAND = 0xC0
    DISPLAY_COMMAND = 0x80
    DISPLAY_ON = 0x08
    
    MAX_BRIGHTNESS = 7
    MAX_POSITION = 15
    MAX_ROWS = 16

    def __init__(self, clk_pin, dio_pin, brightness=5):
        self.pins = LEDBoard(clk=clk_pin, dio=dio_pin, pwm=False)
        self._brightness = None
        self._last_buffer = [0] * self.MAX_ROWS
        self._lock = Lock()
        
        self.set_brightness(brightness)
        self._initialize_display()

    def _initialize_display(self):
        self._send_command(self.DATA_COMMAND)
        self._set_display_control()

    def _send_command(self, command):
        self._start_transmission()
        self._write_byte(command)
        self._stop_transmission()

    def _start_transmission(self):
        self.pins.dio.on()
        self.pins.clk.on()
        self.pins.dio.off()
        self.pins.clk.off()

    def _stop_transmission(self):
        self.pins.clk.off()
        self.pins.dio.off()
        self.pins.clk.on()
        self.pins.dio.on()

    def _write_byte(self, byte):
        for _ in range(8):
            self.pins.clk.off()
            self.pins.dio.value = (byte & 1)
            byte >>= 1
            self.pins.clk.on()

    def _set_display_control(self):
        if self._brightness is not None:
            command = self.DISPLAY_COMMAND | self.DISPLAY_ON | self._brightness
            self._send_command(command)

    def set_brightness(self, brightness):
        with self._lock:
            if 0 <= brightness <= self.MAX_BRIGHTNESS:
                if brightness != self._brightness:
                    self._brightness = brightness
                    self._set_display_control()
            else:
                raise ValueError(f"Brightness must be between 0 and {self.MAX_BRIGHTNESS}")

    def write(self, data, pos=0):
        with self._lock:
            if not 0 <= pos <= self.MAX_POSITION:
                raise ValueError(f"Position must be between 0 and {self.MAX_POSITION}")
            if len(data) > self.MAX_ROWS:
                raise ValueError(f"Data length exceeds maximum rows ({self.MAX_ROWS})")

            if data == self._last_buffer[pos:pos + len(data)]:
                return

            for i in range(len(data)):
                self._last_buffer[pos + i] = data[i]

            self._send_command(self.FIXED_ADDRESS)
            self._start_transmission()
            self._write_byte(self.ADDRESS_COMMAND | pos)
            for byte in data:
                self._write_byte(byte)
            self._stop_transmission()

            self._set_display_control()

    def clear(self):
        if any(self._last_buffer):
            self.write([0] * self.MAX_ROWS, 0)

    def write_int(self, value, pos=0, length=8):
        data = value.to_bytes(length, 'big')
        self.write(data, pos)

    def write_string(self, string, char_map, pos=0):
        data = [char_map.get(c, 0x00) for c in string[:self.MAX_ROWS]]
        self.write(data, pos)

    def __del__(self):
        try:
            self.clear()
            self.pins.close()
        except:
            pass
