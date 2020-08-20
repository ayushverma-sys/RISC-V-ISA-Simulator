from bitstring import BitArray
from collections import OrderedDict
class memory:
	def __init__(self):
		self.memory={}

	def writeByte(self,address,value):
		b = BitArray(int = value, length = 8).hex
		address_to_be_written = address - address % 4
		x0,x1,x2,x3 = "00","00","00","00"
		address_to_be_written = str(BitArray(int = address_to_be_written,length = 32).hex)
		try:
			x0 = self.memory[address_to_be_written][0]
		except: pass
		
		try:
			x1 = self.memory[address_to_be_written][1]
		except: pass
		
		try:
			x2 = self.memory[address_to_be_written][2]
		except: pass
		
		try:
			x3 = self.memory[address_to_be_written][3]
		except: pass
		if address % 4 == 1:
			self.memory[address_to_be_written] = (x0,b,x2,x3)

		if address % 4 == 2:
			self.memory[address_to_be_written] = (x0,x1,b,x3)
		
		if address % 4 == 3:
			self.memory[address_to_be_written] = (x0,x1,x2,b)
	
		if address % 4 == 0 :
			self.memory[address_to_be_written] = (b,x1,x2,x3)

	def writeWord(self,address,value):
		value = BitArray(int = value, length = 32).bin
		b3 = BitArray(bin = value[0:8]).int
		b2 = BitArray(bin = value[8:16]).int
		b1 = BitArray(bin = value[16:24]).int
		b0 = BitArray(bin = value[24:32]).int
		self.writeByte(address,b0)
		self.writeByte(address+1,b1)
		self.writeByte(address+2,b2)
		self.writeByte(address+3,b3)

	def writeHalfWord(self,address,value):
		value = BitArray(int = value, length = 16).bin
		b1 = BitArray(bin = value[0:8]).int
		b0 = BitArray(bin = value[8:16]).int
		self.writeByte(address,b0)
		self.writeByte(address+1,b1)

	def readByte(self,address):
		address_to_be_read = address - address % 4
		address_to_be_read = str(BitArray(int = address_to_be_read,length = 32).hex)
		for i in range(4):
			if address % 4 == i:
				return BitArray(hex = self.memory[address_to_be_read][i]).int
		
	def readHalfWord(self,address):
		address_to_be_read = address - address % 4
		b0,b1 = None,None		
		address_to_be_read = str(BitArray(int = address_to_be_read,length = 32).hex)
		if address % 4 == 0:
			b1 = BitArray(hex = self.memory[address_to_be_read][0]).bin
			b0 = BitArray(hex = self.memory[address_to_be_read][1]).bin
		if address % 4 == 1:
			b1 = BitArray(hex = self.memory[address_to_be_read][1]).bin
			b0 = BitArray(hex = self.memory[address_to_be_read][2]).bin
		if address % 4 == 2:
			b1 = BitArray(hex = self.memory[address_to_be_read][2]).bin
			b0 = BitArray(hex = self.memory[address_to_be_read][3]).bin
		if address % 4 == 3:
			b1 = BitArray(hex = self.memory[address_to_be_read][3]).bin
			x = (address - address%4) + 4
			address_to_be_read = str(BitArray(int = x,length = 32).hex)
			b0 = BitArray(hex = self.memory[address_to_be_read][0]).bin
		return BitArray(bin = b0 + b1).int

	def readWord(self,address):
		address_to_be_read = address - address % 4
		b0,b1,b2,b3 = None,None,None,None
		address_to_be_read = str(BitArray(int = address_to_be_read,length = 32).hex)
		if address % 4 == 0:
			b3 = BitArray(hex = self.memory[address_to_be_read][0]).bin
			b2 = BitArray(hex = self.memory[address_to_be_read][1]).bin
			b1 = BitArray(hex = self.memory[address_to_be_read][2]).bin
			b0 = BitArray(hex = self.memory[address_to_be_read][3]).bin
			
		if address % 4 == 1:
			b3 = BitArray(hex = self.memory[address_to_be_read][1]).bin
			b2 = BitArray(hex = self.memory[address_to_be_read][2]).bin
			b1 = BitArray(hex = self.memory[address_to_be_read][3]).bin
			x = (address - address%4) + 4
			address_to_be_read = str(BitArray(int = x,length = 32).hex)
			b0 = BitArray(hex = self.memory[address_to_be_read][0]).bin
		if address % 4 == 2:
			b3 = BitArray(hex = self.memory[address_to_be_read][2]).bin
			b2 = BitArray(hex = self.memory[address_to_be_read][3]).bin
			x = (address - address%4) + 4
			address_to_be_read = str(BitArray(int = x,length = 32).hex)
			b1 = BitArray(hex = self.memory[address_to_be_read][0]).bin
			b0 = BitArray(hex = self.memory[address_to_be_read][1]).bin
		if address % 4 == 3:
			b3 = BitArray(hex = self.memory[address_to_be_read][3]).bin
			x = (address - address%4) + 4
			address_to_be_read = str(BitArray(int = x,length = 32).hex)
			b2 = BitArray(hex = self.memory[address_to_be_read][0]).bin
			b1 = BitArray(hex = self.memory[address_to_be_read][1]).bin
			b0 = BitArray(hex = self.memory[address_to_be_read][2]).bin
		return BitArray(bin = b0 + b1 + b2 + b3).int
	
	# def writeDoubleWord(self,address,value):
		# not supported by RISC-V 32
	# def readDoubleWord(self,address):
		# not supported by RISC-V 32
	
	def get_Memory(self):
		return self.memory

	def flush(self):
		self.memory.clear()
	
	def printall(self):
		print(self.memory)
	

class register:
	def __init__(self):
		self.registers = {}
		value = 0
		for i in range(32):
			self.registers[i] = BitArray(int = value,length = 32).hex
			
	def read(self,address):
		address = BitArray(bin=address).uint
		return BitArray(hex = self.registers[address]).int
	
	def write(self,address,value):
		if address != "00000":
			address = BitArray(bin=address).uint
			self.registers[address] = BitArray(int = value,length = 32).hex

	def printall(self):
		print(self.registers)

	def returnAll(self):
		return self.registers

	def flush(self):
		for i in range(32):
			self.registers[i] = BitArray(int = 0,length = 32).hex
	
	def getRegisters(self):
		return self.registers
