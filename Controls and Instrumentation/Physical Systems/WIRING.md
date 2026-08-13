# Physical Apparatus and Wiring Guide

This guide describes the current hardware plan for the two physical analogue systems:

1. a dye-concentration controller that mixes dyed and clear water in a control tank; and
2. a temperature controller that heats an aluminium plate and pumps coolant through copper tubing.

The two apparatuses are separate builds. Power everything off before moving wires, and keep every breadboard, driver, relay and Arduino away from water.

> [!IMPORTANT]
> The selected **SEN0101 is a TCS3200 frequency-output colour sensor**, not an I2C TCS34725. The current `rgb/dye_concentration_controller/dye_concentration_controller.ino` and `rgb/test_rgb/test_rgb.ino` sketches have been updated for the SEN0101 and the pin map below.

## 1. Dye-concentration apparatus

### Components

- Arduino UNO R4 Minima and USB-C cable
- DFRobot SEN0101 (TCS3200) colour sensor
- 3 Adafruit 3 V submersible pumps
- 2 DRV8833 dual H-bridge motor-driver boards
- regulated 3 V pump supply rated for at least 1 A
- barrel-jack-to-screw-terminal adapter matching the pump supply
- breadboard and jumper wires
- 500 mL cup used as the control tank; maximum permitted liquid volume `450 mL`
- dyed-water reservoir sized for the planned run (roughly 500 mL to 1 L is a practical bench-demo starting range)
- clear-water reservoir sized for the planned run (roughly 500 mL to 1 L is a practical bench-demo starting range)
- waste reservoir with capacity greater than the total liquid expected to be discharged during the run
- tubing for all three pumps
- cardboard box or another opaque housing to isolate the control tank from room light
- phone with its flashlight enabled, used as the current fixed transmitted-light source
- tape or rigid holders for fixing the sensor and phone alignment
- 10 mL needle-free graduated syringe with 0.2 mL divisions for measuring dyed-water reservoir solution
- 500 mL graduated cylinder, or equivalent measuring vessel, for preparing calibration standards at the chosen control-tank working volume

On Driver 1, `IN1`/`IN2` control `OUT1`/`OUT2` for the dyed-water pump, while `IN3`/`IN4` control `OUT3`/`OUT4` for the clear-water pump. Driver 2 uses `IN1`/`IN2` and `OUT1`/`OUT2` for the waste pump; its `IN3`/`IN4` and `OUT3`/`OUT4` connections remain unused.

### UNO R4 pin map

This map avoids `D0` and `D1`, which are used by serial communication. It uses one PWM input per pump while holding the other input LOW for fixed-direction operation.

| Arduino pin | Connection | Purpose |
| --- | --- | --- |
| `D2` | SEN0101 `OUT` | colour-frequency input |
| `D3` (PWM) | Driver 1 `IN1` | dyed-water pump speed |
| `D4` | Driver 1 `IN2` | driven LOW in code |
| `D5` (PWM) | Driver 1 `IN3` | clear-water pump speed |
| `D7` | Driver 1 `IN4` | driven LOW in code |
| `D6` (PWM) | Driver 2 `IN1` | waste-pump speed |
| `D8` | Driver 2 `IN2` | driven LOW in code |
| `D9` | SEN0101 `S0` | output-frequency scaling |
| `D10` | SEN0101 `S1` | output-frequency scaling |
| `D11` | SEN0101 `S2` | colour-filter selection |
| `D12` | SEN0101 `S3` | colour-filter selection |

The code constants must match this table. Although `D9`–`D11` are PWM-capable pins, they are used as ordinary digital outputs for the sensor in this map.

### Pump power and common ground

1. Connect the 3 V supply to its screw-terminal adapter.
2. Connect supply `+` to the breadboard positive rail and supply `-` to the negative rail.
3. Connect each DRV8833 motor-supply input, labelled `VM`, `VMotor` or sometimes `VCC`, to the positive rail.
4. Connect both DRV8833 `GND` pins to the negative rail.
5. Connect an Arduino `GND` pin to the same negative rail. The Arduino, both drivers and the 3 V pump supply must share this ground.
6. If the module exposes a `SLP`, `SLEEP` or `nSLEEP` pin, connect it to Arduino `5V` so the driver remains enabled. If the module only exposes `IN1`–`IN4`, its sleep connection is handled on the board and no extra wire is required.
7. Power the Arduino from the laptop using its USB-C cable. Do not power the pumps from an Arduino power pin.

