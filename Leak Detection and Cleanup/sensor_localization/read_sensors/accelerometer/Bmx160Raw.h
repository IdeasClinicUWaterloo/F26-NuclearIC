#ifndef BMX160_RAW_H
#define BMX160_RAW_H

#include <Arduino.h>
#include <Wire.h>

class Bmx160Raw {
public:
  Bmx160Raw(TwoWire* wireBus, uint8_t i2cAddr);

  bool begin();
  bool readAccelRaw(int16_t& ax, int16_t& ay, int16_t& az);
  bool readAccelG(float& ax_g, float& ay_g, float& az_g);
  float readVibration();
  bool readAccelXYZ(float &ax, float &ay, float &az);

private:
  TwoWire* wire;
  uint8_t addr;

  int16_t lastAx = 0;
  int16_t lastAy = 0;
  int16_t lastAz = 0;
  bool firstRead = true;

  bool writeReg(uint8_t reg, uint8_t value);
  bool readReg(uint8_t reg, uint8_t& value);
  bool readRegs(uint8_t reg, uint8_t* buf, size_t len);
};

#endif