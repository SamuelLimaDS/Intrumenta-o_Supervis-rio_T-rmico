# ============================================================
# ARQUIVO: interface.py
# OBJETIVO: Apenas desenhar a tela (FrontEnd). Nenhuma lógica aqui!
# ============================================================
from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QGridLayout, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap
import pyqtgraph as pg

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

class InterfaceSupervisorio(QWidget):
    def __init__(self, temp_min, temp_max):
        super().__init__()
        self.setWindowTitle("SUPERVISÓRIO USF - DUAL SENSOR")
        self.setGeometry(100, 100, 1600, 900)
        self.setStyleSheet("background-color:#050505; color:white;")

        self.layout_principal = QVBoxLayout()
        self.criar_cabecalho()
        self.criar_grid_de_cards(temp_min, temp_max)
        self.setLayout(self.layout_principal)

    def criar_cabecalho(self):
        topo_layout = QHBoxLayout()
        titulos_layout = QVBoxLayout()
        linha_titulo_layout = QHBoxLayout()
        linha_titulo_layout.setAlignment(Qt.AlignVertical_Mask)

        titulo = QLabel("MONITORAMENTO TÉRMICO DO FORNO")
        titulo.setFont(QFont("Arial", 26, QFont.Bold))
        linha_titulo_layout.addWidget(titulo)
        
        self.label_logo = QLabel()
        self.label_logo.setStyleSheet("background-color: transparent; margin-left: 20px;")
        pixmap = QPixmap("logo_usf.png")
        
        if not pixmap.isNull():
            pixmap_redimensionado = pixmap.scaledToHeight(100, Qt.SmoothTransformation)
            self.label_logo.setPixmap(pixmap_redimensionado)
            self.label_logo.setStyleSheet("margin-left: 50px;")
        else:
            self.label_logo.setText("[ USF ]")
            self.label_logo.setStyleSheet("color: #00ff66; font-weight: bold; font-size: 26px; margin-left: 20px;")
            
        linha_titulo_layout.addWidget(self.label_logo)
        linha_titulo_layout.addStretch()
        titulos_layout.addLayout(linha_titulo_layout)
        
        subtitulo = QLabel("Samuel, Murilo, Leonardo, Stephanie, Thiago, Filipe, Gabriel, Everton")
        subtitulo.setStyleSheet("color:#00ff66; font-size:18px; margin-top: 1px;")
        titulos_layout.addWidget(subtitulo)
        
        topo_layout.addLayout(titulos_layout)
        topo_layout.addStretch()

        self.label_status = QLabel("● INICIANDO...")
        self.label_status.setStyleSheet("color:gray; font-size:20px; font-weight:bold;")
        topo_layout.addWidget(self.label_status)

        self.layout_principal.addLayout(topo_layout)

    def criar_grid_de_cards(self, temp_min, temp_max):
        grid = QGridLayout()

        # 1. CARD: TEMPERATURAS ATUAIS (Modificado para exibir ambos os sensores)
        card_temp = Card("TEMPERATURAS ATUAIS")
        self.temp_ntc_label = QLabel("NTC: 0.0 °C")
        self.temp_ntc_label.setStyleSheet("color:#00ff66; font-size:28px; font-weight:bold; border: none;")
        self.temp_lm35_label = QLabel("LM35: 0.0 °C")
        self.temp_lm35_label.setStyleSheet("color:#00bfff; font-size:28px; font-weight:bold; border: none;")
        card_temp.layout().addWidget(self.temp_ntc_label)
        card_temp.layout().addWidget(self.temp_lm35_label)
        grid.addWidget(card_temp, 0, 0)

        # 2. CARD: STATUS
        card_status = Card("STATUS DO PROCESSO")
        self.status_processo = QLabel("AGUARDANDO")
        self.status_processo.setAlignment(Qt.AlignCenter)
        self.status_processo.setStyleSheet("color:gray; font-size:36px; font-weight:bold; border: none;")
        card_status.layout().addWidget(self.status_processo)
        grid.addWidget(card_status, 1, 0)

        # 3. CARD: ALERTAS
        card_alerta = Card("ALERTAS")
        self.alerta = QLabel("Verificando...")
        self.alerta.setAlignment(Qt.AlignCenter)
        self.alerta.setStyleSheet("color:white; font-size:20px; border: none;")
        card_alerta.layout().addWidget(self.alerta)
        grid.addWidget(card_alerta, 2, 0)

        # 4. CARD: GRÁFICO (Modificado para duas curvas com legenda)
        card_grafico = Card("HISTÓRICO COMPARATIVO DE TEMPERATURA")
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("#111111")
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setLabel('left', 'Temperatura (°C)')
        self.plot_widget.setLabel('bottom', 'Amostras')
        self.plot_widget.setYRange(0, 100)
        self.plot_widget.addLegend()
        
        # Linha Verde para o NTC, Linha Ciano/Azul claro para o LM35
        self.curve_ntc = self.plot_widget.plot(name="NTC 10K", pen=pg.mkPen("#00ff66", width=3))
        self.curve_lm35 = self.plot_widget.plot(name="LM35", pen=pg.mkPen("#00bfff", width=3))
        
        card_grafico.layout().addWidget(self.plot_widget)
        grid.addWidget(card_grafico, 0, 1, 3, 2)

        # 5. CARD: DADOS DO SENSOR (Modificado para exibir dois ADCs)
        card_sensor = Card("SINAIS DE CAMPO (ADC)")
        self.label_adc_ntc = QLabel("ADC NTC 10K: 0")
        self.label_adc_ntc.setStyleSheet("font-size:18px; color:#00ff66; font-weight:bold; border: none;")
        
        self.label_adc_lm35 = QLabel("ADC LM35: 0")
        self.label_adc_lm35.setStyleSheet("font-size:18px; color:#00bfff; font-weight:bold; border: none; margin-top: 5px;")
        
        card_sensor.layout().addWidget(self.label_adc_ntc)
        card_sensor.layout().addWidget(self.label_adc_lm35)
        grid.addWidget(card_sensor, 3, 0)

        # 6. CARD: PWM
        card_pwm = Card("CONTROLE DE POTÊNCIA (PWM)")
        self.label_pwm = QLabel("Valor PWM: 0")
        self.label_pwm.setAlignment(Qt.AlignCenter)
        self.label_pwm.setStyleSheet("color: white; font-size: 26px; font-weight: bold; border: none;")
        card_pwm.layout().addWidget(self.label_pwm)
        grid.addWidget(card_pwm, 3, 1)

        # 7. CARD: CONFIGURAÇÕES
        card_config = Card("CONFIGURAÇÕES")
        self.config_info = QLabel(f"Limite Superior: {temp_max} °C\nLimite Inferior: {temp_min} °C\nIntervalo: 1000 ms")
        self.config_info.setStyleSheet("font-size:18px; color:white; border: none;")
        card_config.layout().addWidget(self.config_info)
        grid.addWidget(card_config, 3, 2)

        self.layout_principal.addLayout(grid)