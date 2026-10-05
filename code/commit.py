# Qing 
# 29th may 2017
'''
1. commit ROB_buffer
2. fetch header into ROB_buffer
'''

# function: print ROB entry 
def print_ROB(entry, instructions):
    item = instructions[entry.PC].ljust(30)
    item += str(entry.issue).ljust(15) 
    item += str(entry.exe).ljust(15) 
    item += str(entry.mem).ljust(15)
    item += str(entry.cdb).ljust(15)
    item += str(entry.commit)
    print(item)
# function: modify architectual reg
def modify_arch_reg(entry, reg_int, reg_fp):
    if entry.dest_tag[0] == 'F':
        reg_fp[int(entry.dest_tag[1:])] = entry.value
    elif entry.dest_tag == 'R0': # R0 is hardwired to 0
        pass
    elif entry.dest_tag[0] == 'R':
        reg_int[int(entry.dest_tag[1:])] = entry.value
    else:
        pass

# function: commit
# up to issue_width instructions leave the ROB per cycle, in program order
def commit(ROB, reg_int, reg_fp, cycle, instructions, issue_width):
    count = 0
    while (len(ROB)>0)&(count<issue_width):
        op = instructions[ROB[0].PC].split(' ')[0]
        if (op=='Bne')|(op=='Beq'):
            if len(ROB[0].exe)<2: # not resolved yet
                break
            ROB[0].commit.append(cycle+1)
        elif op=='Sd':
            # commit cycle is written by the MEM stage when the store starts writing memory
            if len(ROB[0].commit)==0:
                break
            entry = ROB.popleft()
            print_ROB(entry, instructions)
            continue
        else:
            if len(ROB[0].cdb)==0: # not broadcasted yet
                break
            ROB[0].commit.append(cycle+1)
            modify_arch_reg(ROB[0], reg_int, reg_fp)
        entry = ROB.popleft()
        print_ROB(entry, instructions)
        count += 1
