from PyQt5.QtWidgets import QMainWindow, QWidget, QListWidget, QListWidgetItem
from PyQt5 import uic, QtWidgets
from PyQt5.QtCore import QTimer, Qt
import pyqtgraph as pg
import os


class MainWindow(QMainWindow):
    def __init__(self, resist=None):
        super().__init__()

        base_dir = os.path.dirname(os.path.abspath(__file__))
        ui_file = os.path.join(base_dir, 'GUI', 'mainwindow.ui')
        uic.loadUi(ui_file, self)

        self.resist = resist
        self.device_menu_window = None
        self.window_datalog_files = None
        self.ramp_parameters_window = None

        # self.start_line.setText(str(self.experiment.config['Scan']['start']))
        # self.stop_line.setText(str(self.experiment.config['Scan']['stop']))
        # self.num_steps_line.setText(str(self.experiment.config['Scan']['num_steps']))

        self.start_log_button.clicked.connect(self.start_log_button_clicked)
        self.stop_log_button.clicked.connect(self.stop_log_button_clicked)
        self.start_ramp_button.clicked.connect(self.start_ramp_button_clicked)
        self.open_graph_display_button.clicked.connect(self.open_graph_display_button_clicked)
        
        self.save_log_data_checkbox.stateChanged.connect(self.save_log_data_checkbox_changed)

        # Experiment Setup buttons:
        self.open_devices_menu_button.clicked.connect(self.open_devices_menu_button_clicked)
        self.datalog_files_button.clicked.connect(self.open_datalog_files_button_clicked)

        # Ramp buttons:
        self.open_ramp_parameters_menu.clicked.connect(self.open_ramp_parameters_menu_button_clicked)

        self.window_log_list = []

    def open_ramp_parameters_menu_button_clicked(self):
        if self.ramp_parameters_window == None:
            self.ramp_parameters_window = RampParam(self.resist)
        self.ramp_parameters_window.show()

    def start_ramp_button_clicked(self):
        for start, stop, speed in zip(self.resist.ramp_parameters[0], self.resist.ramp_parameters[1], self.resist.ramp_parameters[2]):
            self.resist.config['Ramp']['ramp_start_T'] = start
            self.resist.config['Ramp']['ramp_end_T'] = stop
            self.resist.config['Ramp']['ramp_speed'] = speed

            self.resist.start_ramp()
            

    def open_graph_display_button_clicked(self):
        self.window_log_list.append(Logwindow(self.resist))
        self.window_log_list[-1].show()

    def open_devices_menu_button_clicked(self):
        if self.device_menu_window == None:
            self.device_menu_window = Devices(self.resist)
        self.device_menu_window.show()

    def open_datalog_files_button_clicked(self):
        if self.window_datalog_files == None:
            self.window_datalog_files = DataLogFile(self.resist)
        self.window_datalog_files.show()

    def save_log_data_checkbox_changed(self):
        if self.save_log_data_checkbox.isChecked() == True:
            self.resist.save_data()
            self.resist.log_saving_checkbox = self.save_log_data_checkbox.isChecked()
        else:
            self.resist.log_saving_checkbox = self.save_log_data_checkbox.isChecked()

    def start_log_button_clicked(self):
        self.resist.start_logging()
        print('Log Started')

    def stop_log_button_clicked(self):
        self.resist.stop_logging()
        print('Log Stopped')

    def clear_log_button_clicked(self):
        self.resist.clear_log()
        print('Log Cleared')

    def save_data_button_clicked(self):
        print('Starting to save data')
        self.resist.start_saving_log()




