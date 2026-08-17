// 35 C temperature controller -- hysteresis (bang-bang), no PID
//
// Bench-test sketch. Simpler sibling of temperature_controller/, which runs the
// same hardware under a split-range PID. Use this one to prove out the wiring,
// the relay polarity and the safety paths before trusting a tuned loop -- there
// are no gains to get wrong here, so anything that misbehaves is hardware.
//
// Sensor:       DS18B20 data -> Arduino D4 (4.7 kOhm pull-up to 5 V)
// Heater relay: DFRobot DFR0473 signal -> Arduino D2, pad wired through COM/NO
// Pump driver:  DRV8833 IN1 -> Arduino D10, IN2 -> Arduino D11
//
// The relay is switched with hysteresis, never PWM: at 490 Hz a mechanical relay
// buzzes, never fully closes, and destroys its own contacts. The dead band
// between the thresholds is what keeps switching down to a sane rate.
//
// Feed DRV8833 VCC from the motor-driver supply. Set it for the selected pump.
// If the module exposes a
// SLP/SLEEP/nSLEEP pin, tie it to 5 V. Do not connect the 12 V heater supply
// to the pump circuit.
#include <OneWire.h>
#include <DallasTemperature.h>
// ---------------- Pins ----------------
const uint8_t HEATER_RELAY_PIN = 2;
const uint8_t ONE_WIRE_BUS     = 4;
const uint8_t PUMP_IN1_PIN     = 10; // PWM-capable on Arduino Uno/Nano
const uint8_t PUMP_IN2_PIN     = 11;
// DFRobot DFR0473 is active HIGH: HIGH = relay on, LOW = relay off.
// Confirm with the LED check in the commissioning notes before wiring the pad.
const bool RELAY_ACTIVE_LOW = false;
const uint8_t RELAY_ON_LEVEL  = RELAY_ACTIVE_LOW ? LOW : HIGH;
const uint8_t RELAY_OFF_LEVEL = RELAY_ACTIVE_LOW ? HIGH : LOW;
// ---------------- Temperature settings ----------------
constexpr float SETPOINT_C     = 35.0;
constexpr float MAX_SETPOINT_C = 45.0;
static_assert(SETPOINT_C <= MAX_SETPOINT_C, "SETPOINT_C must be 45 C or lower");
const float HYSTERESIS_C = 0.5;
const float HEATER_ON_C  = SETPOINT_C - HYSTERESIS_C; // 34.5
const float HEATER_OFF_C = SETPOINT_C + HYSTERESIS_C; // 35.5
// Derived from HEATER_OFF_C, not from SETPOINT_C: this guarantees the cooling
// band sits entirely above the heating band no matter what HYSTERESIS_C is set
// to. Anchoring PUMP_ON_C to the setpoint instead lets the two bands overlap
// once HYSTERESIS_C exceeds the gap, and then both actuators run at once.
const float PUMP_OFF_C = HEATER_OFF_C;       // 35.5, hand-off point
const float PUMP_ON_C  = HEATER_OFF_C + 0.5; // 36.0, cooling starts here
// Independent over-temperature cutoff. Kept well clear of the setpoint because
// bang-bang control plus the pad's stored heat overshoots noticeably on the
// first warm-up -- a tighter limit just nuisance-trips before the rig settles.
const float MAX_SAFE_TEMP_C = 55.0;
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
  // Preload the safe output levels before changing the pins to outputs, so a
  // reset cannot pulse the heater on while the port register is still default.
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
  if (sensors.getDeviceCount() == 0) {
    Serial.println(F("WARNING: no DS18B20 on D4 -- check the 4.7k pull-up to 5 V"));
  }
}
void loop() {
  sensors.requestTemperatures(); // blocks ~750 ms; fine here, nothing is timed
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
  // Note: a DS18B20 reads exactly 85.00 after a power-on reset if polled before
  // its first conversion completes. That passes the plausibility check above and
  // trips the cutoff below, so it fails safe -- an OVER TEMPERATURE line in the
  // first second or two is usually this, not a real event.
  //
  // This cutoff is deliberately self-clearing so the rig recovers on its own
  // during testing. That means a welded relay contact would oscillate here
  // indefinitely rather than stopping; latch it in a static flag if you ever
  // leave the rig running unattended.
  if (temperatureC >= MAX_SAFE_TEMP_C) {
    failSafe(F("OVER TEMPERATURE: heater OFF, pump ON"));
    delay(1000);
    return;
  }
  // Hysteresis: between the two thresholds neither branch fires, so the current
  // state simply persists. That gap is the whole mechanism -- without it the
  // relay would switch on every reading once the plate reached setpoint.
  if (temperatureC <= HEATER_ON_C) {
    setHeater(true);
  } else if (temperatureC >= HEATER_OFF_C) {
    setHeater(false);
  }
  // Cooling band sits above the heating band, so the two never run together.
  if (temperatureC >= PUMP_ON_C) {
    setPump(true);
  } else if (temperatureC <= PUMP_OFF_C) {
    setPump(false);
  }
  Serial.print(F("temp="));     Serial.print(temperatureC, 2);
  Serial.print(F("C heater=")); Serial.print(heaterOn ? F("ON ") : F("off"));
  Serial.print(F(" pump="));    Serial.println(pumpOn ? F("ON ") : F("off"));
  delay(250);
}
/*
 * COMMISSIONING ORDER -- run these in sequence with this sketch, not the PID one
 *
 * 1. Sensor only, nothing else connected. Confirm the printed temperature tracks
 *    a known thermometer at room temperature and in warm water. A stuck -127
 *    means a wiring or pull-up problem; a stuck 85.00 means it is never getting
 *    a completed conversion.
 * 2. Relay polarity, heater pad still DISCONNECTED. Watch the module's LED: dark
 *    at reset, then lit once the loop calls for heat (with a cold probe it will
 *    sit latched on). If it is lit at reset instead, set RELAY_ACTIVE_LOW = true.
 *    Wire the pad through COM and NO -- never NC, which inverts it so the pad
 *    runs whenever the Arduino is off.
 * 3. Pump only, heater still disconnected. Confirm it actually moves water and
 *    that the DRV8833 uses the motor-driver supply, not the heater supply.
 * 4. Check the relay's contact rating against the pad's actual current draw. If
 *    the pad is a MAINS part rather than low-voltage, the switched side is lethal
 *    and the module's open screw terminal is not appropriate. That needs an
 *    enclosed, strain-relieved build checked by someone qualified.
 * 5. Full loop. Expect visible overshoot past 35 C on the first warm-up; that is
 *    expected with bang-bang plate control and is the main thing the PID version
 *    improves on.
 * 6. Fire both safety paths on purpose. Unplug the probe mid-run and confirm the
 *    SENSOR FAULT path cuts the heater. Then, at temperature, drop
 *    MAX_SAFE_TEMP_C below the current reading, confirm the cutoff, and restore
 *    it. A safety path you have never seen trigger is not a safety path.
 */
