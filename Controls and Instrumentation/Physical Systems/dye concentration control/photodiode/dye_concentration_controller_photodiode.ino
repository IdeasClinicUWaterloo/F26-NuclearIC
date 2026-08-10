// Physical dye concentration control system -- photodiode + LED version
// Arduino + LED/photodiode transmittance sensor + 3x solderless MOSFET
// driver breakout modules (one per pump, direct PWM pins -- no motor
// shield, no I2C, no soldering required to assemble)
//
// Sensor: an LED and photodiode mounted facing each other across the
// mixing tank (or a clear section of tubing), so light passes through the
// dyed liquid to reach the photodiode -- same physical principle as a
// colorimeter (Beer-Lambert law: more dye = more light absorbed = lower
// reading). The LED is blinked on/off each reading to cancel out ambient
// light, rather than left constantly on -- see readSignal() below.
//
// Loop 1 (feedback):     PID on measured concentration -> dye_pwm, water_pwm
// Loop 2 (feed-forward): drain_pwm chosen so drain outflow ~= dye+water inflow,
//                        using per-pump PWM->flow calibration curves.
//
// All calibration numbers below are PLACEHOLDERS. Replace after measuring
// each pump's actual mL/min at a few PWM steps, and the sensor's actual
// clear-water reading (see calibration notes at bottom).

#include <PID_v1.h>

// ---------------- Pins ----------------
// Each pump gets its own solderless MOSFET driver module: Arduino PWM pin ->
// module SIG, Arduino 5V -> module VCC, Arduino GND -> module GND. Pump +
// its own supply connect to the module's screw terminals.
const int DYE_PUMP_PIN   = 5;
const int WATER_PUMP_PIN = 6;
const int DRAIN_PUMP_PIN = 3;

// Photodiode/LED transmittance sensor
// No dedicated photodiode on hand? A second LED works reverse-biased as the
// receiver (cathode -> 5V, anode -> A0 node -> pull-down resistor -> GND) --
// see WIRING NOTES at bottom for polarity and resistor-value details.
const int LED_PIN        = 11; // -> resistor -> LED -> GND
const int PHOTODIODE_PIN = A0; // 5V -> photodiode -> A0 node -> resistor -> GND

// ---------------- Concentration PID ----------------
double measuredConcentration = 0.0;
double targetConcentration   = 50.0;   // placeholder units, e.g. % of max dye
double pidOutput              = 0.0;    // -255..255 : +ve = need more dye, -ve = need more water

// Tune these after you see real step-response behavior
double Kp = 4.0, Ki = 0.5, Kd = 0.2;
PID concPID(&measuredConcentration, &pidOutput, &targetConcentration, Kp, Ki, Kd, DIRECT);

// ---------------- Reference reading (calibrate against clear water) ----------------
int clearRef = 900; // placeholder: ambient-compensated photodiode reading with pure water in tank

// ---------------- PWM -> flow (mL/min) calibration ----------------
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

// ---------------- Pump PWM state ----------------
int dyePwm = 0, waterPwm = 0, drainPwm = 0;

// Ambient-compensated photodiode read: measures with the LED off, then on,
// and subtracts -- cancels out room lighting/ambient light so only the
// LED's own light (attenuated by the dye) is measured. Doesn't need to be
// fast; the liquid changes over seconds, not milliseconds.
int readSignal() {
  digitalWrite(LED_PIN, LOW);
  delay(10);
  int ambientReading = analogRead(PHOTODIODE_PIN);

  digitalWrite(LED_PIN, HIGH);
  delay(10);
  int combinedReading = analogRead(PHOTODIODE_PIN);

  digitalWrite(LED_PIN, LOW); // leave LED off between readings
  return combinedReading - ambientReading;
}

void setup() {
  Serial.begin(9600);

  pinMode(DYE_PUMP_PIN, OUTPUT);
  pinMode(WATER_PUMP_PIN, OUTPUT);
  pinMode(DRAIN_PUMP_PIN, OUTPUT);
  analogWrite(DYE_PUMP_PIN, 0);
  analogWrite(WATER_PUMP_PIN, 0);
  analogWrite(DRAIN_PUMP_PIN, 0);

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  concPID.SetMode(AUTOMATIC);
  concPID.SetOutputLimits(-255, 255);
  concPID.SetSampleTime(500); // ms, tune to your tank's mixing/settling time
}

