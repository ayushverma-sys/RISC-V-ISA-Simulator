from flask import Flask, redirect, url_for, render_template, request, session, jsonify, Response
from phase3 import PipelineExecute
from phase1 import AssemblerHelper
from phase2 import Non_PipelineExecute
from bitstring import BitArray
Executer = None

currentView = 'hex'
dataView = ''
jumpAddress = ''
instruction_count = 0
isPipeline = True
cycle = 0
app = Flask(__name__)
@app.route('/', methods=['POST', 'GET'])
def home():
	return render_template('base.html',register={},memory={})


@app.route('/assemble', methods=['POST'])
def assemble():
	input = request.json
	# print(input['text'])
	input_filepath = './input/input.asm'
	f = open(input_filepath, 'w')
	f.write(input['text'])
	f.close()
	Phase1_helper = AssemblerHelper()
	print(input)
	text = []
	global Executer
	original_code, labels, result1 = Phase1_helper.get_original_code_and_label()
	if result1 == False:
		return jsonify(success=labels)

	basic_code, result1 = Phase1_helper.get_basic_code(
		original_code, labels)
	if result1 == False:
		return jsonify(success=basic_code)

	machine_code, result3 = Phase1_helper.get_machine_code()
	if result3 == False:
		return jsonify(success=machine_code)

	global instruction_count
	global isPipeline
	instruction_count = len(machine_code)

	file_read = open('output.mc', 'r')
	mc = file_read.read()
	if input['specialInstruction']=='':
		input['specialInstruction'] = -8
	else:
		input['specialInstruction'] = int(input['specialInstruction'])
	if input['branch_prediction']=='False':
		input['branch_prediction']=False
	else:
		input['branch_prediction']=True
	if input['forwarding'] == 'False':
		input['forwarding'] = False
	else:
		input['forwarding']=True
	if input['pipeline_register'] == 'False':
		input['pipeline_register'] = False
	else:
		input['pipeline_register']=True
	
	if input['pipeline'] == 'True':
		isPipeline = True
		Executer = PipelineExecute()
		Executer.assemble(mc,input['forwarding'],input['branch_prediction'],input['pipeline_register'],input['specialInstruction'])
	else:
		isPipeline = False
		Executer = Non_PipelineExecute()
		Executer.assemble(mc)

	# pc = Executer.next_Instruction()

	PC = 0
	for mc_i, basic_code_i, ori_i in zip(machine_code, basic_code, original_code):
		text.append(('{0:X}'.format(int(PC)),
					mc_i, basic_code_i, ori_i))
		PC = PC + 4
	return jsonify(success='pass', info=text, nextInstruction=('{0:X}'.format(int('0', 16))))


@app.route('/diagram', methods=['POST'])
def diagram():
	if isPipeline:
		path = Executer.getForwardingPath()
		return jsonify(count=instruction_count, data=Executer.getDaigram(),path=path)
	else:
		path = 'no_pipeline'
		return jsonify(count=instruction_count, data=Executer.getDaigram(),path=path)


@app.route('/simulate', methods=['POST'])
def simulate():
	if request.method == 'POST':
		global history
		global cycle
		input = request.form.get('input')
		print(input)
		if(input == 'run'):
			result = 'EXIT'
			_cycle = Executer.run()
			print(_cycle)
			if result:
				return jsonify(success='EXIT', cycle=_cycle)
			else:
				return jsonify(success='BREAKPOINT', cycle=_cycle)
		elif(input == 'step'):
			result, _cycle = Executer.runStep()
			cycle = _cycle
			resp = jsonify(success=result, cycle=cycle)
			return resp
		elif(input == 'prev'):
			if cycle == 0:
				return jsonify(success='INSTRUCTION ERROR: no instruction left to execute\n Hint: Click Step or Run')
			# Phase1_helper.mc_generater()
			file_read = open('output.mc', 'r')
			machine_code = file_read.read()
			cycle = cycle - 1
			Executer.prev(cycle, machine_code)
			print('cycle:', cycle)
			return jsonify(success='update')
		elif(input == 'reset'):
			Executer.reset()
			register = Executer.getRegister()
			memory = Executer.getMemory()
			return register, memory
		elif(input == 'dump'):
			x = ''
			Phase1_helper = AssemblerHelper()
			original_code, labels, result1 = Phase1_helper.get_original_code_and_label()
			if result1 == False:
				return jsonify(success=labels)

			basic_code, result1 = Phase1_helper.get_basic_code(
				original_code, labels)
			if result1 == False:
				return jsonify(success=basic_code)

			machine_code, result3 = Phase1_helper.get_machine_code()
			if result3 == False:
				return jsonify(success=machine_code)

			for i in machine_code:
				x = x + '0x' + i + '\n'
			# print(x)
			return jsonify(success=x)


@app.route('/display', methods=['POST'])
def display():
	if request.method == 'POST':
		global currentView
		input = request.form.get('input')
		print(input)
		currentView = input
		return 'CS204'


