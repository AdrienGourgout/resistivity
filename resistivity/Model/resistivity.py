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
        self.instr_list = [[],[]]
        self.instruments = {}
        # load config file with yaml

    def load_config(self):
        with open(self.config_file, 'r') as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
        self.config = data

    def load_instruments(self):
        if self.instr_list == [[],[]]:
            print('Nothing to load')
        else:
            i = 1
            j = 1
            for instr, address in zip(self.instr_list[0], self.instr_list[1]):
                if instr == 'Lakeshore 350':
                    name = 'tempctrl_' + str(i)
                    temp = TemperatureController(serial_number=None, com_port=None, baud_rate=None, timeout=self.config['LS350']['timeout'], ip_address=address, tcp_port=self.config['LS350']['tcp_port'])
                    new_instr = {name: temp}
                    self.instruments.update(new_instr)
                    i = i+1
                if instr == 'Lock-in SR830':
                    name = 'lockin_' + str(j)
                    temp = device(address)
                    new_instr = {name: temp}
                    self.instruments.update(new_instr)
                    j = j+1
            print('All instruments loaded succesfully')
        
    

#       Logs
        

    def get_log_values(self):
        if self.log_saving_checkbox == True:
            self.temp = self.instruments['tempctrl_1'].get_kelvin_reading(1)
            #self.temp = random.randint(0,100)
            self.voltage = self.instruments['lockin_1'].get_X()
            #self.voltage = random.randint(0,100)
            self.t = time()-self.initial_time
            self.save_data()

        while self.keep_running == True:

            self.temp = self.instruments['tempctrl_1'].get_kelvin_reading(1)
            #self.temp = random.randint(0,100)
            self.voltage = self.instruments['lockin_1'].get_X()
            #self.voltage = random.randint(0,100)
            self.t = time()-self.initial_time

            self.temperature_log = np.append(self.temperature_log, self.temp, axis=None)
            self.data_log = np.append(self.data_log, self.voltage, axis=None)
            self.exptime = np.append(self.exptime, self.t, axis=None)

            if self.log_saving_checkbox == True:
                data = np.vstack([self.t, self.temp, self.voltage]).T
                with open(self.data_file, 'a') as file:
                    np.savetxt(file, data)
            
            self.data_list = [self.exptime, self.temperature_log, self.data_log]

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

        data_folder = self.config['Saving']['folder']
        today_folder = f'{datetime.today():%Y-%m-%d}'
        saving_folder = os.path.join(data_folder, today_folder)
        if not os.path.isdir(saving_folder):
            os.makedirs(saving_folder)

        data = np.vstack([self.t, self.temp, self.voltage]).T
        header = "time in s, Temperature in V"

        filename = self.config['Saving']['logname']
        base_name = filename.split('.')[0]
        ext = filename.split('.')[-1]
        i = 1
        while os.path.isfile(os.path.join(saving_folder,f'{base_name}_{i:04d}.{ext}')):
            i += 1

        self.data_file = os.path.join(saving_folder, f'{base_name}_{i:04d}.{ext}')
        # metadata_file = os.path.join(saving_folder, f'{base_name}_{i:04d}_metadata.yml')
        np.savetxt(self.data_file, data, header=header)
        # with open(metadata_file, 'w') as f:
        #     f.write(yaml.dump(self.config, default_flow_style=False))

# Need a method to save the log file. Clear log should not stop or reset the saving (mostly not reset time to zero)
# Stop log should stop the saving (same is_running?), but not reset it.
# Needs to append to a file
# With Numpy --> create the files first, then open them, then append using savetxt


#   Lakeshore queries:

    """ def get_temperature_log(self, channel):     
        self.temperature_log = self.tempctrl.get_kelvin_reading(channel)
        # query temperature value
        # store it
        return """
    
    """ def get_heater_power(self, channel):
        # query heater power value
        # store it
        return """
    
    """ def change_temperature(self, temperature):
        # turn off ramp if activated
        # set temperature
        # wait till stable --> Set stability condition?
        return """
    
    """ def ramp_temperature(self, channel, temperature, ramp_speed):
        # turn on ramp if off
        # set ramp speed
        # set temperature to target
        # loop until target is reached --> stable at target?
        return """
    
    """ def temperature_stable(self, channel)
        #Check if temperature is stable
        return """


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