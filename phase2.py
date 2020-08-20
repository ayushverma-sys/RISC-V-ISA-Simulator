from bitstring import BitArray
from memory_register import memory, register


class Non_PipelineExecute:
	def __init__(self):
		# stack pointer is sp.
		self.PC = 0
		self.IR = None
		self.PC_Temp = None
		self.PC_prev = 0 # previous pc
		self.prevPC = 0
		# rs1,rs2,rd are addresses of registers while RA,RB,RY(in case of R-format) hold their values,
		# loaded from register file ,respectively
		self.rs1 = None
		self.rs2 = None
		self.rd = None
		self.imm = None
		# instruction will be identified by the help of opcode, funct7 and funct3
		self.opcode = None
		self.funct7 = None
		self.funct3 = None
		# self.cycle to record the cycle count in execution of instructions.
		self.cycle = 0
		# interstage buffer registers
		self.RB = None
		self.RA = None
		self.RZ = None
		self.RY = None
		self.RM = None
		# Registers for PROCESSOR-MEMORY INTERFACE
		self.MDR = None
		self.MAR = None
		# Reg_Write = 1 implies write in register address rd in writeBack stage
		self.Reg_Write = 0
		# operation determines which operation is performed by ALU unit, and is set in decode stage
		self.operation = None
		# Control signal for muxB is B_select, B_select = 0,for 'add' and for 'add_i',B_select = 1
		self.B_select = 0
		# Control signal for muxY is Y_select, Y_select=0 => RY=RZ, Y_select=1 => RY=MDR, Y_select=2 => RY=PC_Temp
		self.Y_select = 0
		# MEM_read and MEM_Write are used to initiate a memory Read or a memory Write operation.
		self.MEM_Read = 0
		self.MEM_Write = 0

		self.RegisterFile = register()
		self.Memory = memory()
		self.gui = {}
		self.mc_code=''
		self.total_instr = 0
		self.total_alu_instr = 0
		self.total_data_instr = 0
		self.total_control_instr = 0

	def assemble(self,mc_code):
		self.RegisterFile.flush()
		self.Memory.flush()
		self.PC = 0
		self.PC_prev = 0
		self.prevPC = 0
		self.cycle = 0
		self.gui.clear()
		self.mc_code = mc_code
		self.RegisterFile.write("00010", 0x7ffffff0)
		self.RegisterFile.write("00011",0x10000000)
		self.total_instr = 0
		self.total_alu_instr = 0
		self.total_data_instr = 0
		self.total_control_instr = 0

		mc_code = mc_code.splitlines()
		for line in mc_code:
			try:
				address,value = line.split()
				address = int(address,16)
				value = BitArray(hex = value).int
				self.Memory.writeWord(address,value)
			except:
				return "fail"

	def run(self):
		try : 
			a = self.Memory.readWord(self.PC)
		except :
			return True,self.cycle
			
		while self.Memory.readWord(self.PC)!= 0:
			self.PC_prev = self.PC
			RESULT = self.fetch()
			print('Ater fetch: PC:',self.PC,', IR:',self.IR,' RA:',self.RA,' RB:',self.RB,'RZ:',self.RZ,'RY:',self.RY,'RM:',self.RM)
			if RESULT == 'BREAKPOINT':
				return False,self.cycle
			self.gui[self.cycle]={'IF':self.prevPC}
			self.decode()
			print('Ater decode: PC:',self.PC,', IR:',self.IR,' RA:',self.RA,' RB:',self.RB,'RZ:',self.RZ,'RY:',self.RY,'RM:',self.RM)
			self.alu()
			print('Ater alu: PC:',self.PC,', IR:',self.IR,' RA:',self.RA,' RB:',self.RB,'RZ:',self.RZ,'RY:',self.RY,'RM:',self.RM)
			self.memory_access()
			print('Ater memory_access: PC:',self.PC,', IR:',self.IR,' RA:',self.RA,' RB:',self.RB,'RZ:',self.RZ,'RY:',self.RY,'RM:',self.RM)
			self.write_back()
			print('Ater write_back: PC:',self.PC,', IR:',self.IR,' RA:',self.RA,' RB:',self.RB,'RZ:',self.RZ,'RY:',self.RY,'RM:',self.RM)
			
			self.cycle = self.cycle + 1
			print('Cycle:',self.cycle)
			try : 
				a = self.Memory.readWord(self.PC)
			except :
				return True,self.cycle

	def runStep(self):
		try : 
			a = self.Memory.readWord(self.PC)
		except :
			return 'EXIT',self.cycle
		if ( a == '00000000000000000000000000000000'):
			self.PC = self.PC + 4
			return 'update',self.cycle
		self.PC_prev = self.PC
		self.fetch()
		print('Ater fetch: PC:',self.PC,', IR:',self.IR,' RA:',self.RA,' RB:',self.RB,'RZ:',self.RZ,'RY:',self.RY,'RM:',self.RM)
		self.gui[self.cycle]={'IF':self.prevPC}
		self.decode()
		print('Ater decode: PC:',self.PC,', IR:',self.IR,' RA:',self.RA,' RB:',self.RB,'RZ:',self.RZ,'RY:',self.RY,'RM:',self.RM)
		self.alu()
		print('Ater alu: PC:',self.PC,', IR:',self.IR,' RA:',self.RA,' RB:',self.RB,'RZ:',self.RZ,'RY:',self.RY,'RM:',self.RM)
		self.memory_access()
		print('Ater memory_access: PC:',self.PC,', IR:',self.IR,' RA:',self.RA,' RB:',self.RB,'RZ:',self.RZ,'RY:',self.RY,'RM:',self.RM)
		self.write_back()
		print('Ater write_back: PC:',self.PC,', IR:',self.IR,' RA:',self.RA,' RB:',self.RB,'RZ:',self.RZ,'RY:',self.RY,'RM:',self.RM)
		self.cycle = self.cycle + 1
		print('Cycle:',self.cycle)
		return 'update',self.cycle

	def prev(self,cycle,mc_code):
		self.assemble(mc_code)
		while self.cycle != cycle :
			self.fetch()
			self.decode()
			self.alu()
			self.memory_access()
			self.write_back()
			self.PC_prev = self.PC
			self.cycle = self.cycle + 1
			
	def fetch(self):
		self.IR = self.Memory.readWord(self.PC)
		self.IR = BitArray(int=self.IR, length=32).bin
		self.prevPC = self.PC
		self.PC = self.PC + 4
		if self.IR == '00000000000000000000000000000001' :
			return 'BREAKPOINT'
		else:
			return 'CONTINUE'

	def decode(self):
		# Step-1,Extract the opcode of the instruction present in IR,then determine the format
		# Step-2,Now determine operation to perform Complete the find_format()
		# Step-3,Extract the rs1.rs2,rd,imm based on the operation
		# Step-4,Read rs1,rs2 from Register_File and put them in RA,RB respectively
		# Step-5,Set control signal which are necessary in execution of a particular type
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

	def find_format(self):
		self.opcode = self.IR[25:32]
		if(self.opcode == "0110011"):
			return 'r'
		elif(self.opcode == "1100011"):
			return 'sb'
		elif(self.opcode == "0100011"):
			return 's'
		elif(self.opcode == "1101111"):
			return 'uj'
		elif(self.opcode == "0010011"):  # for addi,andi & ori
			return 'i1'
		elif(self.opcode == "0000011"):  # for load instructions
			return 'i2'
		elif(self.opcode == "1100111"):  # for jalr
			return 'i3'
		elif(self.opcode == "0110111" or self.opcode == "0010111"):
			return 'u'
		elif(self.opcode == "0000000"):
			return 'special'

	def decode_R(self):
		self.rs1 = self.IR[12:17]   # extract the rs1
		self.rs2 = self.IR[7:12]    # extract the rs2
		self.rd = self.IR[20:25]    # rxtract the rd

		# this value will come from register file after reading file at rs1 address
		self.RA = self.RegisterFile.read(self.rs1)
		# this value will come from register file after reading file at rs2 address
		self.RB = self.RegisterFile.read(self.rs2)

		self.B_select = 0   # => muxB = RB,  Control Signal
		self.Y_select = 0   # => muxY = RZ,  Control Signal
		self.Reg_Write = 1   # => RegisterFile[rd] = RY,  Control Signal
		self.MEM_Read = 0   # => Nothing to read from memory,   Control Signal
		self.MEM_Write = 0  # => Nothing to write in memory,    Control Signal

		self.funct3 = self.IR[17:20]
		self.funct7 = self.IR[0:7]

		if(self.funct3 == "111"):
			self.operation = "and"
		elif(self.funct3 == "110"):
			self.operation = "or"
		elif(self.funct3 == "001"):
			self.operation = "sll"
		elif(self.funct3 == "010"):
			self.operation = "slt"
		elif(self.funct3 == "000"):
			if(self.funct7 == "0000000"):
				self.operation = "add"
			elif(self.funct7 == "0100000"):
				self.operation = "sub"
			elif(self.funct7 == "0000001"):
				self.operation = "mul"
		elif(self.funct3 == "100"):
			if(self.funct7 == "0000001"):
				self.operation = "div"
			elif(self.funct7 == "0000000"):
				self.operation = "xor"
		elif(self.funct3 == "101"):
			if(self.funct7 == "0000000"):
				self.operation = "srl"
			elif(self.funct7 == "0100000"):
				self.operation = "sra"

	def decode_I1(self):            # for addi, andi & ori
		self.rs1 = self.IR[12:17]       # extract the rs1
		self.rd = self.IR[20:25]       # rxtract the rd
		self.imm = self.IR[0:12]        # extract imm

		self.imm = BitArray(bin = self.imm).int      # converting imm to int
		
		self.RA = self.RegisterFile.read(self.rs1) # this value will come from register file after reading file at rs1 address

		self.B_select = 1               # => muxB = imm, Control Signal
		self.Y_select = 0               # => muxY = RZ,  Control Signal
		self.Reg_Write = 1				# => RegisterFile[rd] = RY,  Control Signal
		self.MEM_Read = 0               # => Nothing to read from memory,   Control Signal
		self.MEM_Write = 0              # => Nothing to write in memory,    Control Signal

		self.funct3 = self.IR[17:20]

		if(self.funct3 == "000"):
			self.operation = "addi"
		elif(self.funct3 == "111"):
			self.operation = "andi"
		elif(self.funct3 == "110"):
			self.operation = "ori"

	def decode_I2(self):            # for Load instructions
		self.rs1 = self.IR[12:17]       # extract the rs1
		self.rd = self.IR[20:25]        # rxtract the rd
		self.imm = self.IR[0:12]        # extract imm
		self.imm = BitArray(bin = self.imm).int     # converting imm to int

		# this value will come from register file after reading file at rs1 address
		self.RA = self.RegisterFile.read(self.rs1)

		self.B_select = 1               # => muxB = imm, Control Signal
		self.Y_select = 1               # => muxY = MDR,  Control Signal
		# => RegisterFile[rd] = RY,  Control Signal
		self.Reg_Write = 1
		self.MEM_Read = 1               # => Read from memory,   Control Signal
		self.MEM_Write = 0              # => Nothing to write in memory,    Control Signal

		self.funct3 = self.IR[17:20]

		if(self.funct3 == "000"):
			self.operation = "lb"
		elif(self.funct3 == "001"):
			self.operation = "lh"
		elif(self.funct3 == "010"):
			self.operation = "lw"
		elif(Self.funct3 == "011"):
			self.operation = "ld"

	def decode_I3(self):            # for jalr instruction
		self.rs1 = self.IR[12:17]       # extract the rs1
		self.rd = self.IR[20:25]        # rxtract the rd
		self.imm = self.IR[0:12]        # extract imm
		self.imm = BitArray(bin = self.imm).int     # converting imm to int

		# this value will come from register file after reading file at rs1 address
		self.RA = self.RegisterFile.read(self.rs1)

		self.B_select = 1               # => muxB = imm, Control Signal
		self.Y_select = 2               # => muxY = PC_Temp,  Control Signal
		# => RegisterFile[rd] = RY,  Control Signal
		self.Reg_Write = 1
		self.MEM_Read = 0               # => Nothing to read from memory,   Control Signal
		self.MEM_Write = 0              # => Nothing to write in memory,    Control Signal

		self.funct3 = self.IR[17:20]

		self.operation = "jalr"

	def decode_S(self):             # for Store instructions
		self.rs1 = self.IR[12:17]                   # extract the rs1
		self.rs2 = self.IR[7:12]                    # extract the rs2

		# extract imm from two locations by concatenating them
		self.imm = BitArray(bin=self.IR[0:7]+self.IR[20:25]).int

		# this value will come from register file after reading file at rs1 address
		self.RA = self.RegisterFile.read(self.rs1)
		# this value will come from register file after reading file at rs2 address
		self.RB = self.RegisterFile.read(self.rs2)

		self.RM = self.RB

		self.B_select = 1               # => muxB = imm, Control Signal
		self.Y_select = None            # => muxY = None,  Control Signal
		self.Reg_Write = 0               # => Nothing to write in register file,  Control Signal
		self.MEM_Read = 1               # => Read from memory,   Control Signal
		self.MEM_Write = 1              # => Write in memory,    Control Signal

		self.funct3 = self.IR[17:20]

		if(self.funct3 == "000"):
			self.operation = "sb"
		elif(self.funct3 == "001"):
			self.operation = "sh"
		elif(self.funct3 == "010"):
			self.operation = "sw"
		elif(Self.funct3 == "011"):
			self.operation = "sd"

	def decode_SB(self):            # for branch intructions
		self.rs1 = self.IR[12:17]   # extract the rs1
		self.rs2 = self.IR[7:12]    # rxtract the rs2
		# extract imm from four locations by concatenating them,0 at last because it is initially ignored
		self.imm = BitArray(
			bin=self.IR[0]+self.IR[24]+self.IR[1:7]+self.IR[20:24]+"0").int

		self.RA = self.RegisterFile.read(self.rs1)
		self.RB = self.RegisterFile.read(self.rs2)

		self.B_select = 1               # => muxB = imm, Control Signal
		self.Y_select = None            # => muxY = None,  Control Signal
		self.Reg_Write = 0               # => Nothing to write in register file,  Control Signal
		self.MEM_Read = 0               # => Nothing to read from memory,   Control Signal
		self.MEM_Write = 0              # => Nothing to write in memory,    Control Signal

		self.funct3 = self.IR[17:20]
		if(self.funct3 == "000"):
			self.operation = "beq"
		elif(self.funct3 == "001"):
			self.operation = "bne"
		elif(self.funct3 == "100"):
			self.operation = "blt"
		elif(self.funct3 == "101"):
			self.operation = "bge"

	def decode_U(self):             # for lui,auipc
		self.rd = self.IR[20:25]        # extract the rd
		self.imm = BitArray(bin=self.IR[0:20] + "000000000000").int

		self.RA = 0

		self.B_select = 1               # => muxB = imm, Control Signal
		self.Y_select = 0               # => muxY = RZ,  Control Signal
		self.Reg_Write = 1				# => RegisterFile[rd] = RY,  Control Signal
		self.MEM_Read = 0               # => Nothing to read from memory,   Control Signal
		self.MEM_Write = 0              # => Nothing to write in memory,    Control Signal

		self.funct7 = self.IR[25:32]

		if(self.funct7 == "0110111"):
			self.operation = "lui"
		elif(self.funct7 == "0010111"):
			self.operation = "auipc"

	def decode_UJ(self):            # for jal
		self.rd = self.IR[20:25]        # extract the rd
		self.imm = BitArray(bin=self.IR[0]+self.IR[11:19]+self.IR[19]+self.IR[1:11]+"0").int
		self.B_select = 1               # => muxB = imm, Control Signal
		self.Y_select = 2               # => muxY = PC_Temp,  Control Signal
		self.Reg_Write = 1				# => RegisterFile[rd] = RY,  Control Signal
		self.MEM_Read = 0               # => Nothing to read from memory,   Control Signal
		self.MEM_Write = 0              # => Nothing to write in memory,    Control Signal

		self.operation = "jal"

	def alu(self):
		if self.operation == "add" and self.B_select == 0:
			self.RZ = self.RA + self.RB
		elif self.operation == "and" and self.B_select == 0:
			self.RZ = self.RA & self.RB
		elif self.operation == "or" and self.B_select == 0:
			self.RZ = self.RA | self.RB
		elif self.operation == "sub" and self.B_select == 0:
			self.RZ = self.RA - self.RB
		elif self.operation == "mul" and self.B_select == 0:
			self.RZ = self.RA * self.RB
		elif self.operation == "div" and self.B_select == 0:
			self.RZ = self.RA // self.RB
		elif self.operation == "xor" and self.B_select == 0:
			self.RZ = self.RA ^ self.RB
		elif self.operation == "sll" and self.B_select == 0:
			self.RZ = self.RA << self.RB
		elif self.operation == "srl" and self.B_select == 0:
			self.RZ = self.RA >> self.RB
		elif self.operation == "slt" and self.B_select == 0:
			self.RZ = 1 if self.RA < self.RB else 0
		elif self.operation == "sra" and self.B_select == 0:
			self.RZ = self.RA >> self.RB

		elif self.operation == "addi" and self.B_select == 1:
			self.RZ = self.RA + self.imm
		elif self.operation == "andi" and self.B_select == 1:
			self.RZ = self.RA & self.imm
		elif self.operation == "ori" and self.B_select == 1:
			self.RZ = self.RA | self.imm

		elif self.operation == "lui" and self.B_select == 1:
			self.RZ = self.imm
		elif self.operation == "auipc" and self.B_select == 1:
			self.RZ = self.PC + self.imm - 4

		elif self.operation == "beq" and self.B_select == 1:
			if(self.RA == self.RB):
				self.PC = self.PC + self.imm - 4
		elif self.operation == "bge" and self.B_select == 1:
			if(self.RA >= self.RB):
				self.PC = self.PC + self.imm - 4
		elif self.operation == "blt" and self.B_select == 1:
			if(self.RA < self.RB):
				self.PC = self.PC + self.imm - 4
		elif self.operation == "bne" and self.B_select == 1:
			if(self.RA != self.RB):
				self.PC = self.PC + self.imm - 4

		elif self.operation == "jal" and self.B_select == 1:
			self.PC_Temp = self.PC
			self.PC = self.PC + self.imm - 4
		elif self.operation == "jalr" and self.B_select == 1:
			self.PC_Temp = self.PC
			self.PC = self.RA + self.imm

		elif self.operation == "lb" and self.B_select == 1:
			self.RZ = self.RA + self.imm
			self.MAR = self.RZ
		elif self.operation == "lh" and self.B_select == 1:
			self.RZ = self.RA + self.imm
			self.MAR = self.RZ
		elif self.operation == "lw" and self.B_select == 1:
			self.RZ = self.RA + self.imm
			self.MAR = self.RZ
		elif self.operation == "ld" and self.B_select == 1:
			self.RZ = self.RA + self.imm
			self.MAR = self.RZ

		elif self.operation == "sb" and self.B_select == 1:
			self.RZ = self.RA + self.imm
			self.MAR = self.RZ
			self.MDR = self.RM 
		elif self.operation == "sh" and self.B_select == 1:
			self.RZ = self.RA + self.imm
			self.MAR = self.RZ  
			self.MDR = self.RM  
		elif self.operation == "sw" and self.B_select == 1:
			self.RZ = self.RA + self.imm
			self.MAR = self.RZ  
			self.MDR = self.RM 
		elif self.operation == "sd" and self.B_select == 1:
			self.RZ = self.RA + self.imm
			self.MAR = self.RZ
			self.MDR = self.RM 

	def memory_access(self):
		if self.B_select == 1:	
			if self.MEM_Read == 1 and self.MEM_Write == 0:			# for load instructions
				if self.operation == "lb":
					self.MDR = self.Memory.readByte(self.MAR)   		#lb
				elif self.operation == "lw":
					self.MDR = self.Memory.readWord(self.MAR)   		#lw
				elif self.operation == "lh":
					self.MDR = self.Memory.readHalfWord(self.MAR)   	#lh
				# elif self.operation == "ld":
				# 	self.MDR = self.Memory.readDoubleWord(self.MAR)   	#ld
				
			elif self.MEM_Read == 1 and self.MEM_Write == 1:		# for store instructions
				if self.operation == "sb":                      		#sb
					self.Memory.writeByte(self.MAR,self.MDR)
				elif self.operation == "sw":                    		#sw
					self.Memory.writeWord(self.MAR,self.MDR)
				elif self.operation == "sh":                      		#sh
					self.Memory.writeHalfWord(self.MAR, self.MDR)
				# elif self.operation == "sd":                      		#sd
				# 		self.Memory.writeDoubleWord(self.MAR, self.MDR)
					

		if self.Y_select == 0:
			self.RY = self.RZ
		elif self.Y_select == 1:
			self.RY = self.MDR
		elif self.Y_select == 2:
			self.RY = self.PC_Temp
	
	def write_back(self):
		self.total_instr = self.total_instr + 1
		if self.operation in "beq bne blt bge jal jalr".split():
			self.total_control_instr = self.total_control_instr + 1
		elif self.operation in "lb lh lw sb sh sw".split():
			self.total_data_instr = self.total_data_instr + 1
		else:
			self.total_alu_instr = self.total_alu_instr + 1
		if self.Reg_Write == 1:
			self.RegisterFile.write(self.rd, self.RY)

	def getRegister(self):
		return self.RegisterFile.getRegisters()

	def getMemory(self):
		return self.Memory.get_Memory()

	def getCycleInfo(self):
		return self.PC,self.cycle,self.total_instr,1,self.total_alu_instr,self.total_data_instr,self.total_control_instr
	
	def getDaigram(self):
		return self.gui
	
	def prev_Instruction(self):
		return ('{0:X}'.format(int(self.PC_prev)))

	def printMemory(self):
		self.Memory.printall()