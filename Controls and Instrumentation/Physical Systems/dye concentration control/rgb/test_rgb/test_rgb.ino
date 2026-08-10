// test_rgb.ino
// Bench test for the TCS34725 colour sensor (DFRobot SEN0212 / Gravity, or
// the Adafruit breakout -- same IC, same I2C address 0x29) before
// integrating into dye_concentration_controller.ino.
//
// Lives in its own sketch folder so it compiles on its own: open
// test_rgb/test_rgb.ino in the Arduino IDE and upload. Serial at 9600,
// same as the main controller sketch.
//
// WIRING (4 wires, no soldering -- the Gravity PH2.0 cable is enough):
//   VCC -> Arduino 5V   (3.3V also fine, board takes 3.3-5V)
//   GND -> Arduino GND
//   SDA -> see board note below
//   SCL -> see board note below
//
// WHICH PINS FOR SDA/SCL -- THIS DIFFERS BY BOARD:
//   Classic Uno R3:  A4 = SDA, A5 = SCL. The dedicated SDA/SCL pins next
//                    to AREF are the same bus, so either works.
//   UNO R4 Minima:   use the DEDICATED SDA/SCL pins next to AREF only.
//                    A4/A5 are plain analog pins on the R4 and are NOT
//                    connected to the I2C bus -- wiring there gives an
//                    empty I2C scan and looks exactly like a dead sensor.
//
// Gravity cable colours: red = VCC, black = GND, blue = SDA, green = SCL.
//
// ONBOARD LEDS: the SEN0212's 4 white LEDs are on whenever its LED pin is
// left unconnected, and the 4-pin Gravity cable doesn't break that pin out.
// So this test assumes they're ON and you're measuring REFLECTANCE: the
// LEDs light the dyed water, the sensor reads what comes back. More dye ->
// less light returns -> lower `c`, which is the same direction as the
// transmittance setup, so the absorbance maths below is unchanged.
//
// Keep the sensor and tank shrouded (a cardboard box with a cutout is
// fine) and keep room lighting steady -- ambient light matters more in
// reflectance than it did in transmittance.
//
// WHAT THIS SKETCH IS FOR:
//   1. Confirm the sensor is detected at all.
//   2. Check you aren't saturating the ADC (see SAT_LIMIT below).
//   3. Capture clearRef and find the clear-water-to-dye swing -- the two
//      numbers dye_concentration_controller.ino needs calibrated.
//
// SERIAL COMMANDS (type the letter, press Enter):
//   c  capture the current `c` reading as clearRef
//   r  reset the min/max swing tracker

#include <Wire.h>
#include "Adafruit_TCS34725.h"

// ---------------- Sensor config ----------------
// If readings pin near SAT_LIMIT (see below), lower the gain first:
//   TCS34725_GAIN_1X / _4X / _16X / _60X
// Integration time options:
//   TCS34725_INTEGRATIONTIME_2_4MS / _24MS / _50MS / _101MS / _154MS / _700MS
// Set to 154MS/16X rather than the controller sketch's 50MS/4X: at 50MS/4X
// the raw counts came back around 130, which is the sensor's dark-current
// floor rather than a real measurement. This is ~12x more sensitive.
// More gain amplifies noise as well as signal, so getting actual light
// onto the sensor is the better fix -- treat this as a floor, not a
// substitute for illumination.
Adafruit_TCS34725 tcs = Adafruit_TCS34725(TCS34725_INTEGRATIONTIME_154MS, TCS34725_GAIN_16X);

// Approximate full-scale count for the integration time set above. The
// TCS34725's ceiling is 1024 counts per 2.4ms cycle, capped at 65535:
//   2_4MS ~1000   24MS ~10000   50MS ~21000   101MS ~43000   154MS+ 65535
// Update this if you change the integration time above.
const uint16_t SAT_LIMIT = 65535;

