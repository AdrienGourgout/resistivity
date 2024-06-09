from resistivity.Device.MCLpy.ReadWriteValues import ReadOnlyParameter, ReadWriteParameter
import struct
from collections import namedtuple

__all__ = ['Enumerators', 'LockInControl', 'InputSettings', 'OutputSettings', 'Frequency', 'PhaseLockedLoop', 'General',
           'GeneralPICControl', 'OutputState', 'InputState', 'Offset', 'Feedback', 'Amplitude',
           'Function', 'PhaseShift', 'DutyCycle', 'Scope', 'MultiHarm', 'Composite']

class Enumerators():
    def __init__(self):
        pass

    def Frequency(self):
       return ['Frequency 1', 'Frequency 2', 'Frequency 3', 'Frequency 4', 'Frequency 5',
                              'Frequency 6 PLL', 'Frequency 7 PLL', 'Frequency 8 Comp1']
    def FunctionType(self):
        return ['Sine', 'Square', 'Boxcar']

    def Phase_(self):
        return ['Phase 1', 'Phase 2', 'Phase 3', 'Phase 4', 'Phase 5', 'Phase 6', 'Phase 7', 'Inactive']

    def DutyCycle(self):
        return ['Duty Cycle 1', 'Duty Cycle 2', 'Duty Cycle 3', 'Duty Cycle 4', 'Duty Cycle 5',
                               'Duty Cycle 6', 'Duty Cycle 7', 'Inactive']


