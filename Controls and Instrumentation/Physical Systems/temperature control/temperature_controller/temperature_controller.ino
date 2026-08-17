// Physical aluminium-plate temperature control system
// Arduino + DS18B20 (OneWire) probe
//         + silicone heater pad driven through a relay module
//         + coolant pump driven through a DRV8833 low-voltage motor driver
//
// TWO actuators, ONE PID, SPLIT-RANGE output:
//
//        -255 ............. 0 ............. +255
//     full cooling       neither         full heat
//      (pump PWM)      (both off)     (heater relay)
//
// A single PID computes one "thermal demand" number. Positive demand runs the
// heater, negative demand runs the coolant pump, and neither runs at zero. The
// split guarantees the two actuators can never fight each other (heating and
// cooling simultaneously), which is what would happen if you gave each one its
// own independent loop.
//
// NOTE: this is a rework of the earlier revision of this sketch, where the
// heater ran at constant power and was NOT wired to the Arduino (single
// actuator, PID in REVERSE mode modulating only cooling). Because the heater
// is software-controlled now:
//   - The PID is DIRECT, not REVERSE. Output rises when the plate is too COLD.
//   - The fail-safe inverts. Previously a fault meant "pump to max" because the
//     heater could not be switched off. Now the primary safe action is to CUT
//     THE HEATER; max pump is only the secondary action.
//   - You no longer need the coolant loop to out-cool the heater at full power, since
//     the heat input is now modulated. The pump only has to reject the residual
//     heat while the heater is off.
//
// The heater relay is driven by time-proportional control ("slow PWM"): the
// PID's heat demand becomes an on-fraction of a multi-second window. You must
// NOT analogWrite() a mechanical relay -- at 490 Hz it would buzz, never fully
// close, and destroy its contacts in minutes. The window plus a minimum dwell
// time keeps switching down to a couple of transitions per window, which the
// plate's thermal mass smooths out.

#include <OneWire.h>
#include <DallasTemperature.h>
#include <PID_v1.h>

// ---------------- Pins (match the confirmed physical wiring) ----------------
const int ONE_WIRE_BUS     = 4;  // DS18B20 data pin (needs 4.7k pull-up to 5V)
const int HEATER_RELAY_PIN = 2;  // relay module signal in -> silicone heater pad
const int PUMP_IN1_PIN     = 10; // PWM -> DRV8833 IN1 (pump speed)
const int PUMP_IN2_PIN     = 11; // DRV8833 IN2, held LOW in software (fixed direction)

// DFRobot relay modules are ACTIVE HIGH: a HIGH on the signal pin energises the
// coil and connects COM to NO. (This is the opposite of the cheap blue
// opto-isolated SRD-05VDC modules, which are active LOW -- if you ever swap the
// module out, re-check this.) Active high is the safer polarity here: an Arduino
// that is reset, unprogrammed, or unpowered leaves the pin low, so the heater
// defaults to off.
// Verify it anyway with the click test in the commissioning notes below. Getting
// this backwards means the pad runs at 100% whenever the sketch thinks it is
// off, including during a fault.
const bool RELAY_ACTIVE_LOW = false;

// ---------------- Setpoint ----------------
double targetTempC = 35.0; // adjustable setpoint
const double MAX_SETPOINT_C = 45.0;

// ---------------- Safety limits ----------------
// Backstop sits well above the setpoint so ordinary tuning overshoot does not
// trip it, but far below anything that would damage the pad, tubing or plate.
const double MAX_SAFE_TEMP_C = 55.0;

// Plausible-reading window. Anything outside this is treated as a sensor fault
// rather than a real temperature.
const double MIN_PLAUSIBLE_C = -10.0;
const double MAX_PLAUSIBLE_C = 120.0;

// If no valid reading arrives within this long, assume the sensor died mid-run
// (cut cable, loose pull-up) and fail safe even though the last value looked OK.
const unsigned long SENSOR_TIMEOUT_MS = 3000;

// ---------------- Heater relay: time-proportional control ----------------
const unsigned long HEATER_WINDOW_MS   = 4000; // one full on/off cycle
const unsigned long MIN_RELAY_DWELL_MS = 500;  // shortest on OR off period
unsigned long windowStartMs = 0;
bool heaterOn = false;

// ---------------- Coolant pump ----------------
// Small 3V submersible pumps stall below roughly a quarter duty: they hum and
// draw current without moving water. Map any non-zero cooling demand into
// [MIN_PUMP_PWM, 255] so "a little cooling" is still real flow.
// Find your pump's actual stall point by hand before trusting this number.
const int MIN_PUMP_PWM = 60;

