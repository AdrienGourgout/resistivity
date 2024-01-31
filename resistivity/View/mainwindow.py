from PyQt5.QtWidgets import QMainWindow, QHBoxLayout, QWidget
from PyQt5 import uic, QtWidgets
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
        self.start_ramp_button.clicked.connect(self.start_ramp_button_clicked)
        self.save_data_button.clicked.connect(self.save_data_button_clicked)
        self.open_log_window_button.clicked.connect(self.open_log_window_button_clicked)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(1000)
        self.window_log_list = []

    def open_log_window_button_clicked(self):
        self.window_log_list.append(Logwindow())
        self.window_log_list[-1].show()


    def start_log_button_clicked(self):
        self.resist.start_logging()
        print('Log Started')

    def stop_log_button_clicked(self):
        self.resist.stop_logging()
        print('Log Stopped')

    def clear_log_button_clicked(self):
        self.resist.clear_log()
        print('Log Cleared')

    def start_ramp_button_clicked(self):
        print('Ramp Started')
        self.resist.start_ramp()

    def save_data_button_clicked(self):
        print('Starting to save data')
        self.resist.start_saving_log()


    def update_plot(self):
        self.plot.setData(self.resist.exptime, self.resist.temperature_log)
        self.plot2.setData(self.resist.exptime, self.resist.data_log)


class Logwindow(QWidget):
    def __init__(self, resist=None):
        super().__init__()

        base_dir = os.path.dirname(os.path.abspath(__file__))
        ui_file = os.path.join(base_dir, 'GUI', 'log_window.ui')
        uic.loadUi(ui_file, self)

        self.resist = resist

        # Device definition:
        layout = self.device_menu.layout()

        # Add button
        self.add_button = QtWidgets.QPushButton("Add Device")
        self.add_button.clicked.connect(self.add_new_row)
        layout.addWidget(self.add_button)

        # Delete row button
        self.delete_button = QtWidgets.QPushButton("Delete Device")
        self.delete_button.clicked.connect(self.delete_last_row)
        layout.addWidget(self.delete_button)

        # Table Widget
        self.table_widget = QtWidgets.QTableWidget()
        self.table_widget.setColumnCount(2)  # Two columns for button and dropdown
        self.table_widget.setHorizontalHeaderLabels(["Button", "Dropdown"])
        layout.addWidget(self.table_widget)

    def add_new_row(self):
        # Add a row
        row_position = self.table_widget.rowCount()
        self.table_widget.insertRow(row_position)
        
        # Add a button
        button = QtWidgets.QPushButton("Button")
        self.table_widget.setCellWidget(row_position, 0, button)

        # Add a dropdown menu
        combo_box = QtWidgets.QComboBox()
        combo_box.addItems(["Option 1", "Option 2", "Option 3"])  # Add your items
        self.table_widget.setCellWidget(row_position, 1, combo_box)

    def delete_last_row(self):
        # Delete the last row
        row_position = self.table_widget.rowCount()
        self.table_widget.removeRow(row_position - 1)