class LockInControl(ReadWriteParameter):
    def __init__(self, lock_in_set, my_queue):
        super().__init__(my_queue, 'mcl_config_frequencyctrl',
                         ['frequency_generator', 'time_constant', 'filter_enable', 'stage1_tc', 'stage2_tc',
                          'harmonic', 'wave_type', 'phase_shift', 'duty_cycle'],
                         ['', 1, '', '', '', float("NaN"), False, float("NaN"), float("NaN")],
                         '>Bd?2dH3B',
                         2,
                         6 + lock_in_set)
        self._frequency_enumerator = ['Frequency 1', 'Frequency 2', 'Frequency 3', 'Frequency 4', 'Frequency 5',
                                      'Frequency 6 PLL', 'Frequency 7 PLL', 'Frequency 8 Comp1']
        self._type_enumerator = ['Sine', 'Square', 'Boxcar']
        self._phase_enumerator = ['Phase 1', 'Phase 2', 'Phase 3', 'Phase 4', 'Phase 5', 'Phase 6', 'Phase 7',
                                  'Inactive']
        self._duty_cycle_enumerator = ['Duty Cycle 1', 'Duty Cycle 2', 'Duty Cycle 3', 'Duty Cycle 4', 'Duty Cycle 5',
                                       'Duty Cycle 6', 'Duty Cycle 7', 'Inactive']

    @property
    def frequency_generator(self):
        return self._frequency_enumerator[self.val.frequency_generator]

    @frequency_generator.setter
    def frequency_generator(self, frequency):
        """
        Set the frequency object to use
        Parameters
        ----------
        frequency : str or int
            string for frequency from ['Frequency 1', 'Frequency 2', 'Frequency 3', 'Frequency 4', 'Frequency 5',
                            'Frequency 6 PLL', 'Frequency 7 PLL', 'Frequency 8 Comp1']
        Returns
        -------

        """
        if isinstance(frequency, int):
            if 1 <= frequency <= 8:
                self.val = self.val._replace(frequency_generator=frequency - 1)
            else:
                raise ValueError('Failed to set the new frequency generator. Frequency must be between 1 and 8.')
        elif isinstance(frequency, str):
            try:
                self.val = self.val._replace(frequency_generator=self._frequency_enumerator.index(frequency))
            except:
                print('Failed to set the new frequency generator. String not valid: ', frequency)
                return
        else:
            raise TypeError('Failed to set the new frequency generator. Expecting integer or string.')

    @property
    def harmonic(self):
        return self.val.harmonic

    @harmonic.setter
    def harmonic(self, new_harmonic):
        """
        Set the harmonic to use for the demodulation
        Parameters
        ----------
        harmonic : int
            integer between 1 and 65535
        Returns
        -------

        """
        if type(new_harmonic) is int and 0 < new_harmonic < 65536:
            self.val = self.val._replace(harmonic=new_harmonic)
        else:
            raise ValueError('Failed to set new harmonic. Must be UInt16 > 0')

    @property
    def time_constant(self):
        return self.val.time_constant

    @time_constant.setter
    def time_constant(self, new_value):
        """
        Set the time constant
        Parameters
        ----------
        new_value : float
            new time constant in seconds. There are only certain possible values?

        Returns
        -------

        """
        if type(new_value) is float and new_value > 0:
            self.val = self.val._replace(time_constant=new_value)
        else:
            raise ValueError('Failed to set time constant. Must be float > 0')

    @property
    def filter_enabled(self):
        return self.val.filter_enable

    @filter_enabled.setter
    def filter_enabled(self, enable):
        if type(enable) is bool:
            self.val = self.val._replace(filter_enable=True)
        else:
            raise TypeError('Failed to enable/disable filter. Must provide boolean value.')

    @property
    def filter_stage_1_time_constant(self):
        return self.val.stage1_tc

    @filter_stage_1_time_constant.setter
    def filter_stage_1_time_constant(self, time_constant):
        if type(time_constant) is float and time_constant > 0:
            self.val = self.val._replace(stage1_tc=time_constant)
        else:
            raise ValueError('Failed to set stage 1 time constant. Must supply float')

    @property
    def filter_stage_2_time_constant(self):
        return self.val.stage1_tc

    @filter_stage_2_time_constant.setter
    def filter_stage_2_time_constant(self, time_constant):
        if type(time_constant) is float and time_constant > 0:
            self.val = self.val._replace(stage2_tc=time_constant)
        else:
            raise ValueError('Failed to set stage 2 time constant. Must supply float')

    @property
    def phase_shift(self):
        return self._phase_enumerator[self.val.duty_cycle]

    @phase_shift.setter
    def phase_shift(self, new_value):
        """
        Set the phase object to use
        Parameters
        ----------
        new_value : str or int
            string for phase object from ['Phase 1', 'Phase 2', 'Phase 3', 'Phase 4', 'Phase 5', 'Phase 6', 'Phase 7',
                                 'Inactive']
            int as the phase number: 1 for Phase 1, 8 for Inactive
        Returns
        -------

        """
        if type(new_value) is int:
            if 1 <= new_value <= 8:
                self.val = self.val._replace(phase_shift=new_value - 1)
            else:
                raise ValueError("Failed to set the new phase object. Phase must be between 1 and 8.")
        elif type(new_value) is str:
            try:
                self.val = self.val._replace(phase_shift=self._phase_enumerator.index(new_value))
            except:
                print('Failed to set the new phase object. String not valid: ', new_value)
                return
        else:
            raise TypeError('Failed to set the new phase object. Parameter must be of type int or str.')

    @property
    def duty_cycle(self):
        return self._duty_cycle_enumerator[self.val.duty_cycle]

    @duty_cycle.setter
    def duty_cycle(self, new_value):
        """
        Set the duty cycle object to use
        Parameters
        ----------
        duty_cycle : str or int
            string for duty cycle from ['Duty Cycle 1', 'Duty Cycle 2', 'Duty Cycle 3', 'Duty Cycle 4', 'Duty Cycle 5',
                                       'Duty Cycle 6', 'Duty Cycle 7', 'Inactive']
            int as the duty cycle object number: 1 for Duty Cycle 1, 8 for Inactive.
        Returns
        -------

        """
        if type(new_value) is int:
            if 1 <= new_value <= 8:
                self.val = self.val._replace(duty_cycle=new_value - 1)
            else:
                raise ValueError('Failed to set the new duty cycle generator. Value must be between 1 and 8.')
        elif type(new_value) is str:
            try:
                self.val = self.val._replace(duty_cycle=self._duty_cycle_enumerator.index(new_value))
            except:
                print('Failed to set the new duty cycle generator. String not valid: ', new_value)
                return
        else:
            raise TypeError('Failed to set the new duty cycle generator. Parameter must be of type int or str.')

    @property
    def wave_shape(self):
        return self._type_enumerator[self.val.wave_shape]

    @wave_shape.setter
    def wave_shape(self, shape):
        """
        Set the wave shape to use
        Parameters
        ----------
        wave_shape : str or int
            string for frequency from ['Sine', 'Square', 'Boxcar']
            int 1 for Sine, 2 for Square, 3 for Boxcar
        Returns
        -------

        """
        if type(shape) is int:
            if 1 <= shape <= 3:
                self.val = self.val._replace(wave_type=shape - 1)
            else:
                raise ValueError('Failed to set the new shape setting. Value must be between 1 and 3.')
        elif type(shape) is str:
            try:
                self.val = self.val._replace(wave_type=self._type_enumerator.index(shape))
            except:
                print('Failed to set the new shape setting. String not valid: ', shape)
                return
        else:
            raise TypeError('Failed to set the new shape setting. Parameter must be of type int or str.')

