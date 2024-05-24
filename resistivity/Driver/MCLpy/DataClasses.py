from resistivity.Driver.MCLpy.ReadWriteValues import ReadOnlyParameter
from collections import namedtuple
import struct
import threading

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

__all__ = ['LockInData', 'Scope', 'FFT']




class LockInData(ReadOnlyParameter):
    def __init__(self, index):
        super().__init__('MCL_LIData_datareadings',
                         ['generalreadings', 'moduledata', 'dc', 'x', 'y', 'r', 'thetadeg'],
                         [float("NaN"), float("NaN"), float("NaN"), float("NaN"), float("NaN"), float("NaN"),
                          float("NaN"), ],
                         '>d?d',
                         3,
                         0 + index)
        self.general_readings_nt = namedtuple('MCL_LIData_generalreadings',
                                              ['dt_s', 'cyclespersample', 'syncindex', 'time_s', 'lockinf_hz',
                                               'pll1_hz', 'pll2_hz', 'composite1_hz'])
        self.module_data_nt = namedtuple('MCL_LIData_moduledata',
                                         ['digitalInf_hz', 'digitaloutf_hz', 'amplitude_vrms', 'outputoffset_v'])

        self.lockin_set = index

    def receive(self, chunks):
        """
        Handles incoming data by breaking the chunks down and assembling named tuples.
        It then stores these tuples appropriately, making the values ready for data access
        Parameters
        ----------
        chunks : byte data
            the incoming data in raw byte chunks

        Returns
        -------

        """
        # todo(Holger) check my description is correct
        if(len(chunks) < 888):
            return
        general_readings = self.general_readings_nt._make(struct.unpack('>8d', chunks[660:700] + chunks[864:888]))
        module_data = []
        module_data_container = struct.unpack('>I', chunks[700:704])[0]
        module_data_start_index = 704  # to 864
        for i in range(module_data_container):
            module_data.append(self.module_data_nt._make(
                struct.unpack('>4d', chunks[module_data_start_index + 32 * i:module_data_start_index + 32 * i + 32])))
        # x_container = struct.unpack('>I', chunks[0:4])[0]
        fmt = ">%dd" % 16
        dc = list(struct.unpack(fmt, chunks[4:132]))
        x = list(struct.unpack(fmt, chunks[136:264]))
        y = list(struct.unpack(fmt, chunks[268:396]))
        r = list(struct.unpack(fmt, chunks[400:528]))
        theta = list(struct.unpack(fmt, chunks[532:660]))

        self._val = self._data_tuple(generalreadings=general_readings,
                                     moduledata=module_data,
                                     dc=dc,
                                     x=x,
                                     y=y,
                                     r=r,
                                     thetadeg=theta)
        self._notify_observers(self._val)

    def _notify_observers(self, data_readings):
        for callback in self._callbacks.copy():
            threading.Thread(target=callback, args=(self.lockin_set, data_readings, self._callbacks[callback])).start()

    @property
    def general_readings(self):
        """
        Getter for the general readings named tuple
        Returns
        -------
        general_readings : namedtuple('MCL_LIData_generalreadings',
                                              'dt_s cyclespersample syncindex time_s lockinf_hz pll1_hz pll2_hz '
                                              'composite1_hz')
            named tuple containing all values from the module_data branch of LIData
        """
        return self._val.generalreadings

    @property
    def module_data(self):
        """
        Getter for the module data named tuple
        Returns
        -------
        module_data : namedtuple('MCL_LIData_moduledata',
                                         'digitalInf_hz digitaloutf_hz amplitude_vrms outputoffset_v')
            named tuple containing all values from the module_data branch of LIData
        """
        return self._val.module_data

    @property
    def dc(self):
        """
        Getter for the DC value of the lock in
        Returns
        -------
        dc: float
            DC offset in Volts
        """
        return self._val.dc

    @property
    def x(self):
        """
        Getter for the x value of the lock in
        Returns
        -------
        x : float
            x value in Volts
        """
        return self._val.x

    @property
    def y(self):
        """
        Getter for the y value of the lock in
        Returns
        -------
        y : float
            y value in Volts
        """
        return self._val.y

    @property
    def r(self):
        """
        Getter for the r value of the lock in
        Returns
        -------
        r : float
            r value in Volts
        """
        return self._val.r

    @property
    def theta(self):
        """
        Getter for the theta value of the lock in
        Returns
        -------
        theta : float
            theta value in degrees
        """
        return self._val.thetadeg

    @property
    def time_step(self):
        """
        Getter for the time between measurements (inverse of measurement frequency) value of the lock in
        Returns
        -------
        dt_s : float
            time step value in seconds
        """
        return self._val.generalreadings.dt_s

    @property
    def measurement_rate(self):
        """
        Getter for the number of frequency cycles per measurement (can be used to find the integration time)
        Returns
        -------
        rate : int
            Number of frequency cycles per measurement
        """
        return self._val.generalreadings.cyclespersample

    @property
    def integration_time(self):
        """
        Getter for the integration time per sampled point.
        Returns
        -------
        integration_time : float
            integration time (equivalent to measurement_rate * lock_in_frequency)
        """
        return self.measurement_rate * self.lock_in_frequency

    @property
    def lock_in_frequency(self):
        """
        Getter for the frequency that the lock-in is locked into
        Returns
        -------
        frequency: float
            lock in frequency in Hz
        """
        return self._val.generalreadings.lockinf_hz

    @property
    def time(self):
        """
        Getter for the instruments local time for the latest measurement.
        Returns
        -------
        time : float
            instrument time for latest values in seconds
        """
        return self._val.generalreadings.time_s

    @property
    def input_frequency(self):
        """
        Getter for external input frequency for the lock-in from the "Trigger/phase marker in" connection
        Returns
        -------
        input_frequency : float
            external input frequency in Hz
        """
        return self._val.module_data.digitalInf_hz

    @property
    def output_frequency(self):
        """
        Getter for the external output frequency for the lock-in from the "Trigger/phase marker out" connection
        Returns
        -------
        output_frequency : float
            external output frequency in Hz
        """
        return self._val.module_data.digitaloutf_hz

    @property
    def output_amplitude(self):
        """
        Getter for the external AC voltage output amplitude for the lock-in from the "analog output" connections
        Returns
        -------
        output_amplitude : float
            external output amplitude in Volts RMS
        """
        return self._val.module_data.amplitude_vrms

    @property
    def output_offset(self):
        """
        Getter for the external voltage output DC offset for the lock-in from the "analog output" connections
        Returns
        -------
        output_offset : float
            external output offset in Volts
        """
        return self._val.module_data.outputoffset_v


