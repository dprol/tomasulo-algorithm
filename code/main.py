# Qing 
# 21st May 2017 

# usage: python main.py [input file] [issue width]
#   input file  -- hardware configuration, initial values and instructions (default: test_case.txt)
#   issue width -- 1 to 4, overrides the 'Issue width = n' line of the input file (default: 1)

import sys
from copy import deepcopy
from collections import deque, namedtuple
from init import read_input, build_rs, ld_sd_entry, ld_sd_exe, ld_sd_mem, cdb, ROB_entry, PC
from print_status import ps, pss
from issue import issue, check_rs_space
from exe import exe 
from mem import mem
from wb import wb 
from commit import commit
'''initialize'''
# read configuration and instructions 
input_file = sys.argv[1] if len(sys.argv)>1 else 'test_case.txt'
config = read_input(input_file)
instructions = config['instructions']
issue_width = int(sys.argv[2]) if len(sys.argv)>2 else config['issue_width']
if (issue_width<1)|(issue_width>4):
    sys.exit('Issue width must be between 1 and 4')
'''initialize regs, RAT, memory''' 
# integer REG
reg_int = []
for i in range(32):
    reg_int.extend([0])
for i in config['reg_int']:
    if i != 0: # R0 is hardwired to 0
        reg_int[i] = config['reg_int'][i]
rat_int = deepcopy(reg_int)
# fp REG
reg_fp = []
for i in range(32):
    reg_fp.extend([0])
for i in config['reg_fp']:
    reg_fp[i] = config['reg_fp'][i]
rat_fp = deepcopy(reg_fp)
# memory 
memory = []
for i in range(256):
    memory.extend([0])
for i in config['memory']:
    memory[i] = config['memory'][i]
'''intialize reservation stations'''
# integer adder rs 
size_rs_int_adder = config['size_rs_int_adder']
rs_int_adder = build_rs(size_rs_int_adder)
# fp adder rs
size_rs_fp_adder = config['size_rs_fp_adder']
rs_fp_adder = build_rs(size_rs_fp_adder)
# fp multiplier rs
size_rs_fp_multi = config['size_rs_fp_multi']
rs_fp_multi = build_rs(size_rs_fp_multi)
'''initilize function unit'''
# cycles in int adder 
fu_int_adder = deque()
time_fu_int_adder = config['time_int_adder_exe']
# cycles in fp adder 
fu_fp_adder = deque()
time_fu_fp_adder = config['time_fp_adder_exe']
# cycles in fp multiplier
fu_fp_multi = deque()
time_fu_fp_multi = config['time_fp_multi_exe']
'''initialize load/store queue'''
ld_sd_queue = deque()
size_ld_sd_queue = config['size_rs_ld_sd']
ld_sd_exe = ld_sd_exe()
ld_sd_exe.busy = 0
time_ld_sd_exe = config['time_ld_sd_exe']
ld_sd_mem = ld_sd_mem()
ld_sd_mem.busy = 0
time_ld_sd_mem = config['time_ld_sd_mem']
'''initialize ROB'''
ROB = deque()
size_ROB = config['size_ROB']
'''initialize CDB'''
# the CDB broadcasts up to issue_width results per cycle
results_buffer = deque()
cdb_entry = cdb
cdb = []
for i in range(issue_width):
    cdb.append(cdb_entry())
    cdb[-1].valid = 0
"""issue first instruction"""
# instruction pointer 
PC = PC()
PC.PC = 0
PC.valid = 1 
cycle = 1
last_cycle = 0

# print title 
print ('Issue width = '+str(issue_width))
item = ''.ljust(30)
item += 'ISSUE'.ljust(15)
item += 'EXE'.ljust(15)
item += 'MEM'.ljust(15)
item += 'WB'.ljust(15)
item += 'COMMIT'.ljust(15)
print (item)

# main
# run until all instructions are committed and the last store has left the memory unit
while (len(ROB)>0)|(PC.PC<len(instructions))|(ld_sd_mem.busy==1):
    
    '''ISSUE stage'''
    if (PC.PC<len(instructions))&(PC.valid==1):
        issue(cycle, PC, instructions, ROB, size_ROB, 
                rs_int_adder, 
                rs_fp_adder, 
                rs_fp_multi, 
                ld_sd_queue, size_ld_sd_queue, 
                rat_int, rat_fp, issue_width)

    '''EXE stage'''
    exe(fu_int_adder, time_fu_int_adder, 
        fu_fp_adder, time_fu_fp_adder, 
        fu_fp_multi, time_fu_fp_multi, results_buffer,  
        rs_int_adder, rs_fp_adder, rs_fp_multi, 
        ld_sd_exe, time_ld_sd_exe, ld_sd_queue,
        cycle, ROB, PC)

    '''MEM stage'''
    mem(ld_sd_queue, ld_sd_mem, time_ld_sd_mem, results_buffer,
        memory, ROB, cycle)

    '''CDB stage'''
    wb(cdb, rat_int, rat_fp, 
        rs_int_adder, rs_fp_adder, rs_fp_multi,
        ld_sd_queue, ROB, cycle,
        results_buffer) 
    
    '''COMMIT stage'''
    size = len(ROB)
    commit(ROB, reg_int, reg_fp, cycle, instructions, issue_width)
    if len(ROB)<size: # commits of this stage happen in cycle+1
        last_cycle = cycle+1
    
    # cycle number 
    cycle +=1  
    if cycle > 100000:
        sys.exit('Simulation did not finish after 100000 cycles')

# print registers and memory
print ('')
print ('Total cycles: '+str(max(last_cycle, cycle-1)))
print ('')
print ('REGISTER VALUES')
for name, reg in [('R', reg_int), ('F', reg_fp)]:
    for start in range(0, 32, 8):
        item = ''.ljust(8)
        for i in range(start, start+8):
            item += (name+str(i)).ljust(10)
        print (item)
        item = 'value:'.ljust(8)
        for i in range(start, start+8):
            item += str(reg[i]).ljust(10)
        print (item)
print ('')
print ('NON-ZERO MEMORY VALUES')
print ('Addresses'.ljust(15)+'Values')
for address in range(len(memory)):
    if memory[address] != 0:
        print (str(address).ljust(15)+str(memory[address]))
