from PyQt5.QtWidgets import QMainWindow, QHBoxLayout
from PyQt5 import uic
from PyQt5.QtCore import QTimer
import pyqtgraph as pg
import os

class MainWindow(QMainWindow):
    def __init__(self, resist=None):
        super().__init__()

        base_dir = os.path.dirname(os.path.abspath(__file__))
        ui_file = os.path.join(base_dir, 'GUI', 'mainwindow.ui')
        uic.loadUi(ui_file, self)

        self.resist = resist

        self.plot_widget = pg.PlotWidget(title="Temperature Log")
        self.plot = self.plot_widget.plot([0], [0])
        self.plot_widget.setLabel('bottom','time', units = "s")
        self.plot_widget.setLabel('left','Temperature', units = "K")
        layout = self.graph_box.layout()
        layout.addWidget(self.plot_widget)

        self.plot2_widget = pg.PlotWidget(title="Data Log")
        self.plot2 = self.plot2_widget.plot([0], [0])
        self.plot2_widget.setLabel('bottom','time', units = "s")
        self.plot2_widget.setLabel('left','Voltage', units = "V")
        layout.addWidget(self.plot2_widget)

        # self.start_line.setText(str(self.experiment.config['Scan']['start']))
        # self.stop_line.setText(str(self.experiment.config['Scan']['stop']))
        # self.num_steps_line.setText(str(self.experiment.config['Scan']['num_steps']))

        self.start_log_button.clicked.connect(self.start_log_button_clicked)
        self.stop_log_button.clicked.connect(self.stop_log_button_clicked)
        self.clear_log_button.clicked.connect(self.clear_log_button_clicked)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(1000)

    def start_log_button_clicked(self):
        self.resist.start_logging()
        print('Log Started')

    def stop_log_button_clicked(self):
        self.resist.stop_logging()
        print('Log Stopped')

    def clear_log_button_clicked(self):
        self.resist.clear_log()
        print('Log Cleared')

    def update_plot(self):
        self.plot.setData(self.resist.exptime, self.resist.temperature_log)
        self.plot2.setData(self.resist.exptime, self.resist.data_log)
    

