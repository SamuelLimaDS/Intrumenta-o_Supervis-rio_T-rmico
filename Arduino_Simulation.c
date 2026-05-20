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

Adafruit_SSD1306 display(
  SCREEN_WIDTH,
  SCREEN_HEIGHT,
  &Wire,
  -1
);

// =====================================================
// NTC 10K & AMOSTRAGEM
// =====================================================
const int sensorNTC = A0;

// divisor resistivo
const float resistorFixo = 10000.0;

// parâmetros NTC
const float beta = 3950.0;
const float tempNominal = 25.0;
const float resistenciaNominal = 10000.0;

// Quantidade de amostras para a média (Filtro Anti-Ruído)
const int NUM_AMOSTRAS = 15; 

// =====================================================
// LEDs
// =====================================================
const int ledVerde = 8;
const int ledAmarelo = 9;
const int ledVermelho = 10;

// =====================================================
// BOTÕES
// =====================================================
const int botaoEmergencia = 4;
const int botaoDiminuir = 12;
const int botaoAumentar = 13;

// =====================================================
// BUZZER
// =====================================================
const int buzzer = A3;

// =====================================================
// VARIÁVEIS GLOBAIS
// =====================================================
int adc = 0;
float resistenciaNTC = 0;
float temperatura = 0;

// =====================================================
// SETUP
// =====================================================
void setup()
{
  Serial.begin(9600);
  
  // PWM
  pinMode(peltierPin, OUTPUT);
  analogWrite(peltierPin, pwmValor);
  Serial.println("Controle PWM Peltier via Botoes");

  // OLED
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

  // LEDs
  pinMode(ledVerde, OUTPUT);
  pinMode(ledAmarelo, OUTPUT);
  pinMode(ledVermelho, OUTPUT);

  // Botões
  pinMode(botaoEmergencia, INPUT);
  pinMode(botaoDiminuir, INPUT);
  pinMode(botaoAumentar, INPUT);

  // Buzzer
  pinMode(buzzer, OUTPUT);
}

// =====================================================
// FUNÇÕES AUXILIARES
// =====================================================

void lerSensorNTC() 
{
  long somaADC = 0;

  // Realiza múltiplas leituras para estabilizar o valor
  for(int i = 0; i < NUM_AMOSTRAS; i++) {
    somaADC += analogRead(sensorNTC);
    delay(2); // Pequeno tempo para o ADC estabilizar
  }

  // Calcula a média
  adc = somaADC / NUM_AMOSTRAS;
  if(adc == 0) {
    adc = 1; // Evita divisão por zero
  }

  // Resistência NTC
  resistenciaNTC = resistorFixo * ((1023.0 / adc) - 1.0);

  // Equação Steinhart-Hart (Beta)
  float steinhart = resistenciaNTC / resistenciaNominal;
  steinhart = log(steinhart);
  steinhart /= beta;
  steinhart += 1.0 / (tempNominal + 273.15);
  steinhart = 1.0 / steinhart;
  steinhart -= 273.15;

  temperatura = steinhart;
}

void desenharTemperaturaBaseOLED() 
{
  display.clearDisplay();
  display.setTextSize(1);
  display.setCursor(0,0);
  display.print("Temp:");
  display.setTextSize(2);
  display.setCursor(0,12);
  display.print(temperatura, 1);
  display.print(" C");
  
  // Mostra também o valor atual do PWM no display
  display.setTextSize(1);
  display.setCursor(80,0);
  display.print("PWM:");
  display.setCursor(80,12);
  display.print(pwmValor);
}

