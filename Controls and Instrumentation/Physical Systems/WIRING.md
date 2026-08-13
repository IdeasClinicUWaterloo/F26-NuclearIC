# Apparatus and Wiring Guide

This folder contains two separate Arduino builds:

1. A dye-concentration system that mixes dyed water and clear water in a control tank
2. A temperature system that heats and cools an aluminium plate

Build and test one system at a time. Disconnect every power source before changing wires. Keep the Arduino, breadboards, drivers, relay and power terminals away from all water and tubing.

## Dye-concentration system

### What you need

- Arduino UNO R4 Minima with a USB-C cable
- SEN0101 colour sensor
- Three Adafruit 3 V submersible pumps
- Two DRV8833 motor drivers
- Regulated 3 V pump power supply rated for at least 1 A
- Wire-terminal adapter for the 3 V supply
- Breadboard and jumper wires
- 500 mL cup used as the control tank
- Dyed-water reservoir
- Clear-water reservoir
- Waste reservoir
- Tubing for all three pumps
- Cardboard box to block room light
- Phone flashlight
- Tape or rigid holders for the sensor and phone
- 10 mL graduated syringe for calibration
- 500 mL graduated cylinder or another accurate measuring container

The SEN0101 is a TCS3200 frequency-output sensor. Use the sketches in the `rgb` folder with the wiring below.

### Arduino pin map

| Arduino pin | Connect to | What it does |
| --- | --- | --- |
| `D2` | SEN0101 `OUT` | Reads the colour-sensor frequency |
| `D3` | Driver 1 `IN1` | Controls the dyed-water pump with PWM |
| `D4` | Driver 1 `IN2` | Held LOW by the code |
| `D5` | Driver 1 `IN3` | Controls the clear-water pump with PWM |
| `D7` | Driver 1 `IN4` | Held LOW by the code |
| `D6` | Driver 2 `IN1` | Controls the waste pump with PWM |
| `D8` | Driver 2 `IN2` | Held LOW by the code |
| `D9` | SEN0101 `S0` | Sets the sensor output scale |
| `D10` | SEN0101 `S1` | Sets the sensor output scale |
| `D11` | SEN0101 `S2` | Selects the colour filter |
| `D12` | SEN0101 `S3` | Selects the colour filter |

Do not use `D0` or `D1`. They are used for serial communication.

### 1. Set up the 3 V pump power

1. Connect the 3 V power supply to its wire-terminal adapter.
2. Connect supply `+` to the breadboard positive rail.
3. Connect supply `-` to the breadboard negative rail.
4. Connect `VCC` on both motor drivers to the positive rail.
5. Connect `GND` on both motor drivers to the negative rail.
6. Connect one Arduino `GND` pin to the same negative rail.
7. If a driver has a `SLP`, `SLEEP` or `nSLEEP` pin, connect it to Arduino `5V`.
8. Power the Arduino from the laptop using USB-C.

The Arduino, both drivers and the 3 V supply must share ground. Do not power any pump from the Arduino.

### 2. Connect the pumps

| Motor-driver output | Pump |
| --- | --- |
| Driver 1 `OUT1` and `OUT2` | Dyed-water pump |
| Driver 1 `OUT3` and `OUT4` | Clear-water pump |
| Driver 2 `OUT1` and `OUT2` | Waste pump |

Connect the driver inputs using the Arduino pin map above. Leave Driver 2 `IN3`, `IN4`, `OUT3` and `OUT4` unused.

If a pump does not move water, disconnect power and swap its two output wires. Keep each pump submerged whenever it runs.

### 3. Connect the colour sensor

| SEN0101 pin | Connect to |
| --- | --- |
| `VCC` | Arduino `5V` |
| `GND` | Arduino `GND` |
| `OE` | Arduino `GND` |
| `OUT` | Arduino `D2` |
| `S0` | Arduino `D9` |
| `S1` | Arduino `D10` |
| `S2` | Arduino `D11` |
| `S3` | Arduino `D12` |

