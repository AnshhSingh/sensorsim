const int LDR_PIN = A5;
const int NTC_PIN = A1;  // NTC on A1

// NTC Parameters (Customize these for your thermistor)
const float VCC = 5.0;          // Supply voltage
const float R_SERIES = 10000.0; // Series resistor value (10kΩ)
const float R_NOMINAL = 10000.0; // NTC resistance at 25°C
const float TEMP_NOMINAL = 25.0; // Nominal temperature (25°C)
const float BETA = 3950.0;       // Beta coefficient (check your NTC datasheet)

void setup() {
  Serial.begin(9600);
}

void loop() {
  // Read raw sensor values
  int moistureRaw = analogRead(A0);
  int ntcRaw = analogRead(NTC_PIN);
  int nitrogenRaw = analogRead(A2);
  int phosphorusRaw = analogRead(A3);
  int potassiumRaw = analogRead(A4);
  int ldrRaw = analogRead(LDR_PIN);

  // Convert NTC reading to temperature
  float resistance = R_SERIES / ((1023.0 / ntcRaw) - 1.0);
  float steinhart = resistance / R_NOMINAL;     // (R/Ro)
  steinhart = log(steinhart);                   // ln(R/Ro)
  steinhart /= BETA;                            // 1/B * ln(R/Ro)
  steinhart += 1.0 / (TEMP_NOMINAL + 273.15);   // + (1/To)
  float tempCelsius = (1.0 / steinhart) - 273.15;

  // Other conversions
  float moisturePercent = map(moistureRaw, 0, 1023, 0, 100);
  int sunlightPercent = map(ldrRaw, 0, 1023, 100, 0);
  
  // NPK values (simulated)
  float nitrogen = map(nitrogenRaw, 0, 1023, 0, 100);
  float phosphorus = map(phosphorusRaw, 0, 1023, 0, 100);
  float potassium = map(potassiumRaw, 0, 1023, 0, 100);

  // Build JSON payload
  Serial.print("{");
  Serial.print("\"timestamp\":"); Serial.print(millis());
  Serial.print(",\"sensors\":{");
  Serial.print("\"soil\":{");
  Serial.print("\"moisture\":"); Serial.print(moisturePercent, 1);
  Serial.print(",\"temperature\":"); Serial.print(tempCelsius, 1);
  Serial.print("},");
  Serial.print("\"nutrients\":{");
  Serial.print("\"nitrogen\":"); Serial.print(nitrogen, 1);
  Serial.print(",\"phosphorus\":"); Serial.print(phosphorus, 1);
  Serial.print(",\"potassium\":"); Serial.print(potassium, 1);
  Serial.print("},");
  Serial.print("\"environment\":{");
  Serial.print("\"sunlight\":"); Serial.print(sunlightPercent);
  Serial.print("}");
  Serial.print("}"); // Close sensors object
  Serial.println("}"); // Close root object

  delay(1000);
}