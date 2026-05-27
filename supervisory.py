# ============================================================
# ARQUIVO: supervisory.py
# OBJETIVO: Lógica do sistema, Porta Serial e Controle da Tela
# ============================================================
import sys
import serial
import threading
import time
from collections import deque
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

from interface import InterfaceSupervisorio

# ============================================================
# CONFIGURAÇÕES E VARIÁVEIS GLOBAIS
# ============================================================
SERIAL_PORT = "COM9"      # ALTERAR PARA SUA PORTA COM
BAUD_RATE = 9600
TEMP_3 = 15
TEMP_1 = 25
TEMP_2 = 30

# Variáveis globais duplicadas para os dois sensores
temperatura_ntc = 0.0
temperatura_lm35 = 0.0
adc_ntc = 0
adc_lm35 = 0

pwm_atual = 0
emergencia_ativa = False 

# Históricos individuais para plotagem paralela
historico_ntc = deque(maxlen=100)
historico_lm35 = deque(maxlen=100)

status_serial = False
arduino = None
tela = None

# ============================================================
# FUNÇÃO DA PORTA SERIAL (Thread Paralela)
# ============================================================
def serial_thread():
    global arduino, status_serial, temperatura_ntc, adc_ntc, temperatura_lm35, adc_lm35, pwm_atual, emergencia_ativa
    
    while True:
        try:
            if arduino is None or not arduino.is_open:
                arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
                time.sleep(2)
                status_serial = True

            if arduino.in_waiting:
                linha = arduino.readline().decode().strip()
                partes = linha.split(',')
                
                # Tratamento do novo pacote contendo os 6 parâmetros decimais/inteiros
                if len(partes) == 6:
                    try:
                        temperatura_ntc = float(partes[0])
                        adc_ntc = int(partes[1])
                        temperatura_lm35 = float(partes[2])
                        adc_lm35 = int(partes[3])
                        pwm_atual = int(partes[4])
                        emergencia_ativa = (int(partes[5]) == 1) 
                        
                        historico_ntc.append(temperatura_ntc)
                        historico_lm35.append(temperatura_lm35)
                    except ValueError:
                        pass 

        except Exception:
            status_serial = False
            arduino = None
            time.sleep(2) 

# ============================================================
# FUNÇÃO DE ATUALIZAÇÃO VISUAL (Chamada via Timer PyQt5)
# ============================================================
def atualizar_interface():
    global temperatura_ntc, adc_ntc, temperatura_lm35, adc_lm35, pwm_atual, emergencia_ativa, status_serial, tela
    
    # 1. Atualiza Leituras Diretas na Tela (NTC e LM35)
    tela.temp_ntc_label.setText(f"NTC: {temperatura_ntc:.1f} °C")
    tela.temp_lm35_label.setText(f"LM35: {temperatura_lm35:.1f} °C")
    
    tela.label_adc_ntc.setText(f"ADC NTC 10K: {adc_ntc}")
    tela.label_adc_lm35.setText(f"ADC LM35: {adc_lm35}")
    tela.label_pwm.setText(f"Valor PWM: {pwm_atual}")
    
    # 2. Atualiza o Gráfico com as duas curvas independentes
    tela.curve_ntc.setData(list(historico_ntc))
    tela.curve_lm35.setData(list(historico_lm35))

    # 3. Verifica Status da Conexão Serial
    if status_serial:
        tela.label_status.setText("● ONLINE")
        tela.label_status.setStyleSheet("color:#00ff66; font-size:20px; font-weight:bold;")
    else:
        tela.label_status.setText("● OFFLINE")
        tela.label_status.setStyleSheet("color:red; font-size:20px; font-weight:bold;")

    # 4. Regras de Alarme baseadas na leitura do NTC (Referência principal da câmara)
    if emergencia_ativa:
        tela.status_processo.setText("EMERGÊNCIA ATIVA")
        tela.status_processo.setStyleSheet("color:red; font-size:36px; font-weight:bold; border: none;")
        tela.alerta.setText("SISTEMA BLOQUEADO PELO BOTÃO FÍSICO!")
        tela.alerta.setStyleSheet("color:#ff3333; font-size:20px; font-weight:bold; border: none;")
    
    elif temperatura_ntc <= TEMP_3:
        tela.status_processo.setText("TEMPERATURA BAIXA")
        tela.status_processo.setStyleSheet("color:blue; font-size:36px; font-weight:bold; border: none;")
        tela.alerta.setText("SENSOR DESLIGADO OU AMBIENTE FRIO")
        tela.alerta.setStyleSheet("color:white; font-size:20px; border: none;")
        
    elif TEMP_3 < temperatura_ntc <= TEMP_1:
        tela.status_processo.setText("TEMPERATURA NORMAL")
        tela.status_processo.setStyleSheet("color:#00ff66; font-size:36px; font-weight:bold; border: none;")
        tela.alerta.setText("TEMPERATURA AMBIENTE")
        tela.alerta.setStyleSheet("color:white; font-size:20px; border: none;")
        
    elif TEMP_1 < temperatura_ntc <= TEMP_2:
        tela.status_processo.setText("TEMPERATURA MÉDIA")
        tela.status_processo.setStyleSheet("color:yellow; font-size:36px; font-weight:bold; border: none;")
        tela.alerta.setText("TEMPERATURA MEDIA - FIQUE ATENTO")
        tela.alerta.setStyleSheet("color:white; font-size:20px; border: none;")
    else:
        tela.status_processo.setText("ALTA TEMPERATURA")
        tela.status_processo.setStyleSheet("color:red; font-size:36px; font-weight:bold; border: none;")
        tela.alerta.setText("FORNO MUITO QUENTE!")
        tela.alerta.setStyleSheet("color:white; font-size:20px; border: none;")

# ============================================================
# INÍCIO DO PROGRAMA
# ============================================================
def iniciar_sistema():
    global tela
    app = QApplication(sys.argv)
    tela = InterfaceSupervisorio(TEMP_1, TEMP_2)
    
    thread = threading.Thread(target=serial_thread)
    thread.daemon = True
    thread.start()
    
    timer = QTimer()
    timer.timeout.connect(atualizar_interface)
    timer.start(250) 
    
    tela.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    iniciar_sistema()