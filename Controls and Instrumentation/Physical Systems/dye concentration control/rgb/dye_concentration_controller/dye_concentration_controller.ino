// Physical dye-concentration controller
//
// Hardware:
//   - Arduino UNO R4 Minima
//   - DFRobot SEN0101 / TCS3200 frequency-output colour sensor
//   - 3 x 3 V submersible pumps
//   - 2 x DRV8833 dual H-bridge motor drivers
//
// The dye and clear-water pumps are the two channels of Driver 1. The waste
// pump uses OUT1/OUT2 of Driver 2. Each pump runs in one direction: PWM is
// applied to IN1 while IN2 is held LOW.
// The physical control tank is a 500 mL cup with a strict 450 mL liquid limit.
// Commission at about 350 mL and calibrate the sensor at that same volume. This
// sketch has no level sensor, so its flow-based waste command is not an
// independent overflow safeguard.
//
// Two control modes are available:
//   1. INTENSITY_BAND_MODE targets a raw sensor frequency with a +/- tolerance.
//      It does not require conversion to physical concentration units.
//   2. CALIBRATED_CONCENTRATION_PID_MODE converts frequency to concentration
//      using measured standards, then runs PID in concentration units.

#include <PID_v1.h>

// ---------------- SEN0101 / TCS3200 pins ----------------
const uint8_t SENSOR_OUT_PIN = 2;
const uint8_t SENSOR_S0_PIN  = 9;
const uint8_t SENSOR_S1_PIN  = 10;
const uint8_t SENSOR_S2_PIN  = 11;
const uint8_t SENSOR_S3_PIN  = 12;

// OE is tied directly to GND in the wiring guide, so no Arduino pin is needed.

// ---------------- DRV8833 pump pins ----------------
const uint8_t DYE_PUMP_PWM_PIN     = 3; // Driver 1 IN1
const uint8_t DYE_PUMP_LOW_PIN     = 4; // Driver 1 IN2
const uint8_t WATER_PUMP_PWM_PIN   = 5; // Driver 1 IN3
const uint8_t WATER_PUMP_LOW_PIN   = 7; // Driver 1 IN4
const uint8_t WASTE_PUMP_PWM_PIN   = 6; // Driver 2 IN1
const uint8_t WASTE_PUMP_LOW_PIN   = 8; // Driver 2 IN2

// If exposed, each DRV8833 SLP/SLEEP/nSLEEP pin is tied to Arduino 5V.

// ---------------- TCS3200 colour filters ----------------
enum ColourChannel : uint8_t {
  RED_FILTER,
  BLUE_FILTER,
  CLEAR_FILTER,
  GREEN_FILTER
};

// Red dye often produces its largest useful change in the green channel, but
// this must be confirmed with test_rgb.ino. Change this constant if another
// channel gives a larger, smoother and monotonic calibration curve.
const ColourChannel CONCENTRATION_CHANNEL = GREEN_FILTER;

const unsigned long SENSOR_PULSE_TIMEOUT_US = 50000;
const uint8_t SENSOR_PERIOD_SAMPLES = 12;

// ---------------- Control-mode selection ----------------
enum DyeControlMode : uint8_t {
  INTENSITY_BAND_MODE,
  CALIBRATED_CONCENTRATION_PID_MODE
};

// Raw intensity mode is the simpler default. Use test_rgb.ino to measure the
// desired mixture, enter its frequency below, and confirm whether adding dye
// makes that frequency rise or fall.
const DyeControlMode CONTROL_MODE = INTENSITY_BAND_MODE;
const float TARGET_INTENSITY_HZ = 0.0; // replace with the desired measured value
const float INTENSITY_TOLERANCE_HZ = 100.0;
const bool DYE_MAKES_INTENSITY_DECREASE = true;
const int INTENSITY_CORRECTION_PWM = 140;

