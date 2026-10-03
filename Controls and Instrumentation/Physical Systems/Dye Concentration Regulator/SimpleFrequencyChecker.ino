// Created by 3thanaut

// Colour Sensor input and output pins.
int out = 2;
int s0 = 4;
int s1 = 7;
int s2 = 8;
int s3 = 12;

bool colour_chosen = false;

void setup() {
  // put your setup code here, to run once:
  pinMode(out, INPUT);
  pinMode(s0, OUTPUT);
  pinMode(s1, OUTPUT);
  pinMode(s2, OUTPUT);
  pinMode(s3, OUTPUT);
}

void loop() {
  // put your main code here, to run repeatedly:
  /*
    s0 | s1 | Output Frequency Scaling
     L | L  | Power Off 
     L | H  | 2%
     H | L  | 20%
     H | H  | 100%
  */
  digitalWrite(s0, HIGH);
  digitalWrite(s1, HIGH);

  /*
    s2 | s3 | Photo Diode Type
     L | L  | RED
     L | H  | BLUE
     H | L  | CLEAR
     H | H  | GREEN
  */

  if (!colour_chosen) {

    while (true) {
      if (Serial.available() > 0) {
        char input = Serial.read();

        if (input == 'y' || input == 'Y') {
          break;
        }
      }
      Serial.println("Enter Y to continue.");
      delay(1000);
    }

    Serial.println("What colour do you want to use?");
    Serial.println("r = red");
    Serial.println("g = green");
    Serial.println("b = blue");

    while (true) {
      if (Serial.available() > 0) {
        char input = Serial.read();

        if (input == 'r') {
          
          // GREEN FILTER
          digitalWrite(s2, HIGH);
          digitalWrite(s3, HIGH);

          break;
        }else if (input == 'g') {

          // RED FILTER
          digitalWrite(s2, LOW);
          digitalWrite(s3, LOW);

          break;
        }else if (input == 'b') {

            // RED FILTER
          digitalWrite(s2, LOW);
          digitalWrite(s3, LOW);

          break;
        }
      }
    }
    colour_chosen = true;
  }

  float frequency = 1000000/(2 * pulseIn(out, HIGH));
  Serial.println(frequency);
  delay(1000);
}
