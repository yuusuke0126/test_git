# -*- coding: utf-8 -*-
"""
This is UDP program for recv

@author: Swarm Control 1
"""
import socket
import time


if __name__ == "__main__":
    ipmbed = "127.0.0.1"
    ipopstn = "127.0.0.1"
#    host = "192.168.1.90"
#    hostopstn = '10.249.255.194'
#    hostrpi = '10.249.255.194'
#    hostrpi = '10.249.255.147'
    portmbed = 50000
    portopstn = 60000
    hostmbed = (ipmbed, portmbed)
    hostopstn = (ipopstn, portopstn)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind(hostmbed)
        print("Now waiting...")
        
        for i in range(256):
            recv_msg = sock.recv(1024)
            recv_data = int.from_bytes(recv_msg, "little")
            print("\nReceived ->", recv_data, bin(recv_data))
            time.sleep(0.001)
            
            if recv_data > 3 or recv_data == 0:
                if i % 3 is not 0:
                    data_list = [str((j+i)/2) for j in range(50)]
                    data_str = " ".join(data_list)
                    #print(data_str)
                    send_data = data_str.encode()
                    print("Send data " + data_list[0])
                    sock.sendto(send_data, hostopstn)
                    time.sleep(0.001)
                else:
                    print("\nNot send data")
            elif recv_data == 3:
                print("Quit mode")
                break
            
    finally:
        sock.close()
        print("\nTerminate socket\n")