// ---------------- Intensity -> concentration calibration ----------------
// Use test_rgb.ino and the procedure in Physical Systems/README.md.
//
// Set CAL_POINT_COUNT to the number of standards and enter at least two
// measured points. More points are strongly recommended.
// Standards are measured dilutions of the same prepared dyed-water reservoir
// solution used by the pump. Concentration can be an absolute unit (when the
// reservoir concentration is known) or reservoir-solution volume percent. The
// target below MUST use the same unit and remain inside the calibrated range.
//
// Keep points ordered by increasing concentration. Intensity may increase or
// decrease, but it must move monotonically across the table.
const bool CALIBRATION_READY = false;
const uint8_t CAL_POINT_COUNT = 2;
const float CAL_INTENSITY_HZ[CAL_POINT_COUNT] = {
  0.0, 0.0 // replace with measured SEN0101 frequencies
};
const float CAL_CONCENTRATION[CAL_POINT_COUNT] = {
  0.0, 0.0 // replace with the corresponding known concentrations
};

// ---------------- Concentration PID ----------------
double measuredConcentration = 0.0;
double targetConcentration   = 5.0; // replace; same unit as CAL_CONCENTRATION
double pidOutput              = 0.0; // -255..255: +dye, -clear water

// Starting points only. Tune on the assembled, calibrated apparatus.
double Kp = 4.0;
double Ki = 0.5;
double Kd = 0.2;

PID concentrationPID(
    &measuredConcentration,
    &pidOutput,
    &targetConcentration,
    Kp,
    Ki,
    Kd,
    DIRECT);

// ---------------- PWM -> flow calibration ----------------
// Measure each pump separately. The initial values are placeholders.
struct FlowCalibration {
  double slope;
  double intercept;
};

FlowCalibration dyeFlow  = {0.40, 0.0};
FlowCalibration waterFlow = {0.45, 0.0};
FlowCalibration wasteFlow = {0.50, 0.0};

int dyePwm = 0;
int waterPwm = 0;
int wastePwm = 0;

double pwmToFlow(int pwm, FlowCalibration calibration) {
  if (pwm <= 0) return 0.0;
  return max(0.0, calibration.slope * pwm + calibration.intercept);
}
int flowToPwm(double flow, FlowCalibration calibration) {
  if (flow <= 0.0 || calibration.slope <= 0.0) return 0;
  return constrain(
      (int)((flow - calibration.intercept) / calibration.slope + 0.5),
      0,
      255);
}

void selectColourChannel(ColourChannel channel) {
  switch (channel) {
    case RED_FILTER:   // S2 LOW,  S3 LOW
      digitalWrite(SENSOR_S2_PIN, LOW);
      digitalWrite(SENSOR_S3_PIN, LOW);
      break;
    case BLUE_FILTER:  // S2 LOW,  S3 HIGH
      digitalWrite(SENSOR_S2_PIN, LOW);
      digitalWrite(SENSOR_S3_PIN, HIGH);
      break;
    case CLEAR_FILTER: // S2 HIGH, S3 LOW
      digitalWrite(SENSOR_S2_PIN, HIGH);
      digitalWrite(SENSOR_S3_PIN, LOW);
      break;
    case GREEN_FILTER: // S2 HIGH, S3 HIGH
      digitalWrite(SENSOR_S2_PIN, HIGH);
      digitalWrite(SENSOR_S3_PIN, HIGH);
      break;
  }

  delay(3); // allow the photodiode filter selection to settle
}

float readFrequencyHz(ColourChannel channel) {
  selectColourChannel(channel);

  unsigned long totalPeriodUs = 0;
  uint8_t validPeriods = 0;

  for (uint8_t i = 0; i < SENSOR_PERIOD_SAMPLES; ++i) {
    const unsigned long lowUs =
        pulseIn(SENSOR_OUT_PIN, LOW, SENSOR_PULSE_TIMEOUT_US);
    const unsigned long highUs =
        pulseIn(SENSOR_OUT_PIN, HIGH, SENSOR_PULSE_TIMEOUT_US);

    if (lowUs > 0 && highUs > 0) {
      totalPeriodUs += lowUs + highUs;
      ++validPeriods;
    }
  }

  if (validPeriods == 0 || totalPeriodUs == 0) return NAN;
  return 1000000.0f * validPeriods / totalPeriodUs;
}

bool calibrationTableIsValid() {
  if (!CALIBRATION_READY || CAL_POINT_COUNT < 2) return false;

  const bool intensityIncreasing =
      CAL_INTENSITY_HZ[1] > CAL_INTENSITY_HZ[0];

  for (uint8_t i = 0; i < CAL_POINT_COUNT; ++i) {
    if (CAL_INTENSITY_HZ[i] <= 0.0) return false;
    if (i == 0) continue;
    if (CAL_CONCENTRATION[i] <= CAL_CONCENTRATION[i - 1]) return false;
    if (CAL_INTENSITY_HZ[i] == CAL_INTENSITY_HZ[i - 1]) return false;
    if ((CAL_INTENSITY_HZ[i] > CAL_INTENSITY_HZ[i - 1]) !=
        intensityIncreasing) {
      return false;
    }
  }

  return true;
}

