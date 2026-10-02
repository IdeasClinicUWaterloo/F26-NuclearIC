# Physical Systems Track

This folder contains two Arduino control systems:

+ Dye Concentration Regulator
+ Thermal Regulator

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

[Dye Concentration Regulator](https://github.com/IdeasClinicUWaterloo/F26-NuclearIC/tree/main/Controls%20and%20Instrumentation/Physical%20Systems/Dye%20Concentration%20Regulator)

### Concentration Calibration
The provided Arduino sketches should walk you through the calibration fairly clearly.
Upload [BeerLambertCalibrator.ino](https://github.com/IdeasClinicUWaterloo/F26-NuclearIC/blob/main/Controls%20and%20Instrumentation/Physical%20Systems/Dye%20Concentration%20Regulator/BeerLambertCalibrator.ino) and follow the steps.
1. Prepare at least 5 solutions of dye, and one clear solution (no dye).
2. Allow the sensor to scan the clear solution as a basis.
3. For all other solutions, enter the concentrations in terms of number of drops (a drop is considered 0.05mL).
4. allow sensor to read frequency.
5. Repeat steps 3 and 4 for each solution with dye.
6. Once you have completed all solutions, you have all the information you need!

### Concentration Regulation
The information required for this program is the clear solutions frequency, beta0 and beta1 values, and the dye reservoir frequency (readable via [SimpleFrequencyChecker.ino](https://github.com/IdeasClinicUWaterloo/F26-NuclearIC/blob/main/Controls%20and%20Instrumentation/Physical%20Systems/Dye%20Concentration%20Regulator/SimpleFrequencyChecker.ino))

Each loop initially reads the control tank frequency then requests the reservoir frequency.
Clear frequency, beta1, and beta0 are changed manually by changing their global variable values. This is because these should not change between regulation loops.

When a target frequency is set, a function calculates the time required for the pumps to run to meet the concentration values.
If the time indicates that more reservoir volume is required than is available the program will request a different concentration value.

### Concentration Units
The units are confusing for this relation, since food dye cannot be pure it is always a water solution, how can we know what the true concentration is?
The answer is abstraction, instead of considering the food dye as dye and water, we consider it as a new pure substance.
This makes the concentration measurements (mL(food dye)/mL(water)). This is extremely convenient for this case, but requires careful organization and thinking.

## Plate temperature

The silicone pad heats the aluminium plate. The coolant tube cools it. The DS18B20 (thermocouple) measures the plate temperature.

The default set point is 35 °C. It can be changed up to 45 °C. The heater shuts off at 55 °C.

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
