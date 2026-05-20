# ============================================================
# ARQUIVO: interface.py
# OBJETIVO: Apenas desenhar a tela (FrontEnd). Nenhuma lógica aqui!
# ============================================================

from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QGridLayout, QFrame, QPushButton
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import pyqtgraph as pg

# ------------------------------------------------------------
# COMPONENTE REUTILIZÁVEL: O "Card"
# ------------------------------------------------------------
# Criamos uma classe Card para não ter que repetir o código da
# bordinha cinza e fundo escuro para cada quadro da tela.
class Card(QFrame):
    def __init__(self, titulo):
        super().__init__()
        
        # CSS do PyQt: Define a cor de fundo, borda e cantos arredondados
        self.setStyleSheet("""
            QFrame{
                background-color:#111111;
                border:1px solid #222;
                border-radius:12px;
            }
        """)
        
        # Layout Vertical: O título vai ficar em cima, e o conteúdo que 
        # adicionarmos depois vai ficar embaixo dele.
        layout = QVBoxLayout()
        
        self.titulo = QLabel(titulo)
        self.titulo.setStyleSheet("""
            color:#00ff66;
            font-size:18px; 
            font-weight:bold;
            border: none;
        """)
        
        layout.addWidget(self.titulo)
        self.setLayout(layout) # Aplica a "caixa vertical" dentro deste Card

