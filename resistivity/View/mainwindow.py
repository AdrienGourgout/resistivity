from PyQt5.QtWidgets import QMainWindow, QWidget, QListWidget, QListWidgetItem
from PyQt5 import uic, QtWidgets
from PyQt5.QtCore import QTimer, Qt
import pyqtgraph as pg
import os
from time import time


class MainWindow(QMainWindow):
    def __init__(self, resist=None):
        super().__init__()

        base_dir = os.path.dirname(os.path.abspath(__file__))
        ui_file = os.path.join(base_dir, 'GUI', 'mainwindow.ui')
        uic.loadUi(ui_file, self)

        ## Windows
        self.resist = resist
        self.device_menu_window = None
        self.window_file = None
        self.window_graph_list = []

        ## Buttons
        self.start_button.clicked.connect(self.resist.start_logging)
        self.stop_button.clicked.connect(self.resist.stop_logging)
        self.save_data_checkbox.stateChanged.connect(self.resist.save_log)
        self.open_graph_button.clicked.connect(self.open_graph_window)
        self.open_devices_button.clicked.connect(self.open_devices_window)
        self.open_file_button.clicked.connect(self.open_file_window)

    def open_graph_window(self):
        if self.resist.keep_running == False:
            self.resist.start_logging()
        self.window_graph_list.append(GraphWindow(self.resist))
        self.window_graph_list[-1].show()

    def open_devices_window(self):
        if self.device_menu_window == None:
            self.device_menu_window = DevicesWindow(self.resist)
        self.device_menu_window.show()

    def open_file_window(self):
        if self.window_file == None:
            self.window_file = FileWindow(self.resist)
        self.window_file.show()

    # def save_data(self):
    #     self.resist.saving = self.save_data_checkbox.isChecked()
        # if self.save_data_checkbox.isChecked() == True:
        #     log_path = {self.resist.config['Saving']['log_path']: None}
        #     self.resist.data_file_dict.update(log_path)
        #     self.resist.save_data(self.resist.config['Saving']['log_path'])
        #     self.resist.saving = self.save_data_checkbox.isChecked()
        # else:
        #     self.resist.log_saving_checkbox = self.save_data_checkbox.isChecked()

    ## Ramp buttons:
    # self.open_ramp_parameters_menu.clicked.connect(self.open_ramp_parameters_menu_button_clicked)

    # def open_ramp_parameters_menu_button_clicked(self):
    #     if self.ramp_parameters_window == None:
    #         self.ramp_parameters_window = RampParam(self.resist)
    #     self.ramp_parameters_window.show()

    # def start_ramp_button_clicked(self):
    #     data_path = {self.resist.config['Saving']['data_path']: None}
    #     self.resist.data_file_dict.update(data_path)
    #     self.resist.save_data(self.resist.config['Saving']['data_path'])
    #     for start, stop, speed in zip(self.resist.ramp_parameters[0], self.resist.ramp_parameters[1], self.resist.ramp_parameters[2]):
    #         self.resist.config['Ramp']['ramp_start_T'] = start
    #         self.resist.config['Ramp']['ramp_end_T'] = stop
    #         self.resist.config['Ramp']['ramp_speed'] = speed

    #         self.resist.start_ramp()






class GraphWindow(QWidget):
    def __init__(self, resist=None):
        super().__init__()

        base_dir = os.path.dirname(os.path.abspath(__file__))
        ui_file = os.path.join(base_dir, 'GUI', 'graphwindow.ui')
        uic.loadUi(ui_file, self)

        self.resist = resist
        self.x_axis = []
        self.y_axis = {}
        self.graph_data = {}
        self.graph_initial_time = self.resist.initial_time

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
            self.graph_data[key] = []
            self.x_axis_menu.addItem(f'{key}')
            item = QListWidgetItem(f'{key}')
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.y_axis[key] = []
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
        for keys in self.graph_data.keys():
            if keys == 'Time':
                self.graph_data[keys].append(self.resist.data_dict[keys][-1] + self.resist.initial_time - self.graph_initial_time)
            else:
                self.graph_data[keys].append(self.resist.data_dict[keys][-1])

        self.plot_widget.clear()
        for i, y_item in enumerate(self.y_items):
            color = self.plot_colors[i % len(self.plot_colors)]
            self.plot_widget.plot(self.graph_data[self.x_item], self.graph_data[y_item], name=y_item, pen=color)

    def clear_graph_button_clicked(self):
        for keys in self.graph_data.keys():
            self.graph_data[keys] = []
        self.graph_initial_time = time()





