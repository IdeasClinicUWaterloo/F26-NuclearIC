#include <Wire.h>
#include <Adafruit_PN532.h>
// Define I2C Pins for ESP32 standard configuration
#define I2C_SDA 21
#define I2C_SCL 22
// Define Output Peripheral Pins for Tactile Feedback
const int GREEN_LED = 12;
const int RED_LED   = 14;
const int BUZZER    = 13;
// Initialize the PN532 over I2C hardware bus
Adafruit_PN532 nfc(I2C_SDA, I2C_SCL);
void setup(void) {
 // Initialize standard hardware USB serial connection to the laptop bridge
 Serial.begin(115200);
 while (!Serial) delay(10); // Wait for serial port to open
 // Configure hardware peripheral pins as outputs
 pinMode(GREEN_LED, OUTPUT);
 pinMode(RED_LED, OUTPUT);
 pinMode(BUZZER, OUTPUT);
 // Initialize peripheral pins to low (Off)
 digitalWrite(GREEN_LED, LOW);
 digitalWrite(RED_LED, LOW);
 digitalWrite(BUZZER, LOW);
 // Initialize the PN532 transceiver module
 nfc.begin();
 uint32_t versiondata = nfc.getFirmwareVersion();
 if (!versiondata) {
   Serial.println("[X] HARDWARE ERROR: PN532 board not detected. Check I2C wiring and DIP switches.");
   while (1); // Halt execution if connection is broken
 }
 // Configure PN532 to read RFID/NFC cards safely
 nfc.SAMConfig();
 // Run a quick startup confirmation flash sequence
 digitalWrite(GREEN_LED, HIGH);
 digitalWrite(RED_LED, HIGH);
 delay(300);
 digitalWrite(GREEN_LED, LOW);
 digitalWrite(RED_LED, LOW);
}
void loop(void) {
 uint8_t success;
 uint8_t uid[] = { 0, 0, 0, 0, 0, 0, 0 };  // Buffer spatial matrix to store 7-byte NTAG215 UID
 uint8_t uidLength;                        // Data length tracking register
 // Look for passive ISO14443A cards/tags in the field continuously
 success = nfc.readPassiveTargetID(PN532_MIFARE_ISO14443A, uid, &uidLength);
 if (success) {
   // Verify it is a standard 7-byte NTAG215 tag to maintain data alignment
   if (uidLength == 7) {
     // Print the raw 7-byte UID precisely formatted with colons to match Python's registry lookup
     for (uint8_t i = 0; i < uidLength; i++) {
       if (uid[i] < 0x10) Serial.print("0"); // Enforce zero-padding for single-digit hex values
       Serial.print(uid[i], HEX);
       if (i < uidLength - 1) {
         Serial.print(":");
       }
     }
     Serial.println(); // Conclude serial transmission line string packet
     // Stand by and wait briefly for the host laptop script to compute the policy metrics
     // Timeout guard ensures the hardware doesn't deadlock if the python bridge falls offline
     long timeout = millis();
     char decision = ' ';
     while (millis() - timeout < 1500) {
       if (Serial.available() > 0) {
         decision = Serial.read();
         break;
       }
     }
     // Execute local peripheral actuation based on policy decisions
     if (decision == '1') {
       // Access Granted Sequence
       digitalWrite(GREEN_LED, HIGH);
       delay(1000); // Keep airlock unlatched for 1 second
       digitalWrite(GREEN_LED, LOW);
     }
     else {
       // Access Denied / Breach Sequence (Flash red and sound alarm)
       for (int i = 0; i < 3; i++) {
         digitalWrite(RED_LED, HIGH);
         digitalWrite(BUZZER, HIGH);
         delay(150);
         digitalWrite(RED_LED, LOW);
         digitalWrite(BUZZER, LOW);
         delay(100);
       }
     }
     // Debounce window to prevent continuous duplicate scanning while tag stays resting on reader
     delay(1500);
   }
 }
}