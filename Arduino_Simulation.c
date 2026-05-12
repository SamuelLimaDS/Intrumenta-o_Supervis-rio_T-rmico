/*
============================================================
SIMULADOR DE TEMPERATURA PARA SUPERVISÓRIO PYTHON
USF - Monitoramento Térmico de Processos
============================================================

OBJETIVO:
Simular um sensor LM35 sem precisar conectar componentes.

O Arduino enviará temperaturas falsas pela serial,
permitindo testar o supervisório Python.

============================================================
COMO USAR:
1. Carregue este código no Arduino
2. Descubra a porta COM
3. No Python:
   SERIAL_PORT = "COM3"   <-- alterar
4. Execute o supervisório Python
============================================================
*/

float temperatura = 25.0;

// controle da simulação
bool subindo = true;

void setup()
{
    Serial.begin(9600);

    randomSeed(analogRead(0));
}

void loop()
{
    // =====================================================
    // SIMULAÇÃO DE TEMPERATURA
    // =====================================================

    // sobe lentamente
    if (subindo)
    {
        temperatura += random(1, 5) * 0.1;
    }
    else
    {
        temperatura -= random(1, 5) * 0.1;
    }

    // limites da simulação
    if (temperatura >= 90)
    {
        subindo = false;
    }

    if (temperatura <= 30)
    {
        subindo = true;
    }

    // pequeno ruído aleatório
    temperatura += random(-2, 3) * 0.05;

    // =====================================================
    // ENVIA PARA PYTHON
    // =====================================================

    Serial.println(temperatura);

    // intervalo de atualização
    delay(1000);
}
