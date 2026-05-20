#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <math.h>

// =====================================================
// PWM
// =====================================================
const int peltierPin = 3;
int pwmValor = 0;

// =====================================================
// OLED
// =====================================================
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

// =====================================================
// NTC 10K & AMOSTRAGEM
// =====================================================
const int sensorNTC = A0;
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
int adc = 0;
float resistenciaNTC = 0;
float temperatura = 0;

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
  display.println("Monitoramento");
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

void desenharTemperaturaBaseOLED() {
  display.clearDisplay();
  display.setTextSize(1);
  display.setCursor(0,0);
  display.print("Temp:");
  display.setTextSize(2);
  display.setCursor(0,12);
  display.print(temperatura, 1);
  display.print(" C");
  
  display.setTextSize(1);
  display.setCursor(80,0);
  display.print("PWM:");
  display.setCursor(80,12);
  display.print(pwmValor);
}

void atualizarStatusTemperatura() {
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

void verificarEmergencia() {
  if(digitalRead(botaoEmergencia) == HIGH) {
    // 1. Zera o PWM e desliga a Peltier por segurança
    pwmValor = 0;
    analogWrite(peltierPin, pwmValor);

    // 2. Acende os LEDs de alerta
    digitalWrite(ledVerde, HIGH);
    digitalWrite(ledAmarelo, HIGH);
    digitalWrite(ledVermelho, HIGH);

    // 3. Liga o Buzzer
    tone(buzzer, 1500);

    // 4. Atualiza o Display OLED local
    display.setTextSize(2);
    display.setCursor(0,40);
    display.print("EMERG");
    display.display();
    
    // 5. Envia os dados para o Python avisando que a emergência está ATIVA (1)
    enviarDadosSerial(1); 
    delay(300);
    return true; 
  }
  return false; 
}

// Agora a função recebe o status da emergência (0 para normal, 1 para ativa)
void enviarDadosSerial(int statusEmergencia) {
  // Envia no formato: Temperatura,ADC,PWM,Emergencia
  Serial.print(temperatura);
  Serial.print(",");
  Serial.print(adc);
  Serial.print(",");
  Serial.print(pwmValor);
  Serial.print(",");
  Serial.println(statusEmergencia);
}

void loop() {
  lerSensorNTC();
  desenharTemperaturaBaseOLED();

  // Se estiver em emergência, o loop para aqui e envia o status "1"
  if (verificarEmergencia()) {
    return; 
  }

  atualizarStatusTemperatura();
  tratarBotoesPWM();
  display.display();

  // Loop normal envia o status de emergência como "0"
  enviarDadosSerial(0);
  delay(100);
}