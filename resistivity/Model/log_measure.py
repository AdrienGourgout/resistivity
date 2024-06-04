from time import sleep
import resistivity.Model.Instruments_reading as instruments
import numpy as np
import threading
import os
import yaml
import inspect


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
        self.SkT = None # fake variable for SynkTek to avoid to reload it several times
        # Get the names of all the classes of instruments in this module
        self.instruments_names = [name for name, obj in inspect.getmembers(instruments) if isinstance(obj, type)]

    def load_config(self):
        with open(self.config_file, 'r') as f:
            self.config_dict = yaml.load(f, Loader=yaml.FullLoader)

    def load_instruments(self):
        for data_label in self.config_dict["Measurements"].keys():
            instrument  = self.config_dict["Measurements"][data_label]["instrument"]
            address   = self.config_dict["Measurements"][data_label]["address"]
            quantities = self.config_dict["Measurements"][data_label]["quantities"]
            self.add_instrument(data_label, instrument, address, quantities)

    def add_instrument(self, data_label=None, instrument=None, address=None, quantities=None):
        """
        - data_label: the label of the measured data: T0, VS, etc.
        - instrument: a string that defines the type of instrument: LockinSR830, SynkTek, etc.
        - address: a string for the address
        - quantities: a list of strings with the channels and quantities to measure
        for example: ["Temperature_A", "Temperature_B"] for a LakeShore350, or
        ["A-V1_L1_X", "B-V1_L2_Y"] for a SynkTek
        """
        # Select the class whose name corresponds to the instrument "instrument"
        # in the module instruments
        InstrumentClass = getattr(instruments, instrument)
        inst = InstrumentClass(address=address)
        self.instruments_query[data_label] = inst.get_values
        ## Add entry to the data dictionnary
        for quantity in quantities:
            label = data_label + '_' + quantity.split("_")[-1]
            self.data_dict[label] = np.empty(0)


    def delete_instrument(self, data_label=None):
        #Delete entries from instruments and data dictionnaries
        del self.config_dict["Measurements"][data_label]


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
                    if full_label in self.data_dict:
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




