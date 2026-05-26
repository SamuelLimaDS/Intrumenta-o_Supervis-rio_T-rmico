#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <math.h>

// =====================================================
// PWM
// =====================================================
const int peltierPin = 5;
int pwmValor = 0;

// =====================================================
// OLED
// =====================================================
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

// =====================================================
// CONFIGURAÇÕES DOS SENSORES & AMOSTRAGEM
// =====================================================
const int sensorNTC = A0;
const int sensorLM35 = A1; // Pino adicionado para o LM35

const float resistorFixo = 10000.0;
const float beta = 3950.0;
const float tempNominal = 25.0;
const float resistenciaNominal = 10000.0;
const int NUM_AMOSTRAS = 15; 

// =====================================================
// LEDs, BOTOES E BUZZER
// =====================================================
const int ledVerde = 8;
const int ledAmarelo = 9;
const int ledVermelho = 10;
const int botaoEmergencia = 4;
const int botaoDiminuir = 12;
const int botaoAumentar = 13;
const int buzzer = A3;

// Variáveis Globais
int adc = 0;          // ADC do NTC
int adcLm35 = 0;      // ADC do LM35
float resistenciaNTC = 0;
float temperatura = 0;   // Temperatura do NTC
float tempLm35 = 0;      // Temperatura do LM35

// Protótipo da função para evitar incompatibilidades de compilação
void enviarDadosSerial(int statusEmergencia);

void setup() {
  Serial.begin(9600);
  
  pinMode(peltierPin, OUTPUT);
  analogWrite(peltierPin, pwmValor);

  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    while(true);
  }

  display.clearDisplay();
  display.setTextSize(2);
  display.setTextColor(WHITE);
  display.setCursor(0,0);
  display.println("USF");
  display.setTextSize(1);
  display.println("Monitoramento Dual");
  display.display();
  delay(2000);

  pinMode(ledVerde, OUTPUT);
  pinMode(ledAmarelo, OUTPUT);
  pinMode(ledVermelho, OUTPUT);
  pinMode(botaoEmergencia, INPUT);
  pinMode(botaoDiminuir, INPUT);
  pinMode(botaoAumentar, INPUT);
  pinMode(buzzer, OUTPUT);
}

void lerSensorNTC() {
  long somaADC = 0;
  for(int i = 0; i < NUM_AMOSTRAS; i++) {
    somaADC += analogRead(sensorNTC);
    delay(2);
  }

  adc = somaADC / NUM_AMOSTRAS;
  if(adc == 0) adc = 1;

  resistenciaNTC = resistorFixo * ((1023.0 / adc) - 1.0);
  float steinhart = resistenciaNTC / resistenciaNominal;
  steinhart = log(steinhart);
  steinhart /= beta;
  steinhart += 1.0 / (tempNominal + 273.15);
  steinhart = 1.0 / steinhart;
  steinhart -= 273.15;
  temperatura = steinhart;
}

void lerSensorLM35() {
  long somaADC = 0;
  for(int i = 0; i < NUM_AMOSTRAS; i++) {
    somaADC += analogRead(sensorLM35);
    delay(2);
  }
  
  adcLm35 = somaADC / NUM_AMOSTRAS;
  
  // LM35 fornece 10mV por grau Celsius (Tensão = ADC * 5.0 / 1023)
  float voltagem = (adcLm35 * 5.0) / 1023.0;
  tempLm35 = voltagem * 100.0;
}

void desenharTemperaturaBaseOLED() {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(WHITE);
  
  // Exibição compacta das duas temperaturas
  display.setCursor(0,0);
  display.print("NTC : ");
  display.print(temperatura, 1);
  display.print(" C");
  
  display.setCursor(0,12);
  display.print("LM35: ");
  display.print(tempLm35, 1);
  display.print(" C");
  
  display.setCursor(85,0);
  display.print("PWM:");
  display.setCursor(85,12);
  display.print(pwmValor);
}

void atualizarStatusTemperatura() {
  // A lógica de alertas locais continuará usando o NTC como referência primária
  if(temperatura <= 25) {
    digitalWrite(ledVerde, LOW);
    digitalWrite(ledAmarelo, HIGH);
    digitalWrite(ledVermelho, HIGH);
    noTone(buzzer);
    display.setTextSize(2);
    display.setCursor(0,40);
    display.print("NORMAL");
  }
  else if(temperatura > 25 && temperatura <= 30) {
    digitalWrite(ledVerde, HIGH);
    digitalWrite(ledAmarelo, LOW);
    digitalWrite(ledVermelho, HIGH);
    noTone(buzzer);
    display.setTextSize(2);
    display.setCursor(0,40);
    display.print("ALERTA");
  }
  else if(temperatura >= 31) {
    digitalWrite(ledVerde, HIGH);
    digitalWrite(ledAmarelo, HIGH);
    digitalWrite(ledVermelho, LOW);
    display.setTextSize(2);
    display.setCursor(0,40);
    display.print("CRITICO");
  }
}

void tratarBotoesPWM() {
  bool alterouPWM = false;

  if (digitalRead(botaoDiminuir) == HIGH) {
    pwmValor -= 5;
    alterouPWM = true;
  }
  if (digitalRead(botaoAumentar) == HIGH) {
    pwmValor += 5;
    alterouPWM = true;
  }

  if (alterouPWM) {
    pwmValor = constrain(pwmValor, 0, 255);
    analogWrite(peltierPin, pwmValor);
    delay(200); 
  }
}

bool verificarEmergencia() {
  if(digitalRead(botaoEmergencia) == HIGH) {
    pwmValor = 0;
    analogWrite(peltierPin, pwmValor);

    digitalWrite(ledVerde, HIGH);
    digitalWrite(ledAmarelo, HIGH);
    digitalWrite(ledVermelho, HIGH);

    tone(buzzer, 1500);

    display.setTextSize(2);
    display.setCursor(0,40);
    display.print("EMERG");
    display.display();
    
    enviarDadosSerial(1); 
    delay(300);
    return true; 
  }
  return false; 
}

void enviarDadosSerial(int statusEmergencia) {
  // Novo formato de transmissão: TempNTC,ADCNTC,TempLM35,ADCLM35,PWM,Emergencia
  Serial.print(temperatura);
  Serial.print(",");
  Serial.print(adc);
  Serial.print(",");
  Serial.print(tempLm35);
  Serial.print(",");
  Serial.print(adcLm35);
  Serial.print(",");
  Serial.print(pwmValor);
  Serial.print(",");
  Serial.println(statusEmergencia);
}

void loop() {
  lerSensorNTC();
  lerSensorLM35();
  desenharTemperaturaBaseOLED();

  if (verificarEmergencia()) {
    return; 
  }

  atualizarStatusTemperatura();
  tratarBotoesPWM();
  display.display();

  enviarDadosSerial(0);
  delay(100);
}