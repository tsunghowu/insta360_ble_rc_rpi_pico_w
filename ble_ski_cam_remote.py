from machine import Pin
import time
import asyncio
import bluetooth
from bluetooth import BLE, FLAG_READ, FLAG_WRITE, FLAG_NOTIFY, FLAG_INDICATE
from ble_simple_peripheral import BLESimplePeripheral

# Constants
_360_SERIAL_NUMBER = '_360_sn.txt'
CAMERA_STATUS = 'BLE_WAIT_FOR_CONNECTION'

# Hardware
led = Pin('LED', Pin.OUT)
shutter_gpio = Pin(19, Pin.IN, Pin.PULL_UP)
wake_gpio = Pin(20, Pin.IN, Pin.PULL_UP)

# UUID Definitions
SERVICE_UUID = bluetooth.UUID(0xce80)
CHARACTERISTIC_UUID1 = bluetooth.UUID(0xce81)       # BLECharacteristic *pCharacteristic1 = pService->createCharacteristic(CHARACTERISTIC_UUID1, BLECharacteristic::PROPERTY_WRITE);
CHARACTERISTIC_UUID2 = bluetooth.UUID(0xce82)       # pCharacteristicRx pService->createCharacteristic(CHARACTERISTIC_UUID2, BLECharacteristic::PROPERTY_NOTIFY);
CHARACTERISTIC_UUID3 = bluetooth.UUID(0xce83)       # pCharacteristic3 = pService->createCharacteristic(CHARACTERISTIC_UUID3, BLECharacteristic::PROPERTY_READ);
_360_GPS_REMOTE_UUID = SERVICE_UUID

SECONDARY_SERVICE_UUID = bluetooth.UUID("0000D0FF-3C17-D293-8E48-14FE2E4DA212")
SECONDARY_CHARACTERISTIC_UUID1 = bluetooth.UUID(0xffd1)
SECONDARY_CHARACTERISTIC_UUID2 = bluetooth.UUID(0xffd2)
SECONDARY_CHARACTERISTIC_UUID3 = bluetooth.UUID(0xffd3)
SECONDARY_CHARACTERISTIC_UUID4 = bluetooth.UUID(0xffd4)
SECONDARY_CHARACTERISTIC_UUID5 = bluetooth.UUID(0xffd5)
SECONDARY_CHARACTERISTIC_UUID8 = bluetooth.UUID(0xffd8)
SECONDARY_CHARACTERISTIC_UUID9 = bluetooth.UUID(0xfff1)
SECONDARY_CHARACTERISTIC_UUID10 = bluetooth.UUID(0xfff2)
SECONDARY_CHARACTERISTIC_UUID11 = bluetooth.UUID(0xffe0)

_FLAG_INDICATE = const(0x0020)
BLE_2902_DESCRIPTOR_UUID = bluetooth.UUID(0x2902)
BLE_2902_Descriptor = {
    BLE_2902_DESCRIPTOR_UUID,
    FLAG_INDICATE | FLAG_NOTIFY,
}

_360_GPS_REMOTE_Char1 = (
    CHARACTERISTIC_UUID2,
    FLAG_NOTIFY,  # BLE_2902_Descriptor
)

_360_GPS_REMOTE_Char2 = (
    CHARACTERISTIC_UUID1,
    FLAG_WRITE,
)
_360_GPS_REMOTE_Char3 = (
    CHARACTERISTIC_UUID3,
    FLAG_READ,
)

_360_GPS_REMOTE_SERVICE = (
    _360_GPS_REMOTE_UUID,
    (_360_GPS_REMOTE_Char1, _360_GPS_REMOTE_Char2, _360_GPS_REMOTE_Char3),
)

_360_GPS_REMOTE_Secondary_1 = (
    SECONDARY_CHARACTERISTIC_UUID1,
    FLAG_WRITE,
)
_360_GPS_REMOTE_Secondary_2 = (
    SECONDARY_CHARACTERISTIC_UUID2,
    FLAG_READ,
)
_360_GPS_REMOTE_Secondary_3 = (
    SECONDARY_CHARACTERISTIC_UUID3,
    FLAG_READ,
)
_360_GPS_REMOTE_Secondary_4 = (
    SECONDARY_CHARACTERISTIC_UUID4,
    FLAG_READ,
)
_360_GPS_REMOTE_Secondary_5 = (
    SECONDARY_CHARACTERISTIC_UUID5,
    FLAG_READ,
)

