// temperature_controller_sim.ino
//
// Same PID control loop as temperature_controller.ino, but the DS18B20 is
// replaced by a simulated "plant" -- lets you test and tune the PID logic,
// and watch the real pump respond on the bench, with no sensor wired up.
//
// The simulated temperature reacts to the pump's actual PWM output using a
// simple heat-balance model: constant heat in (standing in for the constant
// heater), heat removed proportional to pump speed, slow drift toward
// ambient. The constants below are arbitrary/for-demo, not calibrated to
// real physical units -- they're just tuned to produce a plausible slow,
// water-bath-like response so the PID has something realistic to react to.
//
// Swap back to temperature_controller.ino once the DS18B20 is wired up --
// the PID block itself (gains, mode, output limits) is identical, so
// whatever you tune here carries over as a starting point.

#include <PID_v1.h>

const int PUMP_PWM_PIN = 10; // match your real wiring/shield pin (confirmed IN1 -> D10)

const double MAX_SAFE_TEMP_C = 90.0;

// ---------------- Simulated plant ----------------
double simulatedTempC      = 25.0; // starting temperature
const double AMBIENT_C     = 22.0;
const double HEAT_RATE     = 5.3;   // degC/sec added by the constant heater
const double COOL_GAIN     = 0.04;  // degC/sec removed, per PWM count, at full pump speed
const double AMBIENT_LOSS  = 0.1;   // passive drift toward ambient, per degC of difference, per sec
// (tuned for a ~10s time constant -- convergence visible within roughly
// 30-50s. Still arbitrary/for-demo, not physically calibrated.)

unsigned long lastUpdateMs = 0;

// ---------------- Temperature PID (identical to the real sketch) ----------------
double currentTempC = 0.0;
double targetTempC  = 60.0; // placeholder setpoint, change as needed
double pumpPwm      = 0.0;

double Kp = 20.0, Ki = 0.8, Kd = 4.0;
PID tempPID(&currentTempC, &pumpPwm, &targetTempC, Kp, Ki, Kd, REVERSE);

void setup() {
  Serial.begin(9600);

  pinMode(PUMP_PWM_PIN, OUTPUT);
  analogWrite(PUMP_PWM_PIN, 0);

  tempPID.SetMode(AUTOMATIC);
  tempPID.SetOutputLimits(0, 255);
  tempPID.SetSampleTime(1000);

  lastUpdateMs = millis();
}

void loop() {
  unsigned long now = millis();
  double dtSeconds = (now - lastUpdateMs) / 1000.0;
  lastUpdateMs = now;

  // ---- Fake sensor: update the simulated temperature based on pump PWM ----
  double heatIn  = HEAT_RATE;
  double coolOut = COOL_GAIN * pumpPwm;
  double lossOut = AMBIENT_LOSS * (simulatedTempC - AMBIENT_C);
  simulatedTempC += (heatIn - coolOut - lossOut) * dtSeconds;

  currentTempC = simulatedTempC;

  // Hard safety backstop, same as the real sketch.
  if (currentTempC >= MAX_SAFE_TEMP_C) {
    analogWrite(PUMP_PWM_PIN, 255);
    Serial.print("OVER TEMP LIMIT ("); Serial.print(currentTempC);
    Serial.println("C) -- coolant pump forced to MAX");
    delay(200);
    return;
  }

  tempPID.Compute();
  analogWrite(PUMP_PWM_PIN, (int)pumpPwm);

  // Labeled format (Arduino IDE 2.x Serial Plotter shows a proper legend
  // with these names instead of generic "Value1/Value2/Value3"). Older
  // (1.x) Serial Plotter versions may not parse labels -- if yours shows
  // nothing with labels, drop the "name:" prefixes and just print the
  // three numbers comma-separated instead.
  Serial.print("simTempC:"); Serial.print(currentTempC); Serial.print(",");
  Serial.print("targetC:"); Serial.print(targetTempC); Serial.print(",");
  Serial.print("pumpPwm:"); Serial.println(pumpPwm);

  delay(200);
}

/*
 * WHAT TO WATCH FOR:
 *
 * 1. Does the simulated temperature actually climb from 25C toward the
 *    60C setpoint, then level off there (not overshoot wildly, not
 *    oscillate forever)? That's a healthy PID response.
 * 2. At steady state, pumpPwm should settle at some nonzero value (not 0,
 *    not 255) -- that's the pump finding the balance point between the
 *    constant heater's output and the setpoint.
 * 3. Try changing Kp/Ki/Kd here and re-uploading to see the effect on
 *    response speed and overshoot before you ever touch the real sensor --
 *    same tuning process described in temperature_controller.ino's
 *    calibration notes applies here, just faster to iterate on.
 * 4. This simulated plant is intentionally simplistic -- treat gains tuned
 *    here as a starting point to refine once the real DS18B20 and heater
 *    are in place, not a final answer.
 */
