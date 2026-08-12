#include <SPI.h>
#include <MFRC522.h>

// Relocated feedback LED pins to avoid SPI bus conflicts
const int GREEN_LED = 7;
const int RED_LED   = 6;

#define RST_PIN         9          // Configurable reset pin
#define SS_PIN          10         // Configurable Slave Select (SDA) pin

MFRC522 mfrc522(SS_PIN, RST_PIN);  // Create MFRC522 instance

void setup() {
  Serial.begin(115200);   // Matches laptop python serial speed
  while (!Serial) delay(10); 

  pinMode(GREEN_LED, OUTPUT);
  pinMode(RED_LED, OUTPUT);
  digitalWrite(GREEN_LED, LOW);
  digitalWrite(RED_LED, LOW);

  SPI.begin();            // Initialize SPI bus
  mfrc522.PCD_Init();     // Initialize the RC522 module

  // --- SPI BUS HARDWARE HANDSHAKE CHECK ---
  byte version = mfrc522.PCD_ReadRegister(mfrc522.VersionReg);

  // A disconnected, unpowered, or unsoldered chip will return 0x00 or 0xFF
  if ((version == 0x00) || (version == 0xFF)) {
    Serial.println("\n[X] HARDWARE ERROR: RC522 card reader not detected!");
    Serial.println("    - Check that VCC is connected to 3.3V (NOT 5V).");
    Serial.println("    - Verify SPI wiring: SDA(10), MOSI(11), MISO(12), SCK(13), RST(9).");
    Serial.println("    - Note: Header pins MUST be soldered; loose friction fit will fail.");
    
    // Loop forever flashing the Red LED to visually indicate a hardware system failure
    while (1) {
      digitalWrite(RED_LED, HIGH);
      delay(200);
      digitalWrite(RED_LED, LOW);
      delay(200);
    }
  }

  // If we pass the check, flash the Green LED once to signal a successful boot sequence
  digitalWrite(GREEN_LED, HIGH);
  delay(500);
  digitalWrite(GREEN_LED, LOW);

  // Print confirmed diagnostic information to the Serial Monitor
  Serial.print("[✔] Hardware Connection Established. RC522 Chip Version: 0x");
  Serial.println(version, HEX);
  Serial.println("System Active: Tap an NTAG215 badge to begin.");
}

void loop() {
  // Look for new physical cards in range
  if ( ! mfrc522.PICC_IsNewCardPresent()) {
    return;
  }

  // Read the card serial data
  if ( ! mfrc522.PICC_ReadCardSerial()) {
    return;
  }

  // Verify it is a 7-byte UID (standard NTAG215 badge)
  if (mfrc522.uid.size == 7) {
    // Print formatted UID to Serial: XX:XX:XX:XX:XX:XX:XX
    for (byte i = 0; i < mfrc522.uid.size; i++) {
      if (mfrc522.uid.uidByte[i] < 0x10) Serial.print("0");
      Serial.print(mfrc522.uid.uidByte[i], HEX);
      if (i < mfrc522.uid.size - 1) Serial.print(":");
    }
    Serial.println(); // Signal completion of transmission

    // Stand by and wait for the laptop's execution decision
    long timeout = millis();
    char decision = ' ';
    while (millis() - timeout < 1500) {
      if (Serial.available() > 0) {
        decision = Serial.read();
        break;
      }
    }

    // Actuate visual feedback based on policy decision
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
    
    // Halt communication with the card so it doesn't read repeatedly
    mfrc522.PICC_HaltA();
    delay(1000); // Cooldown delay
  }
}