import socket
import sys
import threading
from check import ip_checksum
import re
import fcntl, os
import select

def timeout_func(pkt, (host, port)):
        print '[Timeout] Resending ' + str(pkt)
        s.sendto(pkt, (host, port))
try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
except socket.error:
        print 'Failed to create socket'
        sys.exit()

host = 'localhost';
port = 8888;

base = 0 #Number of oldest unacknowledged packet
next_seq_num = 0 #Smallest unused sequence number (next packet to be sent)
window_size = 4 #Used to send packets 0, 1, 2, and 3
pkt_list = []
itr = 0

s.setblocking(0)

while(1):
        if next_seq_num == 9:
                sys.exit() #Exit program before seq num are double digits
#       if itr == 7: #Run X iterations for viewing purposes. TODO: next_seq_num is unbounded. Is that OK?
                #sys.exit()
        try:
                if next_seq_num < (base + window_size):
                        pkt = 'Packet #' + str(next_seq_num)
                        checksum = ip_checksum(pkt)
                        pkt += checksum
                        pkt_list.append(pkt) #Store packet into list[] for potential retransmit
                        s.sendto(pkt, (host, port)) #Transmit packet
                        print 'Sending Packet #' + str(next_seq_num)
                        #In SR, each packet must have its own timer
                        t = threading.Timer(2.0, timeout_func, [pkt, (host, port)])
                        t.start()
                        next_seq_num += 1 #Prepare to send next packet
                else:
                        #k = 0
                        #print '\n[List of Packets in retransmission window]'
                        #for i in pkt_list: #Print packets in window
                #               print 'Packet at ' + str(k) + ' ' + pkt_list[int(k)]
        #                       k += 1
                        break
                ready = select.select([s], [], [], 1) #https://stackoverflow.com/questions/2719017/how-to-set-timeout-on-pythons-socket-recv-method
                if ready[0]:
                        d = s.recvfrom(1024) #Check ACK from server.
                        base = int(d[0][-3:-2]) + 1 #Store ACK # in base
                        print '\nReceived ACK #' + str(d[0][-3:-2])
                        print 'Base #' + str(base) + ', next_seq_num #' + str(next_seq_num) + ', packet in front of list ' + pkt_list[0][-3:-2]
                        if int(base) <= int(next_seq_num): #In FSM, operator is ==. In FSM, it can send packets and wait for packets simultaenously.
                                k = 0 # I use < operator because packets sent in stream at beginning. 
                                for i in pkt_list: #Search pkt_list[] to move retransmission window
                                        if int(pkt_list[k][-3:-2]) == int(d[0][-3:-2]):
                                                t.cancel()
                                                print 'Removing Packet #' + str(pkt_list[k][-3:-2])  + ', moving window'
                                                pkt_list.pop(int(k))
                                        else:
                                                print 'Packet not found'
                                        k += 1
                        else:
                                t = threading.Timer(2.0, timeout_func, [pkt, (host, port)]) #retransmit
                                t.start()
                else:
                        continue
        except socket.error, msg:
                print 'Error Code: ' + str(msg[0]) + ' Message ' + msg[1]
                sys.exit()
        itr += 1

