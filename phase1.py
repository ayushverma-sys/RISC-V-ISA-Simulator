from bitstring import BitArray

dict_of_format = {
	# instructions of I-Format
	'andi': ['I', '0010011', '111'],
	'addi': ['I', '0010011', '000'],
	'ori': ['I', '0010011', '110'],
	'lb': ['I', '0000011', '000'],
	'lh': ['I', '0000011', '001'],
	'lw': ['I', '0000011', '010'],
	'ld': ['I', '0000011', '011'],
	'jalr': ['I', '1100111', '000'],

	# instructions of S-Format
	'sb': ['S', '0100011', '000'],
	'sh': ['S', '0100011', '001'],
	'sw': ['S', '0100011', '010'],
	'sd': ['S', '0100011', '011'],

	# instructions of R-Format
	'add': ['R', '0110011', '000', '0000000'],
	'and': ['R', '0110011', '111', '0000000'],
	'or': ['R', '0110011', '110', '0000000'],
	'sub': ['R', '0110011', '000', '0100000'],
	'mul': ['R', '0110011', '000', '0000001'],
	'div': ['R', '0110011', '100', '0000001'],
	'sll': ['R', '0110011', '001', '0000000'],
	'slt': ['R', '0110011', '010', '0000000'],
	'xor': ['R', '0110011', '100', '0000000'],
	'srl': ['R', '0110011', '101', '0000000'],
	'sra': ['R', '0110011', '101', '0100000'],
	# 'rem':['R','','','']

	# instructions of U-Format
	'lui': ['U', '0110111'],
	'auipc': ['U', '0010111'],

	# instructions of SB-Format
	'beq': ['SB', '1100011', '000'],
	'bne': ['SB', '1100011', '001'],
	'blt': ['SB', '1100011', '100'],
	'bge': ['SB', '1100011', '101'],

	# instructions of UJ-Format
	'jal': ['UJ', '1101111'],

	# instruction for breakpoint
	'breakpoint': ['special','0000000','000','0000000']
}
input_filepath = './input/input.asm'


def R_Type(instruction):
	instruction = instruction.split()
	opcode = dict_of_format[instruction[0]][1]
	funct3 = dict_of_format[instruction[0]][2]
	funct7 = dict_of_format[instruction[0]][3]
	rd = '{0:05b}'.format(int(instruction[1][1:]))
	rs1 = '{0:05b}'.format(int(instruction[2][1:]))
	rs2 = '{0:05b}'.format(int(instruction[3][1:]))
	machine_code = funct7 + rs2 + rs1 + funct3 + rd + opcode
	return '{0:08X}'.format(int(machine_code, 2))
	

def I_Type(instruction):
	instruction = instruction.split()
	opcode = dict_of_format[instruction[0]][1]
	funct3 = dict_of_format[instruction[0]][2]

	rd = '{0:05b}'.format(int(instruction[1][1:]))
	rs1 = '{0:05b}'.format(int(instruction[2][1:]))
	imm = BitArray(int = int(instruction[3]),length = 12).bin

	machine_code = imm + rs1 + funct3 + rd + opcode
	return '{0:08X}'.format(int(machine_code, 2))


def S_Type(instruction):
	instruction = instruction.split()

	opcode = dict_of_format[instruction[0]][1]
	funct3 = dict_of_format[instruction[0]][2]
	
	rs2 = '{0:05b}'.format(int(instruction[1][1:]))
	rs1 = '{0:05b}'.format(int(instruction[2][1:]))
	imm = BitArray(int = int(instruction[3]),length = 12).bin

	imm1 = imm[7:12]
	imm2 = imm[0:7]

	machine_code = imm2 + rs2 + rs1 + funct3 + imm1 + opcode
	return '{0:08X}'.format(int(machine_code, 2))


def U_Type(instruction):
	instruction = instruction.split()
	opcode = dict_of_format[instruction[0]][1]
	rd = '{0:05b}'.format(int(instruction[1][1:]))
	imm = BitArray(int = int(instruction[2]),length = 32).bin
	imm1 = imm[12:32]
	machine_code = imm1 + rd + opcode
	return '{0:08X}'.format(int(machine_code, 2))


