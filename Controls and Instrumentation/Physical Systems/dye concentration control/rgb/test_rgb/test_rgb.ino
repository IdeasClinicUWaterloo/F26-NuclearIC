// SEN0101 / TCS3200 bench test and dye-calibration helper
// Arduino UNO R4 Minima, Serial Monitor at 9600 baud
//
// Wiring:
//   VDD/VCC -> Arduino 5V
//   GND     -> Arduino GND
//   OE      -> GND
//   OUT     -> D2
//   S0      -> D4
//   S1      -> D7
//   S2      -> D8
//   S3      -> D12
//
// Serial commands (set line ending to Newline):
//   r             select red as the calibration channel
//   g             select green as the calibration channel
//   b             select blue as the calibration channel
//   c             select clear as the calibration channel
//   s 5.0         capture the selected channel at concentration 5.0
//   z             capture the selected channel as concentration 0.0
//
// Tape or rigidly mount the sensor outside the transparent control tank. Fix the
// phone flashlight directly opposite at the same height so light passes through
// the liquid into the sensor. Keep the phone/flashlight setting, sensor and light
// positions, 350 mL working volume, tank orientation and closed cardboard
// enclosure fixed for every sample. The printed calibration rows can be copied
// into CAL_INTENSITY_HZ and CAL_CONCENTRATION in the main controller.

const uint8_t SENSOR_OUT_PIN = 2;
const uint8_t SENSOR_S0_PIN  = 4;
const uint8_t SENSOR_S1_PIN  = 7;
const uint8_t SENSOR_S2_PIN  = 8;
const uint8_t SENSOR_S3_PIN  = 12;

enum ColourChannel : uint8_t {
  RED_FILTER,
  BLUE_FILTER,
  CLEAR_FILTER,
  GREEN_FILTER
};

ColourChannel selectedCalibrationChannel = GREEN_FILTER;

const unsigned long SENSOR_PULSE_TIMEOUT_US = 50000;
const uint8_t SENSOR_PERIOD_SAMPLES = 20;
unsigned long lastReportMs = 0;

const char *channelName(ColourChannel channel) {
  switch (channel) {
    case RED_FILTER:   return "red";
    case BLUE_FILTER:  return "blue";
    case CLEAR_FILTER: return "clear";
    case GREEN_FILTER: return "green";
  }
  return "unknown";
}
void selectColourChannel(ColourChannel channel) {
  switch (channel) {
    case RED_FILTER:
      digitalWrite(SENSOR_S2_PIN, LOW);
      digitalWrite(SENSOR_S3_PIN, LOW);
      break;
    case BLUE_FILTER:
      digitalWrite(SENSOR_S2_PIN, LOW);
      digitalWrite(SENSOR_S3_PIN, HIGH);
      break;
    case CLEAR_FILTER:
      digitalWrite(SENSOR_S2_PIN, HIGH);
      digitalWrite(SENSOR_S3_PIN, LOW);
      break;
    case GREEN_FILTER:
      digitalWrite(SENSOR_S2_PIN, HIGH);
      digitalWrite(SENSOR_S3_PIN, HIGH);
      break;
  }
  delay(3);
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

void printHelp() {
  Serial.println(F("Commands: r/g/b/c = select channel, s <concentration> = sample, z = zero sample"));
  Serial.println(F("CSV sample format: calibration,channel,concentration,intensity_hz"));
}

void captureCalibrationPoint(float concentration) {
  const float intensityHz = readFrequencyHz(selectedCalibrationChannel);

  if (isnan(intensityHz)) {
    Serial.println(F("ERROR: no sensor frequency; check OUT, OE, power and ground"));
    return;
  }

  Serial.print(F("calibration,"));
  Serial.print(channelName(selectedCalibrationChannel));
  Serial.print(',');
  Serial.print(concentration, 4);
  Serial.print(',');
  Serial.println(intensityHz, 2);
}

void handleSerialCommand() {
  if (!Serial.available()) return;

  String command = Serial.readStringUntil('\n');
  command.trim();
  if (command.length() == 0) return;

  const char first = tolower(command.charAt(0));

  if (first == 'r' && command.length() == 1) {
    selectedCalibrationChannel = RED_FILTER;
  } else if (first == 'g' && command.length() == 1) {
    selectedCalibrationChannel = GREEN_FILTER;
  } else if (first == 'b' && command.length() == 1) {
    selectedCalibrationChannel = BLUE_FILTER;
  } else if (first == 'c' && command.length() == 1) {
    selectedCalibrationChannel = CLEAR_FILTER;
  } else if (first == 'z' && command.length() == 1) {
    captureCalibrationPoint(0.0);
    return;
  } else if (first == 's') {
    const int separator = command.indexOf(' ');
    if (separator < 0) {
      Serial.println(F("Use: s <known concentration>, for example s 5.0"));
      return;
    }
    captureCalibrationPoint(command.substring(separator + 1).toFloat());
    return;
  } else {
    printHelp();
    return;
  }

  Serial.print(F("Selected calibration channel: "));
  Serial.println(channelName(selectedCalibrationChannel));
}

void setup() {
  Serial.begin(9600);
  while (!Serial && millis() < 3000) {}
  Serial.setTimeout(100);

  pinMode(SENSOR_OUT_PIN, INPUT);
  pinMode(SENSOR_S0_PIN, OUTPUT);
  pinMode(SENSOR_S1_PIN, OUTPUT);
  pinMode(SENSOR_S2_PIN, OUTPUT);
  pinMode(SENSOR_S3_PIN, OUTPUT);

  // S0 LOW + S1 HIGH selects 2% output-frequency scaling.
  digitalWrite(SENSOR_S0_PIN, LOW);
  digitalWrite(SENSOR_S1_PIN, HIGH);

  Serial.println(F("=== SEN0101 / TCS3200 dye calibration ==="));
  Serial.println(F("Default calibration channel: green"));
  printHelp();
}

void loop() {
  handleSerialCommand();

  const unsigned long now = millis();
  if (now - lastReportMs < 1000) return;
  lastReportMs = now;

  const float redHz = readFrequencyHz(RED_FILTER);
  const float greenHz = readFrequencyHz(GREEN_FILTER);
  const float blueHz = readFrequencyHz(BLUE_FILTER);
  const float clearHz = readFrequencyHz(CLEAR_FILTER);

  Serial.print(F("live_hz red="));
  Serial.print(redHz, 2);
  Serial.print(F(" green="));
  Serial.print(greenHz, 2);
  Serial.print(F(" blue="));
  Serial.print(blueHz, 2);
  Serial.print(F(" clear="));
  Serial.print(clearHz, 2);
  Serial.print(F(" selected="));
  Serial.println(channelName(selectedCalibrationChannel));
}
