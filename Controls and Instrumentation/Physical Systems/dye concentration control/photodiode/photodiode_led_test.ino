// photodiode_led_test.ino
// Quick bench test for the LED + photodiode transmittance sensor circuit --
// confirms the wiring works before integrating into the full
// dye_concentration_controller_photodiode.ino sketch.
//
// Wiring (matches the breadboard layout already wired up):
//   Emitter LED: D11 -> resistor (~220-330 ohm) -> LED anode; LED cathode -> GND rail
//   Receiver (LED-as-photodiode): cathode -> 5V, anode -> A0 node -> resistor (1M-10M) -> GND rail

const int LED_PIN = 11;
const int PHOTODIODE_PIN = A0;

void setup() {
  Serial.begin(9600);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
}

void loop() {
  // LED off -> ambient light only
  digitalWrite(LED_PIN, LOW);
  delay(10);
  int ambientReading = analogRead(PHOTODIODE_PIN);

  // LED on -> ambient + the emitter LED's own light reaching the receiver
  digitalWrite(LED_PIN, HIGH);
  delay(10);
  int combinedReading = analogRead(PHOTODIODE_PIN);

  digitalWrite(LED_PIN, LOW); // leave LED off between cycles

  int signal = combinedReading - ambientReading;

  Serial.print("ambient:"); Serial.print(ambientReading); Serial.print(",");
  Serial.print("combined:"); Serial.print(combinedReading); Serial.print(",");
  Serial.print("signal:"); Serial.println(signal);

  delay(200);
}