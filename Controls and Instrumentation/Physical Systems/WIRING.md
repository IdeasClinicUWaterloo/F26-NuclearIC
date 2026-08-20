# Wiring Guide

There are two separate builds: dye concentration and plate temperature control. Turn off all power before moving wires and keep electronics away from water.

## Motor-driver power

The DRV8833 motor drivers use a 9 V battery connected through the breadboard power rails.

### Connecting the 9 V battery

1. Disconnect the battery from its snap connector while making connections.
2. Connect the snap connector's red wire to the motor-driver breadboard + rail.
3. Connect the snap connector's black wire to the motor-driver breadboard - rail.
4. Connect each DRV8833 `VCC` pin to the + rail and each `GND` pin to the - rail.
5. Connect Arduino `GND` to the motor-driver - rail so the Arduino and DRV8833 inputs share a ground reference. Do not connect the motor-driver + rail to Arduino `5V`.
6. Reconnect the battery only when the circuit is ready to test. Disconnect it after testing; do not leave it attached when the apparatus is unattended.

## Dye-concentration system

### Parts

- Arduino UNO R4 Minima
- SEN0101 colour sensor
- Three 3 V submersible pumps
- Two DRV8833 motor drivers
- 9 V battery with a snap connector
- Breadboard (BB), tubing and three reservoirs (clear, dye, waste)
- 500 mL control tank
- Cardboard box, phone flashlight and tape

### Wiring

| From | To |
| --- | --- |
| 9 V battery red wire (`+`) | BB + rail |
| 9 V battery black wire (`-`) | BB - rail |
| Both drivers `VCC` | BB + rail |
| Both drivers `GND` | BB - rail |
| Arduino `GND` | BB - rail |
| Driver 1 `IN1` | Arduino `D3` |
| Driver 1 `IN2` | Arduino `D5` |
| Driver 1 `IN3` | Arduino `D6` |
| Driver 1 `IN4` | Arduino `D9` |
| Driver 2 `IN1` | Arduino `D10` |
| Driver 2 `IN2` | Arduino `D11` |
| Driver 1 `OUT1`  | Dyed-water pump wire 1 |
| Driver 1 `OUT2` | Dyed-water pump wire 2 |
| Driver 1 `OUT3` | Clear-water pump wire 1 |
| Driver 1 `OUT4` | Clear-water pump wire 2 |
| Driver 2 `OUT1` | Waste-pump wire 1 |
| Driver 2 `OUT2` | Waste-pump wire 2 |
| SEN0101 `VCC` | Arduino `5V` |
| SEN0101 `GND` | Arduino `GND` |
| SEN0101 `OE` | Arduino `GND` |
| SEN0101 `OUT` | Arduino `D2` |
| SEN0101 `S0` | Arduino `D4` |
| SEN0101 `S1` | Arduino `D7` |
| SEN0101 `S2` | Arduino `D8` |
| SEN0101 `S3` | Arduino `D12` |

Put each pump wire into the same breadboard row as its matching `OUT` pin. The pump wires do not connect to the positive or negative power rails.

All IN wires from the driver *must* be connected to PWM pins (those with ~)

### Tank and sensor setup

- Dyed-water pump goes from the dyed reservoir to the control tank
- Clear-water pump goes from the clear reservoir to the control tank
- Waste pump goes from the control tank to the waste reservoir
- Mark 350 mL as the normal starting level
- Mark 450 mL as the maximum level
- Keep all three pumps submerged while running
- Tape the SEN0101 outside the clear tank wall without covering its face
- Put the phone flashlight directly opposite the sensor at the same height
- Keep the phone, sensor and tank fixed inside the closed cardboard box

The code does not measure tank level. Watch the tank during operation and do not let it pass 450 mL.

### Calibration

For intensity control, measure the desired sensor reading with `rgb/test_rgb/test_rgb.ino` and enter it as `TARGET_INTENSITY_HZ`.

For concentration control, prepare known mixtures using the same dyed-water reservoir solution used by the pump. Measure every sample at the same 350 mL volume with the sensor and phone in their fixed positions.

See the [Physical Systems README](README.md#optional-dye-intensity-to-concentration-calibration) for the calibration steps.

## Temperature-control system

The silicone pad heats the aluminium plate. The copper tube cools the plate. The DS18B20 measures the plate temperature.

### Parts

- Arduino UNO R4 Minima
- Aluminium plate and 12 V, 15 W silicone heater pad
- DFR0473 relay and 12 V heater supply
- DS18B20 probe and 4.7 kΩ resistor
- One 3 V submersible pump and one DRV8833
- 9 V battery with a snap connector
- Two breadboards (BB), copper tubing and coolant reservoir

The 12 V heater supply and the 9 V motor-driver battery are separate. Never connect the heater supply to the pump breadboard.

### Arduino, sensor and pump wiring

| From | To |
| --- | --- |
| Arduino `5V` | Logic BB + rail |
| Arduino `GND` | Logic BB - rail |
| 9 V battery red wire (`+`) | Pump BB + rail |
| 9 V battery black wire (`-`) | Pump BB - rail |
| Pump BB - rail | Logic BB - rail |
| DRV8833 `VCC` | Pump BB + rail |
| DRV8833 `GND` | Pump BB - rail |
| DRV8833 `IN1` | Arduino `D10` |
| DRV8833 `IN2` | Arduino `D11` |
| DRV8833 `OUT1` | Pump wire 1 |
| DRV8833 `OUT2` | Pump wire 2 |
| DS18B20 red wire | Logic BB + rail |
| DS18B20 black wire | Logic BB - rail |
| DS18B20 yellow wire | Arduino `D4` |
| 4.7 kΩ resistor | Between DS18B20 yellow wire and logic + rail |
| Relay `+` | Logic BB + rail |
| Relay `-` | Logic - rail |
| Relay `D` | Arduino `D2` |

Put each pump wire into the same breadboard row as `OUT1` or `OUT2`. Do not connect the pump wires to a power rail.

The wires of the DS18B20 can be connected to the rails of the logic BB through an extra jumper wire in the same row going to the rails.

### Heater wiring

The heater circuit does not go through a breadboard.

```text
12 V supply (+) → relay COM
relay NO → heater-pad wire 1
heater-pad wire 2 → 12 V supply (-)
```

Cut a small piece Wire 2 before hand, as this can be used to connect relay COM to the 12 V supply (+)

Use `NO`, not `NC`, so the heater is off when relay power is lost. The heater circuit does not need to share Arduino ground.

### Plate setup

- Attach the heater pad flat on the aluminium plate
- Bend the copper tube and secure it on the plate
- Attach the DS18B20 tip directly to the plate with thermal compound and tape or a clamp
- Keep the probe away from direct contact with the pad and copper tube
- Keep the coolant tubing and reservoir away from electronics

## Before running either controller

1. Check power polarity with pumps and heater disconnected.
2. Test one pump channel at a time.
3. Test each sensor before connecting the actuators.
4. Test the relay with the heater disconnected.
5. Confirm the software pins match the tables above.
6. Calibrate the pump flow and sensors.
7. Run the first complete test under supervision.

Never leave either apparatus running unattended.