// ---------------- Sensor ----------------
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

// DS18B20 at 12-bit resolution needs ~750 ms per conversion. We do NOT block
// for it: blocking would freeze the relay window and smear its timing. Instead
// we kick off a conversion, carry on running the control loop, and collect the
// result once it is ready.
const unsigned long CONVERSION_MS = 800;
bool conversionPending = false;
unsigned long conversionStartMs = 0;
unsigned long lastGoodReadingMs = 0;
bool haveReading = false;

// ---------------- PID ----------------
double currentTempC  = 0.0;
double controlOutput = 0.0; // -255 (full cool) .. +255 (full heat)

// Starting points only -- tune against your own rig (see notes at the bottom).
// Error is in degrees C, so Kp = 60 means 1 C below setpoint asks for roughly
// 24% heater duty, and the heater saturates around 4.3 C of error.
double Kp = 60.0, Ki = 0.6, Kd = 15.0;

// DIRECT: output rises as the measured temperature falls below the setpoint,
// i.e. too cold -> more heat. The cooling half of the range is reached by the
// output going negative when the plate overshoots, so there is no need for the
// REVERSE trick the single-actuator version used.
PID tempPID(&currentTempC, &controlOutput, &targetTempC, Kp, Ki, Kd, DIRECT);

// ---------------- Actuator helpers ----------------
void setHeater(bool on) {
  heaterOn = on;
  if (RELAY_ACTIVE_LOW) {
    digitalWrite(HEATER_RELAY_PIN, on ? LOW : HIGH);
  } else {
    digitalWrite(HEATER_RELAY_PIN, on ? HIGH : LOW);
  }
}

void setPump(int pwm) {
  if (pwm < 0)   pwm = 0;
  if (pwm > 255) pwm = 255;
  analogWrite(PUMP_IN1_PIN, pwm);
}

void setup() {
  Serial.begin(9600);

  // Write the OFF level BEFORE switching the pin to an output. On AVR the port
  // register defaults to 0, so pinMode(OUTPUT) drives the pin LOW -- harmless on
  // the active-high DFRobot module (LOW is off), but a momentary heater-ON pulse
  // at every reset if RELAY_ACTIVE_LOW is ever flipped back to true. Setting the
  // register while the pin is still an input makes this correct either way.
  digitalWrite(HEATER_RELAY_PIN, RELAY_ACTIVE_LOW ? HIGH : LOW);
  pinMode(HEATER_RELAY_PIN, OUTPUT);
  setHeater(false);

  pinMode(PUMP_IN1_PIN, OUTPUT);
  pinMode(PUMP_IN2_PIN, OUTPUT);
  // IN2 low + PWM on IN1 = one fixed direction, coasting between PWM pulses.
  // The pin is wired to the Arduino rather than to GND, so it must be driven
  // low here; leaving it floating would let the driver brake or reverse.
  digitalWrite(PUMP_IN2_PIN, LOW);
  setPump(0);

  sensors.begin();
  sensors.setResolution(12);
  sensors.setWaitForConversion(false); // non-blocking reads

  if (sensors.getDeviceCount() == 0) {
    Serial.println("WARNING: no DS18B20 found on pin 4 -- check the 4.7k pull-up to 5V");
  }

  tempPID.SetMode(AUTOMATIC);
  tempPID.SetOutputLimits(-255, 255); // negative half = cooling, positive = heating
  tempPID.SetSampleTime(1000);        // ms; the plate is thermal, so 1 Hz is sufficient

  windowStartMs = millis();
  sensors.requestTemperatures();
  conversionStartMs = millis();
  conversionPending = true;
}

// Cut heat, run the pump flat out, and park the PID. Used for both sensor
// faults and the over-temperature backstop.
void failSafe(const char *reason) {
  setHeater(false);
  setPump(255);
  controlOutput = -255.0;
  // MANUAL freezes the integrator so it cannot wind up while we are overriding
  // it. Returning to AUTOMATIC later re-seeds it from controlOutput, giving a
  // bumpless handover instead of a jump. (The proportional term still dominates
  // on resume, so seeding at -255 does not stall the recovery.)
  tempPID.SetMode(MANUAL);

  // Throttled, because this runs every pass while the fault persists -- and it
  // always fires for the first conversion at boot, before any reading exists.
  static unsigned long lastFaultPrintMs = 0;
  unsigned long now = millis();
  if (now - lastFaultPrintMs >= 1000) {
    lastFaultPrintMs = now;
    Serial.print("FAIL-SAFE: ");
    Serial.println(reason);
  }
}

