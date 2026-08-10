// Physical dye concentration control system -- AS7265x spectral sensor version
// Arduino UNO R4 Minima + SparkFun AS7265x Triad Spectroscopy Sensor (I2C)
// + 3x solderless MOSFET driver breakout modules (one per pump, direct PWM
// pins)
//
// IMPORTANT (electrical): the AS7265x is a 3.3V device. The R4 Minima's
// Renesas RA4M1 runs its I/O logic at 3.3V natively (unlike the classic
// 5V-logic Uno), so SDA/SCL can go straight to the board's SDA/SCL (or
// A4/A5) pins -- no I2C level shifter needed. Power the sensor from the
// board's 3.3V pin, not 5V.
//
// CHANNEL NAMING: the AS7265x library names channels by letter, not color
// (that's the AS7262's library, a different sensor) -- confirmed against
// SparkFun's own Example1_BasicReadings.ino:
//   A=410nm B=435nm C=460nm D=485nm E=510nm F=535nm G=560nm H=585nm
//   R=610nm I=645nm S=680nm J=705nm T=730nm U=760nm V=810nm W=860nm
//   K=900nm L=940nm
//
// This sensor has WAY more spectral channels (18) than you need for
// tracking one dye's concentration -- treat this as a prototyping-only
// swap. The onboard white/IR/UV LEDs are disabled in setup() since you're
// using your own external emitter LED for transmittance, same as the
// TCS34725 and photodiode versions.
//
// Loop 1 (feedback):     PID on measured concentration -> dye_pwm, water_pwm
// Loop 2 (feed-forward): drain_pwm chosen so drain outflow ~= dye+water inflow,
//                        using per-pump PWM->flow calibration curves.
//
// All calibration numbers below are PLACEHOLDERS, including WHICH channel
// to read -- see calibration notes at bottom.

#include <Wire.h>
#include "SparkFun_AS7265X.h"
#include <PID_v1.h>

AS7265X sensor;

// ---------------- Pins ----------------
const int DYE_PUMP_PIN   = 5;
const int WATER_PUMP_PIN = 6;
const int DRAIN_PUMP_PIN = 3;
// SDA/SCL go straight to the R4 Minima's SDA/SCL (or A4/A5) -- no level
// shifter needed, no dedicated pins to declare here beyond the standard
// I2C bus.

// ---------------- Concentration PID ----------------
double measuredConcentration = 0.0;
double targetConcentration   = 50.0;   // placeholder units, e.g. % of max dye
double pidOutput              = 0.0;    // -255..255 : +ve = need more dye, -ve = need more water

double Kp = 4.0, Ki = 0.5, Kd = 0.2;
PID concPID(&measuredConcentration, &pidOutput, &targetConcentration, Kp, Ki, Kd, DIRECT);

// ---------------- Reference reading (calibrate against clear water) ----------------
float clearRef = 500.0; // placeholder: reading with pure water in tank, on whichever channel you pick

// ---------------- PWM -> flow (mL/min) calibration ----------------
struct FlowCal { double a; double b; };
FlowCal dyeCal   = {0.40, 0.0};
FlowCal waterCal = {0.45, 0.0};
FlowCal drainCal = {0.50, 0.0};

double pwmToFlow(int pwm, FlowCal cal) {
  return cal.a * pwm + cal.b;
}

int flowToPwm(double flow, FlowCal cal) {
  if (cal.a == 0) return 0;
  int pwm = (int)((flow - cal.b) / cal.a);
  return constrain(pwm, 0, 255);
}

int dyePwm = 0, waterPwm = 0, drainPwm = 0;

void setup() {
  Serial.begin(9600);
  Wire.begin();

  pinMode(DYE_PUMP_PIN, OUTPUT);
  pinMode(WATER_PUMP_PIN, OUTPUT);
  pinMode(DRAIN_PUMP_PIN, OUTPUT);
  analogWrite(DYE_PUMP_PIN, 0);
  analogWrite(WATER_PUMP_PIN, 0);
  analogWrite(DRAIN_PUMP_PIN, 0);

  if (sensor.begin() == false) {
    Serial.println("AS7265x not detected -- check wiring/3.3V power.");
    while (1);
  }

  // Using an external emitter LED for transmittance, not this board's own
  // illumination -- turn all three onboard LEDs off.
  sensor.disableBulb(AS7265x_LED_WHITE);
  sensor.disableBulb(AS7265x_LED_IR);
  sensor.disableBulb(AS7265x_LED_UV);

  concPID.SetMode(AUTOMATIC);
  concPID.SetOutputLimits(-255, 255);
  concPID.SetSampleTime(500);
}

void loop() {
  // ---- 1. Read sensor, convert to concentration ----
  sensor.takeMeasurements();

  // PLACEHOLDER channel choice -- getCalibratedF() (535nm) is just a
  // starting point, picked because it's close to a green emitter LED's
  // output and a red dye's absorption band (see CHANNEL NAMING note at
  // top for the full letter-to-wavelength map). Test several with
  // test_spectro.ino and use whichever shows the biggest, cleanest swing
  // between clear water and your dye. See calibration notes.
  float reading = sensor.getCalibratedF();

  double absorbance = log10((double)clearRef / max(reading, 1.0f));
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
  Serial.print("reading:"); Serial.print(reading);
  Serial.print(",conc:"); Serial.print(measuredConcentration);
  Serial.print(",dyePwm:"); Serial.print(dyePwm);
  Serial.print(",waterPwm:"); Serial.print(waterPwm);
  Serial.print(",drainPwm:"); Serial.println(drainPwm);

  delay(100);
}

/*
 * WIRING NOTES:
 *
 * AS7265x (3.3V device -- direct connection is fine on the R4 Minima since
 * its I/O is natively 3.3V; do NOT use these direct-connection steps on a
 * classic 5V-logic Uno):
 *   Sensor 3V3  -> R4 Minima 3.3V pin (not 5V)
 *   Sensor GND  -> R4 Minima GND
 *   Sensor SDA  -> R4 Minima SDA (or A4)
 *   Sensor SCL  -> R4 Minima SCL (or A5)
 *
 * Each pump (via its own solderless MOSFET driver breakout module):
 *   Module SIG <- Arduino pin (5 = dye, 6 = water, 3 = drain)
 *   Module VCC <- Arduino 5V
 *   Module GND <- Arduino GND
 *   All three pumps share one 3V supply rail -- not the Arduino 5V rail.
 *
 * CALIBRATION / TUNING NOTES:
 *
 * 1. Pick a channel: fill the tank with pure water, then with your most
 *    concentrated dye mixture, and print several channels (getCalibratedA
 *    through L/R-W, see CHANNEL NAMING note at top) side by side. Use
 *    whichever channel shows the largest, cleanest difference between the
 *    two -- that's your best channel. Replace getCalibratedF() above with
 *    it.
 *
 * 2. clearRef: once you've picked a channel, record its reading with pure
 *    water in the tank and replace the clearRef placeholder.
 *
 * 3. Flow curves (dyeCal / waterCal / drainCal) and PID gains: same process
 *    as the other sensor variants -- see their calibration notes.
 */
