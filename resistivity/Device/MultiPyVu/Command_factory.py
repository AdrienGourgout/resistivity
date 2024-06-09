'''
Command_factory.py is used to instantiate the 'real' or
simulated ICommand class.
'''

from typing import Union

from .CommandMultiVu_imp import CommandMultiVuImp
from .CommandMultiVu_sim import CommandMultiVuSim
from . import CommandTemperature as temperature
from . import CommandField as field
from . import CommandChamber as chamber
from . import CommandSdo as sdo


def create_command_mv(mvu_flavor, win32_dispatch=None):
    '''
    Create a CommandMultiVu Object

    Parameters:
    -----------
    mvu_flavor: str
        The name of the MultiVu flavor
    win32_dispatch (optional): win32com.client.CDispatch or None
        This is the object used to communicate with MultiVu.
        Default is None, which will load CommandMultiVuSim

    Returns:
    --------
    A CommandMultiVu object.  If win32_dispatch is None, it returns
    a simulated object.
    '''
    cmd_dict = {'TEMP': create_command_temp(win32_dispatch),
                'FIELD': create_command_field(win32_dispatch, mvu_flavor),
                'CHAMBER': create_command_chamber(win32_dispatch, mvu_flavor),
                'SDO': create_command_sdo(win32_dispatch),
                }
    if win32_dispatch is None:
        return CommandMultiVuSim(cmd_dict)
    else:
        return CommandMultiVuImp(cmd_dict)


def create_command_temp(
        win32_dispatch=None
        ) -> Union[temperature.CommandTemperatureSim,
                   temperature.CommandTemperatureImp]:
    '''
    Create a CommandTemperature object

    Parameters:
    -----------
    win32_dispatch (optional): win32com.client.CDispatch or None
        This is the object used to communicate with MultiVu.
        Default is None, which will load CommandTemperatureSim

    Returns:
    --------
    CommandTemperature object
    '''
    if win32_dispatch is None:
        return temperature.CommandTemperatureSim()
    else:
        return temperature.CommandTemperatureImp(win32_dispatch)


def create_command_field(
        win32_dispatch=None,
        mvu_flavor=''
        ) -> Union[field.CommandFieldSim,
                   field.CommandFieldImp]:
    '''
    Create a CommandField object

    Parameters:
    -----------
    win32_dispatch (optional): win32com.client.CDispatch or None
        This is the object used to communicate with MultiVu.
        Default is None, which will load CommandFieldSim

    Returns:
    --------
    CommandField object
    '''
    if win32_dispatch is None:
        return field.CommandFieldSim(mvu_flavor)
    else:
        return field.CommandFieldImp(win32_dispatch, mvu_flavor)


def create_command_chamber(
        win32_dispatch=None,
        mvu_flavor=''
        ) -> Union[chamber.CommandChamberSim,
                   chamber.CommandChamberImp]:
    '''
    Create a CommandChamber object

    Parameters:
    -----------
    win32_dispatch (optional): win32com.client.CDispatch or None
        This is the object used to communicate with MultiVu.
        Default is None, which will load CommandChamberSim

    Returns:
    --------
    CommandChamber object
    '''
    if win32_dispatch is None:
        return chamber.CommandChamberSim(mvu_flavor)
    else:
        return chamber.CommandChamberImp(win32_dispatch, mvu_flavor)


def create_command_sdo(
        win32_dispatch=None
        ) -> Union[sdo.CommandSdoSim,
                   sdo.CommandSdoImp]:
    '''
    Create a CommandSdo object

    Parameters:
    -----------
    win32_dispatch (optional): win32com.client.CDispatch or None
        This is the object used to communicate with MultiVu.
        Default is None, which will load CommandSdoSim

    Returns:
    --------
    CommandSdo object
    '''
    if win32_dispatch is None:
        return sdo.CommandSdoSim()
    else:
        return sdo.CommandSdoImp(win32_dispatch)