void loop() {
  // Keep participant-set targets below the apparatus limit.
  if (targetTempC > MAX_SETPOINT_C) {
    targetTempC = MAX_SETPOINT_C;
  }

  unsigned long now = millis();

  // ---- collect a finished conversion, then immediately start the next ----
  if (conversionPending && (now - conversionStartMs >= CONVERSION_MS)) {
    double reading = sensors.getTempCByIndex(0);
    conversionPending = false;

    bool valid = (reading != DEVICE_DISCONNECTED_C) &&
                 (reading > MIN_PLAUSIBLE_C) &&
                 (reading < MAX_PLAUSIBLE_C);
    if (valid) {
      currentTempC = reading;
      lastGoodReadingMs = now;
      haveReading = true;
    }

    sensors.requestTemperatures();
    conversionStartMs = now;
    conversionPending = true;
  }

  // ---- fault checks ----
  bool sensorFault = !haveReading || (now - lastGoodReadingMs > SENSOR_TIMEOUT_MS);
  bool overTemp    = haveReading && (currentTempC >= MAX_SAFE_TEMP_C);

  if (sensorFault || overTemp) {
    failSafe(sensorFault ? "no valid DS18B20 reading -- heater OFF, pump MAX"
                         : "over temperature limit -- heater OFF, pump MAX");
    delay(200);
    return;
  }

  // Coming back from a fault: hand control back to the PID.
  if (tempPID.GetMode() == MANUAL) {
    tempPID.SetMode(AUTOMATIC);
  }

  tempPID.Compute(); // internally rate-limited to SetSampleTime

  // ---- split the single PID output across the two actuators ----
  double heatDemand = (controlOutput > 0) ?  controlOutput : 0; // 0..255
  double coolDemand = (controlOutput < 0) ? -controlOutput : 0; // 0..255

  // Heater: time-proportional. Clamp the on-time away from both ends of the
  // window so the relay always gets at least MIN_RELAY_DWELL_MS on and off,
  // instead of chattering on a 1% duty request.
  while (now - windowStartMs >= HEATER_WINDOW_MS) {
    windowStartMs += HEATER_WINDOW_MS;
  }
  unsigned long onMs = (unsigned long)((heatDemand / 255.0) * HEATER_WINDOW_MS + 0.5);
  if (onMs < MIN_RELAY_DWELL_MS) {
    onMs = 0;                                    // too small to be worth switching
  } else if (onMs > HEATER_WINDOW_MS - MIN_RELAY_DWELL_MS) {
    onMs = HEATER_WINDOW_MS;                     // effectively full power
  }
  setHeater((now - windowStartMs) < onMs);

  // Pump: real PWM, but skip the dead zone below the stall threshold.
  int pumpPwm = 0;
  if (coolDemand > 0) {
    pumpPwm = MIN_PUMP_PWM + (int)((coolDemand / 255.0) * (255 - MIN_PUMP_PWM));
  }
  setPump(pumpPwm);

  // ---- throttled telemetry (the loop itself runs far too fast to print every pass) ----
  static unsigned long lastPrintMs = 0;
  if (now - lastPrintMs >= 1000) {
    lastPrintMs = now;
    Serial.print("temp=");     Serial.print(currentTempC, 2);
    Serial.print("C target="); Serial.print(targetTempC, 1);
    Serial.print("C out=");    Serial.print((int)controlOutput);
    Serial.print(" heater=");  Serial.print(heaterOn ? "ON " : "off");
    Serial.print(" duty=");    Serial.print((int)((onMs * 100UL) / HEATER_WINDOW_MS));
    Serial.print("% pump=");   Serial.println(pumpPwm);
  }

  delay(10); // keep the loop responsive: the relay window and PWM update here
}

