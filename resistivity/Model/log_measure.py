from time import sleep, time
from resistivity.Driver import SR830
from resistivity.Driver.temperature_controllers import TemperatureController
import numpy as np
import threading
import os
import random
import yaml

class LogMeasure:
    def __init__ (self, config_file):
        self.config_file     = config_file
        self.config_dict     = {}
        self.keep_running    = True
        self.saving          = False
        self.argument_dict   = {}
        self.instruments_query = {}
        self.initial_time    = None
        self.time_steps      = 0.5 # secondes
        ## Dictionnary for the data
        self.data_dict = {}
        self.data_dict['Time'] = np.empty(0)


    def load_config(self):
        with open(self.config_file, 'r') as f:
            self.config_dict = yaml.load(f, Loader=yaml.FullLoader)
        for label in self.config_dict["Measurements"].keys():
            inst  = self.config_dict["Measurements"][label]["instrument"]
            adr   = self.config_dict["Measurements"][label]["address"]
            quant = self.config_dict["Measurements"][label]["quantity"]
            self.add_instrument(inst, adr, quant, label)

    def ls350_methods(self, instr=None, quantity=None):
        if quantity == 'Temperature':
            return instr.get_kelvin_reading

    def sr830_methods(self, instr=None, quantity=None):
        if quantity == 'X':
            return instr.get_X
        if quantity == 'Y':
            return instr.get_Y
        if quantity == 'R':
            return instr.get_R
        if quantity == 'theta':
            return instr.get_Theta

    def random_methods(self, instr=None, quantity=None):
        if quantity == 'Random_1':
            return instr.randint
        if quantity == 'Random_2':
            return instr.randint
        if quantity == 'Random_3':
            return instr.randint


    def add_instrument(self, instrument=None, address=None, quantity=None, data_label=None):
        """instrument is a string that defines the type of instrument: LS350
        address is a string for the adress
        quantity is a string that tells if it is: X, Y, channelA, etc.
        data_label is the label of the measured stuff: XX, T0, etc."""
        if instrument == 'LS350':
            temp = TemperatureController(ip_address=address, tcp_port=7777,timeout=1000)
            instr = self.ls350_methods(temp, quantity)
            argument = 1
            new_instr = {data_label: instr}
            new_argument = {data_label: argument}
            self.instruments_query.update(new_instr)
            self.argument_dict.update(new_argument)
        if instrument == 'SR830':
            temp = SR830.device(address)
            instr = self.sr830_methods(temp, quantity)
            argument = None
            new_instr = {data_label: instr}
            new_argument = {data_label: argument}
            self.instruments_query.update(new_instr)
            self.argument_dict.update(new_argument)
        if instrument == 'Random':
            temp = random
            instr = self.random_methods(temp, quantity)
            argument = (1,100)
            new_instr = {data_label: instr}
            new_argument = {data_label: argument}
            self.instruments_query.update(new_instr)
            self.argument_dict.update(new_argument)
        # Add entry to the data dictionnary
        self.data_dict[data_label] = np.empty(0)
        # Clear all values from the data dictionnary
        self.clear_data()


    def delete_instrument(self, data_label=None):
        #Delete entries from instruments and data dictionnaries
        del self.config_dict["Measurements"][data_label]
        del self.instruments_query[data_label]
        del self.data_dict[data_label]

    def get_values(self):
        while self.keep_running == True:
            self.data_dict['Time'] = np.append(self.data_dict['Time'], time() - self.initial_time)
            for data_label in self.instruments_query.keys():
                value = self.instruments_query[data_label](*self.argument_dict[data_label])
                self.data_dict[data_label] = np.append(self.data_dict[data_label], value)
            if self.saving == True:
                self.save_log()
            sleep(self.time_steps)

    def save_log(self):
        ## File
        path = self.config_dict['Saving']['path']
        file = self.config_dict['Saving']['file']
        if path is None:
            path = ""
        filepath = os.path.join(path, file)
        # Header
        if os.path.isfile(filepath) is False:
            with open(filepath, 'a') as file:
                header = [key for key in self.data_dict.keys()]
                line = "#" + ','.join(map(str, header)) + '\n'
                file.write(line)
        # Values extraction
        values = [self.data_dict[key][-1] for key in self.data_dict.keys()]
        # Save values line by line
        with open(filepath, 'a') as file:
            line = ','.join(map(str, values)) + '\n'
            file.write(line)

    def start_logging(self):
        self.keep_running = True
        self.initial_time = time()
        self.log_thread = threading.Thread(target=self.get_values)
        self.log_thread.start()

    def stop_logging(self):
        self.keep_running = False

    def clear_data(self):
        for keys in self.data_dict:
            self.data_dict[keys] = np.empty(0)