def SB_Type(instruction):
	instruction = instruction.split()
	opcode = dict_of_format[instruction[0]][1]
	funct3 = dict_of_format[instruction[0]][2]
	rs1 = '{0:05b}'.format(int(instruction[1][1:]))
	rs2 = '{0:05b}'.format(int(instruction[2][1:]))
	imm = BitArray(int = int(instruction[3]),length = 13).bin	
	imm1 = imm[0]
	imm2 = imm[1]
	imm3 = imm[2:8]
	imm4 = imm[8:12]
	machine_code = imm1 + imm3 + rs2 + rs1 + funct3 + imm4 + imm2 + opcode
	return '{0:08X}'.format(int(machine_code, 2))


def UJ_Type(instruction):
	instruction = instruction.split()
	opcode = dict_of_format[instruction[0]][1]
	rd = '{0:05b}'.format(int(instruction[1][1:]))
	imm = BitArray(int = int(instruction[2]),length = 32).bin
	imm1 = imm[11]
	imm2 = imm[20]
	imm3 = imm[21:31]
	imm4 = imm[12:20]
	machine_code = imm1 + imm3 + imm2 + imm4 + rd + opcode
	return '{0:08X}'.format(int(machine_code, 2))


def data():
	file_read = open(input_filepath, 'r')
	input = file_read.read()
	data = "\n"
	try:
		data = input[input.find('.data'): input.find('.text')]
	except:
		data = input[input.find('.data'):]
	data = data.split('\n')
	del data[0]

	Data_Memory = {}
	# Variables = {}

	Data_Address = int("0x10000000", 16)
	for data_i in data:
		data_i = data_i.replace(',', ' ')
		data_i = data_i.strip()
		if data_i == '' or data_i[0] == '#':
			data.remove(data_i)
			continue
		if (data_i.find('#') > 0):
			data_i = data_i[0:data_i.find('#')]

		if data_i.find('.word') >= 0:
			for word in (data_i[data_i.find('.word')+5:].strip()).split(' '):
				Data_Memory[Data_Address] = str('{0:08X}'.format(int(word)))
				Data_Address = Data_Address+4
		if data_i.find('.byte') >= 0:
			for byte in (data_i[data_i.find('.byte')+5:].strip()).split(' '):
				Data_Memory[Data_Address] = str('{0:08X}'.format(int(byte)))
				Data_Address = Data_Address+1
		if data_i.find('.half') >= 0:
			for half in (data_i[data_i.find('.half')+5:].strip()).split(' '):
				Data_Memory[Data_Address] = str('{0:08X}'.format(int(half)))
				Data_Address = Data_Address+2
		if data_i.find('.dword') >= 0:
			for dword in (data_i[data_i.find('.dword')+6:].strip()).split(' '):
				Data_Memory[Data_Address] = str('{0:08X}'.format(int(dword)))
				Data_Address = Data_Address+8
		if data_i.find('.asciz') >= 0:
			string = data_i[data_i.find('.asciz')+6:].strip()
			string = string[1:-1]
			for i in range(len(string)):
				Data_Memory[Data_Address] = str('{0:08X}'.format(int(ord(string[i]))))
				Data_Address = Data_Address + 1
		# print(Data_Memory)
	return Data_Memory


def encoder(instruction):
	temp_instruction = instruction.split()
	machine_code = ''
	if dict_of_format[temp_instruction[0]][0] == 'R':
		machine_code = R_Type(instruction)
	elif dict_of_format[temp_instruction[0]][0] == 'I':
		machine_code = I_Type(instruction)
	elif dict_of_format[temp_instruction[0]][0] == 'S':
		machine_code = S_Type(instruction)
	elif dict_of_format[temp_instruction[0]][0] == 'U':
		machine_code = U_Type(instruction)
	elif dict_of_format[temp_instruction[0]][0] == 'SB':
		machine_code = SB_Type(instruction)
	elif dict_of_format[temp_instruction[0]][0] == 'UJ':
		machine_code = UJ_Type(instruction)
	elif dict_of_format[temp_instruction[0]][0] == 'special':
		machine_code = "00000001"
	return machine_code


