#include <Wire.h>
#include <Adafruit_PN532.h>

// Relocated feedback LED pins to avoid bus conflicts
const int GREEN_LED = 7;
const int RED_LED   = 6;

// Optional reset/IRQ pins for the PN532 module. Many I2C modules work with only VCC, GND, SDA, and SCL.
#define PN532_IRQ   2
#define PN532_RESET 3

Adafruit_PN532 nfc(PN532_IRQ, PN532_RESET);

void setup() {
  Serial.begin(115200);
  while (!Serial) delay(10);

  pinMode(GREEN_LED, OUTPUT);
  pinMode(RED_LED, OUTPUT);
  digitalWrite(GREEN_LED, LOW);
  digitalWrite(RED_LED, LOW);

  Wire.begin();          // Initialize I2C bus for PN532
  nfc.begin();

  uint32_t versiondata = nfc.getFirmwareVersion();
  if (!versiondata) {
    Serial.println("\n[X] HARDWARE ERROR: PN532 reader not detected over I2C!");
    Serial.println("    - Check that VCC and GND are connected.");
    Serial.println("    - Verify I2C wiring: SDA and SCL.");
    Serial.println("    - Some modules require 3.3V power.");
    while (1) {
      digitalWrite(RED_LED, HIGH);
      delay(200);
      digitalWrite(RED_LED, LOW);
      delay(200);
    }
  }

  nfc.SAMConfig();       // Configure board to read RFID tags
  digitalWrite(GREEN_LED, HIGH);
  delay(500);
  digitalWrite(GREEN_LED, LOW);

  Serial.print("[✔] Hardware Connection Established. PN532 Firmware Version: 0x");
  Serial.println((versiondata >> 24) & 0xFF, HEX);
  Serial.println("System Active: Tap an NTAG215 badge to begin.");
}

void loop() {
  boolean success;
  uint8_t uid[7];
  uint8_t uidLength;

  success = nfc.readPassiveTargetID(PN532_MIFARE_ISO14443A, uid, &uidLength, 1000);
  if (!success) {
    return;
  }

  if (uidLength == 7) {
    for (uint8_t i = 0; i < uidLength; i++) {
      if (uid[i] < 0x10) Serial.print("0");
      Serial.print(uid[i], HEX);
      if (i < uidLength - 1) Serial.print(":");
    }
    Serial.println();

    long timeout = millis();
    char decision = ' ';
    while (millis() - timeout < 1500) {
      if (Serial.available() > 0) {
        decision = Serial.read();
        break;
      }
    }

    if (decision == '1') {
      digitalWrite(GREEN_LED, HIGH);
      delay(1000);
      digitalWrite(GREEN_LED, LOW);
    } else {
      for (int i = 0; i < 3; i++) {
        digitalWrite(RED_LED, HIGH);
        delay(150);
        digitalWrite(RED_LED, LOW);
        delay(100);
      }
    }

    delay(1000);
  }
}
