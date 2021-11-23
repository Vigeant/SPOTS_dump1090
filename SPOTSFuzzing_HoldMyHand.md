# SPOTS Fuzzing Lab (HOLD MY HAND)

## Step 1
Getting familiar with dump1090

1. compile dump1090 using make

	```bash
	$ cd ~/SPOTS_dump1090
	$ make dump1090
	```
	
2. read the help
	
	```bash
	$ ./dump1090 --help
	```
	
1. look for options where we can disable crc checks, bit fixes as this is required for fuzzing

	```bash
	--no-fix                 Disable single-bits error correction using CRC.
	--no-crc-check           Disable messages with broken CRC (discouraged).
	```
		
2. In this lab we will focus on exploring the code parsing the modeS message after their demodualtion from raw signal. Therefore, we will make use of a --ifile option and the --hex option so it interprets the data as hex.

	```bash
	--ifile <filename>       Read data from file (use '-' for stdin).
	--hex                    Read hex message data from ifile.
	```
	
3. run dump1090 with its testfile to get an idea of valid modes messages

	```bash
	$ ./dump1090 --ifile testfiles/testaa --raw
	```
	
4. test a sample execution parsing a hex input from stdin

	```bash
	$ echo "*8f4d2023991093ad087c133060d1;" | ./dump1090 --ifile - --hex --no-crc-check --no-fixA
	```
	
	This should parse the modes message and display its contents to the screen.
	
## step 2 
start fuzzing while we keep working
1. read the AFL README.md

	```bash
	$ cd <afl folder> ; grip
	```

	use a browser to navigate to the rendered README
	
	Read about how AFL works and look for instructions on using qemu mode so we can start fuzzing the current version of dump1090.
	
2. Start fuzzing!
	Start a fuzzing job

	```bash
	$ mkdir in
	$ mkdir out
	$ echo "*8f4d2023991093ad087c133060d1;" >in/test1
	$ afl-fuzz -i in/ -o out/ -Q ./dump1090 --ifile - --hex --no-crc-check --no-fixA
	```
	
	Follow instructions on the screen if this fails (will fail on your first run of the day)
	
3. Look around the nice retro UI a little. You can read all about it in the README file if you want.

4. Take note of the fuzzing speed measured in executions/seconds in the dashboard.

== step 3 ==
Instrumenting dump1090 for faster fuzzing. (x10 faster)

1. read the AFL README.md
	Look for the information on how to instrument your code (follow the instructions for the use of afl-gcc-fast)

2. modify the makefile to create a new recipe where we will use the afl-gcc-fast compiler.

	```bash
	$ vi Makefile
	```

	add the following recipe in the makefile and save.

	```Makefile
	dump1090_afl: dump1090.c anet.c
        	afl-gcc-fast -o dump1090_afl dump1090.c anet.c $(LDFLAGS) $(LDLIBS) -no-pie
	```
		
	**Also modify the clean recipe so that it removes the dump1090_afl.**
	
3. build your new instrumented dump1090

	```bash
	$ make dump1090_afl
	```
	
4. start fuzzing faster (depending on the resources of your vm, you might want to stop your last fuzzing job.)

	```bash
	$ rm -r out/*
	$ afl-fuzz -i in/ -o out/ ./dump1090_afl --ifile - --hex --no-crc-check --no-fixA
	```
	
5. Take note of the fuzzing speed measured in executions/seconds in the dashboard.

**Fun time is over, now we start working!!! Although this fuzzing job should yield something in less than 10 minutes...**

## step 4 
Optimizing our instrumented binary for much faster performance. (x30 faster)

1. read the AFL README.md

	Navigate the readme (you can click on links) to find information about persistent mode.
	
2. save a copy of the original dump1090.c as dump1090.c.bak

	```bash
	$ cp dump1090.c dump1090.c.bak
	```
	
3. Following instructions in the README and the various examples in the ~/AFLplusplus folder, modify your ./dump1090.c file.

	**Go all the way for the technique that uses shared memory fuzzing.**

4. Recompile, stop old fuzzing campaing and start a new fuzzing campaing.

5. Take note of the fuzzing speed measured in executions/seconds in the dashboard.

## step 5
Understanding the crash

1. At this point AFL likely found an input that makes dump1090 crash. Every crashing input can be found in the out/default/crashes folder.
	Inspect the various crashed in this folder to see if you can understand why it crashed dump1090. (do not spend to much time on this)

	```bash
	$ cat out/default/crashes/id<yourcrash>
	```
	
2. To simplify our life when analysing a crashing input, AFL has a tool called afl-tmin that can take a crash input and try and simplify it as much as possible while keeping its coverages stats similar. Use afl-tmin to simplify the first crash and save its output in a file called payload.

	```bash
	$ afl-tmin -i out/default/crashes/id<yourcrash> -o payload ./dump1090_afl --ifile - --hex --no-crc-check --no-fixA
	```
	
3. Inspect the newly created payload file to see if it makes more sense. Again do not spend to much time on this.

	```bash
	$ cat payload
	```
	
4. confirm that this payload makes the dump1090 application crash

	```bash
	$ cat payload | ./dump1090 --ifile - --hex --no-crc-check --no-fix
	```

	or

	```bash
	$ ./dump1090 --ifile payload --hex --no-crc-check --no-fix
	```
	
## step 6 
For the adventurous among you, it is now time to dive into the debugger and understand what happened.

1. debug dump1090 run it while feeding it the crashing payload so you can see where it crashes.

	```bash
	$ gdb ./dump1090
	```
	now let the program run...

	```
	gdb-peda$ r --ifile solutions/payload --hex --no-crc-check --no-fix
	```

	The program should segfaults and you see that its at line 1123 of the dump1090.c
	You can investigate this code in vi in a second terminal.
	When we look at why it crashed, we see that its trying to write in an unnalocated region of memory.
	
2. 	Investigate this using your gdb skills and try to explain what is happening here.
	
3.	Is this dangerous/exploitable?

## step 7 
Crafting an exploit Proof Of Concept

1. the out of bounds write can reach the .got.
2. printf is called after the corruption so targeting printf.got with a one_gadget is a good option
3. use one_gadget on the libc library.
4. put a breakpoint on the printf in gdb to see if it meets the constraints of any of the three one_gadget candidates.
5. the second candidate has potential as r15 is null and rdx points to our elm buffer that we control with mesgtype24.

PWN!


