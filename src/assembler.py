import sys
import struct

class Assembler:
	def __init__(self):
		self.commands = []
		self.labels = {}
		self.current_addr = 0


	def ln_parse(self, ln):
		# del whitespaces in start and end
		ln = ln.strip()
		# if ln is empty or is comment -> ret nothing
		if not ln or ln.startswith('#'):
			return None
		
		# comment del
		if '#' in ln:
			ln = ln.split('#')[0].strip()
		
		parts = ln.split()
		# if no parts -> ret nothing
		if not parts:
			return None
		
		opcode = parts[0].lower()
		args = [int(arg) for arg in parts[1:]]

		return {'opcode': opcode, 'args': args}


	def assemble(self, src, out, test_mode = False):
		with open(src, 'r', encoding='utf-8') as f:
			lns = f.readlines()

		# parsing lines and transforming in IR
		# *IR = Intermediate Representation
		ir = []
		for ln in lns:
			ln_parsed = self.ln_parse(ln)
			if ln_parsed:
				ir.append(ln_parsed)
		
		if test_mode:
			print("-+ Intermediate Representation +-")
			
			print()
			for i, cmd in enumerate(ir):
				print(f'CMD {i} : {cmd}')
			print()

			self.test_spec()

		return ir


	def test_spec(self):
		print('Тесты согласно спецификации УВМ:')

		# ldc
		print('\nЗагрузка константы:')
		print('-' * 25)
		print('tst:\tA = 13, B = 492, C = 964')
		print('exp:\t0x8D, 0x3D, 0x00, 0x20, 0x1E, 0x00')
		
		# ldm
		print('\nЧтение значения из памяти:')
		print('-' * 25)
		print('tst:\tA = 31, B = 615, C = 854')
		print('exp:\t0xFF, 0x4C, 0x00, 0xB0, 0x1A, 0x00, 0x00')
		
		# stm
		print('\nЗапись значения в память:')
		print('-' * 25)
		print('tst:\tA = 7, B = 57, C = 8')
		print('exp:\t0x27, 0x07, 0x00, 0x40, 0x00, 0x00, 0x00')
		
		# max
		print('\nБинарная операция max():')
		print('-' * 25)
		print('tst:\tA = 28, B = 481, C = 498, D = 184')
		print('exp:\t0x3C, 0x3C, 0x00, 0x90, 0x0F, 0x00, 0x70, 0x01, 0x00')


def main():
	if len(sys.argv) < 3:
		print('Wrong argv: use `python assembler.py <file_in> <file_out> [--test]`')
		sys.exit(1)

	f_in = sys.argv[1]
	f_out = sys.argv[2]
	test_mode = '--test' in sys.argv

	assembler = Assembler()
	ir = assembler.assemble(f_in, f_out, test_mode)

	if test_mode:
		print('\nРезультат тестирования:')
		for i, cmd in enumerate(ir):
			print(f'{i:3d}: {cmd}')


if __name__ == '__main__':
	main()