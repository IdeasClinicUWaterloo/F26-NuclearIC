// Physical reactor temperature control system
// Arduino + DS18B20 (OneWire) temperature sensor + coolant pump (solderless MOSFET
// driver breakout module)
//
// The heater is NOT controlled by the Arduino. It runs at constant power,
// plugged straight into its 12V supply through an inline fuse -- like a fixed
// heat source (e.g. constant decay heat). The only actuator is the coolant
// pump: PID modulates flow through the copper coil to hold temperature at
// setpoint. This still demonstrates real closed-loop feedback control
// (sensor -> PID -> actuator), just with a single actuator instead of two,
// and it keeps the ~11A heater circuit completely out of the Arduino/solderless
// wiring (no MOSFET, no gate resistor, no software cutoff needed for it).
//
// IMPORTANT: this only works if the coil can remove at least as much heat as
// the heater puts in at max pump speed. Bench-test this before relying on it:
// run the heater at full power with the pump at full speed and confirm
// temperature plateaus below a safe limit rather than climbing indefinitely.
//
// Heater: Littryee 12V, 120-140W immersion heater -> ~10-11.7A at 12V.
// Wire it directly to its 12V supply through a 15A inline fuse. No MOSFET,
// no Arduino connection, no soldering required for this part at all.
//
// Coolant pump: same small submersible pump used elsewhere (~3V, ~100mA) ->
// drive it with a solderless MOSFET driver breakout module (screw terminals
// for the pump + its supply, 3-pin header to an Arduino PWM pin). Most of
// these modules already include flyback protection onboard for the motor's
// inductive kickback -- check your specific module's datasheet.

#include <OneWire.h>
#include <DallasTemperature.h>
#include <PID_v1.h>

// ---------------- Pins ----------------
const int ONE_WIRE_BUS = 2; // DS18B20 data pin (needs 4.7k pull-up to 5V)
const int PUMP_PWM_PIN = 9; // PWM pin -> coolant pump driver module's SIG pin

// ---------------- Safety limits ----------------
const double MAX_SAFE_TEMP_C = 90.0; // hard backstop regardless of setpoint

// ---------------- Sensor ----------------
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

// ---------------- Temperature PID (single actuator: coolant pump) ----------------
double currentTempC = 0.0;
double targetTempC  = 60.0; // placeholder setpoint, change as needed
double pumpPwm      = 0.0;  // 0..255, PID output drives pump speed directly

// Tune these after observing real step-response behavior.
// Water baths are slow (large thermal mass) -> expect to need a fairly
// large Ki relative to Kp, and watch for overshoot from Kd being too low.
double Kp = 20.0, Ki = 0.8, Kd = 4.0;

// REVERSE mode: increasing pump PWM (more cooling flow) causes temperature
// (the PID's Input) to go DOWN, not up -- that's what REVERSE means here,
// not an error-sign convention. Output rises when currentTempC is above
// targetTempC (too hot, add cooling) and falls toward 0 when temperature is
// below setpoint (too cold, back off cooling and let the constant heater
// warm things back up).
PID tempPID(&currentTempC, &pumpPwm, &targetTempC, Kp, Ki, Kd, REVERSE);

void setup() {
  Serial.begin(9600);

  pinMode(PUMP_PWM_PIN, OUTPUT);
  analogWrite(PUMP_PWM_PIN, 0);

  sensors.begin();

  tempPID.SetMode(AUTOMATIC);
  tempPID.SetOutputLimits(0, 255);
  tempPID.SetSampleTime(1000); // ms; water bath is slow, no need to go faster
}

void loop() {
  sensors.requestTemperatures();
  double reading = sensors.getTempCByIndex(0);

  // DallasTemperature returns -127 (DEVICE_DISCONNECTED_C) on sensor fault.
  // Fail SAFE means max cooling here, since the heater can't be switched off
  // in software -- better to over-cool on a bad reading than under-cool.
  bool sensorFault = (reading == DEVICE_DISCONNECTED_C) || (reading < -10) || (reading > 120);

  if (sensorFault) {
    analogWrite(PUMP_PWM_PIN, 255);
    Serial.println("SENSOR FAULT -- coolant pump forced to MAX (fail-safe)");
    delay(1000);
    return;
  }

  currentTempC = reading;

  // Hard safety backstop, independent of the PID/setpoint.
  if (currentTempC >= MAX_SAFE_TEMP_C) {
    analogWrite(PUMP_PWM_PIN, 255);
    Serial.print("OVER TEMP LIMIT ("); Serial.print(currentTempC);
    Serial.println("C) -- coolant pump forced to MAX");
    delay(1000);
    return;
  }

  tempPID.Compute();
  analogWrite(PUMP_PWM_PIN, (int)pumpPwm);

  Serial.print("temp="); Serial.print(currentTempC);
  Serial.print("C target="); Serial.print(targetTempC);
  Serial.print("C pumpPwm="); Serial.println((int)pumpPwm);

  delay(200);
}

/*
 * WIRING NOTES (fully solderless -- driver modules + screw terminals only):
 *
 * DS18B20 (OneWire, 3-wire external power mode):
 *   VDD  -> Arduino 5V
 *   GND  -> Arduino GND
 *   DATA -> Arduino pin 2, with a 4.7k resistor from DATA to 5V (pull-up)
 *   (a waterproof DS18B20 probe with pre-attached wires avoids any breakout
 *    board handling at all)
 *
 * Heater -- NOT wired to the Arduino:
 *   12V+ supply -> [inline 15A blade fuse] -> heater(+)
 *   heater(-)   -> 12V supply GND
 *   That's it. Runs continuously whenever the 12V supply is on. Add a simple
 *   manual switch inline if you want an easy way to turn it off by hand.
 *
 * Coolant pump (via solderless MOSFET driver breakout module):
 *   Module SIG  <- Arduino pin 9
 *   Module VCC  <- Arduino 5V (logic power; check your module's requirements)
 *   Module GND  <- Arduino GND
 *   Module screw terminals: pump supply+ / pump supply- on one side,
 *                           pump(+) / pump(-) on the other, per the module's
 *                           silkscreen labeling
 *
 * CALIBRATION / TUNING NOTES:
 *
 * 1. Bench-test cooling capacity FIRST: heater at full power, pump at pumpPwm
 *    = 255, confirm temperature plateaus below MAX_SAFE_TEMP_C rather than
 *    climbing indefinitely. If it doesn't plateau, the coil/reservoir can't
 *    keep up and this single-actuator approach won't hold setpoint.
 * 2. Verify DS18B20 readings against a known thermometer before trusting
 *    the control loop.
 * 3. Start PID tuning with Ki = Kd = 0, raise Kp until you see reasonable
 *    response without oscillation, then add Ki to remove steady-state
 *    offset, then Kd if there's overshoot on setpoint changes.
 * 4. MAX_SAFE_TEMP_C is a backstop for the pump's response, not a substitute
 *    for the heater's own fuse -- the fuse is the only thing that protects
 *    against a wiring fault since the heater isn't software-controlled.
 */
