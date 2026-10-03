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

// Constant volume values.
float reservoir_volume = 400;
float control_tank_volume = 350; // in mL
float pump_output = 7; // in mL/s
float residence_time = control_tank_volume / pump_output;

// User input values.
float clear_frequency = 4273.50;
float beta0 = -0.0011347929;
float beta1 =  0.0024182338;

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

  // function derived from differential, need the difference in time
  float time_to_target = -residence_time * log(1 - (target_concentration / reservoir_concentration));
  float time_to_current = -residence_time * log(1 - (initial_concentration / reservoir_concentration));
  float time = abs(time_to_current - time_to_target);

  if (time > max_time) {
    Serial.println("Target concentration outside of attainable range.");
    setTargetConcentration(initial_concentration, reservoir_concentration);
  }else{
    return target_concentration;
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
  // start with proper filter
  digitalWrite(s2, LOW);
  digitalWrite(s3, LOW);

  // give sensor breathing room.
  delay (500);

  // finds the concentration of the control tank.
  float initial_frequency = 1000000/(2 * pulseIn(out, HIGH));
  float initial_absorption = -log10(initial_frequency/clear_frequency);
  float initial_concentration = beta0 + beta1 * initial_absorption;

  if (initial_concentration < 0) {
    initial_concentration = 0;
  }

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

  Serial.print("Control Tank Frequency: ");
  Serial.println(initial_frequency);
  Serial.print("Control Tank Absorption: ");
  Serial.println(initial_absorption);
  Serial.print("Control Tank Concentration: ");
  Serial.println(initial_concentration, 10);

  // after reading the tank concentration, the reservoir concentration is requested.
  // This allows users to keep the reservoir in place, and gives time to put the control tank back.
  // Reservoir frequency may also change between loops, same with control tank, therefore its requested alongside it.
  // However, clear frequency and the calibration values should not have to change.
  Serial.println("Enter the dye reservoir frequency: ");
  float reservoir_frequency = readFloat();
  float reservoir_absorption = -log10(reservoir_frequency / clear_frequency);
  float reservoir_concentration = beta0 + beta1 * reservoir_absorption;

  float target_concentration = setTargetConcentration(initial_concentration, reservoir_concentration);

  // function derived from differential, need the difference in time
  float time_to_target = -residence_time * log(1 - (target_concentration / reservoir_concentration));
  float time_to_current = -residence_time * log(1 - (initial_concentration / reservoir_concentration));
  float time = abs(time_to_current - time_to_target);

  Serial.println(time);

  // Should give roughly 3V to the required pumps
  analogWrite(current_pwm, 170); // needs to be tuned to appropriately run.
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