### 4. Position the sensor and phone light

This setup measures light passing through the liquid.

1. Put the SEN0101 outside the transparent wall of the control tank.
2. Point the sensor horizontally through the liquid.
3. Tape the edges of the sensor board to the tank or use a rigid holder.
4. Do not cover the sensing face, LEDs, pins or wires with tape.
5. Put the phone flashlight directly opposite the sensor on the other side of the tank.
6. Keep the flashlight and sensor at the same height.
7. Secure the phone so it cannot move and keep it away from water.
8. Put the tank, sensor and phone inside the closed cardboard box.
9. Mark the positions of the tank, sensor and phone so the setup can be repeated.

Use the same phone, flashlight setting, tank position and sensor position during calibration and operation. If any part moves or the light changes, repeat the calibration.

### 5. Arrange the water system

- The dyed-water pump moves dyed water into the control tank.
- The clear-water pump moves clear water into the control tank.
- The waste pump removes mixed water from the control tank.
- The control tank is a 500 mL cup.
- Mark `350 mL` as the normal starting level.
- Mark `450 mL` as the absolute maximum level.
- Use roughly 500 mL to 1 L for each inlet reservoir during a normal demonstration.
- Make the waste reservoir large enough for all water removed during the run.
- Secure every tube before starting a pump.

The code estimates waste flow from the calibrated pump curves. It does not measure the water level directly. Supervise the system so the control tank never exceeds 450 mL.

### 6. Choose the dye-control mode

The controller has two options.

**Intensity mode**

Use `rgb/test_rgb/test_rgb.ino` to measure the desired colour-sensor frequency. Enter it as `TARGET_INTENSITY_HZ` and set an acceptable `INTENSITY_TOLERANCE_HZ`. This mode does not require a concentration conversion.

**Concentration mode**

Prepare known mixtures using the same dyed-water reservoir solution that the pump will use. Make every calibration sample at the same 350 mL working volume. Measure each sample using the fixed sensor and phone setup, then copy the averaged readings into `CAL_INTENSITY_HZ` and `CAL_CONCENTRATION`.

