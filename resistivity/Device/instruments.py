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
    _is_first_instance = True
    from .MCLpy.MCL import MCL
    mcl = MCL()

    def __init__(self, address):
        self.address = address
        if SynkTek._is_first_instance:
            SynkTek._is_first_instance = False

    def initialize(self):
        self.mcl.connect(self.address)

    def finalize(self):
        self.mcl.disconnect()

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
        self.sr830 = None

    def initialize(self):
        from .SR830 import SR830
        self.sr830 = SR830.device(self.address)

    def finalize(self):
        self.sr830.rm.close()
        self.sr830 = None

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

    _is_first_instance = True

    import platform
    if platform.system() == 'Windows':
        from .MultiPyVu import Server, Client
        ppms_server = Server(port=6000)
        ppms_client = Client(port=6000)

    def __init__(self, address):
        self.address = int(address)
        if self.address != 6000:
            print("The port needs to be 6000 at ESPCI")
            self.ppms_server.port = address
        if PPMS._is_first_instance:
            PPMS._is_first_instance = False

    def __init__(self, address):
        """
        The port the works on the ESPCI PPMS is port = 6000
        """
        self.address = int(address)

    def initialize(self):
        self.ppms_server.open()
        self.ppms_client.open()

    def finalize(self):
        self.ppms_server.close()
        self.ppms_client.close()

    def get_values(self, channel):
        temperature, status = self.ppms_client.get_temperature()
        field, status = self.ppms_client.get_field()
        values = {'Temperature': temperature,
                  'Field': field}
        return values