class Logwindow(QWidget):
    def __init__(self, resist=None):
        super().__init__()

        base_dir = os.path.dirname(os.path.abspath(__file__))
        ui_file = os.path.join(base_dir, 'GUI', 'graph_display_window.ui')
        uic.loadUi(ui_file, self)

        self.resist = resist

        self.plot_widget = pg.PlotWidget(title="Temperature Log")
        self.plot = self.plot_widget.plot([0], [0])
        self.plot_widget.setLabel('bottom','time', units = "s")
        self.plot_widget.setLabel('left','Temperature', units = "K")
        layout = self.graph_box.layout()
        layout.addWidget(self.plot_widget)

        # self.plot2_widget = pg.PlotWidget(title="Data Log")
        # self.plot2 = self.plot2_widget.plot([0], [0])
        # self.plot2_widget.setLabel('bottom','time', units = "s")
        # self.plot2_widget.setLabel('left','Voltage', units = "V")
        # layout.addWidget(self.plot2_widget)

        
        for key, value in self.resist.data_dict.items():
            self.x_axis_menu.addItem(f'{key}')
            #self.y_axis_menu.addItem(f'{key}')

        for key, value in self.resist.data_dict.items():
            item = QListWidgetItem(f'{key}')
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.y_axis_menu.addItem(item)

        self.x_item = self.x_axis_menu.currentText()
        #self.y_items = [self.y_axis_menu.currentText()]
        self.y_items = [self.y_axis_menu.item(i).text() for i in range(self.y_axis_menu.count()) if self.y_axis_menu.item(i).checkState() == Qt.Checked]
       
        self.plot_colors = ['r', 'g', 'b', 'c', 'm', 'y']
       
        self.timer = QTimer()
        if self.resist.keep_running == True:
            self.timer.timeout.connect(self.update_plot)
        self.timer.start(1000)

        self.x_axis_menu.currentIndexChanged.connect(self.x_axis_menu_index_changed)
        self.y_axis_menu.itemChanged.connect(self.y_axis_menu_index_changed)
        self.clear_graph_button.clicked.connect(self.clear_graph_button_clicked)

    def x_axis_menu_index_changed(self):
        self.x_item = self.x_axis_menu.currentText()

    def y_axis_menu_index_changed(self):
        self.y_items = [self.y_axis_menu.item(i).text() for i in range(self.y_axis_menu.count()) if self.y_axis_menu.item(i).checkState() == Qt.Checked]

    def update_plot(self):
        x_axis = self.resist.data_dict[self.x_item]
        #y_axis = self.resist.data_dict[self.y_item]
        #self.plot.setData(x_axis, y_axis)
        self.plot_widget.clear()
        for i, y_item in enumerate(self.y_items):
            y_axis = self.resist.data_dict[y_item]
            color = self.plot_colors[i % len(self.plot_colors)]
            self.plot_widget.plot(x_axis, y_axis, name=y_item, pen=color)

    def clear_graph_button_clicked(self):
        self.resist.clear_graph()





class Devices(QWidget):
    def __init__(self, resist=None):
        super().__init__()

        base_dir = os.path.dirname(os.path.abspath(__file__))
        ui_file = os.path.join(base_dir, 'GUI', 'device_menu.ui')
        uic.loadUi(ui_file, self)

        self.resist = resist

        # Device definition:
        layout = self.device_menu.layout()

        # Add row button
        self.add_button = QtWidgets.QPushButton("Add Device")
        self.add_button.clicked.connect(self.add_new_row)
        layout.addWidget(self.add_button)

        # Delete row button
        self.delete_button = QtWidgets.QPushButton("Delete Device")
        self.delete_button.clicked.connect(self.delete_last_row)
        layout.addWidget(self.delete_button)

        # Table Widget
        self.table_widget = QtWidgets.QTableWidget()
        self.table_widget.setColumnCount(5)
        self.table_widget.setHorizontalHeaderLabels(["Device", "Address", "Variable", "Name", "Load?"])
        layout.addWidget(self.table_widget)

        self.load_instruments_button.clicked.connect(self.load_instruments_button_clicked)

    def load_instruments_button_clicked(self):
        self.resist.load_instruments()

    def add_new_row(self):
        # Add a row
        row_position = self.table_widget.rowCount()
        self.table_widget.insertRow(row_position)
        
        # Add the address line
        line = QtWidgets.QLineEdit()
        self.table_widget.setCellWidget(row_position, 1, line)

        # Add the instrument selection menu
        combo_box = QtWidgets.QComboBox()
        combo_box.addItems(["","Lakeshore 350", "Lock-in SR830", "RandomGen"])  # Add your items
        self.table_widget.setCellWidget(row_position, 0, combo_box)

        # Add a validate button
        checkbox = QtWidgets.QCheckBox("Load")
        self.table_widget.setCellWidget(row_position, 4, checkbox)

        # Add a dropdown menu to define measured quantity
        combo_box2 = QtWidgets.QComboBox()
        combo_box2.addItems([""])
        self.table_widget.setCellWidget(row_position, 2, combo_box2)

        # Add a line to name your quantity
        line2 = QtWidgets.QLineEdit()
        self.table_widget.setCellWidget(row_position, 3, line2)

        # Connect signals for interaction with cell contents
        #combo_box.currentIndexChanged.connect(lambda index, row=row_position: self.combo_box_changed(row, index))
        #line.textChanged.connect(lambda text, row=row_position: self.line_edit_changed(row, text))
        checkbox.stateChanged.connect(lambda _, row=row_position: self.load_checkbox_changed(row))
        combo_box.currentIndexChanged.connect(lambda index, row=row_position: self.combo_box_changed(row, index))

    def load_checkbox_changed(self, row):
        instrument = self.table_widget.cellWidget(row, 0).currentText()
        address = self.table_widget.cellWidget(row, 1).text()
        quantity = self.table_widget.cellWidget(row, 2).currentText()
        name = self.table_widget.cellWidget(row, 3).text()

        if self.table_widget.cellWidget(row,4).isChecked() == True:
            if (instrument, address, quantity, name) not in zip(self.resist.instr_list[0], self.resist.instr_list[1], self.resist.instr_list[2], self.resist.instr_list[3]):
                self.resist.instr_list[0].append(instrument)
                self.resist.instr_list[1].append(address)
                self.resist.instr_list[2].append(quantity)
                self.resist.instr_list[3].append(name)
            else:
                print('Instrument already exists')
        if self.table_widget.cellWidget(row,4).isChecked() == False:
            # Find the index of the row in instr_list
            index = None
            for i, (inst, addr, quant, nm) in enumerate(zip(*self.resist.instr_list)):
             if inst == instrument and addr == address and quant == quantity and nm == name:
                   index = i
                   break

            # Remove the corresponding row from instr_list
            if index is not None:
                for i in range(len(self.resist.instr_list)):
                    del self.resist.instr_list[i][index]

    def combo_box_changed(self, row, index):
        if index == 1:
            self.table_widget.cellWidget(row, 2).clear()
            self.table_widget.cellWidget(row, 2).addItems(["Temperature"])
            self.table_widget.cellWidget(row, 1).setText(self.resist.config['LS350']['ip_address'])
        if index == 2:
            self.table_widget.cellWidget(row, 2).clear()
            self.table_widget.cellWidget(row, 2).addItems(["X value", "Y value", "R value", "Theta"])
            self.table_widget.cellWidget(row, 1).setText(self.resist.config['SR830']['port'])
        if index == 3:
            self.table_widget.cellWidget(row, 2).clear()
            self.table_widget.cellWidget(row, 2).addItems(["Random 1", "Random 2", "Random 3", "Random 4"])
            self.table_widget.cellWidget(row, 1).setText("1")

    #def combo_box_changed(self, row, index):
    #    self.resist.instr_list[0].append(self.table_widget.cellWidget(row, 0).currentText())

    #def line_edit_changed(self, row, text):
    #    self.resist.instr_list[1].append(text)


    def delete_last_row(self):
        # Delete the last row
        row_position = self.table_widget.rowCount()
        self.table_widget.removeRow(row_position - 1)