See the [Physical Systems README](README.md#optional-dye-intensity-to-concentration-calibration) for the full calibration procedure.

## Temperature-control system

The aluminium plate is the part being temperature-controlled. The silicone pad heats the plate. Water flowing through the copper tube cools the plate. The DS18B20 measures the plate temperature.

### What you need

- Arduino UNO R4 Minima with a USB-C cable
- Aluminium plate
- 12 V DC, 15 W silicone heater pad ([selected heater](https://www.amazon.ca/dp/B0BZN1KXDL))
- Regulated 12 V DC power supply rated for at least 2 A
- Wire-terminal adapter for the 12 V supply
- DFR0473 relay
- Waterproof DS18B20 temperature probe
- 4.7 kΩ resistor
- Adafruit 3 V submersible pump
- DRV8833 motor driver
- Regulated 3 V pump power supply rated for at least 1 A
- Two breadboards
- Copper tubing and tube bender
- Coolant reservoir and flexible tubing
- Jumper wires

### Arduino pin map

| Arduino pin | Connect to | What it does |
| --- | --- | --- |
| `D2` | Relay `D` | Turns the heater on and off |
| `D4` | DS18B20 yellow data wire | Reads the plate temperature |
| `D10` | DRV8833 `IN1` | Controls the coolant pump with PWM |
| `D11` | DRV8833 `IN2` | Held LOW by the code |

### 1. Set up the two breadboards

Use one breadboard for 5 V sensor and relay power:

1. Connect Arduino `5V` to the positive rail.
2. Connect Arduino `GND` to the negative rail.

Use the second breadboard for 3 V pump power:

1. Connect the 3 V supply `+` to the positive rail.
2. Connect the 3 V supply `-` to the negative rail.
3. Connect the second breadboard's negative rail to Arduino `GND`.

The grounds are connected together. Do not connect the 3 V and 5 V positive rails together.

### 2. Connect the coolant pump

1. Connect DRV8833 `VCC` to the 3 V positive rail.
2. Connect DRV8833 `GND` to the 3 V negative rail.
3. Connect `IN1` to Arduino `D10`.
4. Connect `IN2` to Arduino `D11`.
5. Connect the pump wires to `OUT1` and `OUT2`.
6. Leave `IN3`, `IN4`, `OUT3` and `OUT4` unused.
7. If the driver has a `SLP`, `SLEEP` or `nSLEEP` pin, connect it to the 5 V positive rail.

Do not connect the 12 V heater supply to the motor driver.

### 3. Connect the temperature sensor

| DS18B20 wire | Connect to |
| --- | --- |
| Red power wire | 5 V positive rail |
| Black ground wire | Ground rail |
| Yellow data wire | Arduino `D4` |

Place the 4.7 kΩ resistor between the yellow data wire and the 5 V positive rail.

Probe colours can vary. Check the label or datasheet supplied with your probe before applying power.

Fasten the metal probe tip directly to the aluminium plate. Use thermal compound if available, then hold the probe in place with temperature-rated tape or a clamp. Put it away from the heater pad and copper tube so it reads a representative plate temperature instead of one hot or cold spot.

### 4. Connect the relay control pins

| Relay pin | Connect to |
| --- | --- |
| `+` | 5 V positive rail |
| `-` | Ground rail |
| `D` | Arduino `D2` |

The relay uses simple on and off control. Do not send fast PWM to it.

### 5. Connect the heater power circuit

The heater power wires do not go through a breadboard.

```text
12 V supply (+) → relay COM
relay NO → heater-pad wire 1
heater-pad wire 2 → 12 V supply (-)
```

Use a short wire from the positive terminal of the 12 V adapter to `COM`. Connect one heater-pad wire to `NO`. Connect the other heater-pad wire directly to the negative terminal of the adapter.

Use `NO`, not `NC`. This keeps the heater off when the relay or Arduino loses power.

The 12 V heater circuit stays separate from the breadboards and does not need to share Arduino ground. Use a regulated supply with built-in current limiting and short-circuit protection. Keep all exposed terminals covered and dry.

### 6. Assemble the plate

1. Attach the silicone heater pad flat against the aluminium plate.
2. Make sure the whole pad contacts the plate.
3. Do not power the pad while it is folded or loose.
4. Bend the copper tube without creating kinks.
5. Secure the copper tube in close contact with the plate.
6. Keep the tube and its fasteners from damaging the heater pad.
7. Connect the copper loop to the pump and coolant reservoir.
8. Fasten the DS18B20 to the representative plate location described above.
9. Keep the coolant tubing and reservoir away from all electronics.

## Test before closed-loop operation

### Dye system

1. Check the 3 V rail polarity with the pumps disconnected.
2. Confirm both motor drivers and the Arduino share ground.
3. Test one pump and one driver channel at a time.
4. Confirm the colour-sensor readings change between clear and dyed water.
5. Mark the 350 mL working level and 450 mL maximum level.
6. Measure each pump's flow at several PWM values.
7. Calibrate the sensor before using concentration mode.

### Temperature system

1. Test the DS18B20 by itself.
2. Fasten it to the plate and compare it with a contact thermometer.
3. Test the coolant pump with the heater disconnected.
4. Test the relay with the heater disconnected.
5. Confirm the relay is off when the Arduino resets.
6. With power disconnected, check the `COM` and `NO` heater wiring.
7. Run a supervised heating test and confirm the measured plate temperature rises.
8. Confirm the relay turns the heater off at the configured limit.
9. Disconnect the DS18B20 during a supervised test and confirm that the heater turns off and the pump goes to maximum cooling.

Never leave either apparatus running unattended during development.
