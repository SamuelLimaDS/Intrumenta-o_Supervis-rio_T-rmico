# ============================================================
# SUPERVISÓRIO - MONITORAMENTO TÉRMICO DE PROCESSOS
# Universidade São Francisco - USF
#
# Requisitos:
# pip install pyqt5 pyqtgraph pyserial
#
# Execute:
# python supervisório.py
#
# ============================================================

import sys
import serial
import threading
import time
from collections import deque

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QFrame,
    QPushButton, # <-- Adicionado para criar os botões
)

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

import pyqtgraph as pg


# ============================================================
# CONFIGURAÇÕES
# ============================================================

SERIAL_PORT = "COM9"      # ALTERAR PARA SUA PORTA
BAUD_RATE = 9600

TEMP_MIN = 10
TEMP_MAX = 100

# ============================================================
# VARIÁVEIS GLOBAIS
# ============================================================

temperatura_atual = 0
historico_temperatura = deque(maxlen=100)

status_serial = False
arduino = None  # Variável global para permitir o envio de dados pela interface
pwm_atual = 0   # Variável global para armazenar o valor do PWM (0 a 255)


# ============================================================
# LEITURA SERIAL E CONEXÃO
# ============================================================

def serial_thread():
    global temperatura_atual
    global status_serial
    global arduino

    while True: # Mantém a thread rodando para tentar reconectar se cair
        try:
            if arduino is None or not arduino.is_open:
                arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
                time.sleep(2)
                status_serial = True

            if arduino.in_waiting:
                linha = arduino.readline().decode().strip()
                try:
                    temperatura = float(linha)
                    temperatura_atual = temperatura
                    historico_temperatura.append(temperatura)
                except ValueError:
                    pass

        except Exception:
            status_serial = False
            arduino = None
            time.sleep(2) # Aguarda antes de tentar reconectar para não sobrecarregar a CPU


# ============================================================
# CARD ESTILO INDUSTRIAL
# ============================================================

class Card(QFrame):

    def __init__(self, titulo):

        super().__init__()

        self.setStyleSheet("""
            QFrame{
                background-color:#111111;
                border:1px solid #222;
                border-radius:12px;
            }
        """)

        layout = QVBoxLayout()

        self.titulo = QLabel(titulo)
        self.titulo.setStyleSheet("""
            color:#00ff66;
            font-size:18px;
            font-weight:bold;
            border: none;
        """)

        layout.addWidget(self.titulo)
        self.setLayout(layout)


# ============================================================
# JANELA PRINCIPAL
# ============================================================

