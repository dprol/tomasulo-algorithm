# Qing 
# 24th May 2017

''' 
1. calculate valid instructions
    -- for ALU instructions, write results into fu_results, remove that fu entry  
    -- for LD/SD, write address result immediately back to ld_sd_queue
2. fetch instructions into function unit with spare space
    -- remove ALU instructions from rs
    -- don't remove ld/sd instructions
'''
from init import fu_entry, fu_result

# function: find ROB entry by tag
def find_ROB_entry(ROB, tag):
    for index in range(len(ROB)):
        if ROB[index].ROB_tag == tag:
            break
    return index

# function: check rs and return valid instruction index
# only instructions issued in a previous cycle can start execution; 
# the oldest one (first in ROB) is selected
def check_valid_ins_in_rs(rs, ROB, cycle):
    index = -1
    oldest = len(ROB)
    for i in range(len(rs)):
        if (rs[i].valid_1st==1)&(rs[i].valid_2nd==1)&(rs[i].busy==1):
            rob_index = find_ROB_entry(ROB, rs[i].dest_tag)
            if (ROB[rob_index].issue[0]<cycle)&(rob_index<oldest):
                index = i
                oldest = rob_index
    return index

# function: check ld_sd_queue and return valid instruction index
def check_valid_ins_in_ldsd(ldsd, ROB, cycle):
    index = -1
    if len(ldsd)!=0:
        for i in range(len(ldsd)):
            if (ldsd[i].valid==1) & (ldsd[i].ready==0):
                if ROB[find_ROB_entry(ROB, ldsd[i].dest_tag)].issue[0] < cycle:
                    index = i
                    break
    return index

# function: add entry into fu 
def add_entry_into_fu(fu, ins_in_rs):
    fu[-1].cycle = 0
    fu[-1].op = ins_in_rs.op
    fu[-1].value1 = ins_in_rs.value_1st
    fu[-1].value2 = ins_in_rs.value_2nd
    fu[-1].dest_tag = ins_in_rs.dest_tag

# function: functional units execution 
# new_only: only the entry just fetched from rs advances (the others
# already advanced in this cycle)
def fu_exe(fu, fu_results, ROB, time_fu, cycle, PC, new_only=False):
    if len(fu)!=0:
        if new_only:
            fu[-1].cycle += 1
        else:
            for element in fu:
                element.cycle += 1
        # write starting cycle 
        if fu[-1].cycle == 1:
            index = find_ROB_entry(ROB, fu[-1].dest_tag)
            ROB[index].exe.append(cycle)
        # finish cycle
        if fu[0].cycle == time_fu:
            index = find_ROB_entry(ROB, fu[0].dest_tag)
            ROB[index].exe.append(cycle)
            # calculation result
            fu_results.append(fu_result())
            fu_results[-1].dest_tag = fu[0].dest_tag
            if (fu[0].op=='Add')|(fu[0].op=='Add.d')|(fu[0].op=='Addi'):
                fu_results[-1].value = fu[0].value1 + fu[0].value2
            elif (fu[0].op=='Sub')|(fu[0].op=='Sub.d'):
                fu_results[-1].value = fu[0].value1 - fu[0].value2
            elif (fu[0].op=='Mult.d'):
                fu_results[-1].value = fu[0].value1 * fu[0].value2
            elif (fu[0].op=='Bne')|(fu[0].op=='Beq'):
                fu_results.pop()
                if (fu[0].value1 == fu[0].value2) != (fu[0].op=='Beq'): # not taken
                    PC.PC += 1
                    PC.valid = 1
                else:
                    index = find_ROB_entry(ROB, fu[0].dest_tag)
                    offset = ROB[index].dest_tag
                    PC.PC = int(PC.PC + 1 + offset/4)
                    PC.valid = 1
            else:
                pass
            # remove from fu 
            fu.popleft()

