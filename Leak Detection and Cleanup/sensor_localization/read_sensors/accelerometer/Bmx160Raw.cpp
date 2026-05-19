#include "Bmx160Raw.h"

// ---- BMX160 registers ----
static const uint8_t BMX160_REG_CHIP_ID   = 0x00;
static const uint8_t BMX160_REG_DATA      = 0x04;
static const uint8_t BMX160_REG_ACC_CONF  = 0x40;
static const uint8_t BMX160_REG_ACC_RANGE = 0x41;
static const uint8_t BMX160_REG_CMD       = 0x7E;

// ---- Expected chip id ----
static const uint8_t BMX160_CHIP_ID = 0xD8;

// ---- Commands ----
// Common BMX160 PMU commands
static const uint8_t BMX160_CMD_ACC_SUSPEND = 0x10;
static const uint8_t BMX160_CMD_ACC_NORMAL  = 0x11;
static const uint8_t BMX160_CMD_GYR_SUSPEND = 0x14;
static const uint8_t BMX160_CMD_MAG_SUSPEND = 0x18;
static const uint8_t BMX160_CMD_SOFT_RESET  = 0xB6;

// ---- Config ----
// ACC_CONF: ODR + bandwidth/avg
// 0x28 -> ODR 100 Hz, normal mode filtering
// You can increase this later if you want.
static const uint8_t BMX160_ACC_CONF_100HZ = 0x28;

// ACC_RANGE values
static const uint8_t BMX160_ACC_RANGE_2G  = 0x03;
static const uint8_t BMX160_ACC_RANGE_4G  = 0x05;
static const uint8_t BMX160_ACC_RANGE_8G  = 0x08;
static const uint8_t BMX160_ACC_RANGE_16G = 0x0C;

Bmx160Raw::Bmx160Raw(TwoWire* wireBus, uint8_t i2cAddr)
  : wire(wireBus), addr(i2cAddr) {}

bool Bmx160Raw::writeReg(uint8_t reg, uint8_t value) {
  wire->beginTransmission(addr);
  wire->write(reg);
  wire->write(value);
  return (wire->endTransmission() == 0);
}

bool Bmx160Raw::readReg(uint8_t reg, uint8_t& value) {
  wire->beginTransmission(addr);
  wire->write(reg);
  if (wire->endTransmission(false) != 0) return false;

  if (wire->requestFrom((int)addr, 1) != 1) return false;
  value = wire->read();
  return true;
}

bool Bmx160Raw::readRegs(uint8_t reg, uint8_t* buf, size_t len) {
  wire->beginTransmission(addr);
  wire->write(reg);
  if (wire->endTransmission(false) != 0) return false;

  size_t got = wire->requestFrom((int)addr, (int)len);
  if (got != len) return false;

  for (size_t i = 0; i < len; i++) {
    buf[i] = wire->read();
  }
  return true;
}

bool Bmx160Raw::begin() {
  uint8_t chip = 0;

  // Optional reset
  writeReg(BMX160_REG_CMD, BMX160_CMD_SOFT_RESET);
  delay(20);

  if (!readReg(BMX160_REG_CHIP_ID, chip)) return false;
  if (chip != BMX160_CHIP_ID) return false;

  // Keep gyro and mag suspended since you only want vibration
  writeReg(BMX160_REG_CMD, BMX160_CMD_GYR_SUSPEND);
  delay(5);
  writeReg(BMX160_REG_CMD, BMX160_CMD_MAG_SUSPEND);
  delay(5);

  // Put accelerometer in normal mode
  if (!writeReg(BMX160_REG_CMD, BMX160_CMD_ACC_NORMAL)) return false;
  delay(10);

  // Set accel ODR/filter
  if (!writeReg(BMX160_REG_ACC_CONF, BMX160_ACC_CONF_100HZ)) return false;
  delay(2);

  // Set ±2g for best sensitivity to vibration
  if (!writeReg(BMX160_REG_ACC_RANGE, BMX160_ACC_RANGE_2G)) return false;
  delay(2);

  firstRead = true;
  return true;
}

bool Bmx160Raw::readAccelRaw(int16_t& ax, int16_t& ay, int16_t& az) {
  // Accel is at 0x12..0x17
  uint8_t buf[6];
  if (!readRegs(0x12, buf, 6)) return false;

  ax = (int16_t)((buf[1] << 8) | buf[0]);
  ay = (int16_t)((buf[3] << 8) | buf[2]);
  az = (int16_t)((buf[5] << 8) | buf[4]);
  return true;
}

bool Bmx160Raw::readAccelG(float& ax_g, float& ay_g, float& az_g) {
  int16_t ax, ay, az;
  if (!readAccelRaw(ax, ay, az)) return false;

  // ±2g sensitivity is nominally 16384 LSB/g
  ax_g = ax / 16384.0f;
  ay_g = ay / 16384.0f;
  az_g = az / 16384.0f;
  return true;
}

bool Bmx160Raw::readAccelXYZ(float &ax, float &ay, float &az) {
  int16_t rawX, rawY, rawZ;

  if (!readAccelRaw(rawX, rawY, rawZ)) {
    return false;
  }

  // Convert to float (optional scaling)
  ax = (float)rawX;
  ay = (float)rawY;
  az = (float)rawZ;

  return true;
}

float Bmx160Raw::readVibration() {
  int16_t ax, ay, az;
  if (!readAccelRaw(ax, ay, az)) {
    return -1.0f;
  }

  if (firstRead) {
    lastAx = ax;
    lastAy = ay;
    lastAz = az;
    firstRead = false;
    return 0.0f;
  }

  float vibration =
      abs(ax - lastAx) +
      abs(ay - lastAy) +
      abs(az - lastAz);

  lastAx = ax;
  lastAy = ay;
  lastAz = az;

  return vibration;
}