@app.route('/jump', methods=['POST'])
def jump():
	if request.method == 'POST':
		address = request.form.get('input')
		address = BitArray(hex=address).uint
		address = address - address % 4
		if (address >= 0 and address <= 2147483644):
			global dataView
			global jumpAddress
			dataView, jumpAddress = 'jump', address
		return 'CS204'


@app.route('/next_instruction', methods=['GET'])
def next_instruction():
	pc = Executer.next_Instruction()
	IF_pc, ID_pc, EX_pc, MEM_pc, WB_pc = -1, -1, -1, -1, -1
	try:
		IF_pc = pc['IF']
	except:
		pass
	try:
		ID_pc = pc['ID']
	except:
		pass
	try:
		EX_pc = pc['EX']
	except:
		pass
	try:
		MEM_pc = pc['MEM']
	except:
		pass
	try:
		WB_pc = pc['WB']
	except:
		pass
	# print(pc)
	return jsonify(	IF_pc='{0:X}'.format(IF_pc),
					ID_pc='{0:X}'.format(ID_pc), 
					EX_pc='{0:X}'.format(EX_pc), 
					MEM_pc='{0:X}'.format(MEM_pc), 
					WB_pc='{0:X}'.format(WB_pc))


@app.route('/prev_instruction', methods=['GET'])
def prev_instruction():
	pc = Executer.prev_Instruction()
	return jsonify(pc='{0:X}'.format(int(pc, 16)))


@app.route('/refresh_register', methods=['GET'])
def refresh_register():
	return jsonify(success=Executer.getRegister(), view=currentView)


@app.route('/refresh_memory', methods=['GET'])
def refresh_memory():
	return jsonify(success=Executer.getMemory(), view=currentView, dataview=dataView, address=jumpAddress)


@app.route('/memory_section', methods=['POST'])
def memory_section():
	if request.method == 'POST':
		global dataView
		input = request.form.get('input')
		dataView = input
		return 'CS204'


@app.route('/exit_', methods=['GET'])
def exit_():
	print('hello')
	memory = Executer.getMemory()
	f = open('output.mc', 'w')
	for address in memory:
		b3 = BitArray(hex=memory[address][0]).bin
		b2 = BitArray(hex=memory[address][0]).bin
		b1 = BitArray(hex=memory[address][0]).bin
		b0 = BitArray(hex=memory[address][0]).bin
		value = BitArray(bin=b0 + b1 + b2 + b3).hex
		f.write('0x' + address + ' 0x' + value + '\n')
	f.close()
	return jsonify(success="Data Memory updated in output.mc")

@app.route('/cycleinfo',methods=['POST'])
def cycleinfo():
	if isPipeline:
		pc = Executer.next_Instruction()
		IF_pc, ID_pc, EX_pc, MEM_pc, WB_pc = -1, -1, -1, -1, -1
		try:
			IF_pc = pc['IF']
		except:
			pass
		try:
			ID_pc = pc['ID']
		except:
			pass
		try:
			EX_pc = pc['EX']
		except:
			pass
		try:
			MEM_pc = pc['MEM']
		except:
			pass
		try:
			WB_pc = pc['WB']
		except:
			pass
		prediction,hazard,cycle,total_instr,CPI,alu_instr,data_instr,control_instr,data_hazard,control_hazard,misprediction,stalls,data_stalls,control_stalls = Executer.getCycleInfo()
		
		return jsonify(	IF_pc=IF_pc,ID_pc=ID_pc,EX_pc=EX_pc,MEM_pc=MEM_pc,WB_pc=WB_pc,
			prediction=prediction,hazard=hazard,total_cycles=cycle,total_instr=total_instr,CPI=CPI,
			total_alu_instr=alu_instr,total_data_instr=data_instr,total_control_instr=control_instr,
			total_data_hazard=data_hazard,total_control_hazard=control_hazard,total_misprediction=misprediction,
			total_stalls=stalls,total_data_stalls=data_stalls,total_control_stalls=control_stalls)
	else:
		ID_pc, EX_pc, MEM_pc, WB_pc = -1, -1, -1, -1
		prediction,hazard='',''
		IF_pc,cycle,total_instr,CPI,alu_instr,data_instr,control_instr=Executer.getCycleInfo()
		data_hazard,control_hazard,misprediction,stalls,data_stalls,control_stalls=0,0,0,0,0,0
		return jsonify(	IF_pc=IF_pc,ID_pc=ID_pc,EX_pc=EX_pc,MEM_pc=MEM_pc,WB_pc=WB_pc,
			prediction=prediction,hazard=hazard,total_cycles=cycle,total_instr=total_instr,CPI=CPI,
			total_alu_instr=alu_instr,total_data_instr=data_instr,total_control_instr=control_instr,
			total_data_hazard=data_hazard,total_control_hazard=control_hazard,total_misprediction=misprediction,
			total_stalls=stalls,total_data_stalls=data_stalls,total_control_stalls=control_stalls)

if __name__ == '__main__':
	app.run(debug=True, host='0.0.0.0')
