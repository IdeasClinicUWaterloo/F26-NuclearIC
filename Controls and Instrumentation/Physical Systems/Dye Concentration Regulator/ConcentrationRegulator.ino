// Created by 3thanaut

// Colour Sensor input and output pins.
int out = 2;
int s0 = 4;
int s1 = 7;
int s2 = 8;
int s3 = 12;

// Pump motor driver pins.
int DYE_PUMP_PWM_PIN     = 3; // Driver 1 IN1
int DYE_PUMP_LOW_PIN     = 5; // Driver 1 IN2
int CLEAR_PUMP_PWM_PIN   = 6; // Driver 1 IN3
int CLEAR_PUMP_LOW_PIN   = 9; // Driver 1 IN4
int WASTE_PUMP_PWM_PIN   = 10; // Driver 2 IN1
int WASTE_PUMP_LOW_PIN   = 11; // Driver 2 IN2

int current_pwm = DYE_PUMP_PWM_PIN;
int current_low = DYE_PUMP_LOW_PIN;

// USER MUST INPUT THESE VALUES.
float clear_frequency = 0;
float beta0 = 0;
float beta1 =  0;
float dye_reservoir_frequency = 0;
float pump_output = 0; // in mL/s

// Constant volume values.
float reservoir_volume = 400; // mL
float control_tank_volume = 350; // in mL
float residence_time = control_tank_volume / pump_output;

// Bounds so program doesn't run for eternity.
float max_time = (reservoir_volume - 50)/pump_output; // subtracting 50mL to keep pump submerged.

// reads and returns user input floats.
float readFloat() {

  float concentration;
  while (true) {
    if (Serial.available() > 0) {
      // reads the users input number.
      char c = Serial.peek();

      if (isDigit(c)) {
        
        concentration = Serial.parseFloat();
        Serial.print("Selected Value: ");
        Serial.println(concentration, 10);

        break;
      }else{
        Serial.read();
      }
    }
    delay(10);
  }
  return concentration;
}

// Allows users to input target concentration and does not allow impossible targets.
// Also changes current_pwm and low_pwm by external reference.
float setTargetConcentration(float initial_concentration, float reservoir_concentration) {

  Serial.println("Enter the target concentration (remember to try and stay between MAX and MIN).");
  float target_concentration = readFloat();

  // use clear water pump.
  if (initial_concentration > target_concentration) {
    reservoir_concentration = 0;
    current_pwm = CLEAR_PUMP_PWM_PIN;
    current_low = CLEAR_PUMP_LOW_PIN;
  }

  // function derived from differential representing difference in concentration w/r/t time, dC/dV = Cr * v - C(t) * v where Cr is reservoir concentration and v = (pump_output / control tank volume)
  // should function great for the three possible cases (zero concentration to higher concentration, non zero concentration to higher concentration, non zero concentration to lower concentration).
  float time = -residence_time * log((reservoir_concentration - target_concentration)/(reservoir_concentration - initial_concentration));
  
  if (time > max_time) {
    Serial.println("Target concentration outside of attainable range. Reservoirs would drain before completion.");
    setTargetConcentration(initial_concentration, reservoir_concentration);
  }else{
    return time;
  }
}

void setup() {
  // put your setup code here, to run once:

  pinMode(out, INPUT);
  pinMode(s0, OUTPUT);
  pinMode(s1, OUTPUT);
  pinMode(s2, OUTPUT);
  pinMode(s3, OUTPUT);

  pinMode(DYE_PUMP_PWM_PIN, OUTPUT);
  pinMode(DYE_PUMP_LOW_PIN, OUTPUT);

  pinMode(CLEAR_PUMP_PWM_PIN, OUTPUT);
  pinMode(CLEAR_PUMP_LOW_PIN, OUTPUT);

  pinMode(WASTE_PUMP_PWM_PIN, OUTPUT);
  pinMode(WASTE_PUMP_LOW_PIN, OUTPUT);
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
  // USER MUST CHANGE THIS TO APPROPRIATE FILTER.
  // Note that the filter should be the opposite colour of the dye!
  // start with proper filter
  digitalWrite(s2, LOW);
  digitalWrite(s3, LOW);

  // give sensor breathing room.
  // Control tank is read immediately to prevent sensor fault.
  delay (500);

  // finds the concentration of the control tank.
  float initial_frequency = 1000000/(2 * pulseIn(out, HIGH)); // convert from microseconds to seconds.
  float initial_absorption = -log10(initial_frequency/clear_frequency);
  float initial_concentration = beta0 + beta1 * initial_absorption;

  // Pauses so that values may be displayed to the user.
  // Serial monitor has some strange interactions that have to be accounted for.
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

  // prints relevant control tank information.
  Serial.print("Control Tank Frequency: ");
  Serial.println(initial_frequency);
  Serial.print("Control Tank Absorption: ");
  Serial.println(initial_absorption);
  Serial.print("Control Tank Concentration: ");
  Serial.println(initial_concentration, 10);

  // starts with dye reservoir concentration because setTargetConcentration will determine whether it should use dye reservoir or clear reservoir.
  float reservoir_frequency = dye_reservoir_frequency;
  float reservoir_absorption = -log10(reservoir_frequency / clear_frequency);
  float reservoir_concentration = beta0 + beta1 * reservoir_absorption;

  float time = setTargetConcentration(initial_concentration, reservoir_concentration);

  Serial.println(time);

  // USER MUST ADJUST PWM PINS FROM CALIBRATION.
  // Should give roughly 3V to each of the required pumps
  analogWrite(current_pwm, 85);
  digitalWrite(current_low, LOW);

  analogWrite(WASTE_PUMP_PWM_PIN, 85);
  digitalWrite(WASTE_PUMP_LOW_PIN, LOW);

  // Continue with pumps on for time in milliseconds
  delay(time * 1000);

  // Disable pumps once complete.
  analogWrite(current_pwm, 0);
  digitalWrite(current_low, LOW);

  analogWrite(WASTE_PUMP_PWM_PIN, 0);
  digitalWrite(WASTE_PUMP_LOW_PIN, LOW);

  while (true) {
    Serial.println("Regulation Complete!");
    delay(60000);
  }
}