def original_code_and_labels():
	file_read = open(input_filepath, 'r')
	input = file_read.read()
	# print(input)
	text = ''
	try:
		text = input[input.find('.text')+5:]
	except:
		text = "\n"	
	text = text.split('\n')

	i = 0
	n = len(text)
	label_position = {}
	while (i < n):
		text[i] = text[i].strip()
		if (text[i] == '') or (text[i][0] == '#'):
			del text[i]
			n = n-1
			i = i-1
		try:
			x = text[i].find(':')
			if x > 0:
				text[i] = text[i].strip()
				label_position[text[i][0:x]] = i+1
				if(len(text[i][x+1:]) > 0):
					pass
				else:
					del text[i]
					i = i-1
					n = n-1
		except:
			pass
		i = i+1
	# if len(text) == 0 and len(label_position) == 0:
	# 	return text, 'Info: No instruction to execute',False
	return text, label_position, True


def basic_code(temp_original_code, label_position):
	original_code = []
	original_code = temp_original_code.copy()
	i=0
	n = len(original_code)
	while (i < n):
		original_code[i] = original_code[i].replace(",", '')
		if (original_code[i].find('#') > 0):
			original_code[i] = original_code[i][0:original_code[i].find('#')]
		
		# print(original_code[i])
		if original_code[i] == 'breakpoint' :
			i = i + 1
			continue
		x = original_code[i].find(':')
		if x > 0:
			original_code[i] = original_code[i].strip()
			original_code[i] = original_code[i][x+2:]
			
		instruction = original_code[i].split()
		
		q = 'add and or sll slt sra srl sub xor mul div rem'
		if instruction[0] in q.split():
			if len(instruction) != 4:
				return 'ERROR: Got '+str(len(instruction)-1) + ' arguments but expected 3 in ' + original_code[i], False
			try:
				if instruction[1][0] == 'x' or instruction[2][0] == 'x' or instruction[3][0] == 'x':
					rd = '{0:05b}'.format(int(instruction[1][1:]))
					rs1 = '{0:05b}'.format(int(instruction[2][1:]))
					rs2 = '{0:05b}'.format(int(instruction[3][1:]))
			except:
				return "ERROR: Can't extract register in " + original_code[i], False
		
		q = 'addi andi ori lb lh lw sb sh sw jalr'
		if instruction[0] in q.split():
			if len(instruction) != 4:
				return 'ERROR: Got '+str(len(instruction)-1) + ' arguments but expected 3 in ' + original_code[i], False
			try:
				if instruction[1][0] == 'x' or instruction[2][0] == 'x':
					rd = '{0:05b}'.format(int(instruction[1][1:]))
					rs1 = '{0:05b}'.format(int(instruction[2][1:]))
			except:
				return "ERROR: Can't extract register in " + original_code[i], False
			imm = 0
			if instruction[3][0:2] == '0x':
				imm = int(instruction[3][2:],16)
			elif instruction[3][0:2] == '0b':
				imm = int(instruction[3][2:],2)
			else:
				try:
					imm = int(instruction[3][0:])
				except:
					offset = label_position.get(instruction[3][0:])
					if offset != None:
						imm = int(offset)*4-(i+1)*4
					else :
						return 'ERROR: Label '+instruction[3][0:]+' used but not defined \n'+original_code[i],False
			if (imm >= -2048 and imm <= 2047):
				original_code[i] = original_code[i].replace(instruction[3], str(imm))
			else:
				return 'ERROR: Immediate '+instruction[3]+' (= ' + str(imm) +') out of range (should be between -2048 and 2047) in ' + original_code[i], False
		
		q = 'ld sd'
		if instruction[0] in q.split():
			return 'ERROR: Not Supported Instruction(ld,sd)!',False

		q = 'beq bne bge blt'
		if instruction[0] in q.split():
			if len(instruction) != 4:
				return 'ERROR: Got '+str(len(instruction)-1) + ' arguments but expected 3 in ' + original_code[i], False
			try:
				if instruction[1][0] == 'x' or instruction[2][0] == 'x':
					rs1 = '{0:05b}'.format(int(instruction[1][1:]))
					rs2 = '{0:05b}'.format(int(instruction[2][1:]))
			except:
				return "ERROR: Can't extract register in " + original_code[i], False
		
			label = instruction[-1]
			offset = label_position.get(label)
			if offset != None:
				imm = int(offset)*4-(i+1)*4
				if (imm >= -4096 and imm <= 4094):
					original_code[i] = original_code[i].replace(instruction[3], str(imm))
				else:
					return 'ERROR: Too far to make jump in ' + original_code[i], False
			else:
						return 'ERROR: Label '+label+' used but not defined \n'+original_code[i],False

		q = 'auipc lui'
		if instruction[0] in q.split():
			if len(instruction) != 3:
				return 'ERROR: Got '+str(len(instruction)-1) + ' arguments but expected 2 in ' + original_code[i], False
			try:
				if instruction[1][0] == 'x' :
					rd = '{0:05b}'.format(int(instruction[1][1:]))
			except:
				return "ERROR: Can't extract register in " + original_code[i], False
			imm = 0
			if instruction[2][0:2] == '0x':
				imm = int(instruction[2][2:],16)
			elif instruction[2][0:2] == '0b':
				imm = int(instruction[2][2:],2)
			else:
				try:
					imm = int(instruction[2][0:])
				except:
					offset = label_position.get(instruction[2][0:])
					if offset != None:
						imm = int(offset)*4-(i+1)*4
					else :
						return 'ERROR: Label '+instruction[2][0:]+' used but not defined \n'+original_code[i],False
			
			if (imm >= 0 and imm <= 1048575):
				original_code[i] = original_code[i].replace(instruction[2], str(imm))
			else:
				return 'ERROR: Immediate '+instruction[2]+' (= ' + str(imm) +') out of range (should be between 0 and 1048575) in ' + original_code[i], False

		# q = 'jal'
		if instruction[0] == 'jal':
			if len(instruction) != 3:
				return 'ERROR: Got '+str(len(instruction)-1) + ' arguments but expected 3 in ' + original_code[i], False
			try:
				if instruction[1][0] == 'x':
					rd = '{0:05b}'.format(int(instruction[1][1:]))
			except:
				return "ERROR: Can't extract register in " + original_code[i], False
		
			label = instruction[-1]
			offset = label_position.get(label)
			if offset != None:
				imm = int(offset)*4-(i+1)*4
				if (imm >= -1048576 and imm <= 1048574):
					original_code[i] = original_code[i].replace(instruction[2], str(imm))
				else:
					return 'ERROR: Too far to make jump in ' + original_code[i], False
			else:
				return 'ERROR: Label '+label+' used but not defined \n'+original_code[i],False

		q = 'add and or sll slt sra srl sub xor mul div rem addi andi ori lb lh lw sb sh sw jalr beq bne bge blt auipc lui jal'
		if not instruction[0] in q.split():
			return 'ERROR: Instruction with the name "'+ instruction[0] +'" not found \n' + original_code[i],False
		i = i+1
	return original_code, True