double intensityToConcentration(float intensityHz) {
  // Linear interpolation between measured standards. This supports either an
  // increasing or decreasing sensor response.
  for (uint8_t i = 0; i < CAL_POINT_COUNT - 1; ++i) {
    const float x0 = CAL_INTENSITY_HZ[i];
    const float x1 = CAL_INTENSITY_HZ[i + 1];
    const float low = min(x0, x1);
    const float high = max(x0, x1);

    if (intensityHz >= low && intensityHz <= high) {
      const double fraction = (intensityHz - x0) / (x1 - x0);
      return CAL_CONCENTRATION[i] +
             fraction * (CAL_CONCENTRATION[i + 1] - CAL_CONCENTRATION[i]);
    }
  }

  // Clamp out-of-range readings to the nearest calibrated endpoint. The
  // controller should not extrapolate beyond concentrations it has seen.
  const float distanceToFirst = abs(intensityHz - CAL_INTENSITY_HZ[0]);
  const float distanceToLast =
      abs(intensityHz - CAL_INTENSITY_HZ[CAL_POINT_COUNT - 1]);
  return (distanceToFirst <= distanceToLast)
      ? CAL_CONCENTRATION[0]
      : CAL_CONCENTRATION[CAL_POINT_COUNT - 1];
}

void setPump(uint8_t pwmPin, uint8_t lowPin, int pwm) {
  pwm = constrain(pwm, 0, 255);
  digitalWrite(lowPin, LOW);
  analogWrite(pwmPin, pwm);
}

void stopAllPumps() {
  dyePwm = 0;
  waterPwm = 0;
  wastePwm = 0;
  setPump(DYE_PUMP_PWM_PIN, DYE_PUMP_LOW_PIN, 0);
  setPump(WATER_PUMP_PWM_PIN, WATER_PUMP_LOW_PIN, 0);
  setPump(WASTE_PUMP_PWM_PIN, WASTE_PUMP_LOW_PIN, 0);
}

void setup() {
  Serial.begin(9600);
  while (!Serial && millis() < 3000) {}

  pinMode(SENSOR_OUT_PIN, INPUT);
  pinMode(SENSOR_S0_PIN, OUTPUT);
  pinMode(SENSOR_S1_PIN, OUTPUT);
  pinMode(SENSOR_S2_PIN, OUTPUT);
  pinMode(SENSOR_S3_PIN, OUTPUT);

  // TCS3200 output-frequency scaling: S0 LOW + S1 HIGH = 2%.
  // This keeps pulse periods long enough for reliable pulseIn() measurement.
  digitalWrite(SENSOR_S0_PIN, LOW);
  digitalWrite(SENSOR_S1_PIN, HIGH);

  // Preload safe states before enabling the pump pins as outputs.
  digitalWrite(DYE_PUMP_PWM_PIN, LOW);
  digitalWrite(DYE_PUMP_LOW_PIN, LOW);
  digitalWrite(WATER_PUMP_PWM_PIN, LOW);
  digitalWrite(WATER_PUMP_LOW_PIN, LOW);
  digitalWrite(WASTE_PUMP_PWM_PIN, LOW);
  digitalWrite(WASTE_PUMP_LOW_PIN, LOW);

  pinMode(DYE_PUMP_PWM_PIN, OUTPUT);
  pinMode(DYE_PUMP_LOW_PIN, OUTPUT);
  pinMode(WATER_PUMP_PWM_PIN, OUTPUT);
  pinMode(WATER_PUMP_LOW_PIN, OUTPUT);
  pinMode(WASTE_PUMP_PWM_PIN, OUTPUT);
  pinMode(WASTE_PUMP_LOW_PIN, OUTPUT);
  stopAllPumps();

  concentrationPID.SetOutputLimits(-255, 255);
  concentrationPID.SetSampleTime(500);

  if (CONTROL_MODE == INTENSITY_BAND_MODE) {
    concentrationPID.SetMode(MANUAL);
    if (TARGET_INTENSITY_HZ > 0.0 && INTENSITY_TOLERANCE_HZ >= 0.0) {
      Serial.println(F("Raw intensity-band control enabled."));
    } else {
      Serial.println(F("SET TARGET_INTENSITY_HZ: all pumps remain OFF until it is positive."));
    }
  } else if (calibrationTableIsValid()) {
    concentrationPID.SetMode(AUTOMATIC);
    Serial.println(F("Calibrated concentration PID enabled."));
  } else {
    concentrationPID.SetMode(MANUAL);
    Serial.println(F("CALIBRATION REQUIRED for concentration PID: pumps OFF."));
    Serial.println(F("Run rgb/test_rgb/test_rgb.ino and enter real calibration points."));
  }
}

