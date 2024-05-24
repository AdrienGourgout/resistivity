from time import sleep, time
#from resistivity.Driver import SR830
#from resistivity.Driver.temperature_controllers import TemperatureController
#from MCLpy.MCL.MCL import MCL
from resistivity.Model.Instruments_reading import *
import numpy as np
import threading
import os
import random
import yaml
from functools import partial



class LogMeasure:
    def __init__ (self, config_file):
        self.config_file     = config_file
        self.config_dict     = {}
        self.keep_running    = False
        self.saving          = False
        self.instruments_query = {}
        self.time_steps      = 0.5 # seconds
        ## Dictionnary for the data
        self.data_dict = {}
        self.data_dict['Time'] = np.empty(0)
        self.SkT = None


    def load_config(self):
        with open(self.config_file, 'r') as f:
            self.config_dict = yaml.load(f, Loader=yaml.FullLoader)

    def load_instruments(self):
        for label in self.config_dict["Measurements"].keys():
            inst  = self.config_dict["Measurements"][label]["instrument"]
            adr   = self.config_dict["Measurements"][label]["address"]
            channel = self.config_dict["Measurements"][label]["channel"]
            quantities = self.config_dict["Measurements"][label]["quantities"]
            self.add_instrument(instrument=inst, address=adr, channel=channel, data_label=label, quantities=quantities)

    def ls350_methods(self, instr=None, quantity=None):
        if quantity == 'Temperature_A':
            return partial(instr.get_kelvin_reading, input_channel=1)
        if quantity == 'Temperature_B':
            return partial(instr.get_kelvin_reading, input_channel=2)
        if quantity == 'Temperature_C':
            return partial(instr.get_kelvin_reading, input_channel=3)
        if quantity == 'Temperature_D':
            return partial(instr.get_kelvin_reading, input_channel=4)

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
            return partial(instr.randint, 1, 100)
        if quantity == 'Random_2':
            return partial(instr.randint, 1, 100)
        if quantity == 'Random_3':
            return partial(instr.randint, 1, 100)


    def add_instrument(self, instrument=None, address=None, channel=None, data_label=None, quantities=None):
        """instrument is a string that defines the type of instrument: LS350
        address is a string for the adress
        quantity is a string that tells if it is: X, Y, Temperature_A, etc.
        data_label is the label of the measured stuff: XX, T0, etc."""
        if instrument == 'LS350':
            temp = TemperatureController(ip_address=address, tcp_port=7777,timeout=1000)
            instr = self.ls350_methods(temp, channel)
            self.instruments_query[data_label] = instr
        if instrument == 'SR830':
            temp = SR830.device(address)
            instr = self.sr830_methods(temp, channel)
            self.instruments_query[data_label] = instr
        if instrument == 'Random':
            temp = random
            instr = self.random_methods(temp, channel)
            self.instruments_query[data_label] = instr

        if instrument == "SynkTek":
            if self.SkT == None:
                self.SkT = SynkTek(address)
            self.instruments_query[data_label] = self.SkT.get_values
            
        ## Add entry to the data dictionnary
        for quantity in quantities.keys():
            label = data_label + '_' + quantity
            self.data_dict[label] = np.empty(0)


        ## Add entry to the config dictionnary
        # if self.config_dict["Measurements"].get(data_label) == None:
        #     self.config_dict["Measurements"][data_label] = {}
        #     self.config_dict["Measurements"][data_label]["instrument"] = instrument
        #     self.config_dict["Measurements"][data_label]["address"] = address
        #     self.config_dict["Measurements"][data_label]["channel"] = channel
        #     self.config_dict["Measurements"][data_label]["quantities"] = quantities
        ## Clear all values from the data dictionnary
        self.clear_data()


    def delete_instrument(self, data_label=None):
        #Delete entries from instruments and data dictionnaries
        del self.config_dict["Measurements"][data_label]
        # del self.instruments_query[data_label]
        # del self.data_dict[data_label]

    def get_values(self):
        while self.keep_running:
            # Time
            current_time = self.data_dict['Time'][-1] + self.time_steps if self.data_dict['Time'].size else 0 # be zero for the first point
            self.data_dict['Time'] = np.append(self.data_dict['Time'], current_time)
            # Data
            for data_label, data_function in self.instruments_query.items():
                value = data_function(self.config_dict["Measurements"][data_label]["channel"])
                for label in value.keys():
                    full_label = data_label + '_' + label
                    self.data_dict[full_label] = np.append(self.data_dict[full_label], value[label])
            # Save log if saving is enabled
            if self.saving:
                self.save_log()
            ## Sets how long each steps takes
            sleep(self.time_steps)


    def save_log(self):
        if self.keep_running:
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
        self.log_thread = threading.Thread(target=self.get_values)
        self.log_thread.start()

    def stop_logging(self):
        self.keep_running = False

    def clear_data(self):
        for keys in self.data_dict:
            self.data_dict[keys] = np.empty(0)



if __name__ == "__main__":
    log = LogMeasure('../Example/Config.yml')
    log.load_config()
    log.load_instruments()

    log.start_logging()
    print(log.data_dict)
    sleep(10)
    print(log.data_dict)
    log.stop_logging()

        


