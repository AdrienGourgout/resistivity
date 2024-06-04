from PyQt5.QtWidgets import QMainWindow, QWidget, QListWidget, QListWidgetItem, QFileDialog, QDialog
from PyQt5 import uic, QtWidgets
from PyQt5.QtCore import QTimer, Qt
import pyqtgraph as pg
import os
from time import time
import numpy as np
import yaml

class MainWindow(QMainWindow):
    def __init__(self, log=None):
        super().__init__()

        base_dir = os.path.dirname(os.path.abspath(__file__))
        ui_file = os.path.join(base_dir, 'GUI', 'mainwindow.ui')
        uic.loadUi(ui_file, self)

        ## LogMeasure object
        self.log = log

        ## Windows
        self.device_menu_window = None
        self.window_file = None
        self.window_graph_list = []

        ## Buttons
        self.start_button.clicked.connect(self.log.start_logging)
        self.stop_button.clicked.connect(self.log.stop_logging)
        self.save_data_checkbox.stateChanged.connect(self.save_data)
        self.analysis_checkbox.stateChanged.connect(self.analysis_checkbox_changed)
        self.open_graph_button.clicked.connect(self.open_graph_window)
        self.open_devices_button.clicked.connect(self.open_devices_window)
        self.open_file_button.clicked.connect(self.open_file_window)

        ## Timer (trigger periodic actions without interrupting the rest of the program)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_window)
        self.timer.start(50) # trigger timout every 50 ms. There is no point to do
                            # more often because the monitor won't really refresh
                            # faster than 20 Hz, maybe twice faster.

    def open_graph_window(self):
        # if self.log.keep_running == False:
        #     self.log.start_logging()
        self.window_graph_list.append(GraphWindow(self.log))
        self.window_graph_list[-1].show()

    def open_devices_window(self):
        if self.device_menu_window == None:
            self.device_menu_window = DevicesWindow(self.log)
        self.device_menu_window.show()

    def open_file_window(self):
        if self.window_file == None:
            self.window_file = FileWindow(self.log)
        self.window_file.show()

    def analysis_checkbox_changed(self):
        self.analysis_window = AnalysisWindow(self)
        if self.analysis_window.exec_() == QtWidgets.QDialog.Accepted:
            self.log.config_dict['Analysis']['Seebeck'] = self.analysis_window.seebeck_checkbox.isChecked()
        if self.log.config_dict['Analysis']['Seebeck'] == True:
            print('It works')

    def save_data(self):
        if self.save_data_checkbox.isChecked():
            self.window_file = FileWindow(self.log)
            if self.window_file.exec_() == QtWidgets.QDialog.Accepted:
                self.log.saving = self.save_data_checkbox.isChecked()
        else:
            self.log.saving = self.save_data_checkbox.isChecked()

    def update_window(self):
        if self.log.keep_running:
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
        else:
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)

    def closeEvent(self, event):
        """Override the closeEvent (when the user press on the close button)"""
        self.log.stop_logging()



class AnalysisWindow(QtWidgets.QDialog):
    def __init__(self, parent=None, log=None):
        super().__init__(parent)

        self.layout = QtWidgets.QVBoxLayout()


        self.label = QtWidgets.QLabel("Quantity to analyze:")
        self.layout.addWidget(self.label)
        self.seebeck_checkbox = QtWidgets.QCheckBox('Seebeck')
        self.layout.addWidget(self.seebeck_checkbox)

        self.validate_button = QtWidgets.QPushButton('Validate')
        self.layout.addWidget(self.validate_button)

        self.setLayout(self.layout)

        self.validate_button.clicked.connect(self.validate_button_clicked)

    def validate_button_clicked(self):

        self.accept()

class Matching(QtWidgets.QDialog):
    def __init__(self, parent=None, log=None):
        super().__init__(parent)
        self.log = log
        self.layout = QtWidgets.QVBoxLayout()
        for names in self.log.config_dict['Measurements'].keys():
            self.button = QtWidgets.QPushButton(names)
            self.layout.addWidget(self.button)