class InputSettings(ReadWriteParameter):
    def __init__(self, module, my_queue):
        super().__init__(my_queue, 'mcl_config_input',
                         ['gain', 'AC', 'GND', 'auto_range'],
                         ['', False, False, False],
                         '>B3?',
                         2,
                         8 + module)
        self._gain_enumerator = [1, 2, 5, 10, 20, 40, 100, 200, 500, 1000, 2500, 5000]
    #
    # def receive(self, chunk):
    #     print(chunk)

    @property
    def gain(self):
        return self.val.gain

    @gain.setter
    def gain(self, new_gain):
        if new_gain in self._gain_enumerator:
            self.val = self.val._replace(gain=self._gain_enumerator.index(new_gain))
        elif type(new_gain) is int and 1 <= new_gain <= 5000:
            # Finds the closest value
            diffs = [abs(x - new_gain) for x in self._gain_enumerator]
            rounded = diffs.index(min(diffs))
            print('Gain value not found in list. Assigning closest value: ', rounded)
            self.val = self.val._replace(gain=self._gain_enumerator.index(rounded))
        else:
            print('Invalid gain setting. Must be integer between 1 and 5000.')
        return

    @property
    def grounded(self):
        return self.val.GND

    @grounded.setter
    def grounded(self, is_grounded):
        if is_grounded:
            self.val = self.val._replace(GND=True)
        else:
            self.val = self.val._replace(GND=False)

    @property
    def ac_coupling(self):
        return self.val.AC

    @ac_coupling.setter
    def ac_coupling(self, is_ac_coupled):
        if is_ac_coupled:
            self.val = self.val._replace(AC=True)
        else:
            self.val = self.val._replace(AC=False)

    @property
    def auto_range(self):
        return self.val.auto_range

    @auto_range.setter
    def auto_range(self, enable_auto_range):
        if enable_auto_range:
            self.val = self.val._replace(auto_range=True)
        else:
            self.val = self.val._replace(auto_range=False)

class OutputSettings(ReadWriteParameter):
    def __init__(self, module, my_queue):
        super().__init__(my_queue, 'mcl_config_input',
                         ['voltageoutputfloating', 'voltageoutputrange', 'currentmeasrange', 'currentmeasautorange',
                          'fx', 'fy', 'type', 'digitaloutphasemarker_fx', 'outputenabled'],
                         [False, float("NaN"), float("NaN"), False, float("NaN"), float("NaN"), float("NaN"), False, False],
                         '>?2B?3B2?',
                         2,
                         18 + module)

    @property
    def outputenabled(self):
        return self.val.outputenabled

    @outputenabled.setter
    def outputenabled(self, is_outputenabled):
        if is_outputenabled:
            self.val = self.val._replace(outputenabled=True)
        else:
            self.val = self.val._replace(outputenabled=False)



