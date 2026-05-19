#include <Wire.h>
#include "Bmx160Raw.h"
#include <RunningAverage.h>

// ---------- I2C buses ----------
TwoWire I2C_1 = TwoWire(0);
TwoWire I2C_2 = TwoWire(1);

// ---------- Sensors ----------
Bmx160Raw sensor1(&I2C_1, 0x68);  // bus 0
Bmx160Raw sensor2(&I2C_2, 0x68);  // bus 1

// ---------- Results ----------
RunningAverage avg1(20);
RunningAverage avg2(20);

float ax1, ay1, az1;
float ax2, ay2, az2;

void setup() {
  Serial.begin(115200);
  delay(2000);

  Serial.println("Starting BMX160 vibration sensors...");

  // Bus 0
  I2C_1.begin(21, 22, 400000);   // SDA port, SCL port, 400 kHz clock

  // Bus 1
  I2C_2.begin(18, 23, 400000);   // SDA port, SCL port, 400 kHz clock

  delay(100);

  bool ok1 = sensor1.begin();
  bool ok2 = sensor2.begin();

  Serial.print("Sensor1: ");
  Serial.println(ok1 ? "OK" : "FAIL");

  Serial.print("Sensor2: ");
  Serial.println(ok2 ? "OK" : "FAIL");

  Serial.println("vib1,vib2");
}

void loop() {
  sensor1.readAccelXYZ(ax1, ay1, az1);
  sensor2.readAccelXYZ(ax2, ay2, az2);

  float mag1 = sqrt(ax1*ax1 + ay1*ay1 + az1*az1);
  float mag2 = sqrt(ax2*ax2 + ay2*ay2 + az2*az2);

  avg1.addValue(mag1);
  avg2.addValue(mag2);

  float vib1 = abs(mag1 - avg1.getAverage());
  float vib2 = abs(mag2 - avg2.getAverage());

  Serial.print(vib1);
  Serial.print(",");
  Serial.println(vib2);

  delay(20);  // ~50 Hz
}