class GraphWindow(QWidget):
    def __init__(self, log=None):
        super().__init__()

        base_dir = os.path.dirname(os.path.abspath(__file__))
        ui_file = os.path.join(base_dir, 'GUI', 'graphwindow.ui')
        uic.loadUi(ui_file, self)

        self.log = log
        self.x_axis = []
        self.y_axis = {}
        self.graph_data = {}
        self.graph_initial_time = 0

        # Create the main window
        self.plot_widget = pg.GraphicsLayoutWidget(show=True, title='Continuous Data Plot')
        self.plot_widget.resize(800, 600)
        self.plot_widget.setBackground('k')  # Black background

        # Create and store a reference to a plot item
        self.plot = self.plot_widget.addPlot()
        self.plot_items = {}  # Dictionary to hold plot items for each data series

        pg.setConfigOptions(antialias=True)  # Enable anti-aliasing for smoother lines

        # Customize plot appearance
        self.plot.showAxis('top', True)
        self.plot.showAxis('right', True)
        self.plot.getAxis('top').setStyle(showValues=False)
        self.plot.getAxis('right').setStyle(showValues=False)
        color = '#a9a7ab'  # Cyan-like color
        for axis in ['left', 'bottom', 'top', 'right']:
            self.plot.getAxis(axis).setPen(pg.mkPen(color=color, width=1))

        # Customize axis and ticks
        tickFont = pg.QtGui.QFont("Arial", 16)
        textColor = pg.mkColor(color)
        for axis in ['left', 'bottom', 'right', 'top']:
            self.plot.getAxis(axis).setTickFont(tickFont)
            self.plot.getAxis(axis).setTextPen(textColor)

        # Labels with custom font
        labelFont = pg.QtGui.QFont("Arial", 16, pg.QtGui.QFont.Weight.Bold)
        # Set x and y labels
        self.plot.setLabel('bottom', 'Time', color="#a9a7ab")
        self.plot.setLabel('left', 'Values', color="#a9a7ab")
        # Set your custom font for x and y labels
        self.plot.getAxis("bottom").label.setFont(labelFont)
        self.plot.getAxis("left").label.setFont(labelFont)

        ## Add the plot widget to the layout of GUI
        layout = self.graph_box.layout()
        layout.addWidget(self.plot_widget)
        self.plot_widget.setBackground('#25292d')  # Black background

        ## Initialize the list for y-axis
        for key, value in self.log.data_dict.items():
            self.graph_data[key] = np.empty(0)
            self.x_axis_menu.addItem(f'{key}')
            item = QListWidgetItem(f'{key}')
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            if key != "Time":
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            self.y_axis[key] = []
            self.y_axis_menu.addItem(item)

        self.x_item = self.x_axis_menu.currentText()
        self.y_items = [self.y_axis_menu.item(i).text() for i in range(self.y_axis_menu.count()) if self.y_axis_menu.item(i).checkState() == Qt.Checked]

        self.plot_colors = ['r', 'g', 'b', 'c', 'm', 'y']

        self.timer = QTimer()
        #if self.log.keep_running == True:
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(int(self.log.time_steps*1e3))

        self.x_axis_menu.currentIndexChanged.connect(self.x_axis_menu_index_changed)
        self.y_axis_menu.itemChanged.connect(self.y_axis_menu_index_changed)
        self.clear_graph_button.clicked.connect(self.clear_graph_button_clicked)

    def x_axis_menu_index_changed(self):
        self.x_item = self.x_axis_menu.currentText()
        self.plot_widget.setLabel('bottom',self.x_axis_menu.currentText())

    def y_axis_menu_index_changed(self):
        self.y_items = [self.y_axis_menu.item(i).text() for i in range(self.y_axis_menu.count()) if self.y_axis_menu.item(i).checkState() == Qt.Checked]

    def update_plot(self):
        if self.log.keep_running == True:
            for keys in self.graph_data.keys():
                # Time
                if keys == 'Time':
                    current_time = self.graph_data["Time"][-1] + self.log.time_steps if self.graph_data["Time"].size else 0
                    self.graph_data['Time'] = np.append(self.graph_data["Time"], current_time)
                else:
                    self.graph_data[keys] = np.append(self.graph_data[keys], self.log.data_dict[keys][-1])

        # Now update or create plots as needed
        for i, y_item in enumerate(self.y_items):
            if y_item not in self.plot_items:  # If no plot item for this data series, create it
                pen = pg.mkPen(color=self.plot_colors[i % len(self.plot_colors)], width=2)
                # Create a plot item for this series and store it
                self.plot_items[y_item] = self.plot.plot(self.graph_data[self.x_item], self.graph_data[y_item], pen=pen, name=y_item)
            else:
                # Update the data for an existing plot item
                self.plot_items[y_item].setData(self.graph_data[self.x_item], self.graph_data[y_item])


        #Remove plots when box unchecked
        unchecked_items = set(self.plot_items.keys()) - set(self.y_items)
        for item_name in unchecked_items:
            plot_item = self.plot_items.pop(item_name)
            self.plot.removeItem(plot_item)

    def clear_graph_button_clicked(self):
        for keys in self.graph_data.keys():
            self.graph_data[keys] = np.empty(0)
        self.graph_initial_time = 0





