Tomasulo Algorithm Simulation
* includes instructions of int_add, fp_add, fp_multi, load, store, branch (Bne, Beq);
* implements ROB, RAT, load-store-queue;
* implements out-of-order processing and memory disambiguation; 
* issues 1 to 4 instructions per cycle, in program order (issue width); with issue width n,
  up to n results are broadcast on the CDB and up to n instructions commit per cycle;
* reads the hardware configuration, initial values and program from an input file;
* doesn't include branch prediction (fetch stalls until a branch is resolved).

How to run (Python 3):

    cd code
    python3 main.py                           # runs test_case.txt, issue width from the file (default 1)
    python3 main.py ../tests/test2_independent.txt
    python3 main.py ../tests/test2_independent.txt 4    # issue width given on the command line

How to test:

    cd code
    python3 run_tests.py

run_tests.py runs every file in tests/ with issue width 1, 2, 3 and 4. For each run it
compares the final registers and memory with a sequential reference model, and checks
the timing table (at most `issue width` issues, broadcasts and commits per cycle, in-order
issue and commit, one instruction at a time in the integer adder, address adder and memory
port). The timing table of tests/test6_class_example.txt is also compared with the tables of
the example of the class slides (issue width 1 and 2).

Input file

                   # of rs         Cycles in EX    Cycles in Mem   # of FUs
    Integer adder   4               1                               1
    FP adder        3               4                               1
    FP multiplier   2               15                              1
    Load/store unit 5               1               5               1

    ROB entries = 64
    Issue width = 2
    R1=12, R2=32, F20=3.0
    Mem[4]=3.0, Mem[8]=2.0

    Ld F2 0(R1)
    Add.d F4, F2, F20
    Bne R1 R0 -12

* `Issue width` is optional (1 to 4, default 1).
* Instructions are case insensitive; operands are separated by spaces and/or commas.
* The branch offset is in bytes, relative to the next instruction, as in the original
  code: `Bne R1 R0 -12` jumps 3 instructions back from the instruction after the branch.
* Only 1 functional unit per type is supported.

Output: the cycles in which each instruction was in ISSUE, EX (first, last), MEM
(first, last), WB and COMMIT, printed in commit order, followed by the register values
and the non-zero memory values.

Files
* code/ -- simulator (main.py, init.py, issue.py, exe.py, mem.py, wb.py, commit.py) and run_tests.py
* tests/ -- test cases
* results/ -- output of every test case for issue width 1 to 4, and summary.txt
* changes.diff -- every change against the provided code (unified diff)
* the report is the PDF submitted with this code
