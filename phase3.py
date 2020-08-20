from bitstring import BitArray
from memory_register import memory, register
from phase1 import AssemblerHelper


class PipelineExecute:
	def __init__(self):
		self.WB_run = False
		self.MEM_run = False
		self.ALU_run = False
		self.ID_run = False
		self.IF_run = True
		self.stopPipeline = False
		self.wait_time = 0
		self.isBranch = False
		self.isJal = False
		self.stall_type = ''
		self.prediction_result = ''
		self.PC = 0
		self.cycle = 0
		self.prevIR = {}
		self.prevPC = {}
		self.hazard = ''
		self.prevForward_type = {}
		self.prevOperation = {}
		self.total_instr = 0
		self.total_alu_instr = 0
		self.total_data_instr = 0
		self.total_control_instr = 0
		self.total_data_hazard = 0
		self.total_control_hazard = 0
		self.total_misprediction = 0
		self.total_stalls = 0
		self.total_data_stalls = 0
		self.total_control_stalls = 0
		self.cycle_rd = {}
		self.data_hazard = False
		self.RegisterFile = register()
		self.Memory = memory()
		self.knob_forwarding = True
		self.knob_branchPrediction = True
		self.knob_printPipelineRegister = False
		self.knob_specialInstruction = -4
		self.isHit = True
		self.gui = {}
		self.branch_table = {}
		self.IF_ID = {
			'PC': 0,
			'IR': 0,
		}
		self.ID_EX = {
			'RA': 0,
			'RB': 0,
			'RM': 0,
			'rd': "00000",
			'rs1': "00000",
			'rs2': "00000",
			'imm': 0,
			'PC': 0,
			'PC_Temp': 0,
			'B_select': None,
			'Y_select': None,
			'MEM_Read': None,
			'MEM_Write': None,
			'Reg_Write': None,
			'operation': '',
		}
		self.EX_MEM = {
			'rd': "00000",
			'RZ': 0,
			'PC': 0,
			'MAR': 0,
			'MDR': 0,
		}
		self.MEM_WB = {
			'PC': 0,
			'rd': "00000",
			'RY': 0,
		}
		self.WB_end = {
			'PC': 0
		}

	def fetch(self):
		print('Fetch')
		# print('PC:', self.PC)
		try:
			self.Memory.readWord(self.PC)
			IR = self.Memory.readWord(self.PC)
			IR = BitArray(int=IR, length=32).bin
			self.IF_ID['PC'] = self.PC
			self.IF_ID['IR'] = IR
			self.prevIR[self.cycle] = IR
			self.prevPC[self.cycle] = self.PC
			if self.knob_branchPrediction:
				try:
					if self.branch_table[self.PC]['status'] == 'taken':
						self.PC = self.branch_table[self.PC]['PC']
					elif self.branch_table[self.PC]['status'] == 'not taken':
						self.PC = self.PC + 4
				except:
					self.PC = self.PC + 4
			else:
				self.PC = self.PC + 4
			self.ID_run = True
			self.gui[self.cycle].update({'IF': self.IF_ID['PC']})
		except:
			if (not self.ID_run) and (not self.ALU_run) and (not self.MEM_run) and (not self.WB_run):
				self.IF_run = False

	def decode(self):
		self.ID_EX['PC'] = self.IF_ID['PC']
		self.ID_EX['IR'] = self.IF_ID['IR']

		format = self.find_format()
		if format == "r":
			self.decode_R()
		elif format == 'i1':
			self.decode_I1()  # for andi,addi ,ori
		elif format == 'i2':
			self.decode_I2()  # for load
		elif format == 'i3':
			self.decode_I3()  # for jalr
		elif format == 's':
			self.decode_S()
		elif format == "sb":
			self.decode_SB()
		elif format == "u":
			self.decode_U()
		elif format == "uj":
			self.decode_UJ()
		elif format == 'special':
			pass
		self.prevOperation[self.cycle] = self.ID_EX['operation']

		if not self.knob_forwarding:
			if self.cycle_rd[self.cycle - 1] != "00000" and (self.cycle_rd[self.cycle - 1] == self.ID_EX['rs1'] or self.cycle_rd[self.cycle - 1] == self.ID_EX['rs2']):
				self.data_hazard = True
				self.stall_type = "EDF2"
				self.cycle_rd[self.cycle - 1] = "00000"
				if self.ID_EX['rs1'] == self.cycle_rd[self.cycle] or self.ID_EX['rs2'] == self.cycle_rd[self.cycle]:
					self.cycle_rd[self.cycle] = "00000"
				print('hello edf2 data hazard h')
			else:
				if self.cycle_rd[self.cycle - 2] != "00000" and (self.cycle_rd[self.cycle - 2] == self.ID_EX['rs1'] or self.cycle_rd[self.cycle - 2] == self.ID_EX['rs2']):
					self.data_hazard = True
					self.stall_type = "EDF1"
					self.cycle_rd[self.cycle - 2] = "00000"
					if self.ID_EX['rs1'] == self.cycle_rd[self.cycle] or self.ID_EX['rs2'] == self.cycle_rd[self.cycle]:
						self.cycle_rd[self.cycle] = "00000"
					print('hello edf1 data hazard h')
		else:
			if self.prevOperation[self.cycle - 1] != '' and self.cycle_rd[self.cycle - 1] != "00000":
				if self.prevOperation[self.cycle - 1] in "lb lh lw".split():
					if self.prevOperation[self.cycle] in "sb sh sw".split():
						if self.cycle_rd[self.cycle - 1] == self.ID_EX['rs1'] and not self.cycle_rd[self.cycle - 1] == self.ID_EX['rs2']:
							self.prevForward_type[self.cycle] = "Stall"
							self.prevForward_type[self.cycle + 1] = "M2E_A"
							self.prevOperation[self.cycle] = ''
						elif self.cycle_rd[self.cycle - 1] == self.ID_EX['rs2'] and not self.cycle_rd[self.cycle - 1] == self.ID_EX['rs1']:
							self.prevForward_type[self.cycle + 1] = "M2M_B"
						elif self.cycle_rd[self.cycle - 1] == self.ID_EX['rs1'] and self.cycle_rd[self.cycle - 1] == self.ID_EX['rs2']:
							self.prevForward_type[self.cycle] = "Stall"
							self.prevForward_type[self.cycle + 1] = "M2E_AB"
							self.prevOperation[self.cycle] = ''
					elif self.prevOperation[self.cycle] in "lb lh lw".split():
						if self.cycle_rd[self.cycle - 1] == self.ID_EX['rs1']:
							self.prevForward_type[self.cycle] = "Stall"
							self.prevForward_type[self.cycle + 1] = "M2E_A"
							self.prevOperation[self.cycle] = ''
					else:
						self.prevForward_type[self.cycle] = "Stall"
						self.prevOperation[self.cycle] = ''
						if self.cycle_rd[self.cycle - 1] == self.ID_EX['rs1'] and not self.cycle_rd[self.cycle - 1] == self.ID_EX['rs2']:
							self.prevForward_type[self.cycle + 1] = "M2E_A"
						elif self.cycle_rd[self.cycle - 1] == self.ID_EX['rs2'] and not self.cycle_rd[self.cycle - 1] == self.ID_EX['rs1']:
							self.prevForward_type[self.cycle + 1] = "M2M_B"
						elif self.cycle_rd[self.cycle - 1] == self.ID_EX['rs1'] and self.cycle_rd[self.cycle - 1] == self.ID_EX['rs2']:
							self.prevForward_type[self.cycle + 1] = "M2E_AB"
				else:
					if self.prevOperation[self.cycle] in "sb sh sw".split():
						if self.cycle_rd[self.cycle - 1] == self.ID_EX['rs2'] and not self.cycle_rd[self.cycle - 1] == self.ID_EX['rs1']:
							self.prevForward_type[self.cycle + 1] = "M2M_B"
						elif self.cycle_rd[self.cycle - 1] == self.ID_EX['rs1'] and not self.cycle_rd[self.cycle - 1] == self.ID_EX['rs2']:
							self.prevForward_type[self.cycle] = "E2E_A"
						elif self.cycle_rd[self.cycle - 1] == self.ID_EX['rs1'] and self.cycle_rd[self.cycle - 1] == self.ID_EX['rs2']:
							self.prevForward_type[self.cycle] = "E2E_A"
							self.prevForward_type[self.cycle + 1] = "M2M_B"
					else:
						if self.cycle_rd[self.cycle - 1] == self.ID_EX['rs2'] and not self.cycle_rd[self.cycle - 1] == self.ID_EX['rs1']:
							self.prevForward_type[self.cycle] = "E2E_B"
						elif self.cycle_rd[self.cycle - 1] == self.ID_EX['rs1'] and not self.cycle_rd[self.cycle - 1] == self.ID_EX['rs2']:
							self.prevForward_type[self.cycle] = "E2E_A"
						elif self.cycle_rd[self.cycle - 1] == self.ID_EX['rs1'] and self.cycle_rd[self.cycle - 1] == self.ID_EX['rs2']:
							self.prevForward_type[self.cycle] = "E2E_AB"
			if self.prevOperation[self.cycle - 2] != '' and self.cycle_rd[self.cycle - 2] != "00000" and self.cycle_rd[self.cycle - 2] != self.cycle_rd[self.cycle - 1]:
				if self.cycle_rd[self.cycle - 2] == self.ID_EX['rs2'] and not self.cycle_rd[self.cycle - 2] == self.ID_EX['rs1']:
					self.prevForward_type[self.cycle] = self.prevForward_type[self.cycle] + " M2E_B"
				elif self.cycle_rd[self.cycle - 2] == self.ID_EX['rs1'] and not self.cycle_rd[self.cycle - 2] == self.ID_EX['rs2']:
					self.prevForward_type[self.cycle] = self.prevForward_type[self.cycle] + " M2E_A"
				elif self.cycle_rd[self.cycle - 2] == self.ID_EX['rs1'] and self.cycle_rd[self.cycle - 2] == self.ID_EX['rs2']:
					self.prevForward_type[self.cycle] = self.prevForward_type[self.cycle] + " M2E_AB"
		print('Decode')#, 'PC:', self.ID_EX['PC'], self.ID_EX['operation'], 'rd:', self.ID_EX['rd'],
			  #'rs1:', self.ID_EX['rs1'], 'rs2:', self.ID_EX['rs2'], 'imm', self.ID_EX['imm'])

		self.gui[self.cycle].update({'ID': self.ID_EX['PC']})
		self.ALU_run = True
		self.ID_run = False

	def find_format(self):
		IR = self.IF_ID['IR']
		opcode = IR[25:32]
		if(opcode == "0110011"):
			return 'r'
		elif(opcode == "1100011"):
			return 'sb'
		elif(opcode == "0100011"):
			return 's'
		elif(opcode == "1101111"):
			return 'uj'
		elif(opcode == "0010011"):  # for addi,andi & ori
			return 'i1'
		elif(opcode == "0000011"):  # for load instructions
			return 'i2'
		elif(opcode == "1100111"):  # for jalr
			return 'i3'
		elif(opcode == "0110111" or opcode == "0010111"):
			return 'u'
		elif(opcode == "0000000"):
			return 'special'

	def decode_R(self):
		IR = self.IF_ID['IR']
		self.ID_EX['rs1'] = IR[12:17]   # extract the rs1
		self.ID_EX['rs2'] = IR[7:12]    # extract the rs2

		self.ID_EX['rd'] = IR[20:25]
		self.cycle_rd[self.cycle] = self.ID_EX['rd']

		self.ID_EX['RA'] = self.RegisterFile.read(IR[12:17])
		self.ID_EX['RB'] = self.RegisterFile.read(IR[7:12])

		self.ID_EX['B_select'] = 0   # => muxB = RB,  Control Signal
		self.ID_EX['Y_select'] = 0   # => muxY = RZ,  Control Signal
		# => RegisterFile[rd] = RY,  Control Signal
		self.ID_EX['Reg_Write'] = 1
		# => Nothing to read from memory,   Control Signal
		self.ID_EX['MEM_Read'] = 0
		# => Nothing to write in memory,    Control Signal
		self.ID_EX['MEM_Write'] = 0

		funct3 = IR[17:20]
		funct7 = IR[0:7]

		if(funct3 == "111"):
			operation = "and"
		elif(funct3 == "110"):
			operation = "or"
		elif(funct3 == "001"):
			operation = "sll"
		elif(funct3 == "010"):
			operation = "slt"
		elif(funct3 == "000"):
			if(funct7 == "0000000"):
				operation = "add"
			elif(funct7 == "0100000"):
				operation = "sub"
			elif(funct7 == "0000001"):
				operation = "mul"
		elif(funct3 == "100"):
			if(funct7 == "0000001"):
				operation = "div"
			elif(funct7 == "0000000"):
				operation = "xor"
		elif(funct3 == "101"):
			if(funct7 == "0000000"):
				operation = "srl"
			elif(funct7 == "0100000"):
				operation = "sra"

		self.ID_EX['operation'] = operation

	def decode_I1(self):            # for addi, andi & ori
		IR = self.IF_ID['IR']
		rs1 = IR[12:17]       # extract the rs1
		self.ID_EX['rd'] = IR[20:25]       # rxtract the rd
		self.cycle_rd[self.cycle] = self.ID_EX['rd']
		self.ID_EX['imm'] = BitArray(
			bin=IR[0:12]).int      # converting imm to int

		# this value will come from register file after reading file at rs1 address
		self.ID_EX['RA'] = self.RegisterFile.read(rs1)
		self.ID_EX['rs1'] = rs1
		self.ID_EX['rs2'] = "00000"
		# => muxB = imm, Control Signal
		self.ID_EX['B_select'] = 1
		# => muxY = RZ,  Control Signal
		self.ID_EX['Y_select'] = 0
		# => RegisterFile[rd] = RY,  Control Signal
		self.ID_EX['Reg_Write'] = 1
		# => Nothing to read from memory,   Control Signal
		self.ID_EX['MEM_Read'] = 0
		# => Nothing to write in memory,    Control Signal
		self.ID_EX['MEM_Write'] = 0

		funct3 = IR[17:20]

		if(funct3 == "000"):
			operation = "addi"
		elif(funct3 == "111"):
			operation = "andi"
		elif(funct3 == "110"):
			operation = "ori"

		self.ID_EX['operation'] = operation

	def decode_I2(self):            # for Load instructions
		IR = self.IF_ID['IR']
		rs1 = IR[12:17]       # extract the rs1
		self.ID_EX['rd'] = IR[20:25]        # rxtract the rd
		self.cycle_rd[self.cycle] = self.ID_EX['rd']
		self.ID_EX['imm'] = BitArray(
			bin=IR[0:12]).int     # converting imm to int

		# this value will come from register file after reading file at rs1 address
		self.ID_EX['RA'] = self.RegisterFile.read(rs1)
		self.ID_EX['rs1'] = rs1
		self.ID_EX['rs2'] = "00000"
		# => muxB = imm, Control Signal
		self.ID_EX['B_select'] = 1
		# => muxY = MDR,  Control Signal
		self.ID_EX['Y_select'] = 1
		# => RegisterFile[rd] = RY,  Control Signal
		self.ID_EX['Reg_Write'] = 1
		# => Read from memory,   Control Signal
		self.ID_EX['MEM_Read'] = 1
		# => Nothing to write in memory,    Control Signal
		self.ID_EX['MEM_Write'] = 0

		funct3 = IR[17:20]

		if(funct3 == "000"):
			operation = "lb"
		elif(funct3 == "001"):
			operation = "lh"
		elif(funct3 == "010"):
			operation = "lw"
		elif(funct3 == "011"):
			operation = "ld"

		self.ID_EX['operation'] = operation

	def decode_I3(self):            # for jalr instruction
		IR = self.IF_ID['IR']
		rs1 = IR[12:17]       # extract the rs1
		self.ID_EX['rd'] = IR[20:25]        # rxtract the rd
		self.cycle_rd[self.cycle] = self.ID_EX['rd']
		imm = BitArray(bin=IR[0:12]).int
		self.ID_EX['imm'] = imm     # converting imm to int

		# this value will come from register file after reading file at rs1 address
		RA = self.RegisterFile.read(rs1)
		self.ID_EX['RA'] = RA
		self.ID_EX['rs1'] = rs1
		self.ID_EX['rs2'] = "00000"
		# => muxB = imm, Control Signal
		self.ID_EX['B_select'] = 1
		# => muxY = PC_Temp,  Control Signal
		self.ID_EX['Y_select'] = 2
		# => RegisterFile[rd] = RY,  Control Signal
		self.ID_EX['Reg_Write'] = 1
		# => Nothing to read from memory,   Control Signal
		self.ID_EX['MEM_Read'] = 0
		# => Nothing to write in memory,    Control Signal
		self.ID_EX['MEM_Write'] = 0

		funct3 = IR[17:20]
		operation = "jalr"
		self.ID_EX['operation'] = operation

	def decode_S(self):             # for Store instructions
		IR = self.IF_ID['IR']
		rs1 = IR[12:17]                   # extract the rs1
		rs2 = IR[7:12]                    # extract the rs2

		# extract imm from two locations by concatenating them
		self.ID_EX['imm'] = BitArray(bin=IR[0:7]+IR[20:25]).int

		# this value will come from register file after reading file at rs1 address
		self.ID_EX['RA'] = self.RegisterFile.read(rs1)
		# this value will come from register file after reading file at rs2 address
		self.ID_EX['RB'] = self.RegisterFile.read(rs2)

		self.ID_EX['RM'] = self.ID_EX['RB']
		self.ID_EX['rs1'] = rs1
		self.ID_EX['rs2'] = rs2

		# => muxB = imm, Control Signal
		self.ID_EX['B_select'] = 1
		# => muxY = None,  Control Signal
		self.ID_EX['Y_select'] = None
		# => Nothing to write in register file,  Control Signal
		self.ID_EX['Reg_Write'] = 0
		# => Read from memory,   Control Signal
		self.ID_EX['MEM_Read'] = 1
		# => Write in memory,    Control Signal
		self.ID_EX['MEM_Write'] = 1

		funct3 = IR[17:20]

		if(funct3 == "000"):
			operation = "sb"
		elif(funct3 == "001"):
			operation = "sh"
		elif(funct3 == "010"):
			operation = "sw"
		elif(funct3 == "011"):
			operation = "sd"

		self.ID_EX['operation'] = operation

	def decode_SB(self):            # for branch intructions
		IR = self.IF_ID['IR']
		rs1 = IR[12:17]   # extract the rs1
		rs2 = IR[7:12]    # rxtract the rs2
		# extract imm from four locations by concatenating them,0 at last because it is initially ignored
		self.ID_EX['imm'] = BitArray(
			bin=IR[0]+IR[24]+IR[1:7]+IR[20:24]+"0").int

		self.ID_EX['RA'] = self.RegisterFile.read(rs1)
		self.ID_EX['RB'] = self.RegisterFile.read(rs2)
		self.ID_EX['rs1'] = rs1
		self.ID_EX['rs2'] = rs2

		# => muxB = imm, Control Signal
		self.ID_EX['B_select'] = 1
		# => muxY = None,  Control Signal
		self.ID_EX['Y_select'] = None
		# => Nothing to write in register file,  Control Signal
		self.ID_EX['Reg_Write'] = 0
		# => Nothing to read from memory,   Control Signal
		self.ID_EX['MEM_Read'] = 0
		# => Nothing to write in memory,    Control Signal
		self.ID_EX['MEM_Write'] = 0

		funct3 = IR[17:20]
		if(funct3 == "000"):
			operation = "beq"
		elif(funct3 == "001"):
			operation = "bne"
		elif(funct3 == "100"):
			operation = "blt"
		elif(funct3 == "101"):
			operation = "bge"

		self.ID_EX['operation'] = operation

	def decode_U(self):             # for lui,auipc
		IR = self.IF_ID['IR']
		self.ID_EX['rd'] = IR[20:25]        # extract the rd
		self.cycle_rd[self.cycle] = self.ID_EX['rd']
		self.ID_EX['imm'] = BitArray(bin=IR[0:20] + "000000000000").int

		self.ID_EX['RA'] = 0
		self.ID_EX['rs1'] = "00000"
		self.ID_EX['rs2'] = "00000"
		# => muxB = imm, Control Signal
		self.ID_EX['B_select'] = 1
		# => muxY = RZ,  Control Signal
		self.ID_EX['Y_select'] = 0
		# => RegisterFile[rd] = RY,  Control Signal
		self.ID_EX['Reg_Write'] = 1
		# => Nothing to read from memory,   Control Signal
		self.ID_EX['MEM_Read'] = 0
		# => Nothing to write in memory,    Control Signal
		self.ID_EX['MEM_Write'] = 0

		funct7 = IR[25:32]

		if(funct7 == "0110111"):
			operation = "lui"
		elif(funct7 == "0010111"):
			operation = "auipc"

		self.ID_EX['operation'] = operation

	def decode_UJ(self):            # for jal
		IR = self.IF_ID['IR']
		self.ID_EX['rd'] = IR[20:25]        # extract the rd
		self.cycle_rd[self.cycle] = self.ID_EX['rd']
		imm = BitArray(bin=IR[0]+IR[11:19]+IR[19]+IR[1:11]+"0").int
		self.ID_EX['imm'] = imm

		self.ID_EX['rs1'] = "00000"
		self.ID_EX['rs2'] = "00000"

		# => muxB = imm, Control Signal
		self.ID_EX['B_select'] = 1
		# => muxY = PC_Temp,  Control Signal
		self.ID_EX['Y_select'] = 2
		# => RegisterFile[rd] = RY,  Control Signal
		self.ID_EX['Reg_Write'] = 1
		# => Nothing to read from memory,   Control Signal
		self.ID_EX['MEM_Read'] = 0
		# => Nothing to write in memory,    Control Signal
		self.ID_EX['MEM_Write'] = 0

		operation = "jal"
		# Updating PC in decode stage to increase instruction throughput.
		self.ID_EX['operation'] = operation

	def alu(self):
		self.EX_MEM = {**self.EX_MEM, **self.ID_EX}
		RA = self.ID_EX['RA']
		RB = self.ID_EX['RB']
		RM = self.ID_EX['RM']
		imm = self.ID_EX['imm']
		B_select = self.ID_EX['B_select']
		operation = self.ID_EX['operation']
		if operation == "add" and B_select == 0:
			self.EX_MEM['RZ'] = RA + RB
		elif operation == "and" and B_select == 0:
			self.EX_MEM['RZ'] = RA & RB
		elif operation == "or" and B_select == 0:
			self.EX_MEM['RZ'] = RA | RB
		elif operation == "sub" and B_select == 0:
			self.EX_MEM['RZ'] = RA - RB
		elif operation == "mul" and B_select == 0:
			self.EX_MEM['RZ'] = RA * RB
		elif operation == "div" and B_select == 0:
			self.EX_MEM['RZ'] = RA // RB
		elif operation == "xor" and B_select == 0:
			self.EX_MEM['RZ'] = RA ^ RB
		elif operation == "sll" and B_select == 0:
			self.EX_MEM['RZ'] = RA << RB
		elif operation == "srl" and B_select == 0:
			self.EX_MEM['RZ'] = RA >> RB
		elif operation == "slt" and B_select == 0:
			self.EX_MEM['RZ'] = 1 if RA < RB else 0
		elif operation == "sra" and B_select == 0:
			self.EX_MEM['RZ'] = RA >> RB

		elif operation == "addi" and B_select == 1:
			self.EX_MEM['RZ'] = RA + imm
		elif operation == "andi" and B_select == 1:
			self.EX_MEM['RZ'] = RA & imm
		elif operation == "ori" and B_select == 1:
			self.EX_MEM['RZ'] = RA | imm

		elif operation == "lui" and B_select == 1:
			self.EX_MEM['RZ'] = imm
		elif operation == "auipc" and B_select == 1:
			self.EX_MEM['RZ'] = self.PC + imm - 8

		elif operation in "beq bge blt bne".split() and B_select == 1:
			PC = self.PC + imm - 8
			if (operation == "beq" and RA == RB) or (operation == "bge" and RA >= RB) or (operation == "blt" and RA < RB) or (operation == "bne" and RA != RB):
				self.EX_MEM['PC_Temp'] = PC
				self.isBranch = True
				try:
					if self.branch_table[self.EX_MEM['PC']]['status'] == 'taken':
						self.isHit = True
					elif self.branch_table[self.EX_MEM['PC']]['status'] == 'not taken':
						self.isHit = False
						self.branch_table[self.EX_MEM['PC']] = {'status': 'taken', 'PC': PC}
				except:
					self.branch_table[self.EX_MEM['PC']] = {'status': 'taken', 'PC': PC}
					self.isHit = False
			else:
				try:
					if self.branch_table[self.EX_MEM['PC']]['status'] == 'not taken':
						self.isHit = True
					elif self.branch_table[self.EX_MEM['PC']]['status'] == 'taken':
						self.isHit = False
						self.branch_table[self.EX_MEM['PC']] = {'status': 'not taken', 'PC': PC}
				except:
					self.branch_table[self.EX_MEM['PC']] = {'status': 'not taken', 'PC': PC}
					self.isHit = True

		elif operation == "jal" and B_select == 1:
			self.EX_MEM['PC_Temp'] = self.EX_MEM['PC'] + 4
			PC = self.PC + imm - 8
			self.isJal = True
			try:
				if self.branch_table[self.EX_MEM['PC']]['status'] == 'taken':
					self.isHit = True
			except:
				self.branch_table[self.EX_MEM['PC']] = {'status': 'taken', 'PC': PC}
				self.isHit = False
		
		elif operation == "jalr" and B_select == 1:
			self.EX_MEM['PC_Temp'] = self.EX_MEM['PC'] + 4
			PC = RA + imm
			self.isJal = True
			try:
				if self.branch_table[self.EX_MEM['PC']]['status'] == 'taken':
					if self.branch_table[self.EX_MEM['PC']]['PC'] == PC:
						self.isHit = True
					else:
						self.branch_table[self.EX_MEM['PC']] = {'status': 'taken', 'PC': PC}
						self.isHit = False
			except:
				self.branch_table[self.EX_MEM['PC']] = {'status': 'taken', 'PC': PC}
				self.isHit = False

		elif operation in "lb lh lw ld sb sh sw sd".split() and B_select == 1:
			self.EX_MEM['RZ'] = RA + imm
			self.EX_MEM['MAR'] = self.EX_MEM['RZ']
			if operation in "sb sh sw sd".split():
				self.EX_MEM['MDR'] = RM

		print('Alu')#, 'PC:', self.EX_MEM['PC'], operation, 'rd:', self.EX_MEM['rd'],
			  #'rs1:', self.EX_MEM['rs1'], 'rs2:', self.EX_MEM['rs2'])

		self.ALU_run = False
		self.MEM_run = True
		self.gui[self.cycle].update({'EX': self.EX_MEM['PC']})

	def memory_access(self):
		self.MEM_WB = {**self.MEM_WB, **self.EX_MEM}
		MAR = self.EX_MEM['MAR']
		MDR = self.EX_MEM['MDR']
		operation = self.EX_MEM['operation']
		if self.EX_MEM['B_select'] == 1:
			# for load instructions
			if self.EX_MEM['MEM_Read'] == 1 and self.EX_MEM['MEM_Write'] == 0:
				if operation == "lb":
					MDR = self.Memory.readByte(MAR)  # lb
				elif operation == "lw":
					MDR = self.Memory.readWord(MAR)  # lw
				elif operation == "lh":
					MDR = self.Memory.readHalfWord(MAR)  # lh

			# for store instructions
			elif self.EX_MEM['MEM_Read'] == 1 and self.EX_MEM['MEM_Write'] == 1:
				if operation == "sb":  # sb
					self.Memory.writeByte(MAR, MDR)
				elif operation == "sw":  # sw
					self.Memory.writeWord(MAR, MDR)
				elif operation == "sh":  # sh
					self.Memory.writeHalfWord(MAR, MDR)

		if self.EX_MEM['Y_select'] == 0:
			self.MEM_WB['RY'] = self.EX_MEM['RZ']
		elif self.EX_MEM['Y_select'] == 1:
			self.MEM_WB['RY'] = MDR
		elif self.EX_MEM['Y_select'] == 2:
			self.MEM_WB['RY'] = self.EX_MEM['PC_Temp']
		print('Memory')#, 'PC:', self.MEM_WB['PC'], operation, 'rd:', self.MEM_WB['rd'],
			  #'rs1:', self.MEM_WB['rs1'], 'rs2:', self.MEM_WB['rs2'])

		self.MEM_run = False
		self.WB_run = True
		self.gui[self.cycle].update({'MEM': self.MEM_WB['PC']})

	def write_back(self):
		self.WB_end = {**self.WB_end, **self.MEM_WB}
		self.total_instr = self.total_instr + 1
		if self.WB_end['operation'] in "beq bne blt bge jal jalr".split():
			self.total_control_instr = self.total_control_instr + 1
		elif self.WB_end['operation'] in "lb lh lw sb sh sw".split():
			self.total_data_instr = self.total_data_instr + 1
		else:
			self.total_alu_instr = self.total_alu_instr + 1 
		if self.WB_end['Reg_Write'] == 1:
			self.RegisterFile.write(self.WB_end['rd'], self.WB_end['RY'])
		print('Wrie Back')#, 'PC:', self.WB_end['PC'], self.WB_end['operation'], 'rd:', self.WB_end['rd'],
			  #'rs1:', self.WB_end['rs1'], 'rs2:', self.WB_end['rs2'])

		self.WB_run = False
		self.gui[self.cycle].update({'WB': self.WB_end['PC']})

	def flush(self):
		if self.cycle == 0 or self.cycle == 1:
			return
		if self.knob_branchPrediction:
			if self.isHit == False:
				self.ID_run = False
				self.ALU_run = False
				self.cycle_rd[self.cycle-1] = "00000"
				self.prevOperation[self.cycle] = ''
				self.wait_time = 0
				self.stall_type = ''
				self.isHit = True
				self.total_control_hazard = self.total_control_hazard + 1
				self.total_misprediction = self.total_misprediction + 1
				self.prediction_result = 'Miss'
				if self.prevOperation[self.cycle-1] in "jal jalr".split():
					try:
						self.PC = self.branch_table[self.EX_MEM['PC']]['PC']
					except:pass
				if self.prevOperation[self.cycle-1] in "beq bne blt bge".split():
					try:
						if self.branch_table[self.EX_MEM['PC']]['status'] == 'taken':
							self.PC = self.branch_table[self.EX_MEM['PC']]['PC']
						elif self.branch_table[self.EX_MEM['PC']]['status'] == 'not taken':
							self.PC = self.EX_MEM['PC'] + 4
					except:pass
		else:
			if self.isBranch or self.isJal:
				if self.isBranch:
					print('flushing because of beq_bge_blt_bne')
					self.isBranch = False
				if self.isJal:
					print('flushing because of jal_jalr')
					self.isJal = False
				if self.branch_table[self.EX_MEM['PC']]['status'] == 'taken':
					self.ID_run = False
					self.ALU_run = False
					self.cycle_rd[self.cycle-1] = "00000"
					self.wait_time = 0
					self.stall_type = ''
					self.prevOperation[self.cycle] = ''
					self.PC = self.branch_table[self.EX_MEM['PC']]['PC']
					self.total_control_hazard = self.total_control_hazard + 1

		if self.stall_type != '' and self.wait_time == 0:
			self.stall_type = ''
		if self.wait_time != 0:
			self.wait_time = self.wait_time - 1
			self.total_stalls = self.total_stalls + 1
			if self.prevOperation[self.cycle] in 'beq bne blt bge'.split():
				self.total_control_stalls = self.total_control_stalls + 1
			else:
				self.total_data_stalls = self.total_data_stalls + 1

	def stall(self):
		if self.data_hazard:
			self.data_hazard = False
			self.total_data_hazard = self.total_data_hazard + 1
			if self.knob_branchPrediction and self.isHit == False:
				return
			elif (not self.knob_branchPrediction) and (self.isBranch or self.isJal):
				return

			if self.stall_type == "EDF2" and self.wait_time == 0:
				self.wait_time = 2
			elif self.stall_type == "EDF1" and self.wait_time == 0:
				self.wait_time = 1

		if self.stall_type == "EDF2" and self.wait_time == 2:
			print('first')
			self.ALU_run = False
			self.IF_ID['IR'] = self.prevIR[self.cycle-1]
			self.IF_ID['PC'] = self.prevPC[self.cycle-1]
			try:
				self.PC = self.prevPC[self.cycle]
			except:
				self.ID_run = True
		elif self.stall_type == "EDF2" and self.wait_time == 1:
			print('second')
			self.ALU_run = False
			self.IF_ID['IR'] = self.prevIR[self.cycle-2]
			self.IF_ID['PC'] = self.prevPC[self.cycle-2]
			try:
				self.PC = self.prevPC[self.cycle - 1]
			except:
				self.ID_run = True
			if self.ID_EX['rs1'] == self.cycle_rd[self.cycle] or self.ID_EX['rs2'] == self.cycle_rd[self.cycle]:
				self.cycle_rd[self.cycle] = "00000"
		elif self.stall_type == "EDF1" and self.wait_time == 1:
			self.ALU_run = False
			self.IF_ID['IR'] = self.prevIR[self.cycle-1]
			self.IF_ID['PC'] = self.prevPC[self.cycle-1]
			try:
				self.PC = self.prevPC[self.cycle]
			except:
				self.ID_run = True

	def forward(self):
		if self.prevForward_type[self.cycle] != '':
			for forward_type in self.prevForward_type[self.cycle].split():
				# E2E forwarding
				if forward_type == 'E2E_A':
					self.ID_EX['RA'] = self.EX_MEM['RZ']
				if forward_type == 'E2E_B':
					self.ID_EX['RB'] = self.EX_MEM['RZ']
				if forward_type == 'E2E_AB':
					self.ID_EX['RA'] = self.EX_MEM['RZ']
					self.ID_EX['RB'] = self.EX_MEM['RZ']
				# M2E forwarding
				if forward_type == 'M2E_A':
					self.ID_EX['RA'] = self.MEM_WB['RY']
				if forward_type == 'M2E_B':
					self.ID_EX['RB'] = self.MEM_WB['RY']
				if forward_type == 'M2E_AB':
					self.ID_EX['RA'] = self.MEM_WB['RY']
					self.ID_EX['RB'] = self.MEM_WB['RY']
				# M2M forwarding
				if forward_type == 'M2M_B':
					self.EX_MEM['MDR'] = self.MEM_WB['RY']
				# Stalling
				if forward_type == 'Stall':
					self.data_hazard = True
					self.stall_type = 'EDF1'
					self.stall()

	def runStep(self):
		self.gui[self.cycle] = {}
		self.cycle_rd[self.cycle] = "00000"
		self.prevOperation[self.cycle] = ''
		if self.knob_branchPrediction:
			self.prediction_result = 'Hit'
		else:
			self.prediction_result = 'Prediction Enabled'
		print('----------Cycle:', self.cycle + 1,'--------------------------------------------------')
		# print(self.IF_run,self.ID_run,self.ALU_run,self.MEM_run,self.WB_run)
		try:
			if self.prevForward_type[self.cycle] != '':
				self.prevForward_type[self.cycle] = self.prevForward_type[self.cycle] + ' '
		except:
			self.prevForward_type[self.cycle] = ''

		# self.flush()

		if self.WB_run:
			self.write_back()
			if self.knob_printPipelineRegister:
				print('PC:',self.WB_end['PC'],'rd:',self.WB_end['rd'])
			else:
				if self.knob_specialInstruction*4 == self.WB_end['PC']+4:
					print('PC:',self.WB_end['PC'],'rd:',self.WB_end['rd'])

		if self.MEM_run:
			self.memory_access()
			if self.knob_printPipelineRegister:
				print('-----MEM/WB-- PC:',self.MEM_WB['PC'],'rd:',self.MEM_WB['rd'],'RY:',self.MEM_WB['RY'])
			else:
				if self.knob_specialInstruction*4 == self.MEM_WB['PC']+4:
					print('-----MEM/WB-- PC:',self.MEM_WB['PC'],'rd:',self.MEM_WB['rd'],'RY:',self.MEM_WB['RY'])
		
		if self.ALU_run:
			self.alu()
			if self.knob_printPipelineRegister:
				print('-----EX/MEM-- PC:',self.EX_MEM['PC'],'rd:',self.EX_MEM['rd'],'RZ:',self.EX_MEM['RZ'])
			else:
				if self.knob_specialInstruction*4 == self.EX_MEM['PC']+4:
					print('-----EX/MEM-- PC:',self.EX_MEM['PC'],'rd:',self.EX_MEM['rd'],'RZ:',self.EX_MEM['RZ'])
		
		if self.ID_run:
			self.decode()
			if self.knob_printPipelineRegister:
				print('-----ID/EX-- PC:',self.ID_EX['PC'],'rd:',self.ID_EX['rd'],'RA:',self.ID_EX['RA'],'RB:',self.ID_EX['RB'],'Imm:',self.ID_EX['imm'],
				'B_select:',self.ID_EX['B_select'],'Y_select:',self.ID_EX['Y_select'],'Reg_Write:',self.ID_EX['Reg_Write'],'MEM_Read:',self.ID_EX['MEM_Read'],
				'MEM_Write:',self.ID_EX['MEM_Write'])
			else:
				if self.knob_specialInstruction*4 == self.ID_EX['PC']+4:
					print('-----ID/EX-- PC:',self.ID_EX['PC'],'rd:',self.ID_EX['rd'],'RA:',self.ID_EX['RA'],'RB:',self.ID_EX['RB'],'Imm:',self.ID_EX['imm'],
					'B_select:',self.ID_EX['B_select'],'Y_select:',self.ID_EX['Y_select'],'Reg_Write:',self.ID_EX['Reg_Write'],'MEM_Read:',self.ID_EX['MEM_Read'],
					'MEM_Write:',self.ID_EX['MEM_Write'])

		if self.IF_run:
			self.fetch()
			if self.knob_printPipelineRegister:
				print('-----IF/ID-- PC:',self.IF_ID['PC'],'IR:',self.IF_ID['IR'])
			else:
				if self.knob_specialInstruction*4 == self.IF_ID['PC']+4:
					print('-----IF/ID-- PC:',self.IF_ID['PC'],'IR:',self.IF_ID['IR'])

		if self.knob_forwarding:
			self.forward()
		else:
			self.stall()
		self.flush()

		self.cycle = self.cycle+1

		print(self.branch_table)
		if self.returnCondition():
			self.stopPipeline = True
		return 'EXIT', self.cycle

	def assemble(self, mc_code, forwarding, branchPrediction, printPipelineRegister, specialInstruciton):
		self.mc_code = mc_code
		self.knob_forwarding = forwarding
		self.knob_branchPrediction = branchPrediction
		self.knob_printPipelineRegister = printPipelineRegister
		self.knob_specialInstruction = specialInstruciton

		self.PC = 0
		self.cycle = 0
		self.wait_time = 0

		self.total_instr = 0
		self.total_alu_instr = 0
		self.total_data_instr = 0
		self.total_control_instr = 0
		self.total_data_hazard = 0
		self.total_control_hazard = 0
		self.total_misprediction = 0
		self.total_stalls = 0
		self.total_data_stalls = 0
		self.total_control_stalls = 0

		self.gui.clear()
		self.Memory.flush()
		self.prevIR.clear()
		self.prevPC.clear()
		self.cycle_rd.clear()
		self.RegisterFile.flush()
		self.prevForward_type.clear()
		
		self.isHit = True
		self.isJal = False
		self.isBranch = False
		self.prediction_result = ''

		self.data_hazard = False
		self.stall_type = ''
		self.hazard = ''

		self.WB_run = False
		self.MEM_run = False
		self.ALU_run = False
		self.ID_run = False
		self.IF_run = True
		self.stopPipeline = False		
		
		self.RegisterFile.write("00010", 0x7ffffff0)
		self.RegisterFile.write("00011", 0x10000000)
		self.initialise_pipeline_register()
		
		mc = self.mc_code.splitlines()
		for line in mc:
			try:
				address, value = line.split()
				address = int(address, 16)
				value = BitArray(hex=value).int
				self.Memory.writeWord(address, value)
			except:
				return "fail"

	def initialise_pipeline_register(self):
		self.IF_ID.clear()
		self.ID_EX.clear()
		self.EX_MEM.clear()
		self.MEM_WB.clear()
		self.WB_end.clear()
		self.branch_table.clear()
		self.prevOperation.clear()
		self.prevOperation[1] = ''
		self.prevOperation[0] = ''
		self.prevOperation[-1] = ''
		self.cycle_rd[-1] = "00000"
		self.cycle_rd[-2] = "00000"
		self.IF_ID = {
			'PC': 0,
			'IR': 0,
		}
		self.ID_EX = {
			'RA': 0,
			'RB': 0,
			'RM': 0,
			'rd': "00000",
			'rs1': "00000",
			'rs2': "00000",
			'imm': 0,
			'PC': 0,
			'PC_Temp': 0,
			'B_select': None,
			'Y_select': None,
			'MEM_Read': None,
			'MEM_Write': None,
			'Reg_Write': None,
			'operation': '',
		}
		self.EX_MEM = {
			'rd': "00000",
			'RZ': 0,
			'PC': 0,
			'MAR': 0,
			'MDR': 0,
		}
		self.MEM_WB = {
			'PC': 0,
			'rd': "00000",
			'RY': 0,
		}
		self.WB_end = {
			'PC': 0
		}
		
	def returnCondition(self):
		if (not self.IF_run) and (not self.ID_run) and (not self.ALU_run) and (not self.MEM_run) and (not self.WB_run):
			return True
		return False

	def run(self):
		while not self.stopPipeline:
			result, cycle = self.runStep()
		self.stopPipeline = False
		return self.cycle

	def getRegister(self):
		return self.RegisterFile.getRegisters()

	def getMemory(self):
		return self.Memory.get_Memory()

	def next_Instruction(self):
		return self.gui[self.cycle-1]

	def prev_Instruction(self):
		return ('{0:X}'.format(int(0)))

	def printMemory(self):
		self.Memory.printall()

	def getDaigram(self):
		return self.gui

	def getForwardingPath(self):
		if self.knob_forwarding:
			if len(self.prevForward_type[self.cycle - 1]) == 0:
				return 'no_forwarding'
			else:
				if len(self.prevForward_type[self.cycle - 1].split()) == 1:
					if self.prevForward_type[self.cycle - 1].strip()[0:3] in "M2M M2E E2E".split():
						return self.prevForward_type[self.cycle - 1].strip()[0:3]
					elif self.prevForward_type[self.cycle - 1].strip() == 'Stall':
						return 'no_forwarding'
				else:
					forwarding_type = self.prevForward_type[self.cycle - 1].split()
					if forwarding_type[0].strip()[0:3] == "M2M":
						if forwarding_type[1].strip()[0:3] == "M2E":
							return "M2M_M2E"
						elif forwarding_type[1].strip()[0:3] == "E2E":
							return "M2M_E2E"
						elif forwarding_type[1].strip()[0:3] == "M2M":
							return "M2M"
					elif forwarding_type[0].strip()[0:3] == "E2E":
						if forwarding_type[1].strip()[0:3] == "M2E":
							return "M2E_E2E"
						elif forwarding_type[1].strip()[0:3] == "E2E":
							return "E2E"
						elif forwarding_type[1].strip()[0:3] == "M2M":
							return "M2M_E2E"
					elif forwarding_type[0].strip()[0:3] == "M2E":
						if forwarding_type[1].strip()[0:3] == "M2E":
							return "E2E"
						elif forwarding_type[1].strip()[0:3] == "E2E":
							return "M2E_E2E"
						elif forwarding_type[1].strip()[0:3] == "M2M":
							return "M2M_M2E"
		else:
			return 'no_forwarding'

	def getCycleInfo(self):
		CPI=float(0)
		if self.total_instr!=0:
			CPI = float(self.cycle)/self.total_instr
			CPI = "{:.2f}".format(CPI)
		return self.prediction_result, self.hazard,self.cycle,self.total_instr,CPI,self.total_alu_instr,self.total_data_instr,self.total_control_instr,self.total_data_hazard,self.total_control_hazard,self.total_misprediction,self.total_stalls,self.total_data_stalls,self.total_control_stalls

	def reset(self):
		self.assemble(self.mc_code,self.knob_forwarding, self.knob_branchPrediction, self.knob_printPipelineRegister, self.knob_specialInstruciton)

if __name__ == "__main__":
	p = PipelineExecute()
	Phase1_helper = AssemblerHelper()
	original_code, labels, result1 = Phase1_helper.get_original_code_and_label()
	basic_code, result1 = Phase1_helper.get_basic_code(original_code, labels)
	machine_code, result3 = Phase1_helper.get_machine_code()
	file_read = open('output.mc', 'r')
	mc = file_read.read()
	p.assemble(mc)
	# print('cycle:',p.cycle,p.PC,p.ID_EX['rd'],p.EX_MEM['rd'],p.MEM_WB['rd'])
	x = p.run()