class DevicesWindow(QWidget):
    def __init__(self, log=None):
        super().__init__()

        base_dir = os.path.dirname(os.path.abspath(__file__))
        ui_file = os.path.join(base_dir, 'GUI', 'deviceswindow.ui')
        uic.loadUi(ui_file, self)

        self.log = log

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


        #load config instruments
        self.load_config_instruments()

        # Saving the Config in a file
        self.save_config_button.clicked.connect(self.save_config_button_clicked)

        # Load the Config from a file
        self.load_config_button.clicked.connect(self.load_config_button_clicked)


    def load_config_instruments(self):
        # Displays in the window the instruments present in the config file.
        for label in self.log.config_dict['Measurements'].keys():
            # Creates the new row
            self.add_new_row()
            # Fill it with the data
            row = self.table_widget.rowCount() - 1
            self.table_widget.cellWidget(row, 0).setCurrentText(self.log.config_dict['Measurements'][label]['instrument'])
            self.table_widget.cellWidget(row, 1).setText(self.log.config_dict['Measurements'][label]['address'])
            self.table_widget.cellWidget(row, 2).setCurrentText(self.log.config_dict['Measurements'][label]['channel'])
            self.table_widget.cellWidget(row, 3).setText(label)
            self.table_widget.cellWidget(row, 4).setText('Unload')
            self.lock_device_line(row)

    def save_config_button_clicked(self):
        # Opens a browser to select a file to save the current config into.
        config_file_path, _ = QFileDialog.getSaveFileName(self, "Select a file", "", "YAML Files (*.yml)")
        with open(config_file_path, 'w') as f:
            f.write(yaml.dump(self.log.config_dict, default_flow_style=False))
        f.close()

    def load_config_button_clicked(self):
        # Opens a browser to select the config file and load it.
        file_path, _ = QFileDialog.getOpenFileName(self, "Select a file", "", "YAML Files (*.yml)")
        # Stops the program from logging data while the switch is running
        self.log.keep_running = False
        # Load the new config
        self.log.config_file = file_path
        self.log.config_dict = {}
        self.log.load_config()
        # Reset the data and instruments dictionnaries before filling them again
        self.log.data_dict = {'Time': np.empty(0)}
        self.log.instruments_query = {}
        # Restart the logging
        self.log.keep_running = True

        # Clear the table of the previous instruments.
        while self.table_widget.rowCount() > 0:
            self.delete_last_row()
        # Refills the table with the new instruments.
        self.load_config_instruments()

    def add_new_row(self):
        # Add a row
        row_position = self.table_widget.rowCount()
        self.table_widget.insertRow(row_position)

        # Add the address line
        line = QtWidgets.QLineEdit()
        self.table_widget.setCellWidget(row_position, 1, line)

        # Add the instrument selection menu
        combo_box = QtWidgets.QComboBox()
        combo_box.addItems(["","Lakeshore 350", "Lock-in SR830", "Random", "SynkTek"])  # Add your items
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
        channel = self.table_widget.cellWidget(row, 2).currentText()
        name = self.table_widget.cellWidget(row, 3).text()

        if self.table_widget.cellWidget(row, 4).text() == 'Load':
            self.open_quantity_window(instrument, channel)
            #self.log.add_instrument(instrument, address, quantity, name)
            quantities = self.chosen_quantities
            self.log.config_dict['Measurements'][name] = {}
            self.log.config_dict["Measurements"][name]["instrument"] = instrument
            self.log.config_dict["Measurements"][name]["address"] = address
            self.log.config_dict["Measurements"][name]["channel"] = channel
            self.log.config_dict["Measurements"][name]["quantities"] = quantities

            self.table_widget.cellWidget(row, 4).setText('Unload')
            self.lock_device_line(row)
            return

        if self.table_widget.cellWidget(row, 4).text() == 'Unload':
            self.log.delete_instrument(name)
            self.delete_row(row)
            return

    def lock_device_line(self, row):
        #Make the lines unchangeable
        self.table_widget.cellWidget(row, 0).setEnabled(False)
        self.table_widget.cellWidget(row, 1).setReadOnly(True)
        self.table_widget.cellWidget(row, 2).setEnabled(False)
        self.table_widget.cellWidget(row, 3).setReadOnly(True)

    def combo_box_changed(self, row, index):
        if index == 1:
            self.table_widget.cellWidget(row, 2).clear()
            self.table_widget.cellWidget(row, 2).addItems(["A","B","C","D"])
            #self.table_widget.cellWidget(row, 1).setText(self.log.config_dict['LS350']['ip_address'])
        if index == 2:
            self.table_widget.cellWidget(row, 2).clear()
            self.table_widget.cellWidget(row, 2).addItems(["None"])
            #self.table_widget.cellWidget(row, 1).setText(self.log.config_dict['SR830']['port'])
        if index == 3:
            self.table_widget.cellWidget(row, 2).clear()
            self.table_widget.cellWidget(row, 2).addItems(["1", "2", "3", "4"])
            self.table_widget.cellWidget(row, 1).setText("None")
        if index == 4:
            self.table_widget.cellWidget(row, 2).clear()
            self.table_widget.cellWidget(row, 2).addItems(["Output", "A-V1", "A-V2", "B-V1", "B-V2", "C-V1", "C-V2", "D-V1", "D-V2", "E-V1", "E-V2"])
            self.table_widget.cellWidget(row, 1).setText("172.22.11.2")

    def open_quantity_window(self, instr, channel):
        quantity_window = Quantity_choice_window(self, instr=instr, channel=channel)
        if quantity_window.exec_() == QtWidgets.QDialog.Accepted:
            self.chosen_quantities = quantity_window.quantities_chosen


    #def combo_box_changed(self, row, index):
    #    self.log.instr_list[0].append(self.table_widget.cellWidget(row, 0).currentText())

    #def line_edit_changed(self, row, text):
    #    self.log.instr_list[1].append(text)


    def delete_last_row(self):
        # Delete the last row
        row_position = self.table_widget.rowCount()
        self.table_widget.removeRow(row_position - 1)

    def delete_row(self, row):
        # Delete the row on pressing Unload button
        self.table_widget.removeRow(row)

    def closeEvent(self, event):
        print('Loading Instruments')
        self.log.load_instruments()



