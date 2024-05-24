from resistivity.Driver.temperature_controllers import TemperatureController
from resistivity.Driver import SR830
from resistivity.Driver.MCLpy.MCL import MCL
import random


# Class of the SynkTek lock-in Amplifier

class SynkTek:

    def __init__(self,address):
        self.mcl = MCL()
        self.mcl.connect(address)
        self.values_dict = {'A-V1':0, 'A-V2':1, 'B-V1':2, 'B-V2':3, 'C-V1':4, 'C-V2':5, 'D-V1':6, 'D-V2':7, 'E-V1':8, 'E-V2':9, 'A-I':10}
    
    def get_all_values(self):
        values = self.mcl.data.L1.val
        self.dc = values[2]
        self.x = values[3]
        self.y = values[4]
        self.r = values[5]
        self.theta = values[6]
        self.output = [values[1][0][1], values[1][0][2]]

    def test(self, channel):
        print(channel)
    
    def get_values(self, channel):
        self.get_all_values()
        if channel == 'Output':
            values = {'Freq': self.output[0],
                      'Amp': self.output[1]}
        else:
            values = {'DC': self.dc[self.values_dict[channel]],
                      'X': self.x[self.values_dict[channel]],
                      'Y': self.y[self.values_dict[channel]],
                      'R': self.r[self.values_dict[channel]],
                      'theta': self.theta[self.values_dict[channel]]}
        
        return values
    
    
class lockin_SR830:
    def __init__(self, address):
        #load that shit up
        self.sr830 = SR830.device(address)

    def get_values(self, channel):
        values = {'X': self.sr830.get_X,
                  'Y': self.sr830.get_Y,
                  'R': self.sr830.get_R,
                  'theta': self.sr830.get_Theta}
        return values




class LakeShore350:
    def __init__(self, address=None, tcp_port=None, timeout=None):
        #load
        self.ls350 = TemperatureController(ip_address=address, tcp_port=7777, timeout=1000)
        self.channel_dict = {'A': 1, 'B': 2, 'C': 3, 'D': 4}


    def get_values(self, channel):
        values = {'Temperature': self.ls350.get_kelvin_reading(self.channel_dict[channel]),
                  'Power': self.ls350.get_heater_output(self.channel_dict[channel])}
        
        return values


class Random_int:
    def __init__(self, address):
        self.rand = random
        
    
    def get_values(self, channel):
        values = {'Rand_1': self.rand.randint(1,100),
                  'Rand_2': self.rand.randint(50,150),
                  'Rand_3': self.rand.randint(100,200),
                  'Rand_4': self.rand.randint(150,250)}
        return values


class PPMS:
    def __init__(self,address):
        #load the PPMS
        return