// ---------------- State ----------------
uint16_t clearRef = 0;      // 0 = not captured yet
uint16_t cMin = 65535;      // swing tracker
uint16_t cMax = 0;
bool sensorOk = false;      // false -> loop() prints diagnostics instead of readings

void setup() {
  Serial.begin(9600);

  // On native-USB boards (UNO R4, Leonardo, Micro) the serial port isn't
  // ready the instant the sketch starts, so early prints vanish. Wait for
  // it, but time out so a classic Uno (or a board running without the
  // Serial Monitor open) still proceeds.
  while (!Serial && millis() < 3000);

  Serial.println();
  Serial.println("=== test_rgb starting (9600 baud) ===");

  Wire.begin();
  i2cScan();

  sensorOk = tcs.begin();

  if (sensorOk) {
    Serial.println("TCS34725 detected.");

    // Throw away one reading: the first getRawData() after begin() can
    // return 0 before the first integration cycle has finished, which
    // otherwise pins the swing tracker's minimum at 0 forever.
    uint16_t r, g, b, c;
    tcs.getRawData(&r, &g, &b, &c);

    Serial.println("Commands: 'c' = capture clearRef, 'r' = reset min/max");
  } else {
    Serial.println("TCS34725 NOT found.");
  }
  Serial.println();
}

void loop() {
  handleSerialCommand();

  // Don't hang on a failed sensor -- keep reporting, so a blank monitor
  // always means a serial/upload problem and never a silent sketch.
  if (!sensorOk) {
    Serial.println("No sensor (expect 0x29). Check VCC, GND, and SDA/SCL.");
    Serial.println("  UNO R4: use the dedicated SDA/SCL pins past AREF, NOT A4/A5.");
    Serial.println("  Uno R3: A4 = SDA, A5 = SCL.");
    i2cScan();
    sensorOk = tcs.begin();   // retry, so fixing the wiring recovers live
    delay(2000);
    return;
  }

  // Initialised, NOT left as uninitialised locals. If the I2C read fails,
  // uninitialised values would hold constant stack garbage and print as
  // plausible-looking readings that ignore light and gain changes.
  uint16_t r = 0, g = 0, b = 0, c = 0;
  tcs.getRawData(&r, &g, &b, &c);

  // Confirm the chip is really answering. A valid TCS34725 returns 0x44
  // (or 0x4D for the TCS34727 variant). 0xFF or 0x00 means the reads
  // aren't reaching a powered sensor -- check VCC before anything else.
  uint8_t id = readChipId();
  if (id != 0x44 && id != 0x4D && id != 0x10) {
    Serial.print("BAD CHIP ID 0x");
    if (id < 16) Serial.print("0");
    Serial.print(id, HEX);
    Serial.println(" -- sensor not really responding. Check VCC (try 5V) and GND.");
    delay(1000);
    return;
  }

  // Track the swing so you can see how far `c` moves between pure water
  // and your most concentrated dye mixture.
  if (c < cMin) cMin = c;
  if (c > cMax) cMax = c;

  Serial.print("r="); Serial.print(r);
  Serial.print(" g="); Serial.print(g);
  Serial.print(" b="); Serial.print(b);
  Serial.print(" c="); Serial.print(c);

  Serial.print(" | swing="); Serial.print(cMin);
  Serial.print(".."); Serial.print(cMax);

  // Absorbance, only once you've captured a reference. This is the exact
  // expression dye_concentration_controller.ino uses, so whatever you see
  // here is what the PID will be fed.
  if (clearRef > 0) {
    double absorbance = log10((double)clearRef / max((int)c, 1));
    Serial.print(" | ref="); Serial.print(clearRef);
    Serial.print(" A="); Serial.print(absorbance, 4);
    Serial.print(" conc="); Serial.print(absorbance * 100.0, 1);
  } else {
    Serial.print(" | no ref yet (send 'c' with pure water in the tank)");
  }

  // Saturated means the reading stops responding to more light, so the
  // loop goes blind at the bright end while still looking healthy.
  if (c >= SAT_LIMIT) {
    Serial.print("  <-- SATURATED, lower the gain");
  }

  Serial.println();

  delay(250);
}