class Frequency(ReadWriteParameter):
    """

    """

    def __init__(self, index, my_queue):
        super().__init__(my_queue, 'mcl_config_frequencyctrl',
                         ['frequency_hz', 'rampchanges', 'ramptimeconst_s'],
                         [0, False, 0],
                         '>d?d',
                         2,
                         34 + index)

    @property
    def frequency(self):
        return self.val.frequency_hz

    @frequency.setter
    def frequency(self, new_value):
        if isinstance(new_value, float) or isinstance(new_value, int):
            if 0 < new_value < 2E6:
                self.val = self.val._replace(frequency_hz=new_value)
            else:
                raise ValueError('Failed to change frequency. Value must be positive and < 2E6.')
        else:
            raise TypeError('Failed to change frequency. Value must be of type float or int.')

    @property
    def ramptimeconst(self):
        if not self.val.rampchanges:
            return False
        else:
            return self.val.ramptimeconst_s

    @ramptimeconst.setter
    def ramptimeconst(self, new_value):
        """
        Sets the ramp time constant for frequency
        Parameters
        ----------
        ramptimeconst : float or bool
            float for enabling ramping and setting the rate
            bool false for disabling ramping
        Returns
        -------

        """
        if new_value:
            if isinstance(new_value, float) or isinstance(new_value, int):
                if new_value > 0:
                    self.val = self.val._replace(rampchanges=True)
                    self.val = self.val._replace(ramptimeconst_s=new_value)
                else:
                    raise ValueError('Failed to change ramp time constant. Value must be positive.')
            else:
                raise ValueError('Failed to change ramp time constant. Parameter must be of type float or int, or boolean false.')
        else:
            self.val = self.val._replace(rampchanges=False)


class PhaseLockedLoop(ReadWriteParameter):
    def __init__(self, pll_set, my_queue):
        super().__init__(my_queue, 'mcl_config_PLL',
                         ['source', 'falling_edge', 'phase_shift'],
                         ['', False, float("NaN")],
                         '>B?d',
                         2,
                         42 + pll_set)
        self._source_enumerator = ['DIO A', 'DIO B', 'DIO C', 'DIO D', 'DIO E']

    @property
    def phase_shift(self):
        return self.val.stage1_tc

    @phase_shift.setter
    def phase_shift(self, new_value):
        if type(new_value) is float:
            self.val = self.val._replace(phase_shift=new_value)
        else:
            print('Failed to set stage 2 time constant. Must supply float')

    @property
    def source(self):
        return self._source_enumerator[self.val.source]

    @source.setter
    def source(self, new_value):
        if type(new_value) is int and new_value > 0:
            self.val = self.val._replace(source=new_value - 1)
        elif type(new_value) is str:
            try:
                self.val = self.val._replace(source=self._source_enumerator.index(new_value))
            except:
                print('Failed to set the new phase object. String not valid: ', new_value)
                return

    @property
    def falling_edge(self):
        return self.val.falling_edge

    @falling_edge.setter
    def falling_edge(self, new_value):
        if new_value:
            self.val = self.val._replace(falling_edge=True)
        else:
            self.val = self.val._replace(falling_edge=False)


