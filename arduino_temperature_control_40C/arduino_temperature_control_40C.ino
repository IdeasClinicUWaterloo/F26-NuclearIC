// 40 C temperature controller
//
// Sensor:       DS18B20 data -> Arduino D4 (4.7 kOhm pull-up to 5 V)
// Heater relay: DFRobot DFR0473 signal -> Arduino D2
// Pump driver:  IN1 -> Arduino D10, IN2 -> Arduino D11

// The relay is controlled with hysteresis; do not PWM a mechanical relay.

#include <OneWire.h>
#include <DallasTemperature.h>

// ---------------- Pins ----------------
const uint8_t HEATER_RELAY_PIN = 2;
const uint8_t ONE_WIRE_BUS     = 4;
const uint8_t PUMP_IN1_PIN     = 10; // PWM-capable on Arduino Uno/Nano
const uint8_t PUMP_IN2_PIN     = 11;

// DFRobot DFR0473 is active HIGH: HIGH = relay on, LOW = relay off.
const bool RELAY_ACTIVE_LOW = false;
const uint8_t RELAY_ON_LEVEL  = RELAY_ACTIVE_LOW ? LOW : HIGH;
const uint8_t RELAY_OFF_LEVEL = RELAY_ACTIVE_LOW ? HIGH : LOW;

// ---------------- Temperature settings ----------------
const float SETPOINT_C        = 40.0;
const float HYSTERESIS_C      = 0.5;
const float HEATER_ON_C       = SETPOINT_C - HYSTERESIS_C;
const float HEATER_OFF_C      = SETPOINT_C + HYSTERESIS_C;
const float PUMP_ON_C         = SETPOINT_C + 1.0; // cooling starts above heater band
const float PUMP_OFF_C        = SETPOINT_C + HYSTERESIS_C;
const float MAX_SAFE_TEMP_C   = 50.0; // independent over-temperature cutoff

OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

bool heaterOn = false;
bool pumpOn   = false;

void setHeater(bool on) {
  heaterOn = on;
  digitalWrite(HEATER_RELAY_PIN, on ? RELAY_ON_LEVEL : RELAY_OFF_LEVEL);
}

// With IN2 held LOW, PWM on IN1 drives the pump in one direction.
// Driving both inputs LOW stops/coasts the pump and prevents IN2 floating.
void setPump(bool on) {
  pumpOn = on;
  digitalWrite(PUMP_IN2_PIN, LOW);
  analogWrite(PUMP_IN1_PIN, on ? 255 : 0);
}

void failSafe(const __FlashStringHelper *message) {
  setHeater(false); // remove heat
  setPump(true);    // maximum cooling
  Serial.println(message);
}

void setup() {
  Serial.begin(9600);

  // Preload the safe output levels before changing the pins to outputs.
  digitalWrite(HEATER_RELAY_PIN, RELAY_OFF_LEVEL);
  digitalWrite(PUMP_IN1_PIN, LOW);
  digitalWrite(PUMP_IN2_PIN, LOW);

  pinMode(HEATER_RELAY_PIN, OUTPUT);
  pinMode(PUMP_IN1_PIN, OUTPUT);
  pinMode(PUMP_IN2_PIN, OUTPUT);

  setHeater(false);
  setPump(false);

  sensors.begin();
  sensors.setResolution(12);
}

void loop() {
  sensors.requestTemperatures(); // waits for a completed conversion
  const float temperatureC = sensors.getTempCByIndex(0);

  const bool sensorFault =
      (temperatureC == DEVICE_DISCONNECTED_C) ||
      (temperatureC < -20.0) ||
      (temperatureC > 125.0);

  if (sensorFault) {
    failSafe(F("SENSOR FAULT: heater OFF, pump ON"));
    delay(1000);
    return;
  }

  if (temperatureC >= MAX_SAFE_TEMP_C) {
    failSafe(F("OVER TEMPERATURE: heater OFF, pump ON"));
    delay(1000);
    return;
  }

  // Heater hysteresis: retain the previous heater state inside 39.5-40.5 C.
  if (temperatureC <= HEATER_ON_C) {
    setHeater(true);
  } else if (temperatureC >= HEATER_OFF_C) {
    setHeater(false);
  }

  // Cooling hysteresis. Never run cooling while the heater is on.
  if (heaterOn) {
    setPump(false);
  } else if (temperatureC >= PUMP_ON_C) {
    setPump(true);
  } else if (temperatureC <= PUMP_OFF_C) {
    setPump(false);
  }

  Serial.print(F("temp="));
  Serial.print(temperatureC, 2);
  Serial.print(F(" C, setpoint="));
  Serial.print(SETPOINT_C, 1);
  Serial.print(F(" C, heater="));
  Serial.print(heaterOn ? F("ON") : F("OFF"));
  Serial.print(F(", pump="));
  Serial.println(pumpOn ? F("ON") : F("OFF"));

  delay(250); // total update interval is about one second at 12-bit resolution
}