class AssemblerHelper:
	def __init__(self):
		self.text=[]
		self.data = data()
		# self.machine_code=machine_code()
		# self.instruction_info=[]

	def get_original_code_and_label(self):
		return original_code_and_labels()

	def get_basic_code(self, original_code, label_position):
		basic, result = basic_code(original_code, label_position)
		if result == True:
			self.text = basic.copy()
			return basic, result
		else:
			return basic, result

	def get_machine_code(self):
		text_ = self.text.copy()
		machine_code = []
		f = open('output.mc', 'w')
		if len(text_) != 0:
			Text_Address = int("0x00000000", 16)
			for i in range(len(text_)):
				mc = encoder(text_[i])
				machine_code.append(mc)
				f.write('0x'+str('{0:08X}'.format(Text_Address))+' 0x'+mc+'\n')
				Text_Address = Text_Address+4

		if len(self.data)!=0:
			for key, value in self.data.items():
				f.write('0x'+str('{0:08X}'.format(key))+' 0x'+value+'\n')
		f.close()
		return machine_code, True
		# else:
		# 	return basic_code, result


if __name__ == "__main__":
	# text=text()
	# Data_Memory=data()
	# Data_Address = int("0x00000000", 16)
	# f = open('output.mc','w')
	# for i in range(len(text)):
	# 	print(text[i])
	# 	f.write('0x'+str('{0:08X}'.format(Data_Address))+' '+'0x'+encoder(text[i])+'\n')
	# 	Data_Address=Data_Address+4
	# f.close()
	print('CS204')