class General(ReadWriteParameter):
    def __init__(self, my_queue):
        super().__init__(my_queue, 'MCL_config_GeneralLocalCtrl',
                         ['updateuser', 'sendcalibrations', 'installedmodule_a', 'installedmodule_b',
                          'installedmodule_c', 'installedmodule_d', 'installedmodule_e', 'configuration',
                          'applytodefault', 'loadprefs', 'saveprefs'],
                         [False, False, False, False, False, False, False, 0, True, False, False],
                         '>7?B3?',
                         2,
                         44)

        @property
        def update_user(self):
            return self.val.update_user

        @property
        def send_calibrations(self):
            return self.val.send_calibrations

        @property
        def module_a(self):
            return self.val.installedmodule_a

        @property
        def module_b(self):
            return self.val.installedmodule_b

        @property
        def module_c(self):
            return self.val.installedmodule_c

        @property
        def module_d(self):
            return self.val.installedmodule_d

        @property
        def module_e(self):
            return self.val.installedmodule_e

        @property
        def configuration(self):
            return self.val.configuration

        @property
        def apply_to_default(self):
            return self.val.apply_to_default

        @property
        def load_preferences(self):
            return self.val.loadprefs

        @property
        def save_preferences(self):
            return self.val.saveprefs


class GeneralPICControl(ReadOnlyParameter):
    def __init__(self):
        super().__init__('MCL_config_GeneralPIC_ctrl',
                         ['vcc_24v', 'vcc_3p3v_ln', 'vcc_5v_ln', 'vcc_9v', 'vcc_3p3v', 'vcc_5v', 'i_n', 'v_n',
                          'v_p', 'i_p', 'hw_rev'],
                         [float("NaN"), float("NaN"), float("NaN"), float("NaN"), float("NaN"), float("NaN"),
                          float("NaN"), float("NaN"), float("NaN"), float("NaN"), float("NaN")],
                         '>10dB',
                         2,
                         45)

    @property
    def vcc_24v(self):
        return self.val.vcc_24v

    @property
    def vcc_3p3v_ln(self):
        return self.val.vcc_3p3v_ln

    @property
    def vcc_5v_ln(self):
        return self.val.vcc_5v_ln

    @property
    def vcc_9v(self):
        return self.val.vcc_9v

    @property
    def vcc_3p3v(self):
        return self.val.vcc_3p3v

    @property
    def vcc_5v(self):
        return self.val.vcc_5v

    @property
    def i_n(self):
        return self.val.i_n

    @property
    def v_n(self):
        return self.val.v_n

    @property
    def v_p(self):
        return self.val.v_p

    @property
    def i_p(self):
        return self.val.i_p

    @property
    def hardware_revision(self):
        return self.val.hw_rev



class OutputState(ReadOnlyParameter):
    """

    """

    def __init__(self, index):
        super().__init__('mcl_config_outputstate',
                         ['currentrange', 'overload', 'toohighfrequency', 'underrange'],
                         [float("NaN"), False, False, False],
                         '>B3?',
                         2,
                         51 + index)

class InputState(ReadOnlyParameter):
    """

    """

    def __init__(self, index):
        super().__init__('mcl_config_inputstate',
                         ['gain', 'overload', 'underrange'],
                         [float("NaN"), False, False],
                         '>B??',
                         2,
                         56 + index)


class Offset(ReadWriteParameter):
    """
    """

    def __init__(self, index, my_queue):
        super().__init__(my_queue, 'mcl_config_offset',
                         ['offset_v', 'rampchanges', 'ramptimeconst_s'],
                         [float("NaN"), False, float("NaN")],
                         '>d?d',
                         2,
                         66 + index)

    @property
    def offset(self):
        return self.val.offset_v

    @offset.setter
    def offset(self, new_value):
        if isinstance(new_value, float) or isinstance(new_value, int):
            self.val = self.val._replace(offset_v=new_value)
        else:
            raise TypeError('Failed to change offset. Value must be of type float or int.')

    @property
    def ramptimeconst(self):
        if not self.val.rampchanges:
            return False
        else:
            return self.val.ramptimeconst_s

    @ramptimeconst.setter
    def ramptimeconst(self, new_value):
        """
        Sets the ramp time constant for amplitude
        Parameters
        ----------
        ramptimeconst : float or bool
            float for enabling ramping and setting the rate
            bool false for disabling ramping
        Returns
        -------

        """
        if new_value:
            if isinstance(new_value, float) or isinstance(new_value, int):
                if new_value > 0:
                    self.val = self.val._replace(rampchanges=True)
                    self.val = self.val._replace(ramptimeconst_s=new_value)
                else:
                    raise ValueError('Failed to change ramp time constant. Value must be positive.')
            else:
                raise ValueError('Failed to change ramp time constant. Parameter must be of type float or int, or boolean false.')
        else:
            self.val = self.val._replace(rampchanges=False)