class Scope(ReadOnlyParameter):
    def __init__(self):
        super().__init__('MCL_scope',
                         ['dt_s', 'averages_completed', 'df_hz', 'averagingdone', 'waveformtype',
                          'channelstoreturn_label', 'channelstoreturn', 'samplingreductionfactor', 'scopesamples',
                          'averagebetweensamples', 'returnoutputinsteadofimeas', 'data'],
                         [float("NaN"), float("NaN"), float("NaN"), False, 0, [], [], 0, 0, False, False, []],
                         '',
                         4,
                         0)
        self.is_fft = False

    def receive(self, chunks):
        array_len = struct.unpack('>Q', chunks[4:12])[0]
        array_end = 12 + array_len * 8
        data_length = len(chunks)
        format_string = ">%dd" % array_len
        values = list(struct.unpack(format_string, chunks[12:array_end]))

        metadata = chunks[array_end:data_length].decode('ascii').rstrip('\0')
        xml = ET.fromstring(metadata)
        dt_s = float(xml.find("./DBL/[Name='dt (s)']/Val").text)
        averages_completed = float(xml.find("./DBL/[Name='averages completed']/Val").text)
        df_hz = float(xml.find("./DBL/[Name='df (Hz)']/Val").text)
        averaging_done = bool(int(xml.find("./Boolean/[Name='averaging done']/Val").text))
        waveform_type = xml.findall("./EW/[Name='Waveform Type']/Choice")[
            int(xml.find("./EW/[Name='Waveform Type']/Val").text)].text
        sampling_reduction_factor = int(xml.find("./Cluster/U16/[Name='Sampling reduction factor']/Val").text)
        scope_samples = int(xml.findall("./Cluster/EB/[Name='#scope samples']/Choice")[
                                int(xml.find("./Cluster/EB/[Name='#scope samples']/Val").text)].text)
        average_between_samples = bool(int(xml.find("./Cluster/Boolean/[Name='Average between samples']/Val").text))
        returnoutputinsteadofimeas = bool(
            int(xml.find("./Cluster/Boolean/[Name='Return output instead of Imeas']/Val").text))
        channels_to_return = []
        channels_to_return_label = []
        data = []
        dataindex = 0
        if (self.is_fft):
            chunksize = int(scope_samples / 2)
        else:
            chunksize = scope_samples
        for i in xml.findall("./Cluster/Cluster/[Name='Channels to return']/Boolean"):
            channels_to_return_label.append(i.find("Name").text)
            active = bool(int(i.find("Val").text))
            channels_to_return.append(active)
            if active:
                data.append(values[dataindex * chunksize:(dataindex + 1) * chunksize])
                dataindex += 1
            else:
                data.append([])

        self._val = self._data_tuple(
            dt_s=dt_s,
            averages_completed=averages_completed,
            df_hz=df_hz,
            averagingdone=averaging_done,
            waveformtype=waveform_type,
            channelstoreturn_label=channels_to_return_label,
            channelstoreturn=channels_to_return,
            samplingreductionfactor=sampling_reduction_factor,
            scopesamples=scope_samples,
            averagebetweensamples=average_between_samples,
            returnoutputinsteadofimeas=returnoutputinsteadofimeas,
            data=data
        )
        self._notify_observers(waveform_type, self._val)

    def _notify_observers(self, waveformtype, val):
        for callback in self._callbacks.copy():
            threading.Thread(target=callback, args=(waveformtype, val, self._callbacks[callback])).start()

    @property
    def dt_s(self):
        return self._val.dt_s

    @property
    def averages_completed(self):
        return self._val.averages_completed

    @property
    def df_hz(self):
        return self._val.df_hz

    @property
    def averagingdone(self):
        return self._val.averagingdone

    @property
    def waveformtype(self):
        return self._val.waveformtype

    @property
    def channelstoreturn_label(self):
        return self._val.channelstoreturn_label

    @property
    def channelstoreturn(self):
        return self._val.channelstoreturn

    @property
    def samplingreductionfactor(self):
        return self._val.samplingreductionfactor

    @property
    def scopesamples(self):
        return self._val.scopesamples

    @property
    def averagebetweensamples(self):
        return self._val.averagebetweensamples

    @property
    def returnoutputinsteadofimeas(self):
        return self._val.returnoutputinsteadofimeas

    @property
    def data(self):
        return self._val.data


class FFT(Scope):
    def __init__(self):
        super().__init__()
        self.data_kind = 1
        self.is_fft = True