class DevicesWindow(QWidget):
    def __init__(self, resist=None):
        super().__init__()

        base_dir = os.path.dirname(os.path.abspath(__file__))
        ui_file = os.path.join(base_dir, 'GUI', 'deviceswindow.ui')
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

        self.load_config_button.clicked.connect(self.load_config_button_clicked)

        #load config instruments upon opening the window
        for label in self.resist.config_dict['Measurements'].keys():
            # Creates the new row
            self.add_new_row()
            # Fill it with the data
            row = self.table_widget.rowCount() - 1
            self.table_widget.cellWidget(row, 0).setCurrentText(self.resist.config_dict['Measurements'][label]['instrument'])
            self.table_widget.cellWidget(row, 1).setText(self.resist.config_dict['Measurements'][label]['address'])
            self.table_widget.cellWidget(row, 2).setCurrentText(self.resist.config_dict['Measurements'][label]['quantity'])
            self.table_widget.cellWidget(row, 3).setText(label)

            self.load_unload_button_clicked(row)


    def add_new_row(self):
        # Add a row
        row_position = self.table_widget.rowCount()
        self.table_widget.insertRow(row_position)

        # Add the address line
        line = QtWidgets.QLineEdit()
        self.table_widget.setCellWidget(row_position, 1, line)

        # Add the instrument selection menu
        combo_box = QtWidgets.QComboBox()
        combo_box.addItems(["","Lakeshore 350", "Lock-in SR830", "Random"])  # Add your items
        self.table_widget.setCellWidget(row_position, 0, combo_box)

        # Add a load/unload button
        load_unload_button = QtWidgets.QPushButton("Load")
        self.table_widget.setCellWidget(row_position, 4, load_unload_button)

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
        #checkbox.stateChanged.connect(lambda _, row=row_position: self.load_checkbox_changed(row))
        load_unload_button.clicked.connect(lambda _, row=row_position: self.load_unload_button_clicked(row))
        combo_box.currentIndexChanged.connect(lambda index, row=row_position: self.combo_box_changed(row, index))

    def load_unload_button_clicked(self, row):
        instrument = self.table_widget.cellWidget(row, 0).currentText()
        address = self.table_widget.cellWidget(row, 1).text()
        quantity = self.table_widget.cellWidget(row, 2).currentText()
        name = self.table_widget.cellWidget(row, 3).text()

        if self.table_widget.cellWidget(row, 4).text() == 'Load':
            self.resist.add_instrument(instrument, address, quantity, name)
            self.table_widget.cellWidget(row, 4).setText('Unload')

            #Make the lines unchangeable
            self.table_widget.cellWidget(row, 0).setEnabled(False)
            self.table_widget.cellWidget(row, 1).setReadOnly(True)
            self.table_widget.cellWidget(row, 2).setEnabled(False)
            self.table_widget.cellWidget(row, 3).setReadOnly(True)
            return

        if self.table_widget.cellWidget(row, 4).text() == 'Unload':
            self.resist.delete_instrument(name)
            self.delete_row(row)
            return

    def combo_box_changed(self, row, index):
        if index == 1:
            self.table_widget.cellWidget(row, 2).clear()
            self.table_widget.cellWidget(row, 2).addItems(["Temperature_A","Temperature_B","Temperature_C","Temperature_D"])
            self.table_widget.cellWidget(row, 1).setText(self.resist.config_dict['LS350']['ip_address'])
        if index == 2:
            self.table_widget.cellWidget(row, 2).clear()
            self.table_widget.cellWidget(row, 2).addItems(["X", "Y", "R", "Theta"])
            self.table_widget.cellWidget(row, 1).setText(self.resist.config_dict['SR830']['port'])
        if index == 3:
            self.table_widget.cellWidget(row, 2).clear()
            self.table_widget.cellWidget(row, 2).addItems(["Random_1", "Random_2", "Random_3", "Random_4"])
            self.table_widget.cellWidget(row, 1).setText("1")

    #def combo_box_changed(self, row, index):
    #    self.resist.instr_list[0].append(self.table_widget.cellWidget(row, 0).currentText())

    #def line_edit_changed(self, row, text):
    #    self.resist.instr_list[1].append(text)


    def delete_last_row(self):
        # Delete the last row
        row_position = self.table_widget.rowCount()
        self.table_widget.removeRow(row_position - 1)

    def delete_row(self, row):
        # Delete the row on pressing Unload button
        self.table_widget.removeRow(row)

    def load_config_button_clicked(self):
        for keys, values in self.resist.config_dict['Measurements'].items():
            self.add_new_row()