class Feedback(ReadWriteParameter):
    """
    """

    def __init__(self, index, my_queue):
        super().__init__(my_queue, 'mcl_config_feedback',
                         ['signal', 'feedbacktype', 'outputgain', 'reference', 'afterlowpass'],
                         [float("NaN"), float("NaN"), float("NaN"), float("NaN"), False],
                         '>4B?',
                         2,
                         73 + index)


class Amplitude(ReadWriteParameter):
    """
    """

    def __init__(self, index, my_queue):
        super().__init__(my_queue, 'mcl_config_frequencyctrl',
                         ['rampchanges', 'ramptimeconst_s', 'unit', 'amplitude_v'],
                         [False, float("NaN"), float("NaN"), float("NaN")],
                         '>?dBd',
                         2,
                         75 + index)



        self._unit_enumerator = ['Vrms', 'Vp', 'Vpp']


    @property
    def amplitude(self):
        return self.val.amplitude_v

    @amplitude.setter
    def amplitude(self, new_value):
        if isinstance(new_value, float) or isinstance(new_value, int):
            if 0 <= new_value:
                self.val = self.val._replace(amplitude_v=new_value)
            else:
                raise ValueError('Failed to change amplitude. Value must be positive.')
        else:
            raise TypeError('Failed to change amplitude. Value must be of type float or int.')

    @property
    def ramptimeconst(self):
        if not self.val.rampchanges:
            return False
        else:
            return self.val.ramptimeconst_s

    @ramptimeconst.setter
    def ramptimeconst(self, new_value):
        """
        Sets the ramp time constant for amplitude
        Parameters
        ----------
        ramptimeconst : float or bool
            float for enabling ramping and setting the rate
            bool false for disabling ramping
        Returns
        -------

        """
        if new_value:
            if isinstance(new_value, float) or isinstance(new_value, int):
                if new_value > 0:
                    self.val = self.val._replace(rampchanges=True)
                    self.val = self.val._replace(ramptimeconst_s=new_value)
                else:
                    raise ValueError('Failed to change ramp time constant. Value must be positive.')
            else:
                raise ValueError('Failed to change ramp time constant. Parameter must be of type float or int, or boolean false.')
        else:
            self.val = self.val._replace(rampchanges=False)
    @property
    def unit(self):
        return self._unit_enumerator[self.val.unit]

    @unit.setter
    def unit(self, unit):
        """
        Set the unit to use
        Parameters
        ----------
        unit : str or int
            string for unit from ['Vrms', 'Vp', 'Vpp']
            int 1 for Vrms, 2 for Vp, 3 for Vpp
        Returns
        -------

        """
        if type(unit) is int:
            if 1 <= unit <= 3:
                self.val = self.val._replace(unit=unit - 1)
            else:
                raise ValueError('Failed to set the new unit. Value must be between 1 and 3.')
        elif type(unit) is str:
            try:
                self.val = self.val._replace(unit=self._unit_enumerator.index(unit))
            except:
                print('Failed to set the new unit setting. String not valid: ', unit)
                return
        else:
            raise TypeError('Failed to set the new unit setting. Parameter must be of type int or str.')



class Function(ReadWriteParameter):
    """

    """

    def __init__(self, index, my_queue):
        super().__init__(my_queue, 'mcl_config_functionctrl',
                         ['type', 'referencelevel', 'amplitude', 'offset', 'dutycycle', 'frequency', 'phaseshift', 'harmonic'],
                         [float("NaN"), float("NaN"), float("NaN"), float("NaN"), float("NaN"), float("NaN"), float("NaN"), float("NaN")],
                         '>BBBBBBBH',
                         2,
                         80 + index)


