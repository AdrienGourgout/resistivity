from time import sleep, time
from resistivity.Driver.SR830 import device
from resistivity.Driver.temperature_controllers import TemperatureController
import numpy as np
import threading
import os
import random
import yaml

class Resistivity:
    def __init__ (self, config_file):
        self.config_file = config_file
        self.keep_running = True
        self.log_saving_checkbox = False
        self.quantity_dict = {}
        self.argument_dict = {}
        self.instruments_query = {}
        self.data_dict = {}
        self.initial_time_graph = time()
        self.initial_time = time()
        self.ramp_parameters = [[],[],[]]
        self.data_file_dict = {}
        self.is_ramping = False

        #Add the Time array to the data dictionnary
        array = np.empty(0)
        timearray = {'Time': array}
        self.data_dict.update(timearray)

    def load_config(self):
        with open(self.config_file, 'r') as f:
            self.config = yaml.load(f, Loader=yaml.FullLoader)

    def lakeshore_methods(self, instr=None, quantity=None):
        if quantity == 'Temperature':
            return instr.get_kelvin_reading
    
    def SR830_methods(self, instr=None, quantity=None):
        if quantity == 'X value':
            return instr.get_X
        if quantity == 'Y value':
            return instr.get_Y
        if quantity == 'R_value':
            return instr.get_R
        if quantity == 'theta':
            return instr.get_Theta
    
    def Random_methods(self, instr=None, quantity=None):
        if quantity == 'Random 1':
            return instr.randint
        if quantity == 'Random 2':
            return instr.randint
        if quantity == 'Random 3':
            return instr.randint
        if quantity == 'Random 4':
            return instr.randint

    def add_instrument(self, instrument=None, address=None, quantity=None, name=None):

        #Add entry to the instrument dictionnary

        if instrument == 'Lakeshore 350':
            temp = TemperatureController(serial_number=None, com_port=None, baud_rate=None, timeout=self.config['LS350']['timeout'], ip_address=address, tcp_port=self.config['LS350']['tcp_port'])
            instr = self.lakeshore_methods(temp, quantity)
            argument = 1
            new_instr = {name: instr}
            new_argument = {name: argument}
            self.instruments_query.update(new_instr)
            self.argument_dict.update(new_argument)
        if instrument == 'Lock-in SR830':
            temp = device(address)
            instr = self.SR830_methods(temp, quantity)
            argument = None
            new_instr = {name: instr}
            new_argument = {name: argument}
            self.instruments_query.update(new_instr)
            self.argument_dict.update(new_argument)
        if instrument == 'RandomGen':
            temp = random
            instr = self.Random_methods(temp, quantity)
            argument = (1,100)
            new_instr = {name: instr}
            new_argument = {name: argument}
            self.instruments_query.update(new_instr)
            self.argument_dict.update(new_argument)
        
        #Add entry to the data dictionnary
        
        array = np.empty(0)
        new_entry = {name: array}
        self.data_dict.update(new_entry)

        #clear all values from the data dictionnary

        self.clear_graph()

        #Add entry to the Quantity dictionnary
        
        new_quantity = {name: quantity}
        self.quantity_dict.update(new_quantity)


    def delete_instrument(self, instrument=None, address=None, quantity=None, name=None):

        #Delete entries from instruments and data dictionnaries

        del self.instruments_query[name]
        del self.data_dict[name]
        del self.quantity_dict[name]



#       Logs


    def get_log_values(self):

        while self.keep_running == True:
            self.data_dict['Time'] = np.append(self.data_dict['Time'], time() - self.initial_time_graph)

            for name in self.instruments_query.keys():
                self.data_dict[name] = np.append(self.data_dict[name], self.instruments_query[name](*self.argument_dict[name]))

            if self.log_saving_checkbox == True:
                self.save_log()

            if self.is_ramping == True:
                self.save_ramp()

            sleep(1)

    def save_log(self):
        values = np.empty(0)
        for key, values_list in self.data_dict.items():
            if values_list.any():
                np.append(values, values_list[-1])
        flattened_values = values.flatten()
        with open(self.data_file_dict[self.config['Saving']['log_path']], 'a') as file:
                np.savetxt(file, [flattened_values], delimiter = ',')
        file.close()
        
    def save_ramp(self):
        values = np.empty(0)
        for key, values_list in self.data_dict.items():
            if values_list.any():
                np.append(values, values_list[-1])
        flattened_values = values.flatten()
        with open(self.data_file_dict[self.config['Saving']['data_path']], 'a') as file2:
            np.savetxt(file2, [flattened_values], delimiter = ',')
        file2.close()     




    def start_logging(self):
        self.keep_running = True
        self.log_thread = threading.Thread(target=self.get_log_values)
        self.log_thread.start()


    def stop_logging(self):
        self.keep_running = False

    def clear_graph(self):
        for keys in self.data_dict:
            self.data_dict[keys] = np.empty(0)
        self.initial_time_graph = time()

    def start_ramp(self):
        for quantity, name in zip(self.instr_list[2],self.instr_list[3]):
            if quantity == "Temperature":

                self.instruments[name].set_control_setpoint(1, self.config['Ramp']['ramp_start_T'])
                sleep(2)
                self.instruments[name].set_setpoint_ramp_parameter(1, ramp_enable=True, rate_value=self.config['Ramp']['ramp_speed'])
                sleep(2)
                self.instruments[name].set_control_setpoint(1, self.config['Ramp']['ramp_end_T'])
                self.is_ramping = True
                sleep(15)
                while self.instruments[name].get_setpoint_ramp_status(1) == True:
                    sleep(5)
                    print('still ramping')
            break

        print('ramp done')
        self.is_ramping = False

#   Data saving

    def save_data(self, filename=None):
        keys = list(self.data_dict.keys())
        path_folder = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        path_folder = os.path.join(path_folder, 'Data')
        file_path = os.path.join(path_folder, filename)
        base_name = file_path.split('.')[0]
        ext = file_path.split('.')[-1]
        i = 1
        while os.path.isfile(f'{base_name}_{i:04d}.{ext}'):
            i += 1
        self.data_file_dict[filename] = f'{base_name}_{i:04d}.{ext}'
        with open(self.data_file_dict[filename], 'w') as f:
            f.write(','.join(keys) + '\n')
        f.close()

# Lakeshore Queries:


#   Ramp Measurement

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

if __name__ == "__main__":
    resist = Resistivity('Config.yml')
    resist.load_config()