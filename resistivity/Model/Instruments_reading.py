from resistivity.Driver.temperature_controllers import TemperatureController
from resistivity.Driver import SR830
from resistivity.Driver.MCLpy.MCL import MCL



# Class of the SynkTek lock-in Amplifier

class SynkTek:

    def __init__(self,address):
        self.mcl = MCL()
        self.mcl.connect(address)
        self.values_dict = {'A-V1':0, 'A-V2':1, 'B-V1':2, 'B-V2':3, 'C-V1':4, 'C-V2':5, 'D-V1':6, 'D-V2':7, 'E-V1':8, 'E-V2':9, 'A-I':10}
        
        return
    
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
        return
    def get_values(self):
        return




class LakeShore350:
    def __init__(self, address):
        #load
        #self.ls350 = TemperatureController(ip_address=address, tcp_port=7777, timeout=1000)
        return

    def get_all_values(self):
        return




class PPMS:
    def __init__(self,address):
        #load the PPMS
        return