if __name__ == "__main__":
    resist = LogMeasure('../../Example/Config.yml')
    resist.load_config()
    resist.saving = True
    resist.start_logging()
    sleep(2)
    resist.stop_logging()
    print(resist.data_dict["Time"], resist.data_dict["RR"])


#   Ramp Measurement

    # self.ramp_parameters = []
    # self.is_ramping = False

    # def start_ramp(self):
    #     for quantity, name in zip(self.instr_list[2],self.instr_list[3]):
    #         if quantity == "Temperature":

    #             self.instruments[name].set_control_setpoint(1, self.config_dict['Ramp']['ramp_start_T'])
    #             sleep(2)
    #             self.instruments[name].set_setpoint_ramp_parameter(1, ramp_enable=True, rate_value=self.config_dict['Ramp']['ramp_speed'])
    #             sleep(2)
    #             self.instruments[name].set_control_setpoint(1, self.config_dict['Ramp']['ramp_end_T'])
    #             self.is_ramping = True
    #             sleep(15)
    #             while self.instruments[name].get_setpoint_ramp_status(1) == True:
    #                 sleep(5)
    #                 print('still ramping')
    #         break
    #     print('ramp done')
    #     self.is_ramping = False

    # def save_ramp(self):
    # values = np.empty(0)
    # for key, values_list in self.data_dict.items():
    #     if values_list.any():
    #         np.append(values, values_list[-1])
    # flattened_values = values.flatten()
    # with open(self.data_file_dict[self.config_dict['Saving']['data_path']], 'a') as file2:
    #     np.savetxt(file2, [flattened_values], delimiter = ',')
    # file2.close()


    # def save_data(self, filename=None):
    #     keys = list(self.data_dict.keys())
    #     path_folder = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    #     path_folder = os.path.join(path_folder, 'Data')
    #     file_path = os.path.join(path_folder, filename)
    #     base_name = file_path.split('.')[0]
    #     ext = file_path.split('.')[-1]
    #     i = 1
    #     while os.path.isfile(f'{base_name}_{i:04d}.{ext}'):
    #         i += 1
    #     self.data_file_dict[filename] = f'{base_name}_{i:04d}.{ext}'
    #     with open(self.data_file_dict[filename], 'w') as f:
    #         f.write(','.join(keys) + '\n')
    #     f.close()







""" def ramp_measurement(self, config_file):
    self.change_temperature(config_file['ramp']['ramp_start_temp'])
    while temperature_stable == False:
        self.temperature_stable(channel)
        sleep(1)
    self.ramp_temperature(channel, congig_file['ramp']['ramp_end_temp'], config_file['ramp']['ramp_speed'])
    while temperature_stable == False:
        self.save_data()
        sleep(config['ramp']['ramp_delay']) """

#   Steps Measurement

""" def step_measurement(self, config_file):
    self.temperature_array = np.linspace(config_file['steps']['steps_start_temp'], config_file['steps']['steps_stop_temp'], config_file['steps']['steps_num_steps'])
    ave = config_file['steps']['steps_average']
    for i, T in enumerate(self.temperature_array):
        self.change_temperature(T)
        while self.T_stable == False:
            self.temperature_stable(channel)
            sleep(1)
        self.average_temp = 0
        self.average_data = 0
        for j in range(ave):
            self.average_temp = self.average_temp + self.temperature
            self.average_data = self.average_data + self.data
        self.average_temp = self.average_temp/ave
        self.average_data = self.average_data/ave """

