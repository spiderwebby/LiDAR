# import matplotlib.pyplot as plt
# import numpy as np
# from socket import timeout
# import time
import math
import socket

import serial

TELEPLOT_ADDR = ("127.0.0.1", 47269)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Serial port variables
SERIAL_PORT = "COM11"
SERIAL_BAUDRATE = 115200

# Scan variables
scanSamplesSignalQuality = [0.0]
scanSamplesRange = [0.0]
t = 0


# Delta-2G Frame Characteristics
# Constant Frame Parts values
FRAME_HEADER = 0xAA			# Frame Header value
PROTOCOL_VERSION = 0x01		# Protocol Version value
FRAME_TYPE = 0x61			# Frame Type value
# Scan Characteristics
SCAN_STEPS = 15				# How many steps/frames each full 360deg scan is composed of
# Received value scaling
ROTATION_SPEED_SCALE = 0.05 * 60  # Convert received value to RPM (LSB: 0.05 rps)
ANGLE_SCALE = 0.01			# Convert received value to degrees (LSB: 0.01 degrees)
RANGE_SCALE = 0.25  # x0.001	#Convert received value to meters (LSB: 0.25 mm)


theta = []
radius = []


# Delta-2G frame structure
class Delta2Dv005Frame:
    frameHeader = 0			# Frame Header: 1 byte
    frameLength = 0			# Frame Length: 2 bytes, from frame header to checksum (excluded)
    protocolVersion = 0		# Protocol Version: 1 byte
    frameType = 0			# Frame Type: 1 byte
    commandWord = 0			# Command Word: 1 byte, identifier to distinguish parameters
    parameterLength = 0		# Parameter Length: 2 bytes, length of the parameter field
    parameters = [0]		# Parameter Field
    checksum = 0			# Checksum: 2 bytes



def LiDARFrameProcessing(frame: Delta2Dv005Frame):
    
    match frame.commandWord:
        case 0xAE:
            # Device Health Information: Speed Failure
            rpm = frame.parameters[0] * ROTATION_SPEED_SCALE
            print("RPM: %f" % rpm)
        case 0xAD:
            # 1st: Rotation speed (1 byte)
            rpm = frame.parameters[0] * ROTATION_SPEED_SCALE
            # print("RPM: %f" % rpm)

            # 2nd: Zero Offset angle (2 bytes)
            offsetAngle = (frame.parameters[1] << 8) + frame.parameters[2]
            offsetAngle = offsetAngle * ANGLE_SCALE
            #print("zo:", offsetAngle, end=",")

            # 3rd: Start angle of current data freame (2 bytes)
            startAngle = (frame.parameters[3] << 8) + frame.parameters[4]
            startAngle = startAngle * ANGLE_SCALE
            # print(startAngle, end=",")

            # Calculate number of samples in current frame
            sampleCnt = int((frame.parameterLength - 5) / 3)

            # Calculate current angle index of a full frame: For Delta-2G each full rotation has 15 frames
            frameIndex = int(startAngle / (360.0 / SCAN_STEPS))

            if frameIndex == 0:
				#New scan started
                scanSamplesRange.clear()
                scanSamplesSignalQuality.clear()

			#  4th: LiDAR samples, each sample has: Signal Value/Quality (1 byte), Distance Value (2 bytes)
            
            for i in range(sampleCnt):
                signalQuality = frame.parameters[5 + (i * 3)]
                distance = (frame.parameters[5 + (i * 3) + 1] << 8) + frame.parameters[5 + (i * 3) + 2]
                scanSamplesSignalQuality.append(signalQuality)
                scanSamplesRange.append(distance * RANGE_SCALE)

                # polar plot:
                    # print(round((startAngle+i*0.9),2),",", distance
                    # foo = (round((startAngle+i*0.9),2),",", distance)

                # teleplot format example
                    # nameTimestamped:1:1:1627551892437|xy
                    # name:1:1|xy

                # polar to Cartesian:
                thetaa = ((startAngle+i*0.9))
                x = int(round(-distance*math.cos(math.radians(thetaa)),0))
                y = int(round(distance*math.sin(math.radians(thetaa)),0))
                
                # teleplot cartesian
                # foo = f"lidar:{x}:{y}|xy"

                
                # 3d cartesian wip
                global t
                if (x < -0.001) or (x > 0.001):
                    t = t + 1
                    foo = f"3D|mySimpleSphere:{t}:S:sphere:P:{x}:{y}:10:RA:2:C:red"
                    # outspam it!
                    sock.sendto(foo.encode(), TELEPLOT_ADDR)
                    print(foo)
                    
                # theta.append( math.radians(startAngle+i*0.9))
                # radius.append(distance)
                

                # if frameIndex <= (SCAN_STEPS - 1):
                # Scan complete
                # print("SCAN: %d" % len(scanSamplesRange))


