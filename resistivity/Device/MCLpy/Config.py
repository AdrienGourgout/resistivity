from resistivity.Device.MCLpy.ConfigClasses import *
from resistivity.Device.MCLpy.ReadWriteValues import *

__all__ = ['Config']


class Config(object):

    def __init__(self, write_queue):
        self.L1 = LockInControl(0, write_queue)
        self.L2 = LockInControl(1, write_queue)
        self.input_A1 = InputSettings(0, write_queue)
        self.input_A2 = InputSettings(1, write_queue)
        self.input_B1 = InputSettings(2, write_queue)
        self.input_B2 = InputSettings(3, write_queue)
        self.input_C1 = InputSettings(4, write_queue)
        self.input_C2 = InputSettings(5, write_queue)
        self.input_D1 = InputSettings(6, write_queue)
        self.input_D2 = InputSettings(7, write_queue)
        self.input_E1 = InputSettings(8, write_queue)
        self.input_E2 = InputSettings(9, write_queue)

        self.output_A = OutputSettings(0, write_queue)
        self.output_B = OutputSettings(1, write_queue)
        self.output_C = OutputSettings(2, write_queue)
        self.output_D = OutputSettings(3, write_queue)
        self.output_E = OutputSettings(4, write_queue)

        self.frequency_1 = Frequency(0, write_queue)
        self.frequency_2 = Frequency(1, write_queue)
        self.frequency_3 = Frequency(2, write_queue)
        self.frequency_4 = Frequency(3, write_queue)
        self.frequency_5 = Frequency(4, write_queue)
        self.frequency_6_pll1 = Frequency(5, write_queue)
        self.frequency_7_pll2 = Frequency(6, write_queue)
        self.frequency_8_comp1 = Frequency(7, write_queue)
        self.PLL1 = PhaseLockedLoop(0, write_queue)
        self.PLL2 = PhaseLockedLoop(1, write_queue)

        self.general = General(write_queue)
        self.PIC = GeneralPICControl()

        self.outputstate_A = OutputState(0)
        self.outputstate_B = OutputState(1)
        self.outputstate_C = OutputState(2)
        self.outputstate_D = OutputState(3)
        self.outputstate_E = OutputState(4)


        self.inputstate_A1 = InputState(0)
        self.inputstate_A2 = InputState(1)
        self.inputstate_B1 = InputState(2)
        self.inputstate_B2 = InputState(3)
        self.inputstate_C1 = InputState(4)
        self.inputstate_C2 = InputState(5)
        self.inputstate_D1 = InputState(6)
        self.inputstate_D2 = InputState(7)
        self.inputstate_E1 = InputState(8)
        self.inputstate_E2 = InputState(9)

        self.offset_1 = Offset(0, write_queue)
        self.offset_2 = Offset(1, write_queue)
        self.offset_3 = Offset(2, write_queue)
        self.offset_4 = Offset(3, write_queue)
        self.offset_5 = Offset(4, write_queue)
        self.offset_6_feedback_1 = Offset(5, write_queue)
        self.offset_7_feedback_2 = Offset(6, write_queue)

        self.feedback_1 = Feedback(0, write_queue)
        self.feedback_2 = Feedback(1, write_queue)

        self.amplitude_1 = Amplitude(0, write_queue)
        self.amplitude_2 = Amplitude(1, write_queue)
        self.amplitude_3 = Amplitude(2, write_queue)
        self.amplitude_4 = Amplitude(3, write_queue)
        self.amplitude_5 = Amplitude(4, write_queue)

        self.function_1 = Function(0, write_queue)
        self.function_2 = Function(1, write_queue)
        self.function_3 = Function(2, write_queue)
        self.function_4 = Function(3, write_queue)
        self.function_5 = Function(4, write_queue)
        self.function_6 = Function(5, write_queue)
        self.function_7 = Function(6, write_queue)
        self.function_8 = Function(7, write_queue)
        self.function_9 = Function(8, write_queue)
        self.function_10 = Function(9, write_queue)

        self.phaseshift_1 = PhaseShift(0, write_queue)
        self.phaseshift_2 = PhaseShift(1, write_queue)
        self.phaseshift_3 = PhaseShift(2, write_queue)
        self.phaseshift_4 = PhaseShift(3, write_queue)
        self.phaseshift_5 = PhaseShift(4, write_queue)
        self.phaseshift_6 = PhaseShift(5, write_queue)
        self.phaseshift_7 = PhaseShift(6, write_queue)
        self.phaseshift_8 = PhaseShift(7, write_queue)

        self.dutycycle_1 = DutyCycle(0, write_queue)
        self.dutycycle_2 = DutyCycle(1, write_queue)
        self.dutycycle_3 = DutyCycle(2, write_queue)
        self.dutycycle_4 = DutyCycle(3, write_queue)
        self.dutycycle_5 = DutyCycle(4, write_queue)
        self.dutycycle_6 = DutyCycle(5, write_queue)
        self.dutycycle_7 = DutyCycle(6, write_queue)
        self.dutycycle_8 = DutyCycle(7, write_queue)
        self.scope = Scope(write_queue)

        self.multiharm_l1 = MultiHarm(0, write_queue)
        self.multiharm_l2 = MultiHarm(1, write_queue)

        self.composite_1 = Composite(1, write_queue)

    @property
    def children(self):
        return ReadWriteParameter.instances + ReadOnlyParameter.instances