void loop() {
  const float intensityHz = readFrequencyHz(CONCENTRATION_CHANNEL);

  if (isnan(intensityHz) || intensityHz <= 0.0) {
    stopAllPumps();
    Serial.println(F("SENSOR FAULT: no SEN0101 frequency; pumps OFF"));
    delay(500);
    return;
  }

  if (CONTROL_MODE == INTENSITY_BAND_MODE) {
    if (TARGET_INTENSITY_HZ <= 0.0 || INTENSITY_TOLERANCE_HZ < 0.0) {
      stopAllPumps();
      Serial.print(F("set_target intensity_hz="));
      Serial.println(intensityHz, 2);
      delay(500);
      return;
    }

    const float intensityError = intensityHz - TARGET_INTENSITY_HZ;
    if (abs(intensityError) <= INTENSITY_TOLERANCE_HZ) {
      dyePwm = 0;
      waterPwm = 0;
    } else {
      // Determine whether the mixture needs more dye without assuming which
      // direction the selected sensor channel moves.
      const bool needsMoreDye = DYE_MAKES_INTENSITY_DECREASE
          ? intensityHz > TARGET_INTENSITY_HZ
          : intensityHz < TARGET_INTENSITY_HZ;
      dyePwm = needsMoreDye ? INTENSITY_CORRECTION_PWM : 0;
      waterPwm = needsMoreDye ? 0 : INTENSITY_CORRECTION_PWM;
    }
  } else {
    if (!calibrationTableIsValid()) {
      stopAllPumps();
      Serial.print(F("calibration_required intensity_hz="));
      Serial.println(intensityHz, 2);
      delay(500);
      return;
    }

    measuredConcentration = intensityToConcentration(intensityHz);
    concentrationPID.Compute();

    if (pidOutput >= 0.0) {
      dyePwm = constrain((int)(pidOutput + 0.5), 0, 255);
      waterPwm = 0;
    } else {
      dyePwm = 0;
      waterPwm = constrain((int)(-pidOutput + 0.5), 0, 255);
    }
  }

  const double totalInflow =
      pwmToFlow(dyePwm, dyeFlow) + pwmToFlow(waterPwm, waterFlow);
  wastePwm = flowToPwm(totalInflow, wasteFlow);

  setPump(DYE_PUMP_PWM_PIN, DYE_PUMP_LOW_PIN, dyePwm);
  setPump(WATER_PUMP_PWM_PIN, WATER_PUMP_LOW_PIN, waterPwm);
  setPump(WASTE_PUMP_PWM_PIN, WASTE_PUMP_LOW_PIN, wastePwm);

  Serial.print(F("intensity_hz="));
  Serial.print(intensityHz, 2);
  if (CONTROL_MODE == INTENSITY_BAND_MODE) {
    Serial.print(F(" target_intensity_hz="));
    Serial.print(TARGET_INTENSITY_HZ, 2);
    Serial.print(F(" tolerance_hz="));
    Serial.print(INTENSITY_TOLERANCE_HZ, 2);
  } else {
    Serial.print(F(" concentration="));
    Serial.print(measuredConcentration, 3);
    Serial.print(F(" target_concentration="));
    Serial.print(targetConcentration, 3);
  }
  Serial.print(F(" dye_pwm="));
  Serial.print(dyePwm);
  Serial.print(F(" water_pwm="));
  Serial.print(waterPwm);
  Serial.print(F(" waste_pwm="));
  Serial.println(wastePwm);

  delay(100);
}
