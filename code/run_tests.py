# Runs every test case in ../tests with issue width 1 to 4 and checks 
#   -- final registers and memory against a sequential reference model
#   -- the timing table against the hardware constraints of the pipeline
#   -- the timing table of test6 against the example of the class slides (width 1 and 2)
# usage: python run_tests.py [test files]

import os
import re
import sys
import glob
import subprocess
from init import read_input

# timing tables of the example of the class slides (OOO example), issue width 1 and 2
# [ISSUE], [EXE], [MEM], [WB], [COMMIT] for each instruction
expected = {
    ('test6_class_example.txt', 1): [
        [[1], [2, 2], [3, 8], [9], [10]],
        [[2], [3, 3], [9, 14], [15], [16]],
        [[3], [16, 25], [], [26], [27]],
        [[4], [27, 36], [], [37], [38]],
        [[5], [27, 30], [], [31], [39]],
        [[6], [7, 7], [], [8], [40]]],
    ('test6_class_example.txt', 2): [
        [[1], [2, 2], [3, 8], [9], [10]],
        [[1], [3, 3], [9, 14], [15], [16]],
        [[2], [16, 25], [], [26], [27]],
        [[2], [27, 36], [], [37], [38]],
        [[3], [27, 30], [], [31], [38]],
        [[3], [4, 4], [], [5], [39]]],
}

# function: sequential (one instruction at a time) reference model
def reference(config):
    reg = {'R': [0]*32, 'F': [0]*32}
    memory = [0]*256
    for i in config['reg_int']:
        reg['R'][i] = config['reg_int'][i]
    for i in config['reg_fp']:
        reg['F'][i] = config['reg_fp'][i]
    for i in config['memory']:
        memory[i] = config['memory'][i]
    reg['R'][0] = 0
    get = lambda name: reg[name[0]][int(name[1:])]
    def put(name, value):
        if name != 'R0':
            reg[name[0]][int(name[1:])] = value
    instructions = config['instructions']
    trace = []
    pc = 0
    while pc < len(instructions):
        trace.append(instructions[pc])
        f = instructions[pc].split(' ')
        op = f[0]
        pc += 1
        if (op=='Ld')|(op=='Sd'):
            m = re.match(r'(-?\d+)\((R\d+)\)', f[2])
            address = int(m.group(1)) + get(m.group(2))
            if op=='Ld':
                put(f[1], memory[address])
            else:
                memory[address] = get(f[1])
        elif (op=='Add')|(op=='Add.d'):
            put(f[1], get(f[2]) + get(f[3]))
        elif (op=='Sub')|(op=='Sub.d'):
            put(f[1], get(f[2]) - get(f[3]))
        elif op=='Addi':
            put(f[1], get(f[2]) + int(f[3]))
        elif op=='Mult.d':
            put(f[1], get(f[2]) * get(f[3]))
        elif (op=='Bne')|(op=='Beq'):
            if (get(f[1]) == get(f[2])) == (op=='Beq'):
                pc = int(pc + int(f[3])/4)
        else:
            sys.exit('unknown instruction: '+instructions[pc-1])
    return trace, reg['R'], reg['F'], memory

# function: parse the simulator output
def parse(output):
    rows = []
    reg = {'R': [], 'F': []}
    memory = [0]*256
    lines = output.splitlines()
    section = 'table'
    name = ''
    for line in lines[2:]:
        if line.startswith('REGISTER VALUES'):
            section = 'reg'
        elif line.startswith('NON-ZERO MEMORY VALUES'):
            section = 'mem'
        elif (section=='table')&('[' in line):
            stages = [[int(n) for n in re.findall(r'-?\d+', s)] for s in re.findall(r'\[(.*?)\]', line[30:])]
            rows.append([line[:30].strip()] + stages)
        elif section=='reg':
            if line.startswith('value:'):
                reg[name].extend([float(v) for v in line.split()[1:]])
            elif line.strip()!='':
                name = line.split()[0][0]
        elif (section=='mem')&(not line.startswith('Addresses'))&(line.strip()!=''):
            memory[int(line.split()[0])] = float(line.split()[1])
    return rows, reg['R'], reg['F'], memory

# function: at most 'limit' busy units in any cycle 
def check_overlap(intervals, limit):
    busy = {}
    for (start, end) in intervals:
        for c in range(start, end+1):
            busy[c] = busy.get(c, 0) + 1
    return all(n <= limit for n in busy.values())