class Quantity_choice_window(QtWidgets.QDialog):
    def __init__(self, parent=None, instr=None, channel=None):
        super().__init__(parent)

        self.layout = QtWidgets.QVBoxLayout()

        self.label = QtWidgets.QLabel("Enter your configuration:")
        self.layout.addWidget(self.label)

        if instr == "Lakeshore 350":
            self.checkboxes = {}
            quantities = ['Temperature', 'Power']
            for quantity in quantities:
                checkbox = QtWidgets.QCheckBox(quantity)
                self.checkboxes[quantity] = checkbox
                self.layout.addWidget(checkbox)

        if instr == "Lock-in SR830":
            self.checkboxes = {}
            quantities = ['X', 'Y', 'R', 'Theta']
            for quantity in quantities:
                checkbox = QtWidgets.QCheckBox(quantity)
                self.checkboxes[quantity] = checkbox
                self.layout.addWidget(checkbox)
        if instr == "Random":
            self.checkboxes = {}
            quantities = ['Rand_1', 'Rand_2', 'Rand_3', 'Rand_4']
            for quantity in quantities:
                checkbox = QtWidgets.QCheckBox(quantity)
                self.checkboxes[quantity] = checkbox
                self.layout.addWidget(checkbox)
        if instr == 'SynkTek':
            self.checkboxes = {}
            if channel == 'Output':
                quantities = ['Amp', 'Freq']
                for quantity in quantities:
                    checkbox = QtWidgets.QCheckBox(quantity)
                    self.checkboxes[quantity] = checkbox
                    self.layout.addWidget(checkbox)
            else:
                quantities = ['DC', 'X', 'Y', 'R', 'Theta']
                for quantity in quantities:
                    checkbox = QtWidgets.QCheckBox(quantity)
                    self.checkboxes[quantity] = checkbox
                    self.layout.addWidget(checkbox)

        self.save_button = QtWidgets.QPushButton("Save")
        self.save_button.clicked.connect(self.save_config)
        self.layout.addWidget(self.save_button)

        self.setLayout(self.layout)

    def save_config(self):
        self.quantities_chosen = {}
        for quantity, checkbox in self.checkboxes.items():
            if checkbox.isChecked():
                self.quantities_chosen[quantity] = True
        self.accept()