# function: ld_sd_execution 
def ld_sd_execution(ld_sd_exe, time_ld_sd_exe, ld_sd_queue, ROB, cycle):
    if ld_sd_exe.busy == 1:
        # write down starting cycle
        if ld_sd_exe.cycle == 0:            
            for element in ld_sd_queue:
                if element.ld_sd_tag == ld_sd_exe.dest_tag:
                    break
            index = find_ROB_entry(ROB, element.dest_tag)
            ROB[index].exe.append(cycle)
        # execute 
        ld_sd_exe.cycle += 1
        # write address back to ld_sd_queue
        if ld_sd_exe.cycle == time_ld_sd_exe:
            address = ld_sd_exe.value1 + ld_sd_exe.value2
            for element in ld_sd_queue:
                if element.ld_sd_tag == ld_sd_exe.dest_tag:
                    element.address = address
                    element.ready = 1
                    break
            # write down finish cycle
            index = find_ROB_entry(ROB, element.dest_tag)
            ROB[index].exe.append(cycle)
            ld_sd_exe.busy = 0

# function: execution
def exe(fu_int_adder, time_fu_int_adder,
        fu_fp_adder, time_fu_fp_adder,
        fu_fp_multi, time_fu_fp_multi, results_buffer,
        rs_int_adder, rs_fp_adder, rs_fp_multi, 
        ld_sd_exe, time_ld_sd_exe, ld_sd_queue,
        cycle, ROB, PC):
    '''execution in fu and ld_sd address calculation'''
    ld_sd_execution(ld_sd_exe, time_ld_sd_exe, ld_sd_queue, ROB, cycle) 
    # functional units 
    fu_exe(fu_int_adder, results_buffer, ROB, time_fu_int_adder, cycle, PC)
    fu_exe(fu_fp_adder, results_buffer, ROB, time_fu_fp_adder, cycle, PC)
    fu_exe(fu_fp_multi, results_buffer, ROB, time_fu_fp_multi, cycle, PC)
    '''fetch instructions from rs and ld_sd_queue'''
    # from ld_sd_queue
    # check valid ins in ld_sd_queue 
    index = check_valid_ins_in_ldsd(ld_sd_queue, ROB, cycle)
    # put ins into ld_sd_exe
    if (index>=0)&(ld_sd_exe.busy==0):
        ld_sd_exe.busy = 1
        ld_sd_exe.cycle = 0
        ld_sd_exe.value1 = ld_sd_queue[index].reg_value
        ld_sd_exe.value2 = ld_sd_queue[index].immediate
        ld_sd_exe.dest_tag = ld_sd_queue[index].ld_sd_tag
        ld_sd_execution(ld_sd_exe, time_ld_sd_exe, ld_sd_queue, ROB, cycle)
    # from rs 
    # int_adder (unpipelined: fetch only when the adder is free)
    index = check_valid_ins_in_rs(rs_int_adder, ROB, cycle)
    if (index>=0)&(len(fu_int_adder)==0):
        fu_int_adder.append(fu_entry())
        add_entry_into_fu(fu_int_adder, rs_int_adder[index])
        fu_exe(fu_int_adder, results_buffer, ROB, time_fu_int_adder, cycle, PC, True)
        # remove ins from rs 
        rs_int_adder[index].busy = 0
    # fp_adder (pipelined)
    index = check_valid_ins_in_rs(rs_fp_adder, ROB, cycle)
    if index>=0:
        fu_fp_adder.append(fu_entry())
        add_entry_into_fu(fu_fp_adder, rs_fp_adder[index])
        fu_exe(fu_fp_adder, results_buffer, ROB, time_fu_fp_adder, cycle, PC, True)
        # remove ins from rs 
        rs_fp_adder[index].busy = 0
    # fp_multi (pipelined)
    index = check_valid_ins_in_rs(rs_fp_multi, ROB, cycle)
    if index>=0:
        fu_fp_multi.append(fu_entry())
        add_entry_into_fu(fu_fp_multi, rs_fp_multi[index])
        fu_exe(fu_fp_multi, results_buffer, ROB, time_fu_fp_multi, cycle, PC, True)
        # remove ins from rs 
        rs_fp_multi[index].busy = 0
