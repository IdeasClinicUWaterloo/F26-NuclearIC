// Physical dye concentration control system
// Arduino + Adafruit Motor Shield V2 (I2C) + Adafruit TCS34725 color sensor (I2C)

// Loop 1 (feedback):     PID on measured concentration -> dye_pwm, water_pwm
// Loop 2 (feed-forward): drain_pwm chosen so drain outflow ~= dye+water inflow,
//                        using per-pump PWM->flow calibration curves.

// All calibration numbers below are PLACEHOLDERS. Replace after measuring
// each pump's actual mL/min at a few PWM steps (see calibration notes at bottom).

#include <Wire.h>
#include <Adafruit_MotorShield.h>
#include "Adafruit_TCS34725.h"
#include <PID_v1.h>

// Hardware handles 
Adafruit_MotorShield AFMS = Adafruit_MotorShield();
Adafruit_DCMotor *dyePump   = AFMS.getMotor(1);
Adafruit_DCMotor *waterPump = AFMS.getMotor(2);
Adafruit_DCMotor *drainPump = AFMS.getMotor(3);

Adafruit_TCS34725 tcs = Adafruit_TCS34725(TCS34725_INTEGRATIONTIME_50MS, TCS34725_GAIN_4X);

// Concentration PID
double measuredConcentration = 0.0;
double targetConcentration   = 50.0;   // placeholder units, e.g. % of max dye
double pidOutput              = 0.0;    // -255..255 : +ve = need more dye, -ve = need more water

// Tune these after you see real step-response behavior
double Kp = 4.0, Ki = 0.5, Kd = 0.2;
PID concPID(&measuredConcentration, &pidOutput, &targetConcentration, Kp, Ki, Kd, DIRECT);

//  Reference light reading (calibrate against clear water) 
uint16_t clearRef = 800; // placeholder: measured "clear" channel value with pure water in tank

//  PWM -> flow (mL/min) calibration 
// Placeholder LINEAR fits: flow = a * pwm + b. Replace a/b per pump after
// measuring actual mL over a timed interval at a few PWM values (0..255).
struct FlowCal { double a; double b; };
FlowCal dyeCal   = {0.40, 0.0};   // e.g. ~102 mL/min at pwm=255
FlowCal waterCal = {0.45, 0.0};
FlowCal drainCal = {0.50, 0.0};   // drain pump's own curve -- likely different from the other two

double pwmToFlow(int pwm, FlowCal cal) {
  return cal.a * pwm + cal.b;
}

int flowToPwm(double flow, FlowCal cal) {
  if (cal.a == 0) return 0;
  int pwm = (int)((flow - cal.b) / cal.a);
  return constrain(pwm, 0, 255);
}

//  Pump PWM state 
int dyePwm = 0, waterPwm = 0, drainPwm = 0;

void setup() {
  Serial.begin(9600);

  if (!AFMS.begin()) {
    Serial.println("Motor Shield not found!");
    while (1);
  }

  if (!tcs.begin()) {
    Serial.println("TCS34725 not found!");
    while (1);
  }

  dyePump->run(FORWARD);
  waterPump->run(FORWARD);
  drainPump->run(FORWARD);
  dyePump->setSpeed(0);
  waterPump->setSpeed(0);
  drainPump->setSpeed(0);

  concPID.SetMode(AUTOMATIC);
  concPID.SetOutputLimits(-255, 255);
  concPID.SetSampleTime(500); // ms, tune to your tank's mixing/settling time
}

void loop() {
  // ---- 1. Read sensor, convert to concentration ----
  uint16_t r, g, b, c;
  tcs.getRawData(&r, &g, &b, &c);

  // Placeholder absorbance-style estimate. Replace with a real calibration
  // curve (measure `c` at several known dye concentrations, fit a curve).
  double absorbance = log10((double)clearRef / max((int)c, 1));
  measuredConcentration = absorbance * 100.0; // placeholder scale factor

  // ---- 2. Concentration PID ----
  concPID.Compute();

  if (pidOutput >= 0) {
    dyePwm   = constrain((int)pidOutput, 0, 255);
    waterPwm = 0;
  } else {
    dyePwm   = 0;
    waterPwm = constrain((int)(-pidOutput), 0, 255);
  }

  // ---- 3. Feed-forward drain: match combined inflow ----
  double qIn = pwmToFlow(dyePwm, dyeCal) + pwmToFlow(waterPwm, waterCal);
  drainPwm = flowToPwm(qIn, drainCal);

  // ---- 4. Apply ----
  dyePump->setSpeed(dyePwm);
  waterPump->setSpeed(waterPwm);
  drainPump->setSpeed(drainPwm);

  // ---- Debug ----
  Serial.print("conc="); Serial.print(measuredConcentration);
  Serial.print(" dyePwm="); Serial.print(dyePwm);
  Serial.print(" waterPwm="); Serial.print(waterPwm);
  Serial.print(" drainPwm="); Serial.println(drainPwm);

  delay(100);
}

/*
 * CALIBRATION NOTES (do this once hardware is wired up):
 *
 * 1. Flow curves (dyeCal / waterCal / drainCal):
 *    For each pump: run at pwm = 64, 128, 192, 255 for a fixed time (e.g. 30s),
 *    measure mL collected, compute mL/min. Fit a line (or swap the linear
 *    model above for a lookup table if the curve is non-linear).
 *
 * 2. clearRef:
 *    Fill tank with pure water (0% dye), read tcs.getRawData(), record `c`.
 *
 * 3. Concentration curve:
 *    Make several known dye/water mixtures, record `c` (or computed
 *    absorbance) at each, fit measuredConcentration properly instead of
 *    the placeholder scale factor above.
 *
 * 4. PID gains (Kp/Ki/Kd):
 *    Start with Ki=Kd=0, raise Kp until you see reasonable response speed
 *    without oscillation, then add Ki to kill steady-state error, then Kd
 *    if overshoot is a problem.
 */
