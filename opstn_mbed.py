# -*- coding: utf-8 -*-
"""
This is UDP program for Opstn
@author: Swarm Control 1 Sun Apr 19
"""
import select
import signal
import socket
import time


def sigalrm_handler(signum, frame):
    """The handler for SIGALRM."""
    raise TimeoutError


def get_latest(sock, size=1):
    """
    Get the latest input.
    
    This function automatically empties the given socket.
    
    Parameters
    ----------
    sock : socket
        The socket to be emptied.
    size : int
        The number of bytes to read at a time.
        
    Returns
    -------
    data : bytes
        The last received message, or None if the socket was not ready.
    
    """
    data = None
    input_ready, o, e = select.select([sock], [], [], 0.0)  # Check if ready.
    
    while input_ready:
        data = input_ready[0].recv(size)  # Read everything
        input_ready, o, e = select.select([sock], [], [], 0.0)
        
    return data


def receive_data(sock, delay=0.01, size=32):
    """
    Receive UDP data without blocking.
    
    Parameters
    ----------
    sock : socket
        The socket to use.
    delay : float, optional
        The timeout within which to read the socket, in seconds.
    size : int
        The number of bytes to read.
    
    Returns
    -------
    recv_msg : bytes
        The received message, or None if the buffer was empty.
        
    """
    recv_msg = None
    
    try:
        signal.setitimer(signal.ITIMER_REAL, delay, 0)  # Set up interrupt.
        recv_msg = get_latest(sock, size=size)
    except (BlockingIOError, TimeoutError):
        pass
    finally:
        signal.alarm(0)  # Cancel interrupt.
    
    return recv_msg

def get_input():
    mode = linear = pitch = yaw = 0
    key = input(("Press 'wasd' for roll/pitch or 'jk' for linear"
                 " or 'QRS' for quit/reset/startpos: "))
    if key == "w":
        pitch = 1
    elif key == "s":
        pitch = 2
    elif key == "a":
        yaw = 1
    elif key == "d":
        yaw = 2
    elif key == "j":
        linear = 1
    elif key == "k":
        linear = 2
    elif key == "Q":
        mode = 3
    elif key == "R":
        mode = 2
    elif key == "S":
        mode = 1
    else:
        print("ValueError")

    return mode, linear, pitch, yaw


class Arm:
    """
    A arm class.
    
    Send arm commands to mbed and receive sensor and dynamixel data from mbed.
    
    Initialize with ip_address and port of opstn and ip_address and  port of 
    mbed. After initialize, send arm command by 'send_arm' and receive sensor
    and dynamixel date by 'recv_sensor'.
    
    Parameters
    ----------
    hostopstn : str
        opstn's host.
    portopstn : int
        opstn's port.
    hostmbed : str
        mbed's host.
    portmbed : int
        mbed's port.
    
    Attributes
    ----------
    hostopstn : str
        opstn's host.
    portopstn : int
        opstn's port.
    hostmbed : str
        mbed's host.
    portmbed : int
        mbed's port.
    sock : socket
        socket for udp
    
    """
    
    def __init__(self, hostopstn, portopstn, hostmbed, portmbed):
        self.hostopsnt = hostopstn
        self.portopstn = portopstn
        self.hostmbed = hostmbed
        self.portmbed = portmbed
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        self.sock.bind((self.hostopsnt, self.portopstn))
        
        signal.signal(signal.SIGALRM, sigalrm_handler)
        
        mode = 1
        self.sock.sendto(mode.to_bytes(1,"little"), 
                         (self.hostmbed, self.portmbed))
    
    def send_arm(self, mode, linear, pitch, yaw):
        """
        Send the arm command to mbed.
        
        Parameters
        ----------
        mode : int
            A value from 0 to 3.
            0 : nomal mode
            1 : Start position
            2 : Reset
            3 : Quit
        linear : int
            A value from 0 to 2.
            0 : stop
            1 : prolong
            2 : shrink
        pitch : int
            A value from 0 to 2.
            0 : stop
            1 : raise
            2 : lower
        yaw : int
            A value from 0 to 2.
            0 : stop
            1 : turn to right
            2 : turn to left
        
        """
        senddata = 0
        if max(mode, linear, pitch, yaw) > 3:
            raise ValueError
        elif mode is not 0:
            senddata = mode
        else:
            senddata += (linear<<2) + (pitch<<4) + (yaw<<6)
        print("Send data is '{}' '{}'".format(senddata, bin(senddata)))
        self.sock.sendto(senddata.to_bytes(1, "little"), 
                         (self.hostmbed, self.portmbed))
    
    def recv_sensor(self):
        """
        Reveive dynamixel and sensor data.
        
        Returns
        -------
        float list
            Sensor data.
            6 dynamixel data and 33 sensor data can be used.
        
        """
        recv_msg = receive_data(self.sock, size=1024)
        if recv_msg is not None:
            recv_msg_str = recv_msg.decode()
            return [float(i) for i in recv_msg_str.split()]
        else:
            return recv_msg


if __name__ == "__main__":
    hostopstn = "127.0.0.1"
#    ipopstn = "192.168.1.90"
    hostmbed = "127.0.0.1"
#    ipmbed = "192.168.1.100"
    portopstn = 60000
    portmbed = 50000
    
    arm = Arm(hostopstn, portopstn, hostmbed, portmbed)
    time.sleep(1)
    
    try:
        while True:
            mode, linear, pitch, yaw = get_input()
            print(mode, linear, pitch, yaw)
            if mode is 0:
                for i in range(10):
                    arm.send_arm(mode, linear, pitch, yaw)
                    time.sleep(0.05)
                    sensor_data = arm.recv_sensor()
                    if sensor_data is not None:
                        print("Reception success!")
                        print("Received -> ", sensor_data, "\n")
                    else:
                        print("Reception failure!\n")
                    time.sleep(0.05)
            elif mode is not 3:
                arm.send_arm(mode, 0, 0, 0)
                time.sleep(0.05)
                print()
            else:
                print("Quit mode")
                arm.send_arm(mode, 0, 0, 0)
                print()
                break
    
    finally:
        arm.sock.close()
        print("\nTerminate socket\n")
