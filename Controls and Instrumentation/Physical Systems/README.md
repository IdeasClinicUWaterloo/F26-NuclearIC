# Physical Analogue Track

This folder contains two physical control-system builds for the [Controls and Instrumentation challenge](../README.md): a dye-concentration apparatus and a temperature-control apparatus. Both demonstrate feedback control, sensor calibration, actuator limits, disturbances and fail-safe behaviour using an Arduino UNO R4 Minima.

Start with the [apparatus and wiring guide](WIRING.md). It is the current hardware reference and includes the component lists, pin maps, power connections, physical assembly and commissioning order for both systems.

## Current apparatus plan

### Dye-concentration control

The dye apparatus uses:

- a DFRobot SEN0101/TCS3200 colour sensor;
- three 3 V submersible pumps for dyed water, clear water and waste;
- two DRV8833 dual motor-driver boards;
- a 500 mL control-tank cup, limited to a maximum liquid volume of 450 mL and enclosed in a cardboard box to reduce interference from room light;
- a phone flashlight fixed directly opposite the colour sensor across the control tank as the current transmitted-light source; and
- an Arduino UNO R4 Minima powered from a laptop.

The controller adds dyed or clear water to move the measured concentration toward its target. The waste pump removes mixed liquid to manage the control-tank level. Start commissioning at a normal working volume of approximately 350 mL, leaving about 100 mL before the strict 450 mL maximum.

The current [`rgb/dye_concentration_controller/`](dye%20concentration%20control/rgb/dye_concentration_controller/) sketch reads the SEN0101 output frequency and drives the three pumps through the two DRV8833 boards. It supports either raw intensity-band control or calibrated concentration PID.

Raw intensity-band control is the default and does **not** require a concentration calibration. Measure the sensor frequency at the desired mixture, enter it as `TARGET_INTENSITY_HZ`, choose an acceptable `INTENSITY_TOLERANCE_HZ`, and confirm `DYE_MAKES_INTENSITY_DECREASE`. The controller adds dye or clear water only when the reading leaves that band. It keeps the pumps off only while the target remains unset at `0`.

The [`rgb/`](dye%20concentration%20control/rgb/) folder contains the current SEN0101/TCS3200 controller and its calibration test sketch.

### Temperature control

The temperature apparatus uses:

- a waterproof DS18B20 temperature probe;
- a 12 V DC, 15 W silicone heater pad attached to an aluminium plate;
- a DFRobot DFR0473 relay to switch the heater;
- one 3 V submersible coolant pump controlled through a DRV8833;
- copper tubing formed into the coolant loop; and
- an Arduino UNO R4 Minima powered from a laptop.

The aluminium plate is the controlled thermal load. The silicone pad heats the plate directly, copper tubing secured in thermal contact with the plate removes heat when coolant flows, and the DS18B20 is fastened to the plate to measure its temperature. The heater is connected to the relay’s `COM` and `NO` contacts and is therefore off when relay control power is lost.

Available sketches:

- [`temperature_controller/temperature_controller.ino`](temperature%20control/temperature_controller/temperature_controller.ino) implements split-range PID control: positive demand switches the heater using a slow relay window and negative demand controls pump PWM.
- [`temperature_controller_hysteresis/temperature_controller_hysteresis.ino`](temperature%20control/temperature_controller_hysteresis/temperature_controller_hysteresis.ino) provides simpler hysteresis control for initial wiring and safety testing.

The temperature sketches use `D2` for the relay, `D4` for the DS18B20, and `D10`/`D11` for the pump driver. These assignments match [WIRING.md](WIRING.md).

## Documentation

- [`WIRING.md`](WIRING.md) is the current GitHub-readable apparatus and wiring guide.

## Build roadmap

### 1. Assemble and test individual devices

- Verify power-supply polarity before inserting any modules.
- Test each pump and DRV8833 channel separately.
- Tape or rigidly mount the SEN0101 outside the control tank without covering its sensing face. Fix the phone flashlight directly opposite it at the same height, then test the response using clear and dyed water inside the closed cardboard enclosure.
- Test the DS18B20 against a known thermometer.
- Test the DFR0473 indicator and switching action before connecting the heater pad.

### 2. Verify the dye controller

- Use the pin map in `WIRING.md` and confirm every software pin matches the physical connection.
- Upload [`rgb/test_rgb/test_rgb.ino`](dye%20concentration%20control/rgb/test_rgb/test_rgb.ino) and confirm the red, green, blue and clear frequencies respond to changes in dye concentration.
- Confirm all three pumps can be commanded independently before adding tubing to the control tank.

### 3. Calibrate the apparatus

