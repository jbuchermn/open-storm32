import sys
import re

"""
This does NOT parse pl code, outcome depends on formatting used
"""
CMD_g_PARAMETER_ZAHL = 125


class Option:
    def __init__(self, data):
        self.name = ""
        self.type = ""
        self.pos = ""
        self.unit = ""
        self.len = 0
        self.ppos = 0
        self.min = 0
        self.max = 0
        self.steps = 0
        self.size = 16
        self.column = 1
        self.adr = 0
        self.choices = ""
        self.default = 0

        self.readonly = False
        self.expert = False
        self.hidden = False

        def to_int(data):
            if data == "$FunctionInputMax":
                return 42
            elif data == "$SCRIPTSIZE":
                return 128
            elif "CMD_g_PARAMETER_ZAHL-" in data:
                return CMD_g_PARAMETER_ZAHL - int(data.split("-")[-1])
            try:
                return int(data)
            except Exception:
                return 0

        data = re.split(r',\s*(?![^\[\]]*\])', data)
        data = [d.strip() for d in data]
        for d in data:
            if "=>" not in d:
                continue

            key = d.split("=>")[0].strip()
            val = d.split("=>")[1].strip()

            if key == "name":
                self.name = val.strip().replace("'", "")
            elif key == "type":
                self.type = val
                if "+" in self.type:
                    self.type = self.type.replace("OPTTYPE_READONLY", "")
                    self.type = self.type.replace("+", "")
                    self.readonly = True

                self.type = self.type.replace('OPTTYPE_', '')
                self.type = self.type.strip().replace("'", "")
            elif key == "len":
                self.len = to_int(val)
            elif key == "pos":
                self.pos = val
            elif key == "unit":
                self.unit = val.strip().replace("'", "")
            elif key == "ppos":
                self.ppos = to_int(val)
            elif key == "min":
                self.min = to_int(val)
            elif key == "max":
                self.max = to_int(val)
            elif key == "steps":
                self.steps = to_int(val)
            elif key == "size":
                self.size = to_int(val)
            elif key == "column":
                self.column = to_int(val)
            elif key == "expert":
                self.expert = to_int(val) == 1
            elif key == "adr":
                self.adr = to_int(val)
            elif key == "choices":
                self.choices = val
            elif key == "default":
                self.default = to_int(val)
            elif key == "hidden":
                self.hidden = to_int(val) == 1
            else:
                raise Exception("Unknown key %s" % key)


opts = []
with open(sys.argv[1], 'r',
          encoding='utf-8', errors='ignore') as dreadful_perl_file:
    started = False
    text = ""
    for row in dreadful_perl_file:

        if 'my @OptionL094List= (' in row:
            started = True
        elif started and row.strip() == ");":
            started = False
        elif started:
            text += row

    text = text.split('},{')
    text = [t.strip() for t in text]
    text[0] = text[0][1:]
    text[-1] = text[-1][:-1]

    for t in text:
        opts += [Option(t)]

opts = sorted(opts, key=lambda o: o.adr)
with open('options.csv', 'w') as outf:
    outf.write("addr,ppos,len,size,name,type,unit,pos,min,max,steps,column,choices,default,expert,hidden,readonly\n")  # noqa F401
    for o in opts:
        outf.write(("%d,%d,%d,%d,%s,%s,%s,%s,%d,%d,%d,%d,%s,%d,%s,%s,%s" % (  # noqa F401
            o.adr, o.ppos, o.len, o.size,
            o.name, o.type, o.unit,
            o.pos.replace("'", "\"").replace(",", ";"),
            o.min, o.max, o.steps,
            o.column,
            o.choices.replace("'", "\"").replace(",", ";"),
            o.default,
            o.expert, o.hidden, o.readonly
        )).replace("\n", "") + "\n")
