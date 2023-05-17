#!/usr/bin/env python3
import serial
import time


def SendCmd(conn, cmd: str):
    conn.write(cmd)


if __name__ == "__main__":
    ser = serial.Serial("/dev/ttyACM0", 9600, timeout=1)
    ser.flush()
    time.sleep(2)
    while True:
        SendCmd(ser, b"FWD\n")
        """ time.sleep(0.01)
        SendCmd(ser, b"LFT\n")
        time.sleep(0.01)
        SendCmd(ser, b"FWD\n")"""
        time.sleep(1)
        line = ser.readline().decode("utf-8").rstrip()
        print(line)
        time.sleep(4)
        SendCmd(ser, b"BCK\n")
        time.sleep(1)
        line = ser.readline().decode("utf-8").rstrip()
        print(line)
        time.sleep(4)
        SendCmd(ser, b"RGT\n")
        time.sleep(1)
        line = ser.readline().decode("utf-8").rstrip()
        print(line)
        time.sleep(2)
        SendCmd(ser, b"LFT\n")
        time.sleep(1)
        line = ser.readline().decode("utf-8").rstrip()
        print(line)
        time.sleep(2)
        SendCmd(ser, b"STP\n")
        time.sleep(1)
        line = ser.readline().decode("utf-8").rstrip()
        print(line)
        time.sleep(4)


def SendCmd(conn: Serial, cmd: str):
    conn.write(cmd)
    line = conn.readline().decode("utf-8").rstrip()
    print(line)
    return