class PhaseShift(ReadWriteParameter):
    """

    """

    def __init__(self, index, my_queue):
        super().__init__(my_queue, 'mcl_config_phaseshiftctrl',
                         ['phaseshift_deg'],
                         [float("NaN")],
                         '>d',
                         2,
                         90 + index)


class DutyCycle(ReadWriteParameter):
    """

    """

    def __init__(self, index, my_queue):
        super().__init__(my_queue, 'mcl_config_dutycyclectrl',
                         ['dutycycle', 'unit'],
                         [float("NaN"), float("NaN")],
                         '>dB',
                         2,
                         98 + index)


class Scope(ReadWriteParameter):
    """

    """

    def __init__(self, my_queue):
        super().__init__(my_queue, 'mcl_config_scope',
                         ['channelstoreturn', 'samplingreductionfactor', 'numscopesamples', 'averagebetweensamples',
                          'returnoutputinsteadofimeas'],
                         [float("NaN"), float("NaN"), float("NaN"), False, False],
                         '',
                         2,
                         106)

        self._channelstoreturn_val = None
        self.scope_channelstoreturn_nt = namedtuple('mcl_config_channelstoreturn',
                                         ['av1', 'av2', 'bv1', 'bv2', 'cv1', 'cv2', 'dv1', 'dv2', 'ev1', 'ev2',
                                          'aimeas', 'bimeas', 'cimeas', 'dimeas', 'eimeas', 'ref'])

    def receive(self, chunk):
        channelstoreturn = self.scope_channelstoreturn_nt._make(struct.unpack('>16?', chunk[0:16]))
        samplingreductionfactor = struct.unpack('>H', chunk[16:18])
        numscopesamples = struct.unpack('>B', chunk[18:19])
        averagebetweensamples = struct.unpack('>?', chunk[19:20])
        returnoutputinsteadofimeas = struct.unpack('>?', chunk[20:21])
        self._val = self._data_tuple(channelstoreturn=channelstoreturn,
                                     samplingreductionfactor=samplingreductionfactor[0],
                                     numscopesamples=numscopesamples[0],
                                     averagebetweensamples=averagebetweensamples[0],
                                     returnoutputinsteadofimeas=returnoutputinsteadofimeas[0]
                                    )

        def send(self):
            # FIXME
            pass


class MultiHarm(ReadWriteParameter):
    """

    """

    def __init__(self, index, my_queue):
        super().__init__(my_queue, 'mcl_config_scope',
                         ['channelandharmonics', 'multiharmonicsmode'],
                         [float("NaN"), False],
                         '',
                         2,
                         107 + index)

       # self._channelstoreturn_val = None
        self.multiharm_channelandharmonics_nt = namedtuple('mcl_config_multiharm_channelandharmonics',
                                         ['multiharmonicsetting', 'harmonics'])

    def receive(self, chunk):
        multiharmonicsetting = list(struct.unpack('>16B', chunk[4:20]))
        harmonics = list(struct.unpack('>16H', chunk[24:56]))
        multiharmonicsmode = struct.unpack('>?', chunk[56:57])

        channelandharmonics = self.multiharm_channelandharmonics_nt(multiharmonicsetting, harmonics)

        self._val = self._data_tuple(channelandharmonics=channelandharmonics,
                                     multiharmonicsmode=multiharmonicsmode
                                    )

    def send(self):
        # FIXME
        pass

class Composite(ReadWriteParameter):
    """

    """

    def __init__(self, index, my_queue):
        super().__init__(my_queue, 'mcl_config_composite',
                         ['frequency_a', 'frequency_b', 'frequency_8', 'n', 'm'],
                         [float("NaN"), float("NaN"), float("NaN"), float("NaN"), float("NaN")],
                         '>5B',
                         2,
                         110)
