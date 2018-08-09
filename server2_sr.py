import socket
import sys
from check import ip_checksum
import threading
import re

HOST = ''
PORT = 8888

try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print 'Socket created'
except socket.error, msg:
        print 'Failed to create socket. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
        sys.exit()

try:
        s.bind((HOST, PORT))
except socket.error, msg:
        print 'Bind failed. Error Code: ' + str(msg[0]) + ' Message ' + msg[1]
        sys.exit()

print 'Socket bind complete'

expected_seq_num = '0'
itr = 0

#In SR receiver, acknowledge all packets regardless of order.
#Out of order packets are buffered until missing packets received
window_size = 4
rcv_base = 0 #Last ACKed packet
pkt_buffer_list = []

while 1:
        d = s.recvfrom(1024)
        data = d[0]
        if not data: #Check if data is there
                break
        addr = d[1]
        if d[0][-2:] != ip_checksum(d[0][:-2]): #Check if packet is corrupt
                print 'Error: Invalid checksum, resend ACK #' + str(int(expected_seq_num) - 1)
                pkt = 'Acknowledging packet #' + str(int(expected_seq_num) - 1) #Make acknowledgement packet
                checksum = ip_checksum(pkt) #Create checksum
                pkt += checksum #Concat checksum
                reply = 'OK...' + pkt
                s.sendto(reply, addr)
                continue
        #No sequence number check.
        #(Extract)
        #(Deliver)
        if (int(d[0][-3:-2]) < rcv_base + window_size - 1) and (int(d[0][-3:-2]) >= rcv_base): #Sequence # of packet is within window
                #print 'rcv_base: ' + str(rcv_base) + ', expected_seq_num: ' + str(expected_seq_num)
                if int(d[0][-3:-2]) == int(expected_seq_num): #Packet received is front of window. Send ACK
                        pkt = 'Sending ACK for Packet #' + str(expected_seq_num) #Make acknowledgement packet
                        checksum = ip_checksum(pkt) #Create checksum
                        pkt += checksum #Concat checksum
                        reply = 'OK...' + pkt
                        if itr != 2: #TODO: Imitate lost packet
                                s.sendto(reply, addr)
                                print 'Message[' + addr[0] + ':' + str(addr[1]) + '] - ' + reply.strip()
                                var = int(expected_seq_num) #Increment expected_seq_num if received packet correctly
                                var += 1
                                expected_seq_num = str(var) #Change front of window
                                rcv_base += 1
                                j = 0
                                for i in pkt_buffer_list: #Send ACKs for any buffered packets
                                        pkt = 'Sending ACK for Packet #' + str(pkt_buffer_list[j])
                                        checksum = ip_checksum(pkt)
                                        pkt += checksum
                                        reply = '[Buffered]OK...' + pkt
                                        s.sendto(reply, addr)
                                        print 'Message[' + addr[0] + ':' + str(addr[1]) + '] - ' + reply.strip()
                                        var = int(expected_seq_num) #Increment expected_seq_num if received packet correctly
                                        var += 1
                                        expected_seq_num = str(var) #Change front of window
                                        pkt_buffer_list.pop(0)
                                        j += 1
                        else:
                                print 'Not sending ACK for Packet #' + str(expected_seq_num)
                else : #Buffer out of order packet
                        print 'Packet #' + d[0][-3:-2] + ' received out of sequence. Adding to buffer'
                        pkt_buffer_list.append(d[0][-3:-2])
        #else:
                #ignore packet
        itr += 1
s.close()