class DataLogFile(QWidget):
    def __init__(self, resist=None):
        super().__init__()

        base_dir = os.path.dirname(os.path.abspath(__file__))
        ui_file = os.path.join(base_dir, 'GUI', 'data-log_files.ui')
        uic.loadUi(ui_file, self)

        self.resist = resist

        self.saving_log_file_line.setText(self.resist.config['Saving']['log_path'])

        self.validation_button.clicked.connect(self.validation_button_clicked)

    def validation_button_clicked(self):
        log_path = self.saving_log_file_line.text()
        data_path = self.saving_data_file_line.text()

        self.resist.config['Saving']['log_path'] = log_path
        self.resist.config['Saving']['data_path'] = data_path



class RampParam(QWidget):
    def __init__(self, resist=None):
        super().__init__()

        base_dir = os.path.dirname(os.path.abspath(__file__))
        ui_file = os.path.join(base_dir, 'GUI', 'ramp_parameters.ui')
        uic.loadUi(ui_file, self)

        self.resist = resist

        # Device definition:
        layout = self.sequence_menu.layout()

        # Add row button
        self.add_seq_button = QtWidgets.QPushButton("Add Row")
        layout.addWidget(self.add_seq_button)

        # Delete row button
        self.delete_seq_button = QtWidgets.QPushButton("Delete Row")
        layout.addWidget(self.delete_seq_button)

        # Table Widget
        self.table_widget2 = QtWidgets.QTableWidget()
        self.table_widget2.setColumnCount(3)
        self.table_widget2.setHorizontalHeaderLabels(["Start T", "End T", "Ramp Speed"])
        layout.addWidget(self.table_widget2)

        self.add_seq_button.clicked.connect(self.add_new_seq_row)
        self.delete_seq_button.clicked.connect(self.delete_last_seq_row)
        self.validate_sequence_button.clicked.connect(self.validate_sequence)

    def add_new_seq_row(self):
        # Add a row
        row_position = self.table_widget2.rowCount()
        self.table_widget2.insertRow(row_position)
        
        # Add the Start Temperature line
        line = QtWidgets.QLineEdit()
        self.table_widget2.setCellWidget(row_position, 0, line)

        # Add the End Temperature line
        line2 = QtWidgets.QLineEdit()
        self.table_widget2.setCellWidget(row_position, 1, line2)

        # Add the Ramp Speed line
        line3 = QtWidgets.QLineEdit()
        self.table_widget2.setCellWidget(row_position, 2, line3)
    
    def delete_last_seq_row(self):
        # Delete the last row
        row_position = self.table_widget2.rowCount()
        self.table_widget2.removeRow(row_position - 1)

    def validate_sequence(self):
        for row in range(self.table_widget2.rowCount()):
            for column in range(self.table_widget2.columnCount()):
                self.resist.ramp_parameters[column].append(self.table_widget2.cellWidget(row,column).text())
        