# ------------------------------------------------------------
# JANELA PRINCIPAL
# ------------------------------------------------------------
class InterfaceSupervisorio(QWidget):
    def __init__(self, temp_min, temp_max):
        super().__init__()

        # Configurações básicas da janela (título, tamanho e cor de fundo geral)
        self.setWindowTitle("SUPERVISÓRIO USF")
        self.setGeometry(100, 100, 1600, 900)
        self.setStyleSheet("background-color:#050505; color:white;")

        # === LAYOUT PRINCIPAL (VERTICAL) ===
        # Tudo na nossa janela será empilhado verticalmente: 
        # 1. O Cabeçalho (Topo)
        # 2. O Grid com os Cards (Meio)
        self.layout_principal = QVBoxLayout()

        self.criar_cabecalho()
        self.criar_grid_de_cards(temp_min, temp_max)

        # Aplica o layout principal na janela
        self.setLayout(self.layout_principal)

    def criar_cabecalho(self):
        # === LAYOUT DO TOPO (HORIZONTAL) ===
        # Coloca o Título na esquerda e o Status na direita
        topo_layout = QHBoxLayout()

        # Caixa vertical apenas para empilhar o Título e o Subtítulo
        titulos_layout = QVBoxLayout()
        titulo = QLabel("MONITORAMENTO TÉRMICO DE PROCESSOS")
        titulo.setFont(QFont("Arial", 26, QFont.Bold))
        
        subtitulo = QLabel("Monitoramento de Temperatura de Forno")
        subtitulo.setStyleSheet("color:#00ff66; font-size:18px;")
        
        titulos_layout.addWidget(titulo)
        titulos_layout.addWidget(subtitulo)

        # Adiciona os títulos no layout do topo
        topo_layout.addLayout(titulos_layout)
        
        # addStretch cria um "espaço vazio expansível" que empurra 
        # o que vem depois dele lá para o canto direito da tela.
        topo_layout.addStretch()

        # Status Online/Offline
        self.label_status = QLabel("● INICIANDO...")
        self.label_status.setStyleSheet("color:gray; font-size:20px; font-weight:bold;")
        topo_layout.addWidget(self.label_status)

        # Adiciona o topo pronto ao layout principal da janela
        self.layout_principal.addLayout(topo_layout)

    def criar_grid_de_cards(self, temp_min, temp_max):
        # === LAYOUT GRID (TABELA) ===
        # Permite posicionar itens passando (Linha, Coluna)
        grid = QGridLayout()

        # 1. CARD: TEMPERATURA ATUAL (Linha 0, Coluna 0)
        card_temp = Card("TEMPERATURA ATUAL")
        self.temp_label = QLabel("0.0 °C")
        self.temp_label.setAlignment(Qt.AlignCenter)
        self.temp_label.setStyleSheet("color:white; font-size:48px; font-weight:bold; border: none;")
        card_temp.layout().addWidget(self.temp_label)
        grid.addWidget(card_temp, 0, 0)

        # 2. CARD: STATUS DO PROCESSO (Linha 1, Coluna 0)
        card_status = Card("STATUS DO PROCESSO")
        self.status_processo = QLabel("AGUARDANDO")
        self.status_processo.setAlignment(Qt.AlignCenter)
        self.status_processo.setStyleSheet("color:gray; font-size:36px; font-weight:bold; border: none;")
        card_status.layout().addWidget(self.status_processo)
        grid.addWidget(card_status, 1, 0)

        # 3. CARD: ALERTAS (Linha 2, Coluna 0)
        card_alerta = Card("ALERTAS")
        self.alerta = QLabel("Verificando...")
        self.alerta.setAlignment(Qt.AlignCenter)
        self.alerta.setStyleSheet("color:white; font-size:20px; border: none;")
        card_alerta.layout().addWidget(self.alerta)
        grid.addWidget(card_alerta, 2, 0)

        # 4. CARD: GRÁFICO (Linha 0, Coluna 1)
        # O pulo do gato aqui: O gráfico vai ocupar 3 linhas e 2 colunas de espaço!
        # grid.addWidget(widget, linha, coluna, quantidade_linhas_ocupadas, quantidade_colunas_ocupadas)
        card_grafico = Card("HISTÓRICO DE TEMPERATURA")
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("#111111")
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setLabel('left', 'Temperatura (°C)')
        self.plot_widget.setLabel('bottom', 'Tempo')
        self.plot_widget.setYRange(0, 150)
        self.curve = self.plot_widget.plot(pen=pg.mkPen("#00ff66", width=3))
        card_grafico.layout().addWidget(self.plot_widget)
        
        grid.addWidget(card_grafico, 0, 1, 3, 2) # Ocupa 3 linhas e 2 colunas

        # 5. CARD: DADOS DO SENSOR (Linha 3, Coluna 0)
        card_sensor = Card("DADOS DO SENSOR")
        self.sensor_info = QLabel("Sensor: LM35\nResolução ADC: 10 bits\nComunicação: Serial\nFiltro: RC Passa-Baixa")
        self.sensor_info.setStyleSheet("font-size:18px; color:white; border: none;")
        card_sensor.layout().addWidget(self.sensor_info)
        grid.addWidget(card_sensor, 3, 0)

        # 6. CARD: CONTROLE PWM (Linha 3, Coluna 1)
        card_pwm = Card("CONTROLE DE POTÊNCIA (PWM)")
        self.label_pwm = QLabel("Valor PWM: 0")
        self.label_pwm.setAlignment(Qt.AlignCenter)
        self.label_pwm.setStyleSheet("color: white; font-size: 26px; font-weight: bold; border: none;")
        
        # Aqui usamos um layout horizontal apenas para os dois botões ficarem lado a lado
        botoes_layout = QHBoxLayout()
        
        self.btn_diminuir = QPushButton("-20")
        self.btn_diminuir.setStyleSheet("QPushButton { background-color: #aa0000; color: white; font-size: 24px; font-weight: bold; border-radius: 6px; padding: 10px; } QPushButton:hover { background-color: #ff3333; }")
        
        self.btn_aumentar = QPushButton("+20")
        self.btn_aumentar.setStyleSheet("QPushButton { background-color: #00aa00; color: white; font-size: 24px; font-weight: bold; border-radius: 6px; padding: 10px; } QPushButton:hover { background-color: #33ff33; color: black; }")
        
        botoes_layout.addWidget(self.btn_diminuir)
        botoes_layout.addWidget(self.btn_aumentar)
        
        card_pwm.layout().addWidget(self.label_pwm)
        card_pwm.layout().addLayout(botoes_layout)
        grid.addWidget(card_pwm, 3, 1)

        # 7. CARD: CONFIGURAÇÕES (Linha 3, Coluna 2)
        card_config = Card("CONFIGURAÇÕES")
        self.config_info = QLabel(f"Limite Superior: {temp_max} °C\nLimite Inferior: {temp_min} °C\nIntervalo de leitura: 1000 ms")
        self.config_info.setStyleSheet("font-size:18px; color:white; border: none;")
        card_config.layout().addWidget(self.config_info)
        grid.addWidget(card_config, 3, 2)

        # Adiciona o grid completo no layout principal
        self.layout_principal.addLayout(grid)