/*
 * WIRING NOTES (matches the pins at the top of this file)
 *
 * DS18B20 probe (OneWire, 3-wire external power mode):
 *   VDD  -> Arduino 5V
 *   GND  -> Arduino GND
 *   DATA -> Arduino pin 4, PLUS a 4.7k resistor from DATA to 5V (pull-up).
 *           This resistor is not optional -- without it every read returns -127.
 *
 * Silicone heater pad, via DFRobot relay module (active HIGH, 3-pin Gravity
 * header: signal / VCC / GND, plus a screw terminal for NC / COM / NO):
 *   module VCC (red)    -> Arduino 5V   (the coil draws tens of mA, more than one
 *   module GND (black)  -> Arduino GND   I/O pin should source -- never power the
 *   module signal (green/blue) -> pin 2  module from D2 itself)
 *   Pad supply (+) -> relay COM
 *   relay NO       -> pad (+)     (NO, so a dead Arduino or lost 5V = heater off.
 *                                  Do NOT use NC -- that inverts it and the pad
 *                                  runs whenever the board is off.)
 *   Pad supply (-) -> pad (-)
 *   Two checks before the pad goes anywhere near water:
 *   a) Confirm the polarity. Load this sketch with the pad DISCONNECTED and
 *      watch the module's LED: it should be dark at reset, then light and click
 *      as the loop calls for heat (with a cold probe it will sit at 100% duty,
 *      so it should latch on and stay on). If it is lit at reset instead, set
 *      RELAY_ACTIVE_LOW = true.
 *   b) Confirm the relay's contact rating exceeds the pad's current. The DFRobot
 *      modules are typically rated 10 A, so a low-voltage pad is comfortable.
 *      But if the pad is a MAINS (110/230 V) part rather than a low-voltage one,
 *      the switched side is lethal and the Gravity module's open screw terminal
 *      is not an appropriate way to carry it -- that needs a properly enclosed,
 *      strain-relieved build with no exposed conductors, sharing a breadboard
 *      with nothing. Get it checked by someone qualified before energising it.
 *
 * Coolant pump, via DRV8833 OUT1/OUT2:
 *   IN1 <- Arduino pin 10 (PWM, speed)
 *   IN2 <- Arduino pin 11 (driven LOW by this sketch, fixed direction)
 *   GND  <- common ground shared with Arduino GND
 *   VCC  <- motor-driver supply (+), set for the selected pump
 *   OUT1/OUT2 -> the pump's two leads
 *   If exposed, SLP/SLEEP/nSLEEP -> Arduino 5V. Modules that only expose
 *   IN1-IN4 handle the sleep connection on the board.
 *
 *   The selected pump is rated for 3 V. Do NOT connect the 12 V heater supply
 *   to this motor-driver circuit.
 *
 * COMMISSIONING ORDER (do these in sequence, do not skip ahead)
 *
 * 1. Sensor alone. Nothing else connected. Confirm the serial output tracks a
 *    known-good thermometer at room temperature and in warm water. Then mount
 *    it to the plate and compare against a contact thermometer. A stuck -127
 *    or 85.0 means a wiring/pull-up problem, not a control problem.
 * 2. Pump alone. Heater unplugged. Confirm the pump actually moves water and
 *    find the lowest PWM at which it reliably starts -- put that in
 *    MIN_PUMP_PWM. If it will not start from rest below ~100, raise the value.
 * 3. Relay alone, heater still disconnected. Verify polarity per (a) above.
 * 4. Open-loop heater test. Heater connected, pump off. Watch how fast the plate
 *    climbs and how long it keeps rising after you cut power -- that lag is the
 *    dead time, and it is what makes the loop overshoot. A long lag means you
 *    need a smaller Kp and a larger Kd.
 * 5. Closed loop, and only now tune. Set Ki = Kd = 0, raise Kp until the plate
 *    reaches roughly 35 C with a steady oscillation, then halve it. Add Ki to
 *    remove the remaining steady-state offset below setpoint -- go gently, it
 *    can cause slow creeping overshoot. Add Kd last, to damp overshoot when you
 *    step the setpoint.
 * 6. Verify the backstop deliberately. With the rig at temperature, temporarily
 *    lower MAX_SAFE_TEMP_C below the current reading and confirm the heater cuts
 *    and the pump goes to full. Then restore it. Also unplug the probe mid-run
 *    and confirm the same. A safety path you have never seen fire is not a
 *    safety path.
 *
 * WHY 35 C IS THE EASY DIRECTION TO GET WRONG
 *
 * At a 35 C setpoint, ambient is ~15 C below you and the pad is the only thing
 * pushing up, so the loop will spend most of its life on the heating half of the
 * range and barely touch the pump. That is expected. The pump matters during
 * overshoot recovery and setpoint step-downs, which is exactly when a badly
 * tuned Ki will have already carried you past 35 C.
 */
