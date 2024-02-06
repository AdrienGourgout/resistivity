from time import sleep, time
from resistivity.Driver.SR830 import device
from resistivity.Driver.temperature_controllers import TemperatureController
import numpy as np
import threading
import pyqtgraph as pg
import os
import random
import yaml
from datetime import datetime




class Resistivity:

    def __init__ (self, config_file):
        self.config_file = config_file
        self.temperature_log = np.empty(0)
        self.data_log = np.empty(0)
        self.exptime = np.empty(0)
        self.t = None
        self.temp = None
        self.voltage = None
        self.keep_running = True
        self.log_saving_checkbox = False
        self.instr_list = [[],[],[],[]]
        self.instruments = {}
        self.data_dict = {}
        self.data_log_dict = {}
        #self.use_random_values = False
        # load config file with yaml

    def load_config(self):
        with open(self.config_file, 'r') as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
        self.config = data

    def load_instruments(self):
        if self.instr_list == [[],[],[],[]]:
            print('Nothing to load')
        else:
            for instr, address, name in zip(self.instr_list[0], self.instr_list[1], self.instr_list[3]):
                if instr == 'Lakeshore 350':
                    temp = TemperatureController(serial_number=None, com_port=None, baud_rate=None, timeout=self.config['LS350']['timeout'], ip_address=address, tcp_port=self.config['LS350']['tcp_port'])
                    new_instr = {name: temp}
                    self.instruments.update(new_instr)
                if instr == 'Lock-in SR830':
                    temp = device(address)
                    new_instr = {name: temp}
                    self.instruments.update(new_instr)
                if instr == 'RandomGen':
                    temp = random
                    new_instr = {name: temp}
                    self.instruments.update(new_instr)
            print('All instruments loaded succesfully')

            self.load_data_dict()
    
    def load_data_dict(self):
        array = np.empty(0)
        timearray = {'Time': array}
        self.data_dict.update(timearray)
        self.data_log_dict.update(timearray)
        for i, name in enumerate(self.instr_list[3]):
            new_entry = {name: array}
            self.data_dict.update(new_entry)
            self.data_log_dict.update(new_entry)
        
    

#       Logs
        

    def get_log_values(self):

        while self.keep_running == True:
            self.data_log_dict['Time'] = time() - self.initial_time
            self.data_dict['Time'] = np.append(self.data_dict['Time'], time() - self.initial_time)

            for quantity, name in zip(self.instr_list[2],self.instr_list[3]):

                if quantity == 'Temperature':
                    self.data_log_dict[name] = self.instruments[name].get_kelvin_reading(1)
                    self.data_dict[name] = np.append(self.data_dict[name], self.data_log_dict[name])

                if quantity == 'X value':
                    self.data_log_dict[name] = self.instruments[name].get_X()
                    self.data_dict[name] = np.append(self.data_dict[name], self.data_log_dict[name])

                if quantity == 'Y value':
                    self.data_log_dict[name] = self.instruments[name].get_Y()
                    self.data_dict[name] = np.append(self.data_dict[name], self.data_log_dict[name])

                if quantity == 'R value':
                    self.data_log_dict[name] = self.instruments[name].get_R()
                    self.data_dict[name] = np.append(self.data_dict[name], self.data_log_dict[name])

                if quantity == 'Theta':
                    self.data_log_dict[name] = self.instruments[name].get_Theta()
                    self.data_dict[name] = np.append(self.data_dict[name], self.data_log_dict[name])

                if quantity == 'Random 1':
                    self.data_log_dict[name] = self.instruments[name].randint(0,100)
                    self.data_dict[name] = np.append(self.data_dict[name], self.data_log_dict[name])

                if quantity == 'Random 2':
                    self.data_log_dict[name] = self.instruments[name].randint(0,100)
                    self.data_dict[name] = np.append(self.data_dict[name], self.data_log_dict[name])

                if quantity == 'Random 3':
                    self.data_log_dict[name] = self.instruments[name].randint(0,100)
                    self.data_dict[name] = np.append(self.data_dict[name], self.data_log_dict[name])

                if quantity == 'Random 4':
                    self.data_log_dict[name] = self.instruments[name].randint(0,100)
                    self.data_dict[name] = np.append(self.data_dict[name], self.data_log_dict[name])


            if self.log_saving_checkbox == True:
                values = np.array(list(self.data_log_dict.values()))
                flattened_values = values.flatten()
                with open(self.data_file, 'a') as file:
                    np.savetxt(file, [flattened_values], delimiter = ',')
                file.close()

            sleep(1)

    def start_logging(self):
        self.keep_running = True
        self.clear_log()
        self.log_thread = threading.Thread(target=self.get_log_values)
        self.log_thread.start()


    def stop_logging(self):
        self.keep_running = False

    def clear_log(self):
        self.temperature_log = np.empty(0)
        self.data_log = np.empty(0)
        self.exptime = np.empty(0)
        self.initial_time = time()

    def start_ramp(self):
        self.tempctrl.set_control_setpoint(1, self.config['Ramp']['ramp_start_T'])
        sleep(2)
        self.tempctrl.set_setpoint_ramp_parameter(1, ramp_enable=True, rate_value=self.config['Ramp']['ramp_speed'])
        sleep(2)
        self.tempctrl.set_control_setpoint(1, self.config['Ramp']['ramp_end_T'])

        while self.tempctrl.get_setpoint_ramp_status(1) == True:
            sleep(5)
            print('still ramping')

        print('ramp done')

#   Data saving
        
    def save_data(self):

        #data_folder = self.config['Saving']['log_path']
        #today_folder = f'{datetime.today():%Y-%m-%d}'
        #saving_folder = os.path.join(data_folder, today_folder)
        #if not os.path.isdir(saving_folder):
        #    os.makedirs(saving_folder)


        keys = list(self.data_log_dict.keys())

        #data = np.vstack(keys)

        filename = self.config['Saving']['log_path']
        base_name = filename.split('.')[0]
        ext = filename.split('.')[-1]
        i = 1
        while os.path.isfile(f'{base_name}_{i:04d}.{ext}'):
            i += 1

        self.data_file = f'{base_name}_{i:04d}.{ext}'
        # metadata_file = os.path.join(saving_folder, f'{base_name}_{i:04d}_metadata.yml')
        with open(self.data_file, 'w') as f:
            f.write(','.join(keys) + '\n')
        f.close()
        #np.savetxt(self.data_file, data)
        # with open(metadata_file, 'w') as f:
        #     f.write(yaml.dump(self.config, default_flow_style=False))

# Need a method to save the log file. Clear log should not stop or reset the saving (mostly not reset time to zero)
# Stop log should stop the saving (same is_running?), but not reset it.
# Needs to append to a file
# With Numpy --> create the files first, then open them, then append using savetxt


#   Lakeshore queries:

   

#   SR830 queries
        
""" def get_output(self)
    self.data = self.lockin.get_X()
    #get data from the SR830, getting X, Y, R, theta is just a "channel" number, from 1 to 4 in the driver. """

""" def set_output_V(self, output):
        return """
    
"""  def set_output_frequency(self, frequency):
        return """
    

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