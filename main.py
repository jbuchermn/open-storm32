import serial
import glob
import csv


options = []


with open('options.csv', 'r') as opts:
    reader = csv.DictReader(opts)
    for r in reader:
        options += [r]


class STorM32:
    def __init__(self, device, baud):
        self._ser = serial.Serial(device, baud, timeout=1)
        self.ping()

    def _read_answer(self):
        answer = b'\n'.join(self._ser.readlines())
        if answer[-1] == b'e':
            raise Exception("STorM32 returned error code")
        elif answer[-1:] != b'o':
            raise Exception("STorM32 returned bogus")
        else:
            return answer[:-1]

    def ping(self):
        self._ser.write(b't')
        if self._read_answer() != b'':
            raise Exception("Ping failed")

    def get_version(self):
        self.ping()
        self._ser.write(b'v')
        return self._read_answer()

    def get_parameters(self):
        self.ping()
        self._ser.write(b'g')
        params = self._read_answer()

        result = []
        for o in options:
            if o['type'] == 'SCRIPT':
                continue

            addr = int(o['addr']) * 2
            sub = [params[addr+1], params[addr]]

            v = 255 * sub[0] + sub[1]
            if o['type'] == 'SI' and v > 32767:
                v -= 65536
            elif o['type'] == 'SC' and v > 127:
                v -= 256

            print("%30s, %8d, %8d, %8d" % (o['name'], int(o['min']), v, int(o['max'])))

            v = 1
            result += [{
                'option': o,
                'value': v
            }]

        return result


for tty in glob.glob('/dev/tty.usb*'):
    print("Opening: %s" % tty)
    st = STorM32(tty, 9600)
    st.ping()
    print("Version: %s" % st.get_version())
    st.get_parameters()
