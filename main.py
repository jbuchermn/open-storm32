import serial
import glob
import csv
from crccheck.crc import CrcX25


options = []


with open('options.csv', 'r') as opts:
    reader = csv.DictReader(opts)
    for r in reader:
        options += [r]


class Parameter:
    def __init__(self, type, name, options):
        self.type = type
        self.name = name
        self.options = options

        self.value = None

    def read(self, param_bytes):
        addr = int(self.options['addr']) * 2
        sub = [param_bytes[addr+1], param_bytes[addr]]

        self.value = self._parse(sub)

    def set(self, param_bytes):
        value = self._encode()
        value[0], value[1] = value[1], value[0]
        addr = int(self.options['addr']) * 2

        param_bytes[addr:addr+2] = value


class SIParameter(Parameter):
    def __init__(self, options):
        super().__init__("SI", options['name'], options)

    def _parse(self, sub):
        v = 256 * sub[0] + sub[1]
        if v > 32767:
            v -= 65536

        return v

    def _encode(self):
        if self.value < 0:
            self.value += 65536

        return [int(self.value/256), self.value % 256]


class UIParameter(Parameter):
    def __init__(self, options):
        super().__init__("UI", options['name'], options)

    def _parse(self, sub):
        return 256 * sub[0] + sub[1]

    def _encode(self):
        return [int(self.value/256), self.value % 256]


class ListParameter(Parameter):
    def __init__(self, options):
        super().__init__("LISTA", options['name'], options)

    def _parse(self, sub):
        return 256 * sub[0] + sub[1]

    def _encode(self):
        return [int(self.value/256), self.value % 256]


def parameter_factory(option):
    if option['type'] in ['SCRIPT', 'STR']:
        return None
    elif option['type'] == 'SI':
        return SIParameter(option)
    elif option['type'] == 'UI':
        return UIParameter(option)
    elif option['type'] == 'LISTA':
        return ListParameter(option)
    else:
        raise Exception("Unknown type %s" % option['type'])


def checksum(bytelike):
    crc = 0xFFFF
    for b in bytelike:
        tmp = b ^ (crc & 0xFF)
        tmp = (tmp ^ (tmp << 4)) & 0xFF
        crc = (crc >> 8) ^ (tmp << 8) ^ (tmp << 3) ^ (tmp >> 4)
        crc = crc & 0xFFFF

    return bytes([crc % 256, int(crc/256)])


class STorM32:
    def __init__(self, device, baud):
        self._ser = serial.Serial(device, baud, timeout=1)
        self._param_bytes = None
        self._param_bytes_changed = bytearray()
        self._parameters = []
        for o in options:
            p = parameter_factory(o)
            if p is not None:
                self._parameters += [p]

        self.ping()

    def _read_answer(self, answer_size=-1):
        """
        answer_size DOES include o/e status; returned answer does NOT
        """
        if answer_size == -1:
            answer = b''.join(self._ser.readlines())
        else:
            answer = self._ser.read(answer_size)
        if answer[-1] == b'e':
            raise Exception("STorM32 returned error code")
        elif answer[-1:] != b'o':
            raise Exception("STorM32 returned bogus: %s" % answer)
        else:
            return answer[:-1]

    def ping(self):
        self._ser.write(b't')
        if self._read_answer(1) != b'':
            raise Exception("Ping failed")

    def get_version(self):
        self.ping()
        self._ser.write(b'v')
        return self._read_answer()

    def get_parameters(self):
        self.ping()
        self._ser.write(b'g')
        self._param_bytes = self._read_answer()
        crc = self._param_bytes[-2:]
        self._param_bytes = self._param_bytes[:-2]

        print(checksum(self._param_bytes), crc)

        for p in self._parameters:
            p.read(self._param_bytes)

    def set_parameters(self):
        self._param_bytes_changed = bytearray(self._param_bytes)
        for p in self._parameters:
            p.set(self._param_bytes_changed)

        params = b'p' + bytes(self._param_bytes_changed) + \
            checksum(self._param_bytes_changed)

        print("Writing parameters...")
        self._ser.write(params)
        try:
            self._read_answer(answer_size=1)
            print("...success")
        except Exception:
            print("....failed")

    def print_parameters(self):
        for p in self._parameters:
            print("%30s: %d" % (p.name, p.value))

    # def get_live_data(self):
    #     self._ser.write(b'd')
    #     result = self._read_answer()
    #     crc = result[-2:]
    #     result = result[:-2]


for tty in glob.glob('/dev/tty.usb*'):
    print("Opening: %s" % tty)
    st = STorM32(tty, 9600)
    st.ping()
    st.get_parameters()
    st.print_parameters()
    st.set_parameters()
