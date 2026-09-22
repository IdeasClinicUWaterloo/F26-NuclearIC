#include <Wire.h>
#include <DFRobot_BMX160.h>
#include <RunningAverage.h>

 
DFRobot_BMX160 bmx160_1(&Wire);
DFRobot_BMX160 bmx160_2(&Wire1);
 
float ax1, ay1, az1;
float ax2, ay2, az2;
 
RunningAverage avg1(20);
RunningAverage avg2(20);
 
void setup() {
  Serial.begin(115200);
 
  // I2C bus 0
  Wire.begin(23, 22);     // SDA = GPIO23, SCL = GPIO22
 
  // I2C bus 1
  Wire1.begin(6, 7);      // SDA = GPIO6, SCL = GPIO7
 
  // 400 kHz
  Wire.setClock(400000);
  Wire1.setClock(400000);
 
  if (bmx160_2.begin() != true || bmx160_1.begin() != true){
    Serial.println("Initialization failed");
    while(1);
  }
 
  Serial.println("Both sensors are initialized");
 
  delay(100);
}
 
void loop() {
  sBmx160SensorData_t Omagn_1, Ogyro_1, Oaccel_1;
  sBmx160SensorData_t Omagn_2, Ogyro_2, Oaccel_2;
 
  bmx160_1.getAllData(&Omagn_1, &Ogyro_1, &Oaccel_1);
  bmx160_2.getAllData(&Omagn_2, &Ogyro_2, &Oaccel_2);
 
  /* Accelerometer results (accelerometer data is in m/s^2) */
  ax1 = Oaccel_1.x, ay1 =  Oaccel_1.y, az1 = Oaccel_1.z;
  ax2 = Oaccel_2.x, ay2 =  Oaccel_2.y, az2 = Oaccel_2.z;
 
  float mag1 = sqrt(ax1*ax1 + ay1*ay1 + az1*az1);
  float mag2 = sqrt(ax2*ax2 + ay2*ay2 + az2*az2);
 
  avg1.addValue(mag1);
  avg2.addValue(mag2);
 
  float vib1 = abs(mag1 - avg1.getAverage());
  float vib2 = abs(mag2 - avg2.getAverage());
 
  Serial.print(vib1);
  Serial.print(",");
  Serial.println(vib2);
 
  delay(20);  // ~50 Hz
}