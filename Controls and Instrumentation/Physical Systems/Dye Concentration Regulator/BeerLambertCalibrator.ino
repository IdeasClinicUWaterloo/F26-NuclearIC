// Created by Ethan Nauta

// Colour Sensor input and output pins.
int out = 2;
int s0 = 4;
int s1 = 7;
int s2 = 8;
int s3 = 12;

// user input solution information
int solution_count = 0;
int num_drops = 0;
int solution_i = 0; // special iterative so we can break out of for loop early on user command.

// used to assure calibration only happens once.
// can't put calibration function in void setup or else pinmodes dont establish and all readings are zero.
bool calibrated = false;

// state machine bools.
bool _isContinuing             = false;
bool _isChoosingColour         = false;
bool _isCountingDrops          = false;

// beta values for simple linear regression of form y = beta0 + beta1 * x
float beta0;
float beta1;

float clear_frequency = 0;

// records important information about solutions.
// kept global so it can be used to record bounds for interpolation. (avoiding extrapolation because of potential innacuracy).
float solution_frequencies[10]    = {};
float solution_absorptions[10]    = {};
float solution_concentrations[10] = {};

// pauses program to allow user to follow steps and confirm when they are done by entering Y.
// if notify is true, continuously prints "enter y to start"
void query_user(bool notify) {

  while (true) {

    if (_isContinuing) {

      if (Serial.available() > 0) {
        char input = Serial.read();

        if (input == 'y' || input == 'Y') {
          break;
        }
      }
    }

    if (_isCountingDrops) {
      if (Serial.available() > 0) {

        // reads the users input number.
        char c = Serial.peek();

        if (isDigit(c)) {
          num_drops = Serial.parseInt();
          Serial.println(num_drops);
          solution_count += 1;
          break;
        }else if (isAlpha(c)) {
          if (c == 'y' || c == 'Y') {

            solution_i = 10;
            break;
          }
        }else{
          Serial.read();
        }
      }
    }

    // Chooses the colour for the food dye.
    // Filter is chosen based on colour most absorbed by the solution.
    // Red food dye will absorb the most green light, causing most noticable green light intensity change.
    if (_isChoosingColour) {
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

    if (notify == true) {
      delay(1000);
      Serial.println("Enter Y to start.");
    }
  }
}


void calibrate() {

  Serial.println("What colour do you want to use?");
  Serial.println("r = red");
  Serial.println("g = green");
  Serial.println("b = blue");

  _isChoosingColour = true;
  query_user(false);
  _isChoosingColour = false;

  Serial.println("The sensor needs to know what clear water looks like.");
  Serial.println("Fill the control tank with 350mL of clear water, then put a piece of white paper underneath it.");
  Serial.println("Once this is under the sensor, enter Y to continue!");

  _isContinuing = true;
  query_user(false);
  _isContinuing = false;

  // the reciprocal of the period in seconds of the square wave function represents the frequency.
  // the frequency and intensity are directly proportional in terms of how they scale, this means absorption can be found with frequency.
  float clear_pulse = pulseIn(out, HIGH);
  clear_frequency = 1000000/(2 * clear_pulse);

  Serial.print("Clear water frequency recorded!:  ");
  Serial.println(clear_frequency);

  Serial.println("Now, we need more known points to graph concentration against absorption.");
  Serial.println("Prepare at least 5 solutions (you can do up to 10) for the creation of the beer lamberts model.");
  Serial.println("For each solution, you will be asked to enter the INTEGER number of drops of food dye it contains.");
  Serial.println("Entering a number will store that number, and read its frequency. Then it will ask for the next solution.");
  Serial.println("Enter Y to proceed to the process of creating the model.");

  _isContinuing = true;
  query_user(false);
  _isContinuing = false;

  Serial.println("Enter Y when you are happy with the number of solutions you have scanned!");


  // Query loop to let the user add solutions.
  _isCountingDrops = true;
  for (solution_i = 0; solution_i < 10; solution_i++) {
    num_drops = 0;
    Serial.print("Enter number of drops for solution ");
    Serial.println(solution_count + 1);

    // wait for user to input number of drops.
    query_user(false);

    if (num_drops != 0) {
      // reads the wave length for the given solution.
      solution_frequencies[solution_count - 1] = 1000000/(2 * pulseIn(out, HIGH));

      // converts the number of drops to a volume and then a concentration (mL food dye / mL water).
      solution_concentrations[solution_count - 1] = (num_drops * 0.05)/(350);
    }else{
      Serial.println("Clear solution already used in calibration! Need solution with some new concentration of dye.");
      solution_i -= 1;
    }
  }
  _isCountingDrops = false;

  Serial.println("All solutions prepared! Calculating linear fit...");
  Serial.println(solution_count);

  float sumX = 0;
  float sumY = 0;
  float sumXY = 0;
  float sumXX = 0;

  Serial.println("ABSORPTION");
  for (int i = 0; i < solution_count; i++) {

    solution_absorptions[i] = -log10(solution_frequencies[i]/clear_frequency);

    sumX += solution_absorptions[i];
    sumY += solution_concentrations[i];
    sumXX += solution_absorptions[i] * solution_absorptions[i];
    sumXY += solution_absorptions[i] * solution_concentrations[i];

    Serial.println(solution_absorptions[i], 10);
  }

  Serial.println("CONCENTRATION");
  for (int i = 0; i < solution_count; i++) {

    Serial.println(solution_concentrations[i], 10);
  }

  beta1 = (solution_count * sumXY - sumX * sumY) / (solution_count * sumXX - sumX * sumX);
  beta0 = (sumY/solution_count) - beta1 * (sumX/solution_count);
  Serial.print("beta1: ");
  Serial.println(beta1, 10);
  Serial.print("beta0: ");
  Serial.println(beta0, 10);

  calibrated = true;
}


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
  // start with clear filter
  digitalWrite(s2, HIGH);
  digitalWrite(s3, LOW);

  if (!calibrated) {

    _isContinuing = true;
    query_user(true);
    _isContinuing = false;
    calibrate();
  }else{
    Serial.println("Calibration complete! Please copy your ABSORPTION and CONCENTRATION values and move to the concentration regulator program!");
  }
  delay(60000);
}