- Measure each pump’s flow at several PWM values and fit a flow curve or lookup table.
- Record SEN0101 readings for clear water and several known dye concentrations.
- Verify the plate-mounted temperature probe against a known contact thermometer throughout the expected operating range.
- Measure the coolant pump’s lowest reliable starting PWM.

The existing flow curves and PID gains are starting points only; do not treat them as calibrated values.

#### Optional dye intensity-to-concentration calibration

This procedure is needed only for `CALIBRATED_CONCENTRATION_PID_MODE`. Teams that only need repeatable control around a chosen sensor reading can use `INTENSITY_BAND_MODE` instead. The SEN0101 reports light intensity as a frequency; converting that frequency into a concentration unit depends on the dye colour, cup, liquid depth, sensor position and lighting.

1. Prepare one uniform **dyed-water reservoir solution** using a recorded quantity of raw dye and water. Use this same recipe in the apparatus. The operating reservoir can and normally should contain substantially more than the control-tank working volume; roughly 500 mL to 1 L is a practical starting range for a bench demonstration. Raw concentrated dye is not pumped directly into the control tank.
2. Select and mark one normal control-tank working volume. Start with `350 mL`, which leaves about 100 mL below the strict `450 mL` maximum in the 500 mL cup. Every calibration standard and every controlled run must use this same working volume because changing liquid depth changes the optical reading.
3. Prepare at least six standards spanning the range expected during operation. Include clear water as the zero point. For a 350 mL total volume, an example relative series is 0, 7, 14, 21, 28 and 35 mL of dyed-water reservoir solution, with clear water added until each sample reaches exactly 350 mL. These correspond to 0%, 2%, 4%, 6%, 8% and 10% reservoir solution by volume. Measure each completed standard in the control tank; do not create the standards by pumping unmeasured amounts into it.
4. Assign concentration values using one consistent unit:
   - if the dyed-water reservoir concentration is known, `C_standard = C_reservoir × V_reservoir / V_total`;
   - if it is unknown, use relative reservoir-solution concentration, `% v/v = 100 × V_reservoir / V_total`.
5. Tape or rigidly mount the SEN0101 outside the transparent tank wall. Fix the phone flashlight directly opposite the sensor, at the same height, so its light passes through the liquid into the sensor. Keep the same control tank, 350 mL working volume, phone and flashlight setting, sensor/light distance, alignment and closed cardboard housing for every measurement. Do not cover either optical face with tape. Changing any part of this geometry or illumination invalidates the calibration.
6. Upload `rgb/test_rgb/test_rgb.ino`. Compare the live red, green, blue and clear frequencies across the standards. Select the channel with the largest stable, monotonic change; green is the starting choice for red dye, but the measurements decide.
7. For every standard, mix thoroughly, allow bubbles and motion to settle, then record at least three frequency readings. Use their average. In the Serial Monitor, select the channel with `r`, `g`, `b` or `c`, then enter `s <concentration>`; use `z` for the zero sample.
8. Set `CAL_POINT_COUNT` to the number of standards, then enter the averaged frequencies and matching concentrations into `CAL_INTENSITY_HZ` and `CAL_CONCENTRATION` in `rgb/dye_concentration_controller/dye_concentration_controller.ino`, ordered by increasing concentration. Set `CONCENTRATION_CHANNEL` to the selected colour filter, update `targetConcentration` to the same concentration unit, and only then set `CALIBRATION_READY = true`.
9. Test one additional known concentration that was not used to build the table. If the calculated value is poor, add more standards or repeat the measurements before tuning the PID. Do not command a target outside the calibrated concentration range; the sketch clamps out-of-range sensor readings rather than extrapolating them.

Recalibrate whenever the dyed-water reservoir recipe, control tank, fill volume, phone or flashlight output, sensor/light position, enclosure or illumination changes.

### 4. Close the control loops

- Tune the dye controller only after the sensor and pump calibrations are complete.
- Commission the temperature system with the hysteresis sketch before using the PID sketch.
- Confirm the heater and coolant pump do not run against each other.

### 5. Verify safety behaviour

- Keep liquids and tubing physically separated from all electronics.
- Treat 450 mL as the absolute control-tank limit. Mark it visibly and add an independent high-level cutoff; calibrated waste-pump flow alone cannot detect a blockage, stalled pump or accumulating level error.
- Use the 2 A inline fuse in the 12 V heater circuit.
- Disconnect the DS18B20 during a supervised test and confirm that the heater turns off and cooling goes to maximum.
- Trigger the software over-temperature limit deliberately during commissioning.

### 6. Prepare the demonstration

- Plot target versus measured dye concentration or temperature.
- Plot pump PWM and heater state.
- Demonstrate a setpoint change or controlled disturbance.
- Explain how feedback, actuator limits and fail-safe behaviour relate to reactor controls.

Never leave either physical apparatus operating unattended during development.
