# ============================================================
# ARQUIVO: main.py
# OBJETIVO: Lógica do sistema, Porta Serial e Controle da Tela
# ============================================================

import sys
import serial
import threading
import time
from collections import deque
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# Importamos a tela que criamos no outro arquivo
from interface import InterfaceSupervisorio

# ============================================================
# CONFIGURAÇÕES DA REGRA DE NEGÓCIO
# ============================================================
SERIAL_PORT = "COM9"      # ALTERAR PARA SUA PORTA
BAUD_RATE = 9600
TEMP_MIN = 10
TEMP_MAX = 100

class LogicSupervisorio:
    def __init__(self):
        # 1. Cria a tela, passando as configurações de temperatura
        self.tela = InterfaceSupervisorio(TEMP_MIN, TEMP_MAX)
        
        # 2. Variáveis de controle
        self.temperatura_atual = 0.0
        self.historico_temperatura = deque(maxlen=100)
        self.status_serial = False
        self.arduino = None
        self.pwm_atual = 0

        # 3. Conectando os botões da tela com as funções daqui
        self.tela.btn_aumentar.clicked.connect(self.aumentar_pwm)
        self.tela.btn_diminuir.clicked.connect(self.diminuir_pwm)

        # 4. Inicia a Thread que fica lendo o Arduino em segundo plano
        self.thread = threading.Thread(target=self.serial_thread)
        self.thread.daemon = True
        self.thread.start()

        # 5. Timer para atualizar o visual da tela a cada 1 segundo (1000 ms)
        self.timer = QTimer()
        self.timer.timeout.connect(self.atualizar_interface)
        self.timer.start(1000)

    def iniciar(self):
        self.tela.show()

    # ========================================================
    # FUNÇÕES DE PWM
    # ========================================================
    def aumentar_pwm(self):
        self.pwm_atual += 20
        if self.pwm_atual > 255:
            self.pwm_atual = 255
        self.enviar_pwm_serial()

    def diminuir_pwm(self):
        self.pwm_atual -= 20
        if self.pwm_atual < 0:
            self.pwm_atual = 0
        self.enviar_pwm_serial()

    def enviar_pwm_serial(self):
        # Atualiza a interface
        self.tela.label_pwm.setText(f"Valor PWM: {self.pwm_atual}")
        
        # Envia para o Arduino
        if self.status_serial and self.arduino and self.arduino.is_open:
            try:
                comando = f"{self.pwm_atual}\n"
                self.arduino.write(comando.encode('utf-8'))
            except Exception as e:
                print(f"Erro ao enviar comando PWM: {e}")

    # ========================================================
    # THREAD DA PORTA SERIAL (Roda em paralelo)
    # ========================================================
    def serial_thread(self):
        while True:
            try:
                if self.arduino is None or not self.arduino.is_open:
                    self.arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
                    time.sleep(2)
                    self.status_serial = True

                if self.arduino.in_waiting:
                    linha = self.arduino.readline().decode().strip()
                    try:
                        self.temperatura_atual = float(linha)
                        self.historico_temperatura.append(self.temperatura_atual)
                    except ValueError:
                        pass

            except Exception:
                self.status_serial = False
                self.arduino = None
                time.sleep(2) # Evita travamento tentando reconectar muito rápido

    # ========================================================
    # ATUALIZAÇÃO VISUAL (Chamado pelo Timer)
    # ========================================================
    def atualizar_interface(self):
        # 1. Atualiza valor da temperatura
        self.tela.temp_label.setText(f"{self.temperatura_atual:.1f} °C")
        
        # 2. Atualiza o Gráfico
        self.tela.curve.setData(list(self.historico_temperatura))

        # 3. Verifica Status da Conexão
        if self.status_serial:
            self.tela.label_status.setText("● ONLINE")
            self.tela.label_status.setStyleSheet("color:#00ff66; font-size:20px; font-weight:bold;")
        else:
            self.tela.label_status.setText("● OFFLINE")
            self.tela.label_status.setStyleSheet("color:red; font-size:20px; font-weight:bold;")

        # 4. Verifica Regras de Alarme
        if self.temperatura_atual >= TEMP_MAX:
            self.tela.status_processo.setText("ALTA TEMPERATURA")
            self.tela.status_processo.setStyleSheet("color:red; font-size:36px; font-weight:bold; border: none;")
            self.tela.alerta.setText("⚠ TEMPERATURA ACIMA DO LIMITE")
            
        elif self.temperatura_atual <= TEMP_MIN:
            self.tela.status_processo.setText("BAIXA TEMPERATURA")
            self.tela.status_processo.setStyleSheet("color:yellow; font-size:36px; font-weight:bold; border: none;")
            self.tela.alerta.setText("⚠ TEMPERATURA ABAIXO DO LIMITE")
            
        else:
            self.tela.status_processo.setText("NORMAL")
            self.tela.status_processo.setStyleSheet("color:#00ff66; font-size:36px; font-weight:bold; border: none;")
            self.tela.alerta.setText("Nenhum alerta")

# ============================================================
# INÍCIO DO PROGRAMA
# ============================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Instancia a nossa lógica (que por sua vez instancia a tela)
    programa = LogicSupervisorio()
    programa.iniciar()
    
    sys.exit(app.exec_())