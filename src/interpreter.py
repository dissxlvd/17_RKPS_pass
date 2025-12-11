import struct
import json
import sys

from assembler import *


class UVMInterpreter:
	def __init__(self, memory_size=65536):
		self.memory = [0] * memory_size
		self.code_memory = []
		self.pc = 0
		self.running = False


	def load_program(self, program_file):
		with open(program_file, 'rb') as f:
			code = f.read()

		i = 0
		while i < len(code):
			opcode = code[i] & 0x1F

			if opcode == 13:  # ldc
				if i + 6 <= len(code):
					self.code_memory.append(('ldc', code[i:i+6]))
					i += 6
			elif opcode == 31:  # ldm
				if i + 7 <= len(code):
					self.code_memory.append(('ldm', code[i:i+7]))
					i += 7
			elif opcode == 7:  # stm
				if i + 7 <= len(code):
					self.code_memory.append(('stm', code[i:i+7]))
					i += 7
			elif opcode == 28:  # max
				if i + 9 <= len(code):
					self.code_memory.append(('max', code[i:i+9]))
					i += 9
			else:
				i += 1


	def decode_ldc(self, instruction):
		if len(instruction) < 6:
			return None

		word = struct.unpack('<Q', instruction + b'\x00\x00')[0]
		a = word & 0x1F
		b = (word >> 5) & 0x3FFFFF
		c = (word >> 27) & 0xFFFF

		return {'opcode': 'ldc', 'b': b, 'c': c}


	def decode_ldm(self, instruction):
		if len(instruction) < 7:
			return None

		word = struct.unpack('<Q', instruction + b'\x00')[0]
		a = word & 0x1F
		b = (word >> 5) & 0x3FFFFF
		c = (word >> 27) & 0x3FFFFF

		return {'opcode': 'ldm', 'b': b, 'c': c}


	def decode_stm(self, instruction):
		if len(instruction) < 7:
			return None

		word = struct.unpack('<Q', instruction + b'\x00')[0]
		a = word & 0x1F
		b = (word >> 5) & 0x3FFFFF
		c = (word >> 27) & 0x3FFFFF

		return {'opcode': 'stm', 'b': b, 'c': c}


	def decode_max(self, instruction):
		if len(instruction) < 9:
			return None

		word = 0
		for i in range(9):
			word |= (instruction[i] << (i * 8))

		a = word & 0x1F
		b = (word >> 5) & 0x3FFFFF
		c = (word >> 27) & 0x3FFFFF
		d = (word >> 49) & 0x3FFFFF

		return {'opcode': 'max', 'b': b, 'c': c, 'd': d}


	def execute_ldc(self, decoded):
		b_addr = decoded['b']
		constant = decoded['c']

		if 0 <= b_addr < len(self.memory):
			self.memory[b_addr] = constant

		self.pc += 1

	
	def execute_ldm(self, decoded):
		b_addr = decoded['b']
		c_addr = decoded['c']

		if 0 <= c_addr < len(self.memory):
			source_addr = self.memory[c_addr]
		if 0 <= source_addr < len(self.memory):
			value = self.memory[source_addr]
		if 0 <= b_addr < len(self.memory):
			self.memory[b_addr] = value

		self.pc += 1


	def execute_stm(self, decoded):
		b_addr = decoded['b']
		c_addr = decoded['c']

		if 0 <= b_addr < len(self.memory):
			value = self.memory[b_addr]
		if 0 <= c_addr < len(self.memory):
			self.memory[c_addr] = value

		self.pc += 1


	def execute_max(self, decoded):
		b_addr = decoded['b']
		c_addr = decoded['c']
		d_addr = decoded['d']

		if (0 <= b_addr < len(self.memory) and 
      			0 <= c_addr < len(self.memory) and 
			0 <= d_addr < len(self.memory)):

			val1 = self.memory[b_addr]
			val2 = self.memory[d_addr]
			self.memory[c_addr] = max(val1, val2)

		self.pc += 1


	def run(self):
		self.running = True
		self.pc = 0

		while self.running and self.pc < len(self.code_memory):
			opcode, instruction = self.code_memory[self.pc]

			if opcode == 'ldc':
				decoded = self.decode_ldc(instruction)
				if decoded:
					self.execute_ldc(decoded)
			elif opcode == 'ldm':
				decoded = self.decode_ldm(instruction)
				if decoded:
					self.execute_ldm(decoded)
			elif opcode == 'stm':
				decoded = self.decode_stm(instruction)
				if decoded:
					self.execute_stm(decoded)
			elif opcode == 'max':
				decoded = self.decode_max(instruction)
				if decoded:
					self.execute_max(decoded)
			else:
				self.pc += 1


	def save_memory_dump(self, filename, start_addr=0, end_addr=100):
		dump = {}
		for addr in range(start_addr, min(end_addr, len(self.memory))):
			if self.memory[addr] != 0:
				dump[str(addr)] = self.memory[addr]

		with open(filename, 'w') as f:
			json.dump(dump, f, indent=2)