try:
    lidarSerial = serial.Serial(SERIAL_PORT, SERIAL_BAUDRATE, timeout=0)
    # lidarSerial = open('rawcapture.dat', 'rb')
except serial.serialutil.SerialException: # type: ignore
    print("ERROR: Serial Connect Error")
    quit(1)

status = 0
checksum = 0
count = 0
lidarFrame = Delta2Dv005Frame()
# while True:
while True:
    rx = lidarSerial.read(100) 

    for by in rx:
        match status:
            case 0:
                # 1st frame byte: Frame Header
                lidarFrame.frameHeader = by
                if lidarFrame.frameHeader == FRAME_HEADER:	 # AA
                    # Valid Header
                    status = 1
                else:
                    print("ERROR: Frame Header Failed: ", lidarFrame.frameHeader)
                # Reset checksum, new frame start
                checksum = 0
            case 1:
                # 2nd frame byte: Frame Length MSB
                lidarFrame.frameLength = (by << 8)
                status = 2
            case 2:
                # 3rd frame byte: Frame Length LSB
                lidarFrame.frameLength += by
                status = 3
            case 3:
                # 4th frame byte: Protocol Version
                lidarFrame.protocolVersion = by
                if lidarFrame.protocolVersion == PROTOCOL_VERSION:
                    # Valid Protocol Version
                    status = 4
                else:
                    print("ERROR: Frame Protocol Version Failed")
                    status = 0
            case 4:
                # 5th frame byte: Frame Type
                lidarFrame.frameType = by
                if lidarFrame.frameType == FRAME_TYPE:
                    # Valid Frame Type
                    status = 5
                else:
                    print("ERROR: Frame Type Failed")
                    status = 0
            case 5:
                # 6th frame byte: Command Word
                lidarFrame.commandWord = by
                status = 6
            case 6:
                # 7th frame byte: Parameter Length MSB
                lidarFrame.parameterLength = (by << 8)
                status = 7
            case 7:
                # 8th frame byte: Parameter Length LSB
                lidarFrame.parameterLength += by
                lidarFrame.parameters.clear()
                status = 8
            case 8:
                # 9th+ frame bytes: Parameters
                lidarFrame.parameters.append(by)
                if len(lidarFrame.parameters) == lidarFrame.parameterLength:
                    # End of parameter frame bytes
                    status = 9
            case 9:
                # N+1 frame byte: Checksum MSB
                lidarFrame.checksum = (by << 8)
                status = 10
            case 10:
                # N+2 frame byte: Checksum LSB
                lidarFrame.checksum += by
                # End of frame reached
                # Compare received and calculated frame checksum
                if lidarFrame.checksum == checksum:
                    # Checksum match: Valid frame
                    LiDARFrameProcessing(lidarFrame)
                    # print(time.time)
                    count += 1

                else:
                    # Checksum missmatach: Invalid frame
                    print("ERROR: Frame Checksum Failed");
                status = 0
        if status < 10:  # Calculate current frame checksum, all bytes excluding the last 2, which are the checksum
            checksum = (checksum + by) % 0xFFFF
