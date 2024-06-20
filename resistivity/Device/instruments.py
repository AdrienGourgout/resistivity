from resistivity.Device import temperature_controllers
from resistivity.Device import SR830
from .MCLpy.MCL import MCL
import MultiPyVu as mpv
import random


class Instrument:
    """API for all the instruments"""
    channel_dict = {} # this are class attributes, accessible without declaring the object
    quantities = []

    def __init__(self, address):
        self.address = address
        pass

    def get_values(self, channel):
        pass


class SynkTek(Instrument):
    channel_dict = {'A-V1':0, 'A-V2':1, 'B-V1':2, 'B-V2':3, 'C-V1':4,
                'C-V2':5, 'D-V1':6, 'D-V2':7, 'E-V1':8, 'E-V2':9, 'A-I':10}
    quantities = ["R", "theta", "X", "Y", "DC"]
    _is_first_instance = True
    mcl = MCL()

    def __init__(self, address):
        self.address = address
        if SynkTek._is_first_instance:
            print(SynkTek._is_first_instance)
            self.mcl.connect(address)
            SynkTek._is_first_instance = False

    def get_values(self, channel):
        # channel = channel.split("_")[0]
        lockin = "L1" #channel.split("_")[-1]
        ## Choose the right lockin
        if "L1" in lockin:
            values = self.mcl.data.L1
        elif "L2" in lockin:
            values = self.mcl.data.L2
        else:
            print("You defined a lockin L that does not exist")
        ## Choose the variables to save
        # if channel == 'Output':
        #     values = {'Freq': self.values.lock_in_frequency,
        #               'Amp': self.values.output_amplitude}
        # else:
        values = {'R': values.r[self.channel_dict[channel]],
                  'theta': values.theta[self.channel_dict[channel]],
                  'X': values.x[self.channel_dict[channel]],
                  'Y': values.y[self.channel_dict[channel]],
                  'DC': values.dc[self.channel_dict[channel]]
                  }
        return values


class LockinSR830(Instrument):
    channel_dict = {}
    quantities = ["R", "theta", "X", "Y"]

    def __init__(self, address):
        self.address = address
        self.sr830 = SR830.device(address)

    def get_values(self, channel):
        values = {'X': self.sr830.get_X,
                  'Y': self.sr830.get_Y,
                  'R': self.sr830.get_R,
                  'theta': self.sr830.get_Theta}
        return values


class LakeShore350(Instrument):
    channel_dict = {'A': 1, 'B': 2, 'C': 3, 'D': 4}
    quantities = ["Temperature", "Power"]

    def __init__(self, address):
        self.address = address
        self.ls350 = temperature_controllers.TemperatureController(ip_address=address, tcp_port=7777, timeout=1000)

    def get_values(self, channel):
        values = {'Temperature': self.ls350.get_kelvin_reading(self.channel_dict[channel]),
                  'Power': self.ls350.get_heater_output(self.channel_dict[channel])}
        return values


class RandomInt(Instrument):
    channel_dict = {}
    quantities = ["Rand1", "Rand2", "Rand3", "Rand4"]
    def __init__(self, address):
        self.address = address
        self.rand = random

    def get_values(self, channel):
        values = {'Rand1': self.rand.randint(1,100),
                  'Rand2': self.rand.randint(50,150),
                  'Rand3': self.rand.randint(100,200),
                  'Rand4': self.rand.randint(150,250)}
        return values


class Constant(Instrument):
    """The address will be used a constant value to save in one column"""
    channel_dict = {}
    quantities = ["Value"]

    def __init__(self, address):
        self.address = address

    def get_values(self, channel):
        values = {'Value': float(self.address)}
        return values


class PPMS(Instrument):
    channel_dict = {}
    quantities = ['Temperature','Field']
    def __init__(self, address):
        """
        The port the works on the ESPCI PPMS is port = 6000
        """
        address = int(address)
        self.ppms_server = mpv.Server(port=address)
        self.ppms_client = mpv.Client(port=address)
        self.ppms_server.open()
        self.ppms_client.open()

    def get_values(self, channel):
        temperature, status = self.ppms_client.get_temperature()
        field, status = self.ppms_client.get_field()
        values = {'Temperature': temperature,
                  'Field': field}
        return values

if __name__ == "__main__":

    from time import sleep
    test = PPMS(6000)
    for _ in range(5):
        sleep(0.5)
        print(test.get_values(''))

