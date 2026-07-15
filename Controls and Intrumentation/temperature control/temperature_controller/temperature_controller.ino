// Physical reactor temperature control system
// Arduino + DS18B20 (OneWire) temperature sensor
// Two actuators, mutually exclusive, driven by one PID:
//   - 12V immersion heater (adds heat)      -> MOSFET/SSR, PWM
//   - coolant pump through copper coil (removes heat via flow rate) -> MOSFET, PWM
//
// PID error > 0 (too cold) -> heater PWM proportional to error, pump off
// PID error < 0 (too hot)  -> pump PWM proportional to |error|, heater off
//
// Heater: Littryee 12V, 120-140W immersion heater -> ~10-11.7A at 12V.
// Use a MOSFET/SSR rated >=20A continuous WITH a heatsink, plus an inline
// ~15A fuse on the 12V supply line. Do not substitute a low-current
// (e.g. ~5A) MOSFET breakout for this load.
//
// Coolant pump: same small submersible pump used elsewhere (~3V, ~100mA) ->
// small logic-level MOSFET switch is enough, but unlike the heater this is
// an inductive load and needs a flyback diode across its terminals.

#include <OneWire.h>
#include <DallasTemperature.h>
#include <PID_v1.h>

// ---------------- Pins ----------------
const int ONE_WIRE_BUS   = 2;  // DS18B20 data pin (needs 4.7k pull-up to 5V)
const int HEATER_PWM_PIN = 9;  // PWM pin -> heater MOSFET gate / SSR control input
const int PUMP_PWM_PIN   = 10; // PWM pin -> coolant pump MOSFET gate

// ---------------- Safety limits ----------------
const double MAX_SAFE_TEMP_C = 90.0; // hard cutoff regardless of setpoint

// ---------------- Sensor ----------------
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

// ---------------- Temperature PID ----------------
double currentTempC = 0.0;
double targetTempC  = 60.0;   // placeholder setpoint, change as needed
double pidOutput    = 0.0;    // -255..255 : +ve = need more heat, -ve = need more cooling

// Tune these after observing real step-response behavior.
// Water baths are slow (large thermal mass) -> expect to need a fairly
// large Ki relative to Kp, and watch for overshoot from Kd being too low.
double Kp = 20.0, Ki = 0.8, Kd = 4.0;
PID tempPID(&currentTempC, &pidOutput, &targetTempC, Kp, Ki, Kd, DIRECT);

int heaterPwm = 0, pumpPwm = 0;

void setup() {
  Serial.begin(9600);

  pinMode(HEATER_PWM_PIN, OUTPUT);
  pinMode(PUMP_PWM_PIN, OUTPUT);
  analogWrite(HEATER_PWM_PIN, 0); // both off until first good reading
  analogWrite(PUMP_PWM_PIN, 0);

  sensors.begin();

  tempPID.SetMode(AUTOMATIC);
  tempPID.SetOutputLimits(-255, 255); // signed: sign picks heater vs. pump
  tempPID.SetSampleTime(1000);        // ms; water bath is slow, no need to go faster
}

void loop() {
  sensors.requestTemperatures();
  double reading = sensors.getTempCByIndex(0);

  // DallasTemperature returns -127 (DEVICE_DISCONNECTED_C) on sensor fault.
  // Treat any implausible reading as a fault and force both actuators off.
  bool sensorFault = (reading == DEVICE_DISCONNECTED_C) || (reading < -10) || (reading > 120);

  if (sensorFault) {
    analogWrite(HEATER_PWM_PIN, 0);
    analogWrite(PUMP_PWM_PIN, 0);
    Serial.println("SENSOR FAULT -- heater and pump forced OFF");
    delay(1000);
    return;
  }

  currentTempC = reading;

  // Hard safety cutoff, independent of the PID/setpoint: heater off, and
  // actively assist cooling by running the coolant pump at full speed.
  if (currentTempC >= MAX_SAFE_TEMP_C) {
    analogWrite(HEATER_PWM_PIN, 0);
    analogWrite(PUMP_PWM_PIN, 255);
    Serial.print("OVER TEMP LIMIT ("); Serial.print(currentTempC);
    Serial.println("C) -- heater OFF, coolant pump forced to MAX");
    delay(1000);
    return;
  }

  tempPID.Compute();

  if (pidOutput >= 0) {
    heaterPwm = constrain((int)pidOutput, 0, 255);
    pumpPwm   = 0;
  } else {
    heaterPwm = 0;
    pumpPwm   = constrain((int)(-pidOutput), 0, 255);
  }

  analogWrite(HEATER_PWM_PIN, heaterPwm);
  analogWrite(PUMP_PWM_PIN, pumpPwm);

  Serial.print("temp="); Serial.print(currentTempC);
  Serial.print("C target="); Serial.print(targetTempC);
  Serial.print("C heaterPwm="); Serial.print(heaterPwm);
  Serial.print(" pumpPwm="); Serial.println(pumpPwm);

  delay(200);
}

/*
 * WIRING NOTES:
 *
 * DS18B20 (OneWire, 3-wire external power mode):
 *   VDD  -> Arduino 5V
 *   GND  -> Arduino GND
 *   DATA -> Arduino pin 2, with a 4.7k resistor from DATA to 5V (pull-up)
 *
 * Heater path (MOSFET low-side switch example):
 *   12V+ supply -> [15A fuse] -> heater(+)
 *   heater(-)   -> MOSFET drain
 *   MOSFET source -> GND (common ground with Arduino)
 *   MOSFET gate  <- Arduino pin 9, through a ~220 ohm series resistor
 *   MOSFET gate-to-source: ~10k pulldown resistor (prevents floating gate /
 *                           unintended heater-on at power-up before setup() runs)
 *
 * If using a DC SSR instead of a discrete MOSFET, follow the module's own
 * control-input wiring (typically just +control/-control from an Arduino
 * PWM-capable pin, no gate resistor needed) -- check the specific SSR's
 * datasheet for its control-side current draw.
 *
 * Coolant pump path (MOSFET low-side switch, same style as the dye/water
 * pumps -- small logic-level MOSFET is enough at ~100mA):
 *   pump supply+ -> pump(+)
 *   pump(-)      -> MOSFET drain
 *   MOSFET source -> GND (common ground with Arduino)
 *   MOSFET gate  <- Arduino pin 10, through a ~220 ohm series resistor
 *   MOSFET gate-to-source: ~10k pulldown resistor
 *   Flyback diode: cathode to pump supply+, anode to pump(-)/MOSFET drain
 *                  (protects the MOSFET from the motor's inductive kickback
 *                  when switched off -- NOT needed on the heater circuit,
 *                  which is purely resistive)
 *
 * CALIBRATION / TUNING NOTES:
 *
 * 1. Verify DS18B20 readings against a known thermometer before trusting
 *    the control loop.
 * 2. Start PID tuning with Ki = Kd = 0, raise Kp until you see reasonable
 *    response without oscillation, then add Ki to remove steady-state
 *    offset, then Kd if there's overshoot on setpoint changes.
 * 3. MAX_SAFE_TEMP_C is a hard backstop, not the setpoint -- keep it well
 *    above targetTempC but below anything that risks the tank/materials.
 */