_360_GPS_REMOTE_Secondary_8 = (
    SECONDARY_CHARACTERISTIC_UUID8,
    FLAG_WRITE,
)
_360_GPS_REMOTE_Secondary_9 = (
    SECONDARY_CHARACTERISTIC_UUID9,
    FLAG_READ,
)
_360_GPS_REMOTE_Secondary_10 = (
    SECONDARY_CHARACTERISTIC_UUID10,
    FLAG_WRITE,
)
_360_GPS_REMOTE_Secondary_11 = (
    SECONDARY_CHARACTERISTIC_UUID11,
    FLAG_READ,
)

_360_GPS_REMOTE_SECONDARY_SERVICE = (
    SECONDARY_SERVICE_UUID,
    ( 
      _360_GPS_REMOTE_Secondary_1, 
      _360_GPS_REMOTE_Secondary_2, 
      _360_GPS_REMOTE_Secondary_3,
      _360_GPS_REMOTE_Secondary_4,
      _360_GPS_REMOTE_Secondary_5,
      _360_GPS_REMOTE_Secondary_8,
      _360_GPS_REMOTE_Secondary_9,
      _360_GPS_REMOTE_Secondary_10,
      _360_GPS_REMOTE_Secondary_11
    ),
)

SERVICES = (_360_GPS_REMOTE_SERVICE, _360_GPS_REMOTE_SECONDARY_SERVICE,)

# BLE Manager Class
class BLEManager:
    def __init__(self):
        self.ble = bluetooth.BLE()
        self.ble_360_Sp = None
        self.manuf_data = bytearray(26)
        self.wake_up_event_triggered = False
        self.shutter_gpio_debounce_time = 0
        self.wake_gpio_debounce_time = 0

        self.setup_ble()
        self.setup_interrupts()

    def setup_ble(self):
        global CAMERA_STATUS
        """Initialize BLE setup."""
        print("Starting BLE work!")
        self.ble_360_Sp = BLESimplePeripheral(self.ble, name="Insta360 GPS Remote", 
            _BLE_SERVICE=SERVICES, 
            _BLE_SERVICE_UUID=_360_GPS_REMOTE_UUID)
        self.ble_360_Sp.on_write(self.on_rx)
        CAMERA_STATUS = 'BLE_WAIT_FOR_CONNECTION'

    def setup_interrupts(self):
        """Attach hardware interrupt handlers."""
        shutter_gpio.irq(trigger=Pin.IRQ_FALLING, handler=self.shutter_callback)
        wake_gpio.irq(trigger=Pin.IRQ_FALLING, handler=self.wake_button_callback)

    def on_rx(self, data):
        """Handle received BLE data."""
        global CAMERA_STATUS
        print("Data received:", data)
        if len(data) > 5 and data[:5] == b'\xfe\xef\xfe\x07\x00':
            self.manuf_data[14:20] = data[-6:]
            print(self.manuf_data[14:20])

            try:
                with open(_360_SERIAL_NUMBER, 'rb') as fp:
                    sn = fp.read()
                    if sn != self.manuf_data[14:20]:
                        with open(_360_SERIAL_NUMBER, 'wb') as fp_write:
                            fp_write.write(self.manuf_data[14:20])
            except Exception:
                with open(_360_SERIAL_NUMBER, 'wb+') as fp:
                    fp.write(self.manuf_data[14:20])

            if CAMERA_STATUS != 'BLE_CONNECTED':
                CAMERA_STATUS = 'BLE_CONNECTED'
        elif len(data) == 8 and data[0:7] == b'\xfe\xef\xfe\x55\x00\x01\x00':
            if CAMERA_STATUS != 'CUSTOM_EVENT':
                CAMERA_STATUS = 'CUSTOM_EVENT'
        elif len(data) >= 8 and data[0:8] == b'\xfe\xef\xfe\x10\x81\x0c\x01\x1c':
            if CAMERA_STATUS != 'BLE_CONNECTED':
                CAMERA_STATUS = 'BLE_CONNECTED'

    def shutter_callback(self, pin):
        """Shutter button interrupt handler."""
        if (time.ticks_ms() - self.shutter_gpio_debounce_time) > 500:
            data_8 = bytearray(30)
            data_8[:9] = b'\xfc\xef\xfe\x86\x00\x03\x01\x02\x00'
            self.ble_360_Sp.send(data_8)

            self.shutter_gpio_debounce_time = time.ticks_ms()
            print('Shutter button pressed')

    def wake_button_callback(self, pin):
        """Wake button interrupt handler."""
        if (time.ticks_ms() - self.wake_gpio_debounce_time) > 500 and not self.wake_up_event_triggered:
            self.wake_gpio_debounce_time = time.ticks_ms()

            if not self.ble_360_Sp.is_connected():
                self.manuf_data[0] = 0x4c;
                self.manuf_data[1] = 0x00;
                self.manuf_data[2] = 0x02;
                self.manuf_data[3] = 0x15;
                self.manuf_data[4] = 0x09;
                self.manuf_data[5] = 0x4f;
                self.manuf_data[6] = 0x52;
                self.manuf_data[7] = 0x42;
                self.manuf_data[8] = 0x49;
                self.manuf_data[9] = 0x54;
                self.manuf_data[10] = 0x09;
                self.manuf_data[11] = 0xff;
                self.manuf_data[12] = 0x0f;
                self.manuf_data[13] = 0x00;

                # /* */
                self.manuf_data[20] = 0x00;
                self.manuf_data[21] = 0x00;
                self.manuf_data[22] = 0x00;
                self.manuf_data[23] = 0x00;
                self.manuf_data[24] = 0xe4;
                self.manuf_data[25] = 0x01;

                try:
                    with open(_360_SERIAL_NUMBER, 'rb') as fp:
                        sn = fp.read()
                        fp.close()
                        self.manuf_data[14:20] = sn
                except Exception as e:
                    print(e)

                _adv_buffer = b'\x01\x1a\x1b\xff' + self.manuf_data  # Add Header (0x02, 0x01, 0x1a), Length of Manufacturer Data (0x1b), Manufacturer Specific Data Type (0xFF)
                print(_adv_buffer)
                self.ble.gap_advertise(100000, adv_data=_adv_buffer)
                print('Wake button pressed')
                self.wake_up_event_triggered = True

                asyncio.create_task(self.reinitialize_ble())

    async def reinitialize_ble(self):
        """Handle BLE reconnection asynchronously."""
        await asyncio.sleep(5)
        self.wake_up_event_triggered = False
        self.setup_ble()

    async def manage_events(self):
        """Manage LED blinking based on BLE state."""
        global CAMERA_STATUS
        while True:
            if not self.ble_360_Sp.is_connected():
                if CAMERA_STATUS != 'BLE_WAIT_FOR_CONNECTION':
                    CAMERA_STATUS = 'BLE_WAIT_FOR_CONNECTION'
            await asyncio.sleep(1)  # Check event change every second
        
