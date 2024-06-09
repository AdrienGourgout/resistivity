import struct
from collections import namedtuple


__all__ = ['ReadOnlyParameter', 'ReadWriteParameter']

class ReadOnlyParameter:
    """
    Settings that do not contain any editable setting should inherit from this object.
    """
    instances = []

    def __init__(self, tuple_name, tuple_values, defaults, format_string, data_type, data_kind):
        self.__class__.instances.append(self)
        self._data_tuple = namedtuple(tuple_name, tuple_values, defaults=defaults)
        self.format_string = format_string
        self.data_type = data_type
        self.data_kind = data_kind
        self._val = self._data_tuple()
        self._callbacks = {}

    def receive(self, chunk):
        self._val = self._data_tuple._make(struct.unpack(self.format_string, chunk))

    def register_callback(self, callback, mcl_instance):
        """
        Register a callback function.
        """
        if callback in self._callbacks:
            raise ValueError(f"Callback with name '{callback}' already exists.")
        self._callbacks[callback] = mcl_instance

    def unregister_callback(self, callback):
        """
        Unregister a callback function.
        """
        if callback not in self._callbacks:
            raise ValueError(f"Callback with name '{callback}' does not exist.")
        del self._callbacks[callback]


    @property
    def val(self):
        return self._val


class ReadWriteParameter(ReadOnlyParameter):
    """

    """
    instances = []

    def __init__(self, my_queue, tuple_name, tuple_values, defaults, format_string, data_type, data_kind):
        super().__init__(tuple_name, tuple_values, defaults, format_string, data_type, data_kind)
        self._write_queue = my_queue

    def send(self):
        data = struct.pack(self.format_string, *tuple(self._val))
        data_length = len(data)
        self._write_queue.put(
            bytearray(struct.pack('>bhi', self.data_type, self.data_kind, data_length)) + bytearray(data))

    @property
    def val(self):
        return self._val

    @val.setter
    def val(self, new_named_tuple):
        self._val = new_named_tuple
        self.send()

