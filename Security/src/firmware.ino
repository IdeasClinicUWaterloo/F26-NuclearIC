#include <Wire.h>
#include <Adafruit_PN532.h>
// Pins for our optional feedback LEDs
const int GREEN_LED = 12;
const int RED_LED   = 11;
// The Uno handles default hardware I2C pins (A4/A5) automatically.
// We just need placeholders to satisfy the library constructor.
#define PN532_IRQ   (2)
#define PN532_RESET (3)
Adafruit_PN532 nfc(PN532_IRQ, PN532_RESET);
void setup(void) {
  Serial.begin(115200);
  while (!Serial) delay(10); // Wait for serial connection
  pinMode(GREEN_LED, OUTPUT);
  pinMode(RED_LED, OUTPUT);
  digitalWrite(GREEN_LED, LOW);
  digitalWrite(RED_LED, LOW);
  nfc.begin();
  uint32_t versiondata = nfc.getFirmwareVersion();
  if (!versiondata) {
    Serial.println("System Alert: PN532 board not detected! Check wiring/switches.");
    while (1); // Halt if hardware is disconnected
  }
  nfc.SAMConfig(); // Configure board to read RFID tags
  // Flash LEDs to confirm setup success
  digitalWrite(GREEN_LED, HIGH);
  digitalWrite(RED_LED, HIGH);
  delay(300);
  digitalWrite(GREEN_LED, LOW);
  digitalWrite(RED_LED, LOW);
  Serial.println("System Active: Tap an NTAG215 badge on the terminal.");
}
void loop(void) {
  uint8_t success;
  uint8_t uid[] = { 0, 0, 0, 0, 0, 0, 0 };  // Buffer to store 7-byte NTAG215 UID
  uint8_t uidLength;
  success = nfc.readPassiveTargetID(PN532_MIFARE_ISO14443A, uid, &uidLength);
  if (success) {
    if (uidLength == 7) { // Ensure it is our NTAG215 tag
      // Print formatted UID to Serial: XX:XX:XX:XX:XX:XX:XX
      for (uint8_t i = 0; i < uidLength; i++) {
        if (uid[i] < 0x10) Serial.print("0");
        Serial.print(uid[i], HEX);
        if (i < uidLength - 1) Serial.print(":");
      }
      Serial.println(); // Complete the packet string
      // Stand by and wait for the laptop's decision
      long timeout = millis();
      char decision = ' ';
      while (millis() - timeout < 1500) {
        if (Serial.available() > 0) {
          decision = Serial.read();
          break;
        }
      }
      // Actuate visual feedback
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
      delay(1500); // Debounce cooldown window
    }
  }
}