# LED Blinking Manager
class LEDManager:
    def __init__(self):
        self.led = Pin('LED', Pin.OUT)
        self.stop_event = asyncio.Event()

    async def blink_led(self, interval):
        """Blink LED asynchronously at a given interval."""
        self.stop_event.clear()
        while not self.stop_event.is_set():
            self.led.on()
            await asyncio.sleep(interval)
            self.led.off()
            await asyncio.sleep(interval)

    async def manage_events(self):
        """Manage LED blinking based on BLE state."""
        global CAMERA_STATUS
        event = None
        while True:
            if event != CAMERA_STATUS:
                event = CAMERA_STATUS
                self.stop_event.set()
                await asyncio.sleep(3)  # Allow previous task to stop
                self.stop_event.clear()
                print(event)
                if event == "BLE_CONNECTED":
                    asyncio.create_task(self.blink_led(0.5))  # 500 ms interval, total 1 second
                elif event == "BLE_WAIT_FOR_CONNECTION":
                    asyncio.create_task(self.blink_led(1.5))  # 1.5 sec interval, total 3 seconds
                elif event == "CUSTOM_EVENT":
                    self.led.on()

            await asyncio.sleep(1)  # Check event change every second


# Main asyncio loop
async def main():
    ble_manager = BLEManager()
    led_manager = LEDManager()

    asyncio.create_task(led_manager.manage_events())  # Start LED manager
    asyncio.create_task(ble_manager.manage_events())  # Start BLE manager

    while True:
        await asyncio.sleep(2)  # Keep the event loop running

if __name__ == '__main__':
    asyncio.run(main())  # Run the asyncio event loop