class FileWindow(QtWidgets.QDialog):
    def __init__(self, log=None):
        super().__init__()

        base_dir = os.path.dirname(os.path.abspath(__file__))
        ui_file = os.path.join(base_dir, 'GUI', 'filewindow.ui')
        uic.loadUi(ui_file, self)

        self.log = log

        self.saving_file_line.setText(self.log.config_dict['Saving']['file'])
        self.saving_file_line.setReadOnly(True)

        self.select_file_button.clicked.connect(self.select_file_button_clicked)


    def select_file_button_clicked(self):
        log_file_path, _ = QFileDialog.getSaveFileName(self, "Select a file", "", "DAT Files (*.dat)")
        example_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'Example')
        total_path = os.path.relpath(log_file_path,example_path)
        log_path, log_file = os.path.split(total_path)
        self.saving_file_line.setText(log_file_path)
        self.log.config_dict['Saving']['file'] = log_file
        self.log.config_dict["Saving"]['path'] = log_path
        print(log_file)
        print(log_path)
        self.accept()

if __name__ == "__main__":
    test = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    test2 = os.path.join(test, 'Example')
    print(test2)


# class RampParam(QWidget):
#     def __init__(self, log=None):
#         super().__init__()

#         base_dir = os.path.dirname(os.path.abspath(__file__))
#         ui_file = os.path.join(base_dir, 'GUI', 'ramp_parameters.ui')
#         uic.loadUi(ui_file, self)

#         self.log = log

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
#                 self.log.ramp_parameters[column].append(self.table_widget2.cellWidget(row,column).text())