// Reads the TCS34725's ID register (0x12, with the 0x80 command bit set)
// directly over I2C, bypassing the library. This is the ground truth for
// "is a real sensor answering": it can't be faked by stale variables.
uint8_t readChipId() {
  const uint8_t TCS_ADDR = 0x29;

  Wire.beginTransmission(TCS_ADDR);
  Wire.write(0x80 | 0x12);
  if (Wire.endTransmission() != 0) return 0xFF;

  if (Wire.requestFrom(TCS_ADDR, (uint8_t)1) != 1) return 0xFF;
  return Wire.read();
}

// Probes every I2C address and reports which ones answer. This separates a
// wiring problem from a sketch/library problem: if 0x29 shows up here, the
// sensor is physically fine and the issue is above the wiring. If nothing
// shows up at all, it's power, SDA/SCL, or a missing common ground.
void i2cScan() {
  Serial.print("I2C scan:");
  int found = 0;

  for (uint8_t addr = 1; addr < 127; addr++) {
    Wire.beginTransmission(addr);
    if (Wire.endTransmission() == 0) {
      Serial.print(" 0x");
      if (addr < 16) Serial.print("0");
      Serial.print(addr, HEX);
      found++;
    }
  }

  if (found == 0) {
    Serial.println(" nothing found -- check power and SDA/SCL wiring");
  } else {
    Serial.print("  (");
    Serial.print(found);
    Serial.println(" device(s); TCS34725 should appear as 0x29)");
  }
}

void handleSerialCommand() {
  if (!Serial.available()) return;

  char cmd = Serial.read();
  while (Serial.available()) Serial.read(); // discard newline / rest of line

  uint16_t r, g, b, c;

  switch (cmd) {
    case 'c':
    case 'C':
      tcs.getRawData(&r, &g, &b, &c);
      clearRef = c;
      Serial.print(">>> clearRef captured: ");
      Serial.println(clearRef);
      Serial.println(">>> Put this in dye_concentration_controller.ino as clearRef.");
      break;

    case 'r':
    case 'R':
      cMin = 65535;
      cMax = 0;
      Serial.println(">>> min/max swing reset");
      break;

    default:
      break; // ignore stray characters, including bare newlines
  }
}

/*
 * HOW TO USE THIS, IN ORDER:
 *
 * 1. Upload with nothing in the tank but pure water. Confirm you get
 *    readings and no "not found" message.
 *
 * 2. Check saturation. If `c` sits at SAT_LIMIT, drop the gain to
 *    TCS34725_GAIN_1X and re-upload. Repeat until `c` sits comfortably
 *    below the limit -- somewhere in the middle of the range is ideal, so
 *    there's room to move in both directions.
 *
 * 3. Send 'c' to capture clearRef with pure water in the tank.
 *
 * 4. Send 'r', then add dye up to your most concentrated mixture, watching
 *    the swing tracker. A useful swing is a large, steady gap between cMin
 *    and cMax. If the gap is small or noisy, fix that before tuning any
 *    PID gains -- no amount of tuning recovers a signal that isn't there.
 *    Things to try: shroud out more ambient light, move the sensor closer
 *    to the tank wall, or raise the gain if you have headroom.
 *
 * 5. Copy the clearRef value from step 3 into
 *    dye_concentration_controller.ino, replacing the placeholder 800.
 *
 * 6. The `conc` column is the placeholder scale factor (absorbance * 100)
 *    from the main sketch. It is NOT calibrated to real concentration
 *    units. To fix that, mix several known dye concentrations, record `A`
 *    at each, and fit a curve -- see the calibration notes at the bottom
 *    of dye_concentration_controller.ino.
 */