> [!NOTE]
> DRV8833 board labels vary. On the Adafruit breakout, `VMotor` is the motor-power connection and there is no separate logic-power input. Check the labels printed on the actual board before connecting power.

### Pump outputs

Make these connections with power disconnected:

| Driver output | Pump |
| --- | --- |
| Driver 1 `OUT1` and `OUT2` | dyed-water reservoir pump |
| Driver 1 `OUT3` and `OUT4` | clear-water reservoir pump |
| Driver 2 `OUT1` and `OUT2` | waste-reservoir pump |

The order of a pump’s two wires only sets its direction. If a pump does not move water with its inlet submerged, disconnect power and swap its two output wires.

### Pump-control inputs

1. Connect Driver 1 `IN1` to Arduino `D3` and `IN2` to `D4`.
2. Connect Driver 1 `IN3` to Arduino `D5` and `IN4` to `D7`.
3. Connect Driver 2 `IN1` to Arduino `D6` and `IN2` to `D8`.
4. In the controller code, apply PWM to `D3`, `D5` and `D6`, and keep `D4`, `D7` and `D8` LOW.

This arrangement needs only three PWM pins. It is unnecessary to use two PWM pins for each pump when every pump runs in one direction.

### SEN0101 colour sensor

| SEN0101 pin | Connection |
| --- | --- |
| `VDD`/`VCC` | Arduino `5V` |
| `GND` | Arduino `GND` |
| `OE` | `GND` to keep the frequency output enabled |
| `OUT` | Arduino `D2` |
| `S0` | Arduino `D9` |
| `S1` | Arduino `D10` |
| `S2` | Arduino `D11` |
| `S3` | Arduino `D12` |

Use the current setup in **transmitted-light geometry**:

1. Place the SEN0101 outside the transparent wall of the control tank, facing horizontally through the liquid.
2. Tape the sensor securely around its board edges or mount it in a rigid holder. Do not cover the sensing face, LEDs or electrical connections with tape, and keep the board dry.
3. Place the phone flashlight directly opposite the sensor on the other side of the control tank. Centre the flashlight and sensor at the same height so the light travels through the liquid before reaching the sensor.
4. Tape or clamp the phone in place without covering the flashlight. Keep the phone dry and do not leave a charging connection beside the liquid.
5. Mark the sensor position, phone position and tank orientation so they can be reproduced. Use the same phone, flashlight setting, distance and alignment during calibration and control.
6. Put the complete tank, sensor and light path inside the closed cardboard housing to reject room light. Do not move the phone, sensor or tank after calibration.

A phone flashlight is acceptable for the prototype only if repeated readings are stable. Its output can change with the phone, battery state or temperature, so a fixed regulated LED source is preferable for a later repeatable build. If the SEN0101's onboard illumination is active, keep its state unchanged throughout calibration and operation.

### Dye sensor calibration

Two control options are available:

- `INTENSITY_BAND_MODE` needs no conversion to concentration. Measure the desired mixture with [`rgb/test_rgb/test_rgb.ino`](dye%20concentration%20control/rgb/test_rgb/test_rgb.ino), enter that frequency as `TARGET_INTENSITY_HZ`, and set a `+/- INTENSITY_TOLERANCE_HZ` band.
- `CALIBRATED_CONCENTRATION_PID_MODE` uses physical or relative concentration units. First prepare the dyed-water reservoir solution using a recorded raw-dye-to-water recipe. Prepare multiple standards by measuring that reservoir solution and diluting it with clear water to the normal control-tank working volume. Measure each completed standard with the taped sensor and directly opposite phone flashlight in their fixed positions, then copy the averaged frequency and concentration pairs into the controller’s `CAL_INTENSITY_HZ` and `CAL_CONCENTRATION` tables. Do not add raw concentrated dye directly to the control tank.

