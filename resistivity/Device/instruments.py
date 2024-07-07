from time import sleep

class Instrument:
    """API for all the instruments"""
    channel_dict = {} # this are class attributes, accessible without declaring the object
    quantities = []

    def __init__(self, address):
        self.address = address
        pass

    def get_values(self, channel):
        pass

    def initialize(self):
        pass

    def finalize(self):
        pass


class SynkTek(Instrument):
    channel_dict = {'A-V1':0, 'A-V2':1, 'B-V1':2, 'B-V2':3, 'C-V1':4,
                'C-V2':5, 'D-V1':6, 'D-V2':7, 'E-V1':8, 'E-V2':9, 'A-I':10}
    quantities = ["R", "theta", "X", "Y", "DC"]
    communicating = False
    from .MCLpy.MCL import MCL
    mcl = MCL()

    def __init__(self, address):
        self.address = address

    def initialize(self):
        if not SynkTek.communicating:
            self.mcl.connect(self.address)
            SynkTek.communicating = True

    def finalize(self):
        if SynkTek.communicating:
            self.mcl.disconnect()
            SynkTek.communicating = False

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

    def switch_source(self, state):
        self.mcl.config.output_A.outputenabled = state


class LockinSR830(Instrument):
    channel_dict = {}
    quantities = ["R", "theta", "X", "Y"]

    def __init__(self, address):
        self.address = address
        self.sr830 = None

    def initialize(self):
        from .SR830 import SR830
        self.sr830 = SR830.device(self.address)

    def finalize(self):
        self.sr830.rm.close()
        self.sr830 = None

    def get_values(self, channel):
        values = {'X': self.sr830.get_X(),
                  'Y': self.sr830.get_Y(),
                  'R': self.sr830.get_R(),
                  'theta': self.sr830.get_Theta()
                  }
        return values


class LakeShore350(Instrument):
    channel_dict = {'A': 1, 'B': 2, 'C': 3, 'D': 4}
    quantities = ["Temperature", "Power"]

    def __init__(self, address):
        self.address = address
        self.ls350 = None

    def initialize(self):
        from .LakeShore350 import temperature_controllers
        self.ls350 = temperature_controllers.TemperatureController(ip_address=self.address, tcp_port=7777, timeout=1000)

    def finalize(self):
        del self.ls350 # that shuts down the communication
        self.ls350 = None

    def get_values(self, channel):
        values = {'Temperature': self.ls350.get_kelvin_reading(self.channel_dict[channel]),
                  'Power': self.ls350.get_heater_output(self.channel_dict[channel])}
        return values


class RandomInt(Instrument):
    channel_dict = {}
    quantities = ["Rand1", "Rand2", "Rand3", "Rand4"]
    def __init__(self, address):
        import random
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

    communicating = False

    import platform
    if platform.system() == 'Windows':
        from MultiPyVu import Server, Client
        ppms_server = Server(port=6000)
        ppms_client = Client(port=6000)

    def __init__(self, address):
        self.address = int(address)
        if self.address != 6000:
            print("The port needs to be 6000 at ESPCI")
            self.ppms_server.port = address


    def initialize(self):
        if not PPMS.communicating:
            self.ppms_server.open()
            self.ppms_client.open()
            PPMS.communicating = True
            #self.ppms_client.log_event.shutdown() # turn off logging
            self.ppms_client.log_event.remove()

    def finalize(self):
        if PPMS.communicating:
            self.ppms_client.close_client()
            self.ppms_server.close()
            PPMS.communicating = False

    def get_values(self, channel):
        self.ppms_client.log_event.remove()
        temperature, status_temperature = self.ppms_client.get_temperature()
        sleep(0.5)
        field, status_field = self.ppms_client.get_field()
        if status_temperature == 'Stable':
            status_temperature = 1
        else:
            status_temperature = 0
        values = {'Temperature': temperature,
                  'StatusTemperature': status_temperature,
                  'Field': field,
                  'StatusField': status_field}
        return values

    def set_temp(self, temperature, rate):
        self.ppms_client.set_temperature(temperature, rate, self.ppms_client.temperature.approach_mode.fast_settle)


