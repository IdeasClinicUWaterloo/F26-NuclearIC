# Physical Systems Track

This folder contains two Arduino control systems:

- Dye concentration control
- Aluminium plate temperature control

Use [WIRING.md](WIRING.md) to build either system.

The DRV8833 motor drivers are powered by a 9 V battery connected to the motor-driver power rails on the breadboard. See [Motor-driver power](WIRING.md#motor-driver-power) for the connection steps.

## Dye Concentration Regulator

Three pumps add dyed water, add clear water and remove waste water. A SEN0101 colour sensor measures the mixture in the control tank.

It is required for accuracy and precision that the colour sensor maintains a consistent height from the liquid surface.
For this reason, all samples should be the same mL, which by default is 350mL.
If you intend to change the control tank, dye tank, or clear tanks volume, this information must be appropriately translated into the program.
By default, the dye and clear tanks should contain 400mL, whereas the control tank should contain 350mL.

No lighting solutions are required to assist the colour sensor, but the lighting should remain consistent to do this avoid the following:
+ casting shadows over measurements.
+ moving to another place in the room before taking a measure.
+ introducing a different colour or background object.
+ changing the lighting in any way.

LIGHTING MUST REMAIN AS CONSISTENT AS POSSIBLE THROUGHOUT THE CALIBRATION PROCESS.

Provided Arduino Uno R4 Sketches:

- [Dye Concentration Regulator]:(https://github.com/IdeasClinicUWaterloo/F26-NuclearIC/tree/main/Controls%20and%20Instrumentation/Physical%20Systems/Dye%20Concentration%20Regulator)

### Concentration Calibration
The provided Arduino sketches should walk you through the calibration fairly clearly.
1. Prepare at least 5 solutions of dye.
2. Enter the concentrations in terms of number of drops (a drop is considered 0.05mL).
3. allow sensor to read concentration.
4. Repeat steps 2 and 3 for each solution.
5. Once you have completed all solutions, you will find a beta0 and beta1 value, these are the required linear regression values.

## UPDATE THIS SECTION
6. Upload `test_rgb.ino` and choose the most stable colour channel.
7. Mix each sample and average at least three readings.
8. Enter the readings in `CAL_INTENSITY_HZ`.
9. Enter the matching concentrations in `CAL_CONCENTRATION`.
10. Set `CAL_POINT_COUNT`, `CONCENTRATION_CHANNEL` and `targetConcentration`.
11. Set `CALIBRATION_READY = true`.
12. Test one extra sample before tuning the PID.

Use one concentration unit throughout:

- Known reservoir concentration: `C_sample = C_reservoir × V_reservoir / V_total`
- Unknown reservoir concentration: `% v/v = 100 × V_reservoir / V_total`

Recalibrate when results change unexpectedly.

## Plate temperature

The silicone pad heats the aluminium plate. The coolant tube cools it. The DS18B20 measures the plate temperature.

The default setpoint is 35 °C. It can be changed up to 45 °C. The heater shuts off at 55 °C.

Sketches:

- [PID controller](temperature%20control/temperature_controller/temperature_controller.ino)
- [Hysteresis controller](temperature%20control/temperature_controller_hysteresis/temperature_controller_hysteresis.ino)

Use the hysteresis controller for the first hardware test. Use the PID controller after the relay, sensor and pump work correctly.

The starting PID values must be tuned on the real plate.

## Final checks

- Test each pump separately
- Check every power connection
- Confirm the software pins match `WIRING.md`
- Calibrate pump flow before closed-loop control
- Test the relay before connecting the heater
- Confirm a sensor fault turns the heater off
- Keep the control tank below 450 mL
- Keep electronics away from water
- Supervise every test