class Supervisorio(QWidget):

    def __init__(self):

        super().__init__()

        self.setWindowTitle("SUPERVISÓRIO USF")
        self.setGeometry(100, 100, 1600, 900)

        self.setStyleSheet("""
            background-color:#050505;
            color:white;
        """)

        self.init_ui()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(1000)

    # ========================================================

    def init_ui(self):

        layout_principal = QVBoxLayout()

        # ====================================================
        # TOPO
        # ====================================================

        topo = QHBoxLayout()

        titulo = QLabel("MONITORAMENTO TÉRMICO DE PROCESSOS")
        titulo.setFont(QFont("Arial", 26, QFont.Bold))
        titulo.setStyleSheet("color:white;")

        subtitulo = QLabel("Monitoramento de Temperatura de Forno")
        subtitulo.setStyleSheet("""
            color:#00ff66;
            font-size:18px;
        """)

        titulo_layout = QVBoxLayout()
        titulo_layout.addWidget(titulo)
        titulo_layout.addWidget(subtitulo)

        topo.addLayout(titulo_layout)
        topo.addStretch()

        self.label_status = QLabel("● ONLINE")
        self.label_status.setStyleSheet("""
            color:#00ff66;
            font-size:20px;
            font-weight:bold;
        """)

        topo.addWidget(self.label_status)
        layout_principal.addLayout(topo)

        # ====================================================
        # GRID PRINCIPAL
        # ====================================================

        grid = QGridLayout()

        # ====================================================
        # TEMPERATURA ATUAL
        # ====================================================

        card_temp = Card("TEMPERATURA ATUAL")

        self.temp_label = QLabel("0.0 °C")
        self.temp_label.setAlignment(Qt.AlignCenter)

        self.temp_label.setStyleSheet("""
            color:white;
            font-size:48px;
            font-weight:bold;
            border: none;
        """)

        card_temp.layout().addWidget(self.temp_label)
        grid.addWidget(card_temp, 0, 0)

        # ====================================================
        # STATUS PROCESSO
        # ====================================================

        card_status = Card("STATUS DO PROCESSO")

        self.status_processo = QLabel("NORMAL")
        self.status_processo.setAlignment(Qt.AlignCenter)

        self.status_processo.setStyleSheet("""
            color:#00ff66;
            font-size:36px;
            font-weight:bold;
            border: none;
        """)

        card_status.layout().addWidget(self.status_processo)
        grid.addWidget(card_status, 1, 0)

        # ====================================================
        # ALERTAS
        # ====================================================

        card_alerta = Card("ALERTAS")

        self.alerta = QLabel("Nenhum alerta")
        self.alerta.setAlignment(Qt.AlignCenter)

        self.alerta.setStyleSheet("""
            color:white;
            font-size:20px;
            border: none;
        """)

        card_alerta.layout().addWidget(self.alerta)
        grid.addWidget(card_alerta, 2, 0)

        # ====================================================
        # GRÁFICO
        # ====================================================

        card_grafico = Card("HISTÓRICO DE TEMPERATURA")

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("#111111")
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setLabel('left', 'Temperatura (°C)')
        self.plot_widget.setLabel('bottom', 'Tempo')
        self.plot_widget.setYRange(0, 150)

        self.curve = self.plot_widget.plot(
            pen=pg.mkPen("#00ff66", width=3)
        )

        card_grafico.layout().addWidget(self.plot_widget)
        grid.addWidget(card_grafico, 0, 1, 3, 2)

        # ====================================================
        # DADOS SENSOR
        # ====================================================

        card_sensor = Card("DADOS DO SENSOR")

        self.sensor_info = QLabel("""
Sensor: LM35
Resolução ADC: 10 bits
Comunicação: Serial
Filtro: RC Passa-Baixa
        """)

        self.sensor_info.setStyleSheet("""
            font-size:18px;
            color:white;
            border: none;
        """)

        card_sensor.layout().addWidget(self.sensor_info)
        grid.addWidget(card_sensor, 3, 0)

        # ====================================================
        # CONTROLE PWM (BOTÕES)
        # ====================================================

        card_pwm = Card("CONTROLE DE POTÊNCIA (PWM)")

        self.label_pwm = QLabel(f"Valor PWM: {pwm_atual}")
        self.label_pwm.setAlignment(Qt.AlignCenter)
        self.label_pwm.setStyleSheet("""
            color: white;
            font-size: 26px;
            font-weight: bold;
            border: none;
        """)

        botoes_layout = QHBoxLayout()

        self.btn_diminuir = QPushButton("-20")
        self.btn_diminuir.setStyleSheet("""
            QPushButton {
                background-color: #aa0000; color: white; font-size: 24px; font-weight: bold; border-radius: 6px; padding: 10px;
            }
            QPushButton:hover { background-color: #ff3333; }
        """)
        self.btn_diminuir.clicked.connect(self.diminuir_pwm)

        self.btn_aumentar = QPushButton("+20")
        self.btn_aumentar.setStyleSheet("""
            QPushButton {
                background-color: #00aa00; color: white; font-size: 24px; font-weight: bold; border-radius: 6px; padding: 10px;
            }
            QPushButton:hover { background-color: #33ff33; color: black; }
        """)
        self.btn_aumentar.clicked.connect(self.aumentar_pwm)

        botoes_layout.addWidget(self.btn_diminuir)
        botoes_layout.addWidget(self.btn_aumentar)

        card_pwm.layout().addWidget(self.label_pwm)
        card_pwm.layout().addLayout(botoes_layout)
        
        grid.addWidget(card_pwm, 3, 1)

        # ====================================================
        # CONFIGURAÇÕES
        # ====================================================

        card_config = Card("CONFIGURAÇÕES")

        self.config_info = QLabel(f"""
Limite Superior: {TEMP_MAX} °C
Limite Inferior: {TEMP_MIN} °C
Intervalo de leitura: 1000 ms
        """)

        self.config_info.setStyleSheet("""
            font-size:18px;
            color:white;
            border: none;
        """)

        card_config.layout().addWidget(self.config_info)
        grid.addWidget(card_config, 3, 2)

        layout_principal.addLayout(grid)
        self.setLayout(layout_principal)

    # ========================================================
    # FUNÇÕES DOS BOTÕES PWM
    # ========================================================

    def aumentar_pwm(self):
        global pwm_atual
        pwm_atual += 20
        if pwm_atual > 255:
            pwm_atual = 255
        self.atualizar_e_enviar_pwm()

    def diminuir_pwm(self):
        global pwm_atual
        pwm_atual -= 20
        if pwm_atual < 0:
            pwm_atual = 0
        self.atualizar_e_enviar_pwm()

    def atualizar_e_enviar_pwm(self):
        global arduino, status_serial
        
        # Atualiza a interface
        self.label_pwm.setText(f"Valor PWM: {pwm_atual}")
        
        # Envia para a porta serial (se conectada)
        if status_serial and arduino and arduino.is_open:
            try:
                # Envia o valor em formato texto seguido de uma quebra de linha (\n)
                # No Arduino, você pode ler usando: Serial.parseInt() ou leitura de String
                comando = f"{pwm_atual}\n"
                arduino.write(comando.encode('utf-8'))
            except Exception as e:
                print(f"Erro ao enviar comando PWM: {e}")

    # ========================================================

    def update_ui(self):

        global temperatura_atual
        global status_serial

        self.temp_label.setText(f"{temperatura_atual:.1f} °C")

        # ====================================================
        # STATUS SERIAL
        # ====================================================

        if status_serial:
            self.label_status.setText("● ONLINE")
            self.label_status.setStyleSheet("""
                color:#00ff66;
                font-size:20px;
                font-weight:bold;
            """)
        else:
            self.label_status.setText("● OFFLINE")
            self.label_status.setStyleSheet("""
                color:red;
                font-size:20px;
                font-weight:bold;
            """)
            # Nota: O travamento da interface foi resolvido ao remover 
            # o "while((serial.Serial..." daqui e passá-lo para a thread.

        # ====================================================
        # ALERTAS
        # ====================================================

        if temperatura_atual >= TEMP_MAX:
            self.status_processo.setText("ALTA TEMPERATURA")
            self.status_processo.setStyleSheet("""
                color:red;
                font-size:36px;
                font-weight:bold;
                border: none;
            """)
            self.alerta.setText("⚠ TEMPERATURA ACIMA DO LIMITE")

        elif temperatura_atual <= TEMP_MIN:
            self.status_processo.setText("BAIXA TEMPERATURA")
            self.status_processo.setStyleSheet("""
                color:yellow;
                font-size:36px;
                font-weight:bold;
                border: none;
            """)
            self.alerta.setText("⚠ TEMPERATURA ABAIXO DO LIMITE")

        else:
            self.status_processo.setText("NORMAL")
            self.status_processo.setStyleSheet("""
                color:#00ff66;
                font-size:36px;
                font-weight:bold;
                border: none;
            """)
            self.alerta.setText("Nenhum alerta")

        # ====================================================
        # UPDATE GRÁFICO
        # ====================================================
        self.curve.setData(list(historico_temperatura))


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    # Thread Serial
    thread = threading.Thread(target=serial_thread)
    thread.daemon = True
    thread.start()

    app = QApplication(sys.argv)

    window = Supervisorio()
    window.show()

    sys.exit(app.exec_())