class UVMInterpreterWithALU(UVMInterpreter): 
	def __init__(self, memory_size=65536):
		super().__init__(memory_size)

	def execute_max(self, decoded):
		b_addr = decoded['b']
		c_addr = decoded['c']
		d_addr = decoded['d']

		if not (0 <= b_addr < len(self.memory) and
			0 <= c_addr < len(self.memory) and
			0 <= d_addr < len(self.memory)):
			self.pc += 1
			return

		val1 = self.memory[b_addr]
		val2 = self.memory[d_addr]

		result = val1 if val1 > val2 else val2

		self.memory[c_addr] = result

		self.pc += 1


def main_interpreter():
	if len(sys.argv) < 3:
		print("Использование: python interpreter.py <программа.bin> <дамп.json> [начало конец]")
		sys.exit(1)

	program_file = sys.argv[1]
	dump_file = sys.argv[2]

	start_addr = 0
	end_addr = 100

	if len(sys.argv) >= 5:
		start_addr = int(sys.argv[3])
		end_addr = int(sys.argv[4])

	uvm = UVMInterpreter()

	uvm.load_program(program_file)

	uvm.run()

	uvm.save_memory_dump(dump_file, start_addr, end_addr)

	print(f"Программа выполнена. Дамп памяти сохранен в {dump_file}")


def test_task():
	# Программа для тестовой задачи
	program = """
# Инициализация вектора из 7 элементов
ldc 1000 45    # элемент 0
ldc 1001 89    # элемент 1
ldc 1002 151   # элемент 2
ldc 1003 67    # элемент 3
ldc 1004 200   # элемент 4
ldc 1005 120   # элемент 5
ldc 1006 151   # элемент 6

# Константа для сравнения
ldc 999 151    # число 151

# Вычисление max() для каждого элемента
max 2000 1000 999  # max(45, 151) = 151
max 2001 1001 999  # max(89, 151) = 151
max 2002 1002 999  # max(151, 151) = 151
max 2003 1003 999  # max(67, 151) = 151
max 2004 1004 999  # max(200, 151) = 200
max 2005 1005 999  # max(120, 151) = 151
max 2006 1006 999  # max(151, 151) = 151
"""

	# Создание и запуск интерпретатора
	uvm = UVMInterpreterWithALU(10000)

	# Ассемблирование и выполнение программы
	assembler = Assembler()

	# Сохранение программы во временный файл
	with open('./tests/test_task.asm', 'w', encoding='utf-8') as f:
		f.write(program)

	# Ассемблирование
	assembler.assemble_binary('./tests/test_task.asm', './test_task_out.bin')

	# Загрузка и выполнение
	uvm.load_program('./test_task_out.bin')
	uvm.run()

	# Вывод результатов
	print("Результаты тестовой задачи:")
	print("Исходный вектор:", [uvm.memory[1000 + i] for i in range(7)])
	print("Число для сравнения:", uvm.memory[999])
	print("Результат (новый вектор):", [uvm.memory[2000 + i] for i in range(7)])

	# Проверка
	expected = [151, 151, 151, 151, 200, 151, 151]
	actual = [uvm.memory[2000 + i] for i in range(7)]

	if actual == expected:
		print("✓ Тест пройден!")
	else:
		print("✗ Тест не пройден")
		print(f"Ожидалось: {expected}")
		print(f"Получено: {actual}")


if __name__ == '__main__':
	test_task()
	# main_interpreter()