class FileWindow(QWidget):
    def __init__(self, resist=None):
        super().__init__()

        base_dir = os.path.dirname(os.path.abspath(__file__))
        ui_file = os.path.join(base_dir, 'GUI', 'filewindow.ui')
        uic.loadUi(ui_file, self)

        self.resist = resist

        self.saving_file_line.setText(self.resist.config_dict['Saving']['file'])
        # self.saving_data_file_line.setText(self.resist.config['Saving']['data_path'])

        self.validation_button.clicked.connect(self.validation_button_clicked)

    def validation_button_clicked(self):
        log_path = self.saving_file_line.text()
        # data_path = self.saving_data_file_line.text()

        self.resist.config_dict['Saving']['file'] = log_path
        # self.resist.config['Saving']['data_path'] = data_path



# class RampParam(QWidget):
#     def __init__(self, resist=None):
#         super().__init__()

#         base_dir = os.path.dirname(os.path.abspath(__file__))
#         ui_file = os.path.join(base_dir, 'GUI', 'ramp_parameters.ui')
#         uic.loadUi(ui_file, self)

#         self.resist = resist

#         # Device definition:
#         layout = self.sequence_menu.layout()

#         # Add row button
#         self.add_seq_button = QtWidgets.QPushButton("Add Row")
#         layout.addWidget(self.add_seq_button)

#         # Delete row button
#         self.delete_seq_button = QtWidgets.QPushButton("Delete Row")
#         layout.addWidget(self.delete_seq_button)

#         # Table Widget
#         self.table_widget2 = QtWidgets.QTableWidget()
#         self.table_widget2.setColumnCount(3)
#         self.table_widget2.setHorizontalHeaderLabels(["Start T", "End T", "Ramp Speed"])
#         layout.addWidget(self.table_widget2)

#         self.add_seq_button.clicked.connect(self.add_new_seq_row)
#         self.delete_seq_button.clicked.connect(self.delete_last_seq_row)
#         self.validate_sequence_button.clicked.connect(self.validate_sequence)

#     def add_new_seq_row(self):
#         # Add a row
#         row_position = self.table_widget2.rowCount()
#         self.table_widget2.insertRow(row_position)

#         # Add the Start Temperature line
#         line = QtWidgets.QLineEdit()
#         self.table_widget2.setCellWidget(row_position, 0, line)

#         # Add the End Temperature line
#         line2 = QtWidgets.QLineEdit()
#         self.table_widget2.setCellWidget(row_position, 1, line2)

#         # Add the Ramp Speed line
#         line3 = QtWidgets.QLineEdit()
#         self.table_widget2.setCellWidget(row_position, 2, line3)

#     def delete_last_seq_row(self):
#         # Delete the last row
#         row_position = self.table_widget2.rowCount()
#         self.table_widget2.removeRow(row_position - 1)

#     def validate_sequence(self):
#         for row in range(self.table_widget2.rowCount()):
#             for column in range(self.table_widget2.columnCount()):
#                 self.resist.ramp_parameters[column].append(self.table_widget2.cellWidget(row,column).text())
