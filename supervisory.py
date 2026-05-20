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
SERIAL_PORT = "COM9"      # ALTERAR PARA SUA PORTA
BAUD_RATE = 9600
TEMP_3 = 15
TEMP_1 = 25
TEMP_2 = 30

temperatura_atual = 0.0
adc_atual = 0
pwm_atual = 0
emergencia_ativa = False # Nova variável para monitorar o botão físico
historico_temperatura = deque(maxlen=100)
status_serial = False
arduino = None
tela = None

# ============================================================
# FUNÇÃO DA PORTA SERIAL (Roda em paralelo)
# ============================================================
def serial_thread():
    global arduino, status_serial, temperatura_atual, adc_atual, pwm_atual, emergencia_ativa, historico_temperatura
    
    while True:
        try:
            if arduino is None or not arduino.is_open:
                arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
                time.sleep(2)
                status_serial = True

            if arduino.in_waiting:
                linha = arduino.readline().decode().strip()
                
                # Agora espera 4 partes: Temperatura, ADC, PWM, Emergencia
                partes = linha.split(',')
                if len(partes) == 4:
                    try:
                        temperatura_atual = float(partes[0])
                        adc_atual = int(partes[1])
                        pwm_atual = int(partes[2])
                        # Se for 1, vira True. Se for 0, vira False.
                        emergencia_ativa = (int(partes[3]) == 1) 
                        
                        historico_temperatura.append(temperatura_atual)
                    except ValueError:
                        pass 

        except Exception:
            status_serial = False
            arduino = None
            time.sleep(2) 

# ============================================================
# FUNÇÃO DE ATUALIZAÇÃO VISUAL (Chamada a cada 250 ms)
# ============================================================
def atualizar_interface():
    global temperatura_atual, adc_atual, pwm_atual, emergencia_ativa, status_serial, historico_temperatura, tela
    
    # 1. Atualiza Leituras Diretas
    tela.temp_label.setText(f"{temperatura_atual:.1f} °C")
    tela.label_adc.setText(f"Valor AD: {adc_atual}")
    tela.label_pwm.setText(f"Valor PWM: {pwm_atual}")
    
    # 2. Atualiza o Gráfico
    tela.curve.setData(list(historico_temperatura))

    # 3. Verifica Status da Conexão Serial
    if status_serial:
        tela.label_status.setText("● ONLINE")
        tela.label_status.setStyleSheet("color:#00ff66; font-size:20px; font-weight:bold;")
    else:
        tela.label_status.setText("● OFFLINE")
        tela.label_status.setStyleSheet("color:red; font-size:20px; font-weight:bold;")

    # 4. Verifica Regras de Alarme (Modo Emergência tem prioridade máxima)
    if emergencia_ativa:
        tela.status_processo.setText("EMERGÊNCIA ATIVA")
        tela.status_processo.setStyleSheet("color:red; font-size:36px; font-weight:bold; border: none;")
        tela.alerta.setText("SISTEMA BLOQUEADO PELO BOTÃO FÍSICO!")
        tela.alerta.setStyleSheet("color:#ff3333; font-size:20px; font-weight:bold; border: none;")
    
    # Se não estiver em emergência, segue as regras de temperatura normais
    elif temperatura_atual <= TEMP_3:
        tela.status_processo.setText("TEMPERATURA BAIXA")
        tela.status_processo.setStyleSheet("color:blue; font-size:36px; font-weight:bold; border: none;")
        tela.alerta.setText("SENSOR DESLIGADO OU AMBIENTE FRIO")
        tela.alerta.setStyleSheet("color:white; font-size:20px; border: none;")
    elif temperatura_atual <= TEMP_1:
        tela.status_processo.setText("TEMPERATURA MEDIA")
        tela.status_processo.setStyleSheet("color:yellow; font-size:36px; font-weight:bold; border: none;")
        tela.alerta.setText("FORNO ESQUENTANDO")
        tela.alerta.setStyleSheet("color:white; font-size:20px; border: none;")
    elif TEMP_3 < temperatura_atual <= TEMP_1:
        tela.status_processo.setText("TEMPERATURA NORMAL")
        tela.status_processo.setStyleSheet("color:#00ff66; font-size:36px; font-weight:bold; border: none;")
        tela.alerta.setText("TEMPERATURA AMBIENTE")
        tela.alerta.setStyleSheet("color:white; font-size:20px; border: none;")
    elif TEMP_1 < temperatura_atual <= TEMP_2:
        tela.status_processo.setText("TEMPERATURA MEDIA")
        tela.status_processo.setStyleSheet("color:yellow; font-size:36px; font-weight:bold; border: none;")
        tela.alerta.setText("FORNO ESQUENTANDO")
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