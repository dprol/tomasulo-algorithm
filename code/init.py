# Qing 
# 21st May 2017 

import re
from collections import namedtuple

'''define data types'''
# reservation station 
def rs_entry():
    rs_entry = namedtuple('rs_entry', 'busy, op, tag_1st, value_1st, valid_1st, tag_2nd, value_2nd, valid_2nd, dest_tag')
    temp = rs_entry
    return temp 
# functional unit 
def fu_entry():
    fu_entry = namedtuple('fu_entry', 'cycle, op, value1, value2, dest_tag')
    temp = fu_entry
    return temp
# function result 
def fu_result():
    fu_result = namedtuple('fu_result', 'value, dest_tag')
    temp = fu_result
    return temp
# ld/sd entry
def ld_sd_entry():
    ld_sd_entry = namedtuple('ld_sd_entry', 'ld_sd_tag, ready, op, address, data, dest_tag, immediate, reg_tag, reg_value, valid')
    temp = ld_sd_entry
    return temp
# ld/sd exe
def ld_sd_exe():
    ld_sd_exe = namedtuple('ld_sd_exe', 'busy, cycle, value1, value2, dest_tag')
    temp = ld_sd_exe
    return temp
# ld/sd mem
def ld_sd_mem():
    ld_sd_mem = namedtuple('ld_sd_mem', 'busy, cycle, op, data, address, dest_tag')
    temp = ld_sd_mem
    return temp
# cdb
def cdb():
    cdb = namedtuple('cdb', 'valid, value, dest_tag')
    temp = cdb
    return temp
# ROB_entry 
def ROB_entry():
    ROB_entry = namedtuple('ROB_entry', 'ROB_tag, PC, value, dest_tag, issue, exe, mem, cdb, commit')
    temp = ROB_entry
    temp.issue = []
    temp.exe = []
    temp.mem = []
    temp.cdb = []
    temp.commit =[]
    return temp
# PC 
def PC():
    PC = namedtuple('PC', 'PC, valid')
    temp = PC
    return temp
# function: read instructions
def read_instruction(codefile):
    with open(codefile) as f:
            instructions = f.read().splitlines()
    return instructions
# function: convert a string into int or float
def to_number(text):
    try:
        return int(text)
    except ValueError:
        return float(text)
# function: normalize an instruction, e.g. 'ld f4, 8(r1)' --> 'Ld F4 8(R1)'
def normalize_instruction(line):
    tokens = [t for t in re.split(r'[,\s]+', line.strip()) if t != '']
    return ' '.join([tokens[0].capitalize()] + [t.upper() for t in tokens[1:]])
# function: read hardware configuration, initial values and instructions
def read_input(inputfile):
    config = {'issue_width': 1, 'size_ROB': 64,
              'reg_int': {}, 'reg_fp': {}, 'memory': {}, 'instructions': []}
    units = [('integer adder', 'int_adder'), ('fp adder', 'fp_adder'),
             ('fp multiplier', 'fp_multi'), ('load/store unit', 'ld_sd')]
    with open(inputfile) as f:
        lines = f.read().splitlines()
    for line in lines:
        line = line.strip()
        lower = line.lower()
        if (line == '') or ('# of' in lower):
            continue
        # functional unit rows: # of rs, cycles in EX, [cycles in Mem], # of FUs
        unit = [name for (prefix, name) in units if lower.startswith(prefix)]
        if len(unit) > 0:
            numbers = [int(n) for n in re.findall(r'\d+', line)]
            config['size_rs_' + unit[0]] = numbers[0]
            config['time_' + unit[0] + '_exe'] = numbers[1]
            if unit[0] == 'ld_sd':
                config['time_ld_sd_mem'] = numbers[2]
            if numbers[-1] != 1:
                print('Warning: only 1 FU per type is supported, using 1 for ' + unit[0])
        elif lower.startswith('rob entries'):
            config['size_ROB'] = int(line.split('=')[1])
        elif lower.startswith('issue width'):
            config['issue_width'] = int(line.split('=')[1])
        elif '=' in line:
            # initial values: R1=10, F2=30.1, Mem[4]=1
            for item in line.split(','):
                name, value = [x.strip() for x in item.split('=')]
                if name.lower().startswith('mem'):
                    config['memory'][int(name[4:-1])] = to_number(value)
                elif name[0].upper() == 'R':
                    config['reg_int'][int(name[1:])] = to_number(value)
                else:
                    config['reg_fp'][int(name[1:])] = to_number(value)
        else:
            config['instructions'].append(normalize_instruction(line))
    return config
# function: build rs
def build_rs(num):
    rs = []
    for _ in range(num):
        temp = rs_entry()
        temp.busy = 0
        rs.extend([temp])
    return rs

