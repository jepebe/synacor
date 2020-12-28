import sys


class VM:
    def __init__(self) -> None:
        self.stack = []
        self.registers = {
            0x8000: 0,
            0x8001: 0,
            0x8002: 0,
            0x8003: 0,
            0x8004: 0,
            0x8005: 0,
            0x8006: 0,
            0x8007: 0,
        }
        self.ram = [0] * 0x7FFF
        self.pc = 0
        self.halted = False
        self.words = []

        self.opcodes = {
            0: self.halt,
            1: self.set,
            2: self.push,
            3: self.pop,
            4: self.equal,
            5: self.greater_than,
            6: self.jmp,
            7: self.jmp_true,
            8: self.jmp_false,
            9: self.add,
            10: self.mult,
            11: self.mod,
            12: self.bitwise_and,
            13: self.bitwise_or,
            14: self.bitwise_not,
            15: self.rmem,
            16: self.wmem,
            17: self.call,
            18: self.ret,
            19: self.out,
            20: self.input,
            21: self.noop,
        }
        self.buffer = []
        self.char_buffer = []

    def read(self, addr):
        addr &= 0x7FFF
        value = self.ram[addr]
        self.words.append(value)
        return value

    def write(self, addr, value):
        addr &= 0x7FFF
        self.ram[addr] = value

    def fetch_value(self):
        value = self.read(self.pc)
        if 0x8000 <= value < 0x8008:
            value = self.registers[value]
        self.pc += 1
        return value

    def fetch_address(self):
        value = self.read(self.pc)
        self.pc += 1
        return value

    def store_value(self, addr, value):
        if 0x8000 <= addr < 0x8008:
            self.registers[addr] = value
        else:
            self.write(addr, value)

    def clock(self):
        self.words.clear()
        # pc = self.pc
        opcode = self.fetch_value()

        # name = self.opcodes[opcode].__name__
        self.opcodes[opcode]()
        # words = ' '.join(f'{w:04X}' for w in self.words)
        regs = ''
        for reg, addr in enumerate(range(0x8000, 0x8008)):
            regs += f'R{reg}: {self.registers[addr]:04X} '
        #  print(f'${pc:04X} {words:<19} {name:<20} {regs}')

    def halt(self):
        self.halted = True

    def add(self):
        addr = self.fetch_address()
        b = self.fetch_value()
        c = self.fetch_value()
        self.store_value(addr, (b + c) & 0x7FFF)

    def mult(self):
        addr = self.fetch_address()
        b = self.fetch_value()
        c = self.fetch_value()
        self.store_value(addr, (b * c) & 0x7FFF)

    def mod(self):
        addr = self.fetch_address()
        b = self.fetch_value()
        c = self.fetch_value()
        self.store_value(addr, b % c)

    def push(self):
        a = self.fetch_value()
        self.stack.insert(0, a)

    def pop(self):
        addr = self.fetch_address()
        value = self.stack.pop(0)
        self.store_value(addr, value)

    def equal(self):
        addr = self.fetch_address()
        b = self.fetch_value()
        c = self.fetch_value()
        self.store_value(addr, 1 if b == c else 0)

    def greater_than(self):
        addr = self.fetch_address()
        b = self.fetch_value()
        c = self.fetch_value()
        self.store_value(addr, 1 if b > c else 0)

    def bitwise_and(self):
        addr = self.fetch_address()
        b = self.fetch_value()
        c = self.fetch_value()
        self.store_value(addr, b & c)

    def bitwise_or(self):
        addr = self.fetch_address()
        b = self.fetch_value()
        c = self.fetch_value()
        self.store_value(addr, b | c)

    def bitwise_not(self):
        addr = self.fetch_address()
        b = self.fetch_value()
        b = (~b) & 0x7FFF
        self.store_value(addr, b)

    def rmem(self):
        to_addr = self.fetch_address()
        from_addr = self.fetch_value()
        if 0x8000 <= from_addr < 0x8008:
            b = self.registers[from_addr]
        else:
            b = self.ram[from_addr]
        self.store_value(to_addr, b)

    def wmem(self):
        to_addr = self.fetch_value()
        b = self.fetch_value()
        # if 0x8000 <= from_addr < 0x8008:
        #     b = self.registers[from_addr]
        # else:
        #     b = self.ram[from_addr]
        self.store_value(to_addr, b)

    def call(self):
        self.stack.insert(0, self.pc + 1)
        self.jmp()

    def ret(self):
        if not self.stack:
            self.halted = True
        else:
            addr = self.stack.pop(0)
            self.pc = addr

    def out(self):
        value = self.fetch_value()
        self.buffer.append(chr(value))
        if chr(value) == '\n':
            print(''.join(self.buffer))
            self.buffer.clear()

    def input(self):
        to_addr = self.fetch_address()
        if not self.char_buffer:
            inp = input('>')
            self.char_buffer.extend(inp)
            self.char_buffer.append('\n')

        if self.char_buffer:
            ch = self.char_buffer.pop(0)
        else:
            ch = '\n'

        self.store_value(to_addr, ord(ch))

    def set(self):
        a = self.fetch_address()
        b = self.fetch_value()
        self.store_value(a, b)

    def noop(self):
        pass

    def jmp(self):
        addr = self.fetch_value()
        self.pc = addr

    def jmp_true(self):
        a = self.fetch_value()
        b = self.fetch_value()
        if a != 0:
            self.pc = b

    def jmp_false(self):
        a = self.fetch_value()
        b = self.fetch_value()
        if a == 0:
            self.pc = b


if __name__ == '__main__':
    binary = sys.argv[1]
    vm = VM()
    with open(binary, 'rb') as f:
        data = f.read()
        for i in range(len(data) // 2):
            lo = data[i * 2]
            hi = data[i * 2 + 1]
            value = (hi << 8) | lo
            vm.write(i, value)

    while not vm.halted:
        vm.clock()