The complete preparation formula, Serial Monitor commands and validation procedure are in the [Physical Systems README](README.md#optional-dye-intensity-to-concentration-calibration). In raw intensity mode, the controller only requires a positive target frequency; in concentration mode, it requires a valid calibration table.

### Fluid arrangement

- The dyed-water pump transfers dyed water into the control tank.
- The clear-water pump transfers clear water into the same control tank.
- The waste pump transfers mixed liquid from the control tank to the waste reservoir.
- The control tank is a 500 mL cup, but `450 mL` is the absolute maximum permitted liquid volume. Mark that level visibly on the cup.
- Start commissioning with a normal working volume of approximately `350 mL`, leaving about 100 mL between the working level and the maximum. A different normal volume may be selected after testing, but it must remain below 450 mL and the sensor must be recalibrated at that exact volume.
- The controller estimates waste flow from calibrated pump curves but has no direct level measurement. Therefore, software flow matching alone cannot guarantee the 450 mL limit if a tube blocks, a pump stalls or a calibration is inaccurate. Supervise operation and add an independent high-level cutoff before unattended operation.
- Size each inlet reservoir from its calibrated flow rate multiplied by its maximum expected cumulative pump-on time, then add at least 25% margin. For a simple demonstration, 500 mL to 1 L per inlet reservoir is a reasonable starting range.
- Size the waste reservoir for at least the expected total discharged volume plus 25% margin. If the apparatus has no independent high-level cutoff, the safest passive choice is a waste reservoir that can hold the control tank's starting volume plus the usable contents of both inlet reservoirs.
- Keep each submersible pump immersed while it is running; these pumps must be primed with water.
- Secure every tube so a loose outlet cannot spray the electronics.

## 2. Temperature-control apparatus

### Components

- Arduino UNO R4 Minima and USB-C cable
- Adafruit 3 V submersible pump
- DRV8833 motor-driver board
- waterproof DS18B20 temperature probe
- 4.7 kΩ resistor
- DFRobot DFR0473 relay module
- 12 V DC, 15 W silicone heater pad ([selected product](https://www.amazon.ca/dp/B0BZN1KXDL))
- regulated 12 V DC supply rated for at least 2 A
- barrel-jack-to-screw-terminal adapter matching the 12 V supply
- 2 A inline fuse and fuse holder
- regulated 3 V pump supply rated for at least 1 A
- two breadboards: one for the pump circuit and one for the sensor circuit
- aluminium plate
- copper tubing and a copper-tube bender
- coolant reservoir and flexible tubing needed to connect the pump to the copper loop

The **aluminium plate is the controlled thermal load**. The apparatus is not controlling the temperature of a water bath or a vessel placed on the plate.

### UNO R4 pin map

| Arduino pin | Connection | Purpose |
| --- | --- | --- |
| `D2` | DFR0473 `D` | heater on/off control; not PWM |
| `D4` | DS18B20 data/yellow wire | OneWire temperature input |
| `D10` (PWM) | DRV8833 `IN1` | coolant-pump speed |
| `D11` | DRV8833 `IN2` | driven LOW in code |

These assignments match the current temperature-controller sketches.

### Temperature-system power rails

The single Arduino `5V` pin is distributed through the sensor/logic breadboard:

```text
Arduino 5V → logic breadboard positive rail
               ├─ DS18B20 red/VDD wire
               ├─ 4.7 kΩ pull-up to DS18B20 yellow/data wire
               ├─ DFR0473 relay `+`
               └─ optional DRV8833 SLP/SLEEP pin, if exposed

Arduino GND → logic breadboard negative rail
               ├─ DS18B20 black/GND wire
               ├─ DFR0473 relay `-`
               └─ pump breadboard negative rail / DRV8833 GND
```

The other breadboard’s positive rail carries the external **3 V pump supply**. Never join the 3 V and 5 V positive rails. Only their grounds are connected together. The separate 12 V heater circuit does not connect to either breadboard.

### Coolant pump and DRV8833

Use the first breadboard for the low-voltage pump circuit:

1. Connect the external 3 V supply to the breadboard rails: `+` to positive and `-` to negative.
2. Connect DRV8833 `VM`/`VMotor` to the positive rail and `GND` to the negative rail.
3. Connect this negative rail to the logic breadboard’s negative rail, which is connected to Arduino `GND`.
4. If the module exposes `SLP`, `SLEEP` or `nSLEEP`, connect it to the logic breadboard’s 5 V positive rail. Skip this step on a module that only exposes `IN1`–`IN4`.
5. Connect `IN1` to Arduino `D10` and `IN2` to `D11`.
6. Connect the pump’s two wires to `OUT1` and `OUT2`. Leave `IN3`, `IN4`, `OUT3` and `OUT4` unused.
7. The code applies PWM to `D10` and holds `D11` LOW.

Do not power the pump from the Arduino and do not connect the 12 V heater supply to the DRV8833.

### DS18B20 temperature sensor

Use a separate breadboard for the sensor:

1. Connect Arduino `5V` to this logic breadboard’s positive rail.
2. Connect Arduino `GND` to its negative rail.
3. Connect the probe’s red supply wire to the positive rail.
4. Connect the probe’s black ground wire to the negative rail.
5. Connect the probe’s yellow data wire to Arduino `D4`.
6. Place the 4.7 kΩ resistor between the yellow data connection and the positive 5 V rail. This is the required OneWire pull-up resistor.

Probe wire colours can vary by manufacturer. Verify the probe’s supplied pinout before applying power.

Mechanically fasten the probe tip in direct thermal contact with the aluminium plate at a representative measurement point. Use a thin layer of thermal compound if available and secure it with temperature-rated tape or a clamp. The probe must measure the plate, not the surrounding air, heater-pad surface or coolant itself.

### DFR0473 relay control side

The relay module’s low-voltage control side shares the Arduino ground:

| DFR0473 control pin | Connection |
| --- | --- |
| `+` | 5 V logic breadboard positive rail |
| `-` | common-ground negative rail |
| `D` | Arduino `D2` |

The DFR0473 accepts a 2.8–5.5 V supply, so either Arduino rail is electrically valid. Use `5V` here so the relay module and DS18B20 share one clearly identified logic supply. The relay is switched on and off with a digital signal; do not use fast PWM on a mechanical relay.

### Heater-pad power circuit

The selected heater is rated at 12 V DC and 15 W, so its nominal current is approximately 1.25 A. This circuit uses the relay’s isolated screw terminals and the 12 V supply’s terminal adapter. It does **not** go through a breadboard.

```text
12 V supply (+)
    → 2 A inline fuse
    → relay COM
relay NO
    → heater-pad wire 1
heater-pad wire 2
    → 12 V supply (−)
```

In practical terms, use a short wire from the terminal adapter’s positive terminal to the fuse and then to `COM`. Connect one pad wire to `NO`, and connect the other pad wire directly to the adapter’s negative terminal.

Use `NO` (normally open), not `NC` (normally closed). With `NO`, the pad is disconnected whenever the Arduino or relay loses power.

The heater’s 12 V negative terminal does not need to connect to Arduino ground. The relay contacts electrically isolate the heater-power circuit from the Arduino control circuit.

### Mechanical and fluid assembly

1. Attach the silicone heater pad flat against the aluminium plate with full surface contact, following the pad manufacturer’s mounting instructions. The pad heats the plate directly. Do not power the pad while it is loose or folded.
2. Use the tube bender to form the copper tubing without kinks, then secure the tubing in close thermal contact with the aluminium plate so circulating coolant removes heat from the plate. Do not let the tubing or its fasteners puncture or damage the heater pad.
3. Connect the copper loop to the pump and coolant reservoir using suitable flexible tubing.
4. Fasten the DS18B20 probe tip directly to a representative location on the aluminium plate, with good thermal contact. Place it away from direct contact with both the heater pad and copper tube so it measures representative plate temperature rather than a local hot or cold spot.
5. Add thermal insulation over the back of the probe if needed to reduce room-air influence, while keeping the plate-side contact intact.
6. Keep the 12 V terminals, relay, Arduino, motor driver and breadboards dry and physically separated from the coolant tubing and reservoir.

## 3. Commissioning order

Do not connect and energize the entire apparatus for the first test.

### Dye system

1. With pumps disconnected, verify the 3 V rail polarity and confirm both drivers share Arduino ground.
2. Test one pump and one driver channel at a time using a short, fixed PWM command.
3. Tape the SEN0101 in place and secure the phone flashlight directly opposite it at the same height. Test the sensor separately and confirm its output changes between clear and dyed water inside the closed cardboard enclosure at the selected control-tank working volume.
4. Confirm the SEN0101 controller’s pin constants still match this guide.
5. Mark the 350 mL initial working level and the 450 mL maximum level on the control tank. Calibrate all three pump flow rates and the sensor response before enabling closed-loop control.

### Temperature system

1. Test the DS18B20 by itself, then fasten it to the aluminium plate and compare its plate reading with a known contact thermometer at several temperatures.
2. Test the coolant pump with the heater disconnected.
3. Test the relay with the heater disconnected. Its indicator should be off at reset and turn on only when `D2` is commanded HIGH.
4. With all power disconnected, check that the heater is on `COM`/`NO`, the inline fuse is installed, and the 12 V polarity is correct.
5. Run a supervised heater test and confirm the measured aluminium-plate temperature rises and the relay turns the pad off at the configured limit.
6. Unplug the DS18B20 during a test and confirm the software turns the heater off and commands maximum cooling.

Never leave either apparatus operating unattended during development.