void loop() {
  // ---- 1. Read sensor, convert to concentration ----
  int signal = readSignal();

  // Placeholder absorbance-style estimate. Replace with a real calibration
  // curve (measure `signal` at several known dye concentrations, fit a curve).
  double absorbance = log10((double)clearRef / max(signal, 1));
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
  analogWrite(DYE_PUMP_PIN, dyePwm);
  analogWrite(WATER_PUMP_PIN, waterPwm);
  analogWrite(DRAIN_PUMP_PIN, drainPwm);

  // ---- Debug ----
  Serial.print("signal:"); Serial.print(signal);
  Serial.print(",conc:"); Serial.print(measuredConcentration);
  Serial.print(",dyePwm:"); Serial.print(dyePwm);
  Serial.print(",waterPwm:"); Serial.print(waterPwm);
  Serial.print(",drainPwm:"); Serial.println(drainPwm);

  delay(100);
}

/*
 * WIRING NOTES (fully solderless -- driver modules + jumper wires only):
 *
 * LED/photodiode transmittance sensor (mount LED and photodiode facing each
 * other across the mixing tank or a clear section of tubing, from OUTSIDE
 * the tank wall -- no need to submerge either component):
 *   Emitter LED anode   -> resistor (~220-330 ohm) -> Arduino D11
 *   Emitter LED cathode -> GND
 *   Photodiode  -> 5V -> photodiode -> A0 node -> resistor (~10k) -> GND
 *
 *   No photodiode on hand -- using a second LED as the receiver instead:
 *   an LED's junction works as a photodiode when REVERSE biased (opposite
 *   polarity from a normal LED hookup). Wire it:
 *     Receiver LED cathode -> Arduino 5V
 *     Receiver LED anode   -> A0 node -> pull-down resistor -> GND
 *   Backwards and it won't conduct at all. Also: an LED's reverse-bias
 *   photocurrent is much smaller than a real photodiode's, so bump the
 *   pull-down resistor way up (try 1M-10M ohm instead of 10k) to get a
 *   measurable voltage swing. And an LED only absorbs light at or above
 *   its own bandgap energy (roughly, wavelength <= what it emits) --
 *   use a receiver LED the same color as the emitter, or a shorter
 *   wavelength/bluer one, or it may not detect the emitter's light at all.
 *
 * Each pump (via its own solderless MOSFET driver breakout module):
 *   Module SIG <- Arduino pin (5 = dye, 6 = water, 3 = drain)
 *   Module VCC <- Arduino 5V
 *   Module GND <- Arduino GND
 *   Module screw terminals: pump supply+ / pump supply- on one side,
 *                           pump(+) / pump(-) on the other
 *   All three pumps can share one 3V supply rail -- do not power them from
 *   the Arduino's 5V rail.
 *
 * CALIBRATION / TUNING NOTES:
 *
 * 1. clearRef:
 *    Fill tank with pure water (0% dye), call readSignal() (or watch the
 *    "signal:" debug print), record the value. Replace the clearRef
 *    placeholder with this number.
 *
 * 2. Check for saturation/weak signal:
 *    Test your expected max dye concentration and confirm the reading
 *    doesn't bottom out near 0 (too much absorption, path length or dye
 *    too strong) and isn't barely different from clearRef at low
 *    concentrations (too little absorption, signal too weak). This is
 *    especially worth checking if you're using a receiver LED instead of a
 *    real photodiode -- its sensitivity is much lower, so the usable range
 *    may be narrower than expected. Adjust the pull-down resistor value or
 *    LED brightness/resistor if the usable range is too narrow.
 *
 * 3. Flow curves (dyeCal / waterCal / drainCal):
 *    For each pump: run at pwm = 64, 128, 192, 255 for a fixed time (e.g. 30s),
 *    measure mL collected, compute mL/min. Fit a line (or swap the linear
 *    model above for a lookup table if the curve is non-linear).
 *
 * 4. Concentration curve:
 *    Make several known dye/water mixtures, record `signal` (or computed
 *    absorbance) at each, fit measuredConcentration properly instead of
 *    the placeholder scale factor above.
 *
 * 5. PID gains (Kp/Ki/Kd):
 *    Start with Ki=Kd=0, raise Kp until you see reasonable response speed
 *    without oscillation, then add Ki to kill steady-state error, then Kd
 *    if overshoot is a problem.
 */