bool verificarEmergencia() 
{
  if(digitalRead(botaoEmergencia) == HIGH) {
    // 1. Zera o PWM e desliga a Peltier por segurança
    pwmValor = 0;
    analogWrite(peltierPin, pwmValor);

    // 2. Acende o LED Vermelho e apaga os demais
    digitalWrite(ledVerde, HIGH);
    digitalWrite(ledAmarelo, HIGH);
    digitalWrite(ledVermelho, HIGH);

    // 3. Liga o Buzzer
    tone(buzzer, 1500);

    // 4. Atualiza o Display
    display.setTextSize(2);
    display.setCursor(0,40);
    display.print("EMERG");
    display.display();

    // 5. Avisa no Serial
    Serial.println("===============================");
    Serial.println("EMERGENCIA ACIONADA! PWM ZERADO.");
    Serial.println("===============================");
    Serial.println(temperatura);
    
    delay(300);
    
    return true; // Retorna verdadeiro se a emergência foi ativada
  }
  return false; // Retorna falso se não houver emergência
}

void atualizarStatusTemperatura() 
{
  if(temperatura <= 25) {
    // NORMAL
    digitalWrite(ledVerde, LOW);
    digitalWrite(ledAmarelo, HIGH);
    digitalWrite(ledVermelho, HIGH);
    noTone(buzzer);

    display.setTextSize(2);
    display.setCursor(0,40);
    display.print("NORMAL");
  }
  else if(temperatura > 25 && temperatura <= 30) {
    // ALERTA
    digitalWrite(ledVerde, HIGH);
    digitalWrite(ledAmarelo, LOW);
    digitalWrite(ledVermelho, HIGH);
    noTone(buzzer);

    display.setTextSize(2);
    display.setCursor(0,40);
    display.print("ALERTA");
  }
  else if(temperatura >= 31) {
    // CRÍTICO
    digitalWrite(ledVerde, HIGH);
    digitalWrite(ledAmarelo, HIGH);
    digitalWrite(ledVermelho, LOW);

    display.setTextSize(2);
    display.setCursor(0,40);
    display.print("CRITICO");
  }
}

void tratarBotoesPWM() 
{
  bool alterouPWM = false;
  String acao = "";

  // Verifica se o botão de diminuir (Pino 12) foi pressionado
  if (digitalRead(botaoDiminuir) == HIGH) {
    pwmValor -= 5;
    acao = "Diminuiu (-5). ";
    alterouPWM = true;
  }

  // Verifica se o botão de aumentar (Pino 13) foi pressionado
  if (digitalRead(botaoAumentar) == HIGH) {
    pwmValor += 5;
    acao = "Aumentou (+5). ";
    alterouPWM = true;
  }

  // Se algum botão foi apertado, atualiza o limite e a saída
  if (alterouPWM) {
    // Limita o PWM entre 0 e 255 para não dar erro na porta analógica
    pwmValor = constrain(pwmValor, 0, 255);
    
    analogWrite(peltierPin, pwmValor);

    // Printa a alteração de forma destacada no Serial Monitor
    Serial.println("===============================");
    Serial.print("Acao no Botao: ");
    Serial.print(acao);
    Serial.print("Novo Valor PWM: ");
    Serial.println(pwmValor);
    Serial.println("===============================");
    
    // Pequeno delay para evitar múltiplos acionamentos rápidos (debounce)
    delay(200); 
  }
}

// =====================================================
// LOOP PRINCIPAL
// =====================================================
void loop()
{
  // 1. Lê os dados do sensor
  lerSensorNTC();

  // 2. Prepara as informações base no display
  desenharTemperaturaBaseOLED();

  // 3. Verifica botão de emergência
  if (verificarEmergencia()) {
    return; // Se estiver em emergência, para o loop aqui (ignora os botões de PWM e LEDs de temperatura)
  }

  // 4. Verifica o status de temperatura para acender LEDs
  atualizarStatusTemperatura();

  // 5. Verifica os botões de aumentar e diminuir a potência (PWM)
  tratarBotoesPWM();

  // 6. Atualiza o OLED com todas as informações montadas
  display.display();

  // 7. Envia dados da temperatura para o Python/Serial Monitor
  Serial.println(temperatura);
  
  // Mantém o delay curto para os botões responderem rápido
  delay(100);
}