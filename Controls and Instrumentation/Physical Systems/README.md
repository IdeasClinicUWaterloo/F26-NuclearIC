# Physical Systems Track

This folder contains two Arduino control systems:

- Dye concentration control
- Aluminium plate temperature control

Use [WIRING.md](WIRING.md) to build either system.

## Dye concentration

Three pumps add dyed water, add clear water and remove waste water. A SEN0101 colour sensor measures the mixture in the control tank.

Tank levels:

- Normal starting level: 350 mL
- Maximum level: 450 mL

Keep the phone flashlight directly opposite the sensor. Tape both in place and close the cardboard box.

Sketches:

- [Dye controller](dye%20concentration%20control/rgb/dye_concentration_controller/dye_concentration_controller.ino)
- [Sensor test and calibration](dye%20concentration%20control/rgb/test_rgb/test_rgb.ino)

### Control modes

`INTENSITY_BAND_MODE` controls around a sensor reading. Set `TARGET_INTENSITY_HZ` and `INTENSITY_TOLERANCE_HZ`. Concentration calibration is not needed.

`CALIBRATED_CONCENTRATION_PID_MODE` converts the sensor reading to concentration using measured samples.

### Concentration calibration

1. Mix the dyed-water reservoir and record the dye-to-water recipe.
2. Keep every sample at 350 mL.
3. Keep the sensor, phone and tank in the same positions.
4. Prepare samples across the expected concentration range.
5. Include clear water as the zero sample.

Example samples:

| Dyed reservoir water | Add clear water to | Relative concentration |
| --- | --- | --- |
| 0 mL | 350 mL | 0% |
| 7 mL | 350 mL | 2% |
| 14 mL | 350 mL | 4% |
| 21 mL | 350 mL | 6% |
| 28 mL | 350 mL | 8% |
| 35 mL | 350 mL | 10% |

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
