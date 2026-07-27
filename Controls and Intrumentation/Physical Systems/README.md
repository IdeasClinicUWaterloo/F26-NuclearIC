# Physical Analogue Track

This folder details physical-analogue solutions of the Instrumentation and Controls challenge (see the [top-level README](../README.md) for the challenge overview). Two working example builds already exist here: a dye-concentration control loop and a temperature control loop. Teams can wire up as-is, modify, or simply use as reference while building a different physical analogue.

## Files

### Dye concentration control

- `dye concentration control/dye_concentration_controller/` : PID on a TCS34725 I2C colour sensor drives dye and water pump PWM; a drain pump runs feed-forward off their combined flow (via a linear PWM→flow calibration curve) to prevent tank overflow.
- `dye concentration control/dye_concentration_controller_photodiode/` : same PID/pump logic, but concentration is sensed via an LED + photodiode transmittance pair instead of the I2C colour sensor (useful if you don't have a TCS34725 on hand).
- `dye concentration control/photodiode_led_test/` : a standalone bench-test sketch to verify the LED/photodiode wiring in isolation before wiring the full photodiode controller.

### Temperature control

- `temperature control/temperature_controller/` : a DS18B20 (OneWire) sensor and a single-actuator, reverse-mode PID that only drives a coolant pump. The heater runs at constant power on its own 12V/fused supply, outside Arduino control (see `wiring_reference.html`). Includes a fail-safe: forces the pump to max cooling on a sensor fault or if temperature exceeds `MAX_SAFE_TEMP_C`, since the heater itself can't be switched off in software.
- `temperature control/temperature_controller_sim/` : the same PID and pin logic, but with the DS18B20 replaced by a simulated heat-balance plant, so you can bench-test PID tuning before wiring any hardware.

### Reference

- `wiring_reference.html` : open in a browser. Pin maps, power domains, and step-by-step wiring instructions for both systems, plus safety callouts (15A fuse on the heater's 12V feed, don't power pumps from the Arduino's 5V rail, common-ground notes).

Both real sketches ship with placeholder calibration constants (pump flow curves, sensor reference readings, the dye concentration-vs-reading curve). Calibrate these on the bench, don't trust the numbers already in the code.

## Roadmap

These milestones describe what already works in the two example builds and what to verify or build on next. They apply to the dye and temperature systems here, and to other physical analogues (pumps, motors, light control) built from scratch.

### Milestone 1: Build and Test the Physical Setup

- If you don't yet have hardware, start with `temperature_controller_sim.ino` (no wiring needed) or `photodiode_led_test.ino` (verifies just the LED/photodiode pair) to get something running first.
- Wire the real sketches following `wiring_reference.html`, flash them, and confirm sane readings over Serial (9600 baud) before connecting pump tubing or turning the heater on.

Good demo: the sensor reading changes visibly when the actuator is turned on or adjusted.

### Milestone 2: Add Basic Feedback Control

- Both real sketches already run closed-loop PID: `dye_concentration_controller.ino` on dye/water pump PWM, `temperature_controller.ino` in reverse mode on the coolant pump only.
- The task here is tuning for your actual hardware rather than writing the loop from scratch: the temperature sketch starts from `Kp=20, Ki=0.8, Kd=4`; the dye sketch's flow/concentration constants are placeholders and need real calibration.

Good demo: the system moves toward a target value and settles without large oscillations.

### Milestone 3: Add Safety Limits

- `temperature_controller.ino` already has a hard `MAX_SAFE_TEMP_C` backstop and forces max cooling on a sensor fault, but this is only a backstop for the pump's response, not a substitute for the heater's own fuse.
- The dye system has an overflow line in the tank but no software cutoff yet. Consider adding a max-runtime limit, a level/overflow sensor, or a hard stop if pump commands saturate for too long.

Good demo: when the system goes outside a safe range, the controller limits or stops the actuator (or, for the heater, you can show the fuse and bench-tested cooling-capacity margin that back it up).

### Milestone 4: Improve Measurements

- Compare the TCS34725 and photodiode variants for the dye loop, and calibrate the concentration-vs-reading curve against known dye concentrations.
- Verify the DS18B20 against a known thermometer.
- Calibrate the pump flow curves (currently placeholders) so PWM-to-flow assumptions match the real hardware.

Good demo: the controller behaves more smoothly, or tracks more accurately, using calibrated rather than placeholder constants.

### Milestone 5: Test Disturbances and Faults

- Change the setpoint mid-run.
- For the dye loop: pinch or partially block a tube, introduce bubbles, or cover the photodiode/sensor.
- For the temperature loop: disconnect the DS18B20 to confirm the fail-safe engages, or run the heater at full power with the pump at max speed to bench-test that temperature plateaus below `MAX_SAFE_TEMP_C` rather than climbing indefinitely.

Good demo: the system detects or recovers from at least one disturbance without unsafe behavior.

### Milestone 6: Build a Clear Demo

- Log or plot target vs. measured value, actuator PWM over time, and any safety/fault events.
- Explain the reactor-control analogy for your build: dye concentration ↔ reactor power, drain-pump feed-forward ↔ coolant removal capacity and overflow safety; the temperature loop's fixed-power heater with pump-only control ↔ a fixed heat source that safety systems must be able to remove heat fast enough to handle.

Good demo: the team can clearly show the system tracking a target, responding to a disturbance, and staying within safe limits.