# function: check one run
def check(name, config, width, output):
    errors = []
    trace, ref_int, ref_fp, ref_mem = reference(config)
    rows, reg_int, reg_fp, memory = parse(output)
    # functional results
    if [r[0] for r in rows] != trace:
        errors.append('committed instructions differ from the reference model')
    close = lambda a, b: len(a)==len(b) and all(abs(x-y) < 1e-9 for x, y in zip(a, b))
    if not close(reg_int, ref_int):
        errors.append('integer registers differ from the reference model')
    if not close(reg_fp, ref_fp):
        errors.append('fp registers differ from the reference model')
    if not close(memory, ref_mem):
        errors.append('memory differs from the reference model')
    # timing
    key = (os.path.basename(name), width)
    if (key in expected) and ([r[1:] for r in rows] != expected[key]):
        errors.append('timing table differs from the class example')
    issue = [r[1][0] for r in rows]
    commit = [r[5][0] for r in rows]
    if any(issue.count(c) > width for c in issue):
        errors.append('more than issue width instructions issued in a cycle')
    if issue != sorted(issue):
        errors.append('instructions are not issued in order')
    if any(commit.count(c) > width for c in commit):
        errors.append('more than issue width instructions committed in a cycle')
    if commit != sorted(commit):
        errors.append('instructions are not committed in order')
    for r in rows:
        op = r[0].split(' ')[0]
        stages = [r[1][0], r[2][0], r[2][1]] + r[3] + r[4] + ([] if op=='Sd' else r[5])
        if any(a >= b for a, b in zip(stages, stages[1:]) if (a, b) != (r[2][0], r[2][1])):
            errors.append('stages out of order: '+str(r))
        if (op=='Sd') and not (r[3][0] == r[5][0] > r[2][1]):
            errors.append('store does not write memory at commit: '+str(r))
    op_of = lambda r: r[0].split(' ')[0]
    int_ops = ['Add', 'Addi', 'Sub', 'Bne', 'Beq']
    if not check_overlap([r[2] for r in rows if op_of(r) in int_ops], 1):
        errors.append('integer adder used by 2 instructions in a cycle')
    if not check_overlap([r[2] for r in rows if op_of(r) in ['Ld', 'Sd']], 1):
        errors.append('address adder used by 2 instructions in a cycle')
    # a forwarded load has a single MEM cycle and does not use the memory port
    if not check_overlap([r[3] for r in rows if len(r[3])==2], 1):
        errors.append('memory port used by 2 instructions in a cycle')
    for ops in [['Add.d', 'Sub.d'], ['Mult.d']]:
        if not check_overlap([(r[2][0], r[2][0]) for r in rows if op_of(r) in ops], 1):
            errors.append('2 instructions entered the same fp unit in a cycle')
    # every instruction stays in EX for the configured number of cycles
    time = {'Ld': 'ld_sd', 'Sd': 'ld_sd', 'Add.d': 'fp_adder', 'Sub.d': 'fp_adder', 'Mult.d': 'fp_multi'}
    for r in rows:
        if r[2][1]-r[2][0]+1 != config['time_'+time.get(op_of(r), 'int_adder')+'_exe']:
            errors.append('wrong number of EX cycles: '+str(r))
        if (len(r[3])==2) and (r[3][1]-r[3][0]+1 != config['time_ld_sd_mem']):
            errors.append('wrong number of MEM cycles: '+str(r))
    wb = [r[4][0] for r in rows if len(r[4])>0]
    if any(wb.count(c) > width for c in wb):
        errors.append('more than issue width results broadcasted in a cycle')
    cycles = int(re.search(r'Total cycles: (\d+)', output).group(1))
    return errors, cycles

files = sys.argv[1:] if len(sys.argv)>1 else sorted(glob.glob('../tests/*.txt'))
failed = 0
print('test'.ljust(40)+''.join(('width '+str(w)).ljust(12) for w in range(1, 5)))
for name in files:
    config = read_input(name)
    item = name.ljust(40)
    messages = []
    for width in range(1, 5):
        run = subprocess.run([sys.executable, 'main.py', name, str(width)], 
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        if run.returncode != 0:
            errors, cycles = ['simulator crashed:\n'+run.stdout], 0
        else:
            errors, cycles = check(name, config, width, run.stdout)
        item += ((str(cycles)+' cycles') if len(errors)==0 else 'FAIL').ljust(12)
        messages += ['  width '+str(width)+': '+e for e in errors]
    print(item)
    for m in messages:
        print(m)
    failed += len(messages)
print('ALL TESTS PASSED' if failed==0 else str(failed)+' ERRORS')
sys.exit(1 if failed else 0)
