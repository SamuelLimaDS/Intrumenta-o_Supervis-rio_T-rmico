#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <math.h>

// =====================================================
// OLED
// =====================================================

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64

Adafruit_SSD1306 display(
  SCREEN_WIDTH,
  SCREEN_HEIGHT,
  &Wire,
  -1
);

// =====================================================
// NTC 10K
// =====================================================

const int sensorNTC = A0;

// divisor resistivo
const float resistorFixo = 10000.0;

// parâmetros NTC
const float beta = 3950.0;
const float tempNominal = 25.0;
const float resistenciaNominal = 10000.0;

// =====================================================
// LEDs
// =====================================================

const int ledVerde = 8;
const int ledAmarelo = 9;
const int ledVermelho = 10;

// =====================================================
// BOTÃO
// =====================================================

const int botao = 4;

// =====================================================
// BUZZER
// =====================================================

const int buzzer = A3;

// =====================================================
// VARIÁVEIS
// =====================================================

int adc = 0;

float resistenciaNTC = 0;
float temperatura = 0;

// =====================================================

void setup()
{
  Serial.begin(9600);

  // ==========================================
  // OLED
  // ==========================================

  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C))
  {
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

  // ==========================================
  // LEDs
  // ==========================================

  pinMode(ledVerde, OUTPUT);
  pinMode(ledAmarelo, OUTPUT);
  pinMode(ledVermelho, OUTPUT);

  // ==========================================
  // Botão
  // ==========================================

  pinMode(botao, INPUT_PULLUP);

  // ==========================================
  // Buzzer
  // ==========================================

  pinMode(buzzer, OUTPUT);
}

// =====================================================

void loop()
{
  // ==========================================
  // LEITURA ADC
  // ==========================================

  adc = analogRead(sensorNTC);

  if(adc == 0)
  {
    adc = 1;
  }

  // ==========================================
  // RESISTÊNCIA NTC
  // ==========================================

  resistenciaNTC =
    resistorFixo *
    ((1023.0 / adc) - 1.0);

  // ==========================================
  // EQUAÇÃO BETA
  // ==========================================

  float steinhart;

  steinhart = resistenciaNTC / resistenciaNominal;
  steinhart = log(steinhart);
  steinhart /= beta;
  steinhart += 1.0 / (tempNominal + 273.15);
  steinhart = 1.0 / steinhart;
  steinhart -= 273.15;

  temperatura = steinhart;

  // ==========================================
  // OLED
  // ==========================================

  display.clearDisplay();

  display.setTextSize(1);

  display.setCursor(0,0);
  display.print("Temp:");

  display.setTextSize(2);

  display.setCursor(0,12);
  display.print(temperatura,1);
  display.print(" C");

  // ==========================================
  // EMERGÊNCIA
  // ==========================================

  if(digitalRead(botao) == LOW)
  {
    digitalWrite(ledVerde, LOW);
    digitalWrite(ledAmarelo, LOW);
    digitalWrite(ledVermelho, HIGH);

    tone(buzzer, 1500);

    display.setTextSize(2);

    display.setCursor(0,40);
    display.print("EMERG");

    display.display();

    Serial.println(temperatura);

    delay(300);

    return;
  }

  // ==========================================
  // NORMAL
  // ==========================================

  if(temperatura < 30)
  {
    digitalWrite(ledVerde, HIGH);
    digitalWrite(ledAmarelo, LOW);
    digitalWrite(ledVermelho, LOW);

    noTone(buzzer);

    display.setTextSize(2);

    display.setCursor(0,40);
    display.print("NORMAL");
  }

  // ==========================================
  // ALERTA
  // ==========================================

  else if(temperatura >= 30 && temperatura < 50)
  {
    digitalWrite(ledVerde, LOW);
    digitalWrite(ledAmarelo, HIGH);
    digitalWrite(ledVermelho, LOW);

    noTone(buzzer);

    display.setTextSize(2);

    display.setCursor(0,40);
    display.print("ALERTA");
  }

  // ==========================================
  // CRÍTICO
  // ==========================================

  else
  {
    digitalWrite(ledVerde, LOW);
    digitalWrite(ledAmarelo, LOW);
    digitalWrite(ledVermelho, HIGH);

    tone(buzzer, 1200);

    display.setTextSize(2);

    display.setCursor(0,40);
    display.print("CRITICO");
  }

  // ==========================================
  // UPDATE OLED
  // ==========================================

  display.display();

  // ==========================================
  // SERIAL PARA PYTHON
  // ==========================================

  Serial.println(temperatura);

  delay(1000);
}