void setup() {
    Serial.begin(9600);
  }
  
  void loop() {
    int moistureRaw = analogRead(A0);    // Soil moisture
    int temperatureRaw = analogRead(A1); // NTC/LM35
    int nitrogenRaw   = analogRead(A2);  // Potentiometer
    int phosphorusRaw = analogRead(A3);  // Potentiometer
    int potassiumRaw  = analogRead(A4);  // Potentiometer
  
    // Convert to real-world units
    float tempCelsius = map(temperatureRaw, 0, 1023, 100, 0); // crude inversion
  
    float moisturePercent = map(moistureRaw, 0, 1023, 0, 100);   // 0–100%
    float nitrogen   = map(nitrogenRaw, 0, 1023, 0, 100);        // mg/kg
    float phosphorus = map(phosphorusRaw, 0, 1023, 0, 100);      // mg/kg
    float potassium  = map(potassiumRaw, 0, 1023, 0, 100);       // mg/kg
  
    // Print JSON with units
    Serial.print("{");
    Serial.print("\"nitrogen_mgkg\":");   Serial.print(nitrogen);
    Serial.print(",\"phosphorus_mgkg\":"); Serial.print(phosphorus);
    Serial.print(",\"potassium_mgkg\":");  Serial.print(potassium);
    Serial.print(",\"moisture_percent\":"); Serial.print(moisturePercent);
    Serial.print(",\"temperature_celsius\":"); Serial.print(tempCelsius);
    Serial.println("}");
  
    delay(3000);
  }
  