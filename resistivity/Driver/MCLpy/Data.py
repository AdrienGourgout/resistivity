from resistivity.Driver.MCLpy.DataClasses import *
from resistivity.Driver.MCLpy.ReadWriteValues import *

__all__ = ['Data']


class Data(object):

    def __init__(self):
        self.L1 = LockInData(0)
        self.L2 = LockInData(1)
        self.scope = Scope()
        self.fft = FFT()

    @property
    def children(self):
        return ReadOnlyParameter.instances
