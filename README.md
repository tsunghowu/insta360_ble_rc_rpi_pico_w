# R-Pi Pico W insta360 ble remote controller 

This work is based on the esp-based insta360 remote at https://github.com/pchwalek/insta360_ble_esp32. 

# Overview
R-Pi Pico W based remote control for insta360 X4 sport camera. 

```
R-Pi Pico W 
                +----+
  [Btn1]--------| p  |------+ +---+--------------+-----------------------+
                | i  |--------|6  |--------------|Battery Charging Board |
  [Btn2]--------| c  |        |0  |              +-----------------------+
                | o  |        |0mA| Battery
                +----+        +---+ 
```
There's also a case for the R-Pi Pico W, 600mA battery, charging pad, and buttons. The shell can attach
to any ski pole with 18 mm in diameter.

## CAD
![cad_preview](https://github.com/user-attachments/assets/076afc8f-4b0a-4f64-8543-6e612d2e5b84)

## Printing instructions: TPU, 0.2mm.

## Implemented Functions:
### Shutter: 
Send byte stream 
`0xfc 0xef 0xfe 0x86 0x00 0x03 0x01 0x02 0x00` over BLE gatts_notify() to
Insta 360 X4.

### Power On:

Broadcast raw byte stream 
```
0x02; 0x01; 0x1a; 0x1b; 0xff; 0x4c; 0x00; 0x02; 0x15; 
0x09; 0x4f; 0x52; 0x42; 0x49; 0x54; 0x09; 0xff; 0x0f; 
0x00; 0x38; 0x51; 0x53; 0x4a; 0x38; 0x52; 0x00; 0x00; 
0x00; 0x00; 0xe4; 0x01;
```
as the payload in BLE gap_advertise() to wake up Insta 360 X4 device.

See break down at below link.
https://chatgpt.com/share/6797d220-6bf4-800d-a0ac-b3b53ce1bc25 

### What does it look like.
![pole_real_thing_small](https://github.com/user-attachments/assets/ffa7f29c-5bcd-46cc-8edb-e8e6c4edf601)

