from resistivity.Driver.temperature_controllers import TemperatureController
from resistivity.Driver import SR830
from resistivity.Driver.MCLpy.MCL import MCL
import random

class Instrument:
    """API for all the instruments"""
    def __init__(self, address):
        self.address = address
        pass

    def get_values(self, channel):
        pass

class SynkTek(Instrument):
    def __init__(self, address):
        self.address = address
        self.mcl = MCL()
        self.mcl.connect(address)
        self.channel_labels_dict = {'A-V1':0, 'A-V2':1, 'B-V1':2, 'B-V2':3, 'C-V1':4, 'C-V2':5, 'D-V1':6, 'D-V2':7, 'E-V1':8, 'E-V2':9, 'A-I':10}

    def get_values(self, channel):
        channel = channel.split("_")[0]
        lockin = channel.split("_")[-1]
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
        values = {'DC': values.dc[self.channel_labels_dict[channel]],
                  'X': values.x[self.channel_labels_dict[channel]],
                  'Y': values.y[self.channel_labels_dict[channel]],
                  'R': values.r[self.channel_labels_dict[channel]],
                  'theta': values.theta[self.channel_labels_dict[channel]]
                  }
        return values


class LockinSR830(Instrument):
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
    def __init__(self, address):
        self.address = address
        self.ls350 = TemperatureController(ip_address=address, tcp_port=7777, timeout=1000)
        self.channel_dict = {'A': 1, 'B': 2, 'C': 3, 'D': 4}

    def get_values(self, channel):
        values = {'Temperature': self.ls350.get_kelvin_reading(self.channel_dict[channel]),
                  'Power': self.ls350.get_heater_output(self.channel_dict[channel])}
        return values


class RandomInt(Instrument):
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
    def __init__(self, address):
        self.address = address
        self.values = None

    def get_values(self, channel):
        values = {'value': float(self.address)}
        return values


class PPMS(Instrument):
    def __init__(self, address):
        pass

    def get_values(self, channel):
        pass