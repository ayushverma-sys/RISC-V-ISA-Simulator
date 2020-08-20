from flask import Flask, redirect, url_for, render_template, request, session, jsonify, Response
from phase1 import AssemblerHelper
from phase2 import Non_PipelineExecute
from phase3 import PipelineExecute
from bitstring import BitArray
import sys

# Phase1_helper = AssemblerHelper()
Executer = PipelineExecute()
app = Flask(__name__)

currentView = 'hex'
dataView = ''
jumpAddress = ''
cycle = 0
@app.route('/', methods=['POST', 'GET'])
def home():
	# text = Phase1_helper.instruction_info
	register = Executer.getRegister()
	memory = Executer.getMemory()
	pc = Executer.next_Instruction()
	# basic_code = 'EXIT'
	# machine_code = '00000000'
	# for i in range(len(text)):
	# 	if(text[i][0] == pc):
	# 		try:
	# 			basic_code, machine_code = text[i][1], text[i][2]
	# 			break
	# 		except:
	# 			pass
	return render_template('index.html', register=register, nextInstruction=('{0:X}'.format(int(pc, 16))),
						    memory=memory)

@app.route('/assemble', methods=['POST'])
def assemble():
	if request.method == 'POST':
		input = request.form.get('input')
		text = request.form.get('text')
		# print(text)
		input_filepath = './input/input.asm'
		f = open(input_filepath, 'w')
		f.write(text)
		f.close()
		Phase1_helper = AssemblerHelper()
		print(input)
		if(input == 'assemble'):
			text = []
			original_code,labels,result1 = Phase1_helper.get_original_code_and_label()
			if result1 == False :
				return jsonify(success = labels)

			basic_code,result1 = Phase1_helper.get_basic_code(original_code,labels)
			if result1 == False :
				return jsonify(success = basic_code)
			
			machine_code,result3 = Phase1_helper.get_machine_code()
			if result3 == False :
				return jsonify(success = machine_code)
			
			file_read = open('output.mc', 'r')
			mc = file_read.read()
			Executer.assemble(mc)
			pc = Executer.next_Instruction()
			
			PC=0
			for mc_i,basic_code_i,ori_i in zip(machine_code,basic_code,original_code):
				text.append(('{0:X}'.format(int(PC)),mc_i,basic_code_i,ori_i))
				PC = PC + 4
			return jsonify(success ='pass', info = text,nextInstruction=('{0:X}'.format(int(pc, 16))))

@app.route('/simulate', methods=['POST'])
def simulate():
	if request.method == 'POST':
		global history
		global cycle
		input = request.form.get('input')
		print(input)
		if(input == 'run'):
			result = ''
			result,cycle = Executer.run()
			print(result)
			if result:
				return  jsonify(success='EXIT',cycle = cycle)
			else:
				return jsonify(success='BREAKPOINT',cycle = cycle)
			
		elif(input == 'step'):
			result,_cycle = Executer.step()
			cycle = _cycle
			# print('cycle:',cycle,'from step function :',_cycle)
			pc = Executer.next_Instruction()
			resp = jsonify(success=result, cycle = cycle)
			return resp
		elif(input == 'prev'):
			if cycle == 0:
				return jsonify(success='INSTRUCTION ERROR: no instruction left to execute\n Hint: Click Step or Run')
			# Phase1_helper.mc_generater()
			file_read = open('output.mc', 'r')
			machine_code = file_read.read()
			cycle = cycle - 1
			Executer.prev(cycle,machine_code)
			print('cycle:',cycle)
			return jsonify(success='update')
		elif(input == 'reset'):
			# Phase1_helper.mc_generater()
			file_read=open('output.mc', 'r')
			machine_code=file_read.read()
			Executer.assemble(machine_code)
			register=Executer.getRegister()
			memory=Executer.getMemory()
			return register, memory
		elif(input == 'dump'):
			x = ''
			Phase1_helper = AssemblerHelper()
			original_code,labels,result1 = Phase1_helper.get_original_code_and_label()
			if result1 == False :
				return jsonify(success = labels)

			basic_code,result1 = Phase1_helper.get_basic_code(original_code,labels)
			if result1 == False :
				return jsonify(success = basic_code)
			
			machine_code,result3 = Phase1_helper.get_machine_code()
			if result3 == False :
				return jsonify(success = machine_code)
			
			for i in machine_code:
				x = x + '0x' + i + '\n'
			# print(x)
			return jsonify(success = x)

@app.route('/display', methods=['POST'])
def display():
	if request.method == 'POST':
		global currentView
		input=request.form.get('input')
		print(input)
		currentView=input
		return 'CS204'

@app.route('/jump', methods=['POST'])
def jump():
	if request.method == 'POST':
		address = request.form.get('input')
		address = BitArray(hex = address).uint
		address = address - address % 4
		if (address >= 0 and address <= 2147483644 ) :
			global dataView
			global jumpAddress 
			dataView,jumpAddress= 'jump',address
		return 'CS204'

@app.route('/next_instruction', methods=['GET'])
def next_instruction():
	pc = Executer.next_Instruction()
	return jsonify(pc = '{0:X}'.format(int(pc, 16)))

@app.route('/prev_instruction', methods=['GET'])
def prev_instruction():
	pc = Executer.prev_Instruction()
	return jsonify(pc = '{0:X}'.format(int(pc, 16)))

@app.route('/refresh_register', methods=['GET'])
def refresh_register():
	return jsonify(success=Executer.getRegister(), view=currentView)

@app.route('/refresh_memory', methods=['GET'])
def refresh_memory():
	return jsonify(success=Executer.getMemory(), view=currentView, dataview = dataView ,address = jumpAddress)
		
@app.route('/memory_section', methods=['POST'])
def memory_section():
	if request.method == 'POST':
		global dataView
		input = request.form.get('input')
		dataView = input
		return 'CS204'

@app.route('/exit_',methods=['GET'])
def exit_():
	print('hello')
	memory = Executer.getMemory()
	f = open('output.mc','w')
	for address in memory:
		b3 = BitArray(hex = memory[address][0]).bin
		b2 = BitArray(hex = memory[address][0]).bin
		b1 = BitArray(hex = memory[address][0]).bin
		b0 = BitArray(hex = memory[address][0]).bin
		value = BitArray(bin = b0 + b1 + b2 + b3).hex
		f.write('0x' + address + ' 0x' + value + '\n')
	f.close()
	return jsonify( success="Data Memory updated in output.mc" )

if __name__ == '__main__':
	app.run(debug=True, host='0.0.0.0')
	# print('anmol')
