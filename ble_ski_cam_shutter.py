#Include the library files
from machine import Pin
import socket
import struct
import time
from time import sleep
from machine import WDT
import bluetooth
from bluetooth import BLE, FLAG_READ, FLAG_WRITE, FLAG_NOTIFY, FLAG_INDICATE
from ble_simple_peripheral import BLESimplePeripheral
import rp2

_360_SERIAL_NUMBER = '_360_sn.txt'

shutter_gpio = Pin(19, Pin.IN, Pin.PULL_UP)
shutter_gpio_debounce_time=0
shutter_is_pressed = False
wake_gpio = Pin(20, Pin.IN, Pin.PULL_UP)
wake_gpio_debounce_time=0
wake_button_is_pressed = False
wake_up_event_triggered = False

'''
_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)
'''

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

manuf_data = bytearray(26)

ble = BLE()
_360_ble_Sp = None

def setup(ble):
    global manuf_data
    print("Starting BLE work!")

    # Create an instance of the BLESimplePeripheral class with the BLE object
    _360_ble_Sp = BLESimplePeripheral(ble, 
        name="Insta360 GPS Remote", 
        _BLE_SERVICE=SERVICES, 
        _BLE_SERVICE_UUID=_360_GPS_REMOTE_UUID)

    return _360_ble_Sp

def on_rx(data):
    global manuf_data
    print("Data received: ", data)  # Print the received data
    '''
    New connection 64
    Data received:  b'\xfe\xef\xfe\x02\x00\x05\x01(\x17\x01`'
    Data received:  b'\xfe\xef\xfe\x05\x00\x01\x01'
    Data received:  b'\xfe\xef\xfe\x07\x00\x06 8ABCDE '
    Data received:  b'\xfe\xef\xfe\x02\x80\x05\x01T\x00\nP'
    Data received:  b'\xfe\xef\xfe\x0f\x00\x00'
    Data received:  b'\xfe\xef\xfe\x02\x80\x05\x01T\x00\nP'
    Data received:  b'\xfe\xef\xfe\x02\x80\x05\x01T\x00\nP'
    '''
    if len(data) > 5:
        if data[0:5] == b'\xfe\xef\xfe\x07\x00':
            manuf_data[14:20] = data[-6:]
            print(manuf_data[14:20])
            try:
                with open(_360_SERIAL_NUMBER, 'rb') as fp:
                    sn = fp.read()
                    if sn != manuf_data[14:20]:
                        fp.seek(0)
                        fp.write(manuf_data[14:20])
                    fp.close()
            except Exception as e:
                with open(_360_SERIAL_NUMBER, 'wb+') as fp:
                    fp.write(manuf_data[14:20])
                    fp.close()

def screen_toggle():
    data_8 = bytearray(30)
    data_8[:9] = b'\xfc\xef\xfe\x86\x00\x03\x01\x00\x00'
    ble_360_Sp.send(data_8)

def power_off():
    data_8 = bytearray(30)
    data_8[:9] = b'\xfc\xef\xfe\x86\x00\x03\x01\x00\x03'
    ble_360_Sp.send(data_8)

def mode_button():
    data_8 = bytearray(30)
    data_8[:9] = b'\xfc\xef\xfe\x86\x00\x03\x01\x01\x00'
    ble_360_Sp.send(data_8)

'''
def shutter_button():
    data_8 = bytearray(30)
    data_8[:9] = b'\xfc\xef\xfe\x86\x00\x03\x01\x02\x00'
    ble_360_Sp.send(data_8)
'''

def shutter_callback(pin):
    global shutter_gpio_debounce_time
    if (time.ticks_ms()-shutter_gpio_debounce_time) > 500:
        data_8 = bytearray(30)
        data_8[:9] = b'\xfc\xef\xfe\x86\x00\x03\x01\x02\x00'
        ble_360_Sp.send(data_8)

        shutter_gpio_debounce_time=time.ticks_ms()
        print('shutter button is pressed')

def wake_button_callback(pin):
    global wake_gpio_debounce_time, manuf_data, wake_up_event_triggered
    if (time.ticks_ms()-wake_gpio_debounce_time) > 500 and wake_up_event_triggered == False:
        wake_gpio_debounce_time=time.ticks_ms()

        if ble_360_Sp.is_connected() == False:
            # /* set the manufacturing data for wake-up packet */
            manuf_data[0] = 0x4c;
            manuf_data[1] = 0x00;
            manuf_data[2] = 0x02;
            manuf_data[3] = 0x15;
            manuf_data[4] = 0x09;
            manuf_data[5] = 0x4f;
            manuf_data[6] = 0x52;
            manuf_data[7] = 0x42;
            manuf_data[8] = 0x49;
            manuf_data[9] = 0x54;
            manuf_data[10] = 0x09;
            manuf_data[11] = 0xff;
            manuf_data[12] = 0x0f;
            manuf_data[13] = 0x00;

            # /* */
            manuf_data[20] = 0x00;
            manuf_data[21] = 0x00;
            manuf_data[22] = 0x00;
            manuf_data[23] = 0x00;
            manuf_data[24] = 0xe4;
            manuf_data[25] = 0x01;

            try:
                with open(_360_SERIAL_NUMBER, 'rb') as fp:
                    sn = fp.read()
                    fp.close()
                    manuf_data[14:20] = sn
            except Exception as e:
                pass
            #manuf_data[14:20] = b'\x38\x55\x45\x46\x45\x48' #8ABCDE, This is the model number got from the text in Camera->Device Info.

            _adv_buffer = b'\x01\x1a\x1b\xff' + manuf_data  # Add Header (0x02, 0x01, 0x1a), Length of Manufacturer Data (0x1b), Manufacturer Specific Data Type (0xFF)
            print(_adv_buffer)
            ble_360_Sp._ble.gap_advertise(100000, adv_data=_adv_buffer)
            print('wake button is pressed')
            wake_up_event_triggered = True

if __name__ == '__main__':

    led = machine.Pin('LED', machine.Pin.OUT)
    led.on()
    sleep(1)
    led.off()

    machine.Pin(23, machine.Pin.OUT).high() #turn on wifi module

    ble = bluetooth.BLE()
    ble_360_Sp = setup(ble)
    ble_360_Sp.on_write(on_rx)  # Set the callback function for data reception

    shutter_gpio.irq(trigger=Pin.IRQ_FALLING, handler=shutter_callback)
    wake_gpio.irq(trigger=Pin.IRQ_FALLING, handler=wake_button_callback)

    while True:
        sleep(1)
        if wake_up_event_triggered == True:
            end = time.time() + 5
            now = time.time()
            while end > now:
                now = time.time()

            wake_up_event_triggered = False
            #ble_360_Sp.disconnect()
            #ble_360_Sp._advertise()
            ble_360_Sp = setup(ble)
            ble_360_Sp.on_write(on_rx)
        print('no action, waiting')
