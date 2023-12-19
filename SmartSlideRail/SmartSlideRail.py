import serial,time,math,os,sys
import serial
import sys,os,cv2,math
import serial.tools.list_ports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Logger import LoggerHelper
from Common import CommonHelper
from Config import Config
from Camera import SmartCamera
from RoboticArm import RoboticArm
from Logger import LoggerHelper

SlideRailDeviceDes = "Prolific PL2303GT USB Serial COM Port"
deviceName = ''
stopRun = "CJXRp"
continueRun = "CJXRr"
COMM = None

def SlideRailSerialOpen():
    global deviceName
    global COMM
    if COMM == None:
        serial_port =  CommonHelper.getDeviceName(SlideRailDeviceDes)
        COMM = serial.Serial(serial_port, 115200, timeout=0.01)
    else:
        print(COMM)

# 关闭串口
def SlideRailSerialClose():
    global COMM
    if COMM != None:
        COMM.close()
    COMM = None

def SlideRailComReceive():
    try:
        rx_buf = ''
        rx_buf = COMM.read() # 转化为整型数字
        if rx_buf != b'':
            time.sleep(0.01)
            rx_buf = rx_buf + COMM.read_all()
            return rx_buf.decode("gb2312")
        else:
            return None
    except Exception as e:
        LoggerHelper.app_logger.error('SlideRailComReceive' + str(e))
        pass
    
def ScanAllMachines():
    currentDistance = 0
    # 判断滑轨是否通电
    global COMM
    SlideRailSerialClose()
    SlideRailSerialOpen()
    # CJXSA:查询当前坐标,速度等信息
    search_data = "CJXSA"
    COMM.write(search_data.encode())
    time.sleep(0.5)
    data = SlideRailComReceive()
    if data == None: #Not Energized
        LoggerHelper.app_logger.info('ScanAllMachines 滑轨未通电' )
        return
    SlideRailSerialClose()
    if os.path.exists(Config.CurrentSlideBarDistanceFile):
        with open(Config.CurrentSlideBarDistanceFile) as f:
            content = f.read()    
            currentDistance = content
    distance = 0 - round(float(currentDistance))
    if distance != 0:
        MoveSlideRail(distance)
    if os.path.exists(Config.CurrentSlideBarDistanceFile):
        os.remove(Config.CurrentSlideBarDistanceFile)
    else:
        print("The file does not exist")
    if os.path.exists(Config.SlideBarDistanceFile):
        os.remove(Config.SlideBarDistanceFile)
    if MachinesDistance != None:
        MachinesDistance.clear()
        
    ScanMachine()
    time.sleep(2)

def ScanMachine():
    moveLength = 0
    needMoveHigh = False
    slider_ratio = 2.7
    if COMM == None:
        SlideRailSerialOpen()    
    moveStepDistance = -10
    sendPreID = -1
    MachinesDistance = {}
    while abs(moveLength) < abs(Config.SlideTotalLength):
        # => 尝试 先拍一张图片，计算距离，步长二分 
        sendStr = "CJXCGX{}F6000$".format(moveStepDistance)
        COMM.write(sendStr.encode())
        waitTime = abs(moveStepDistance / 15) + 1
        time.sleep(waitTime)
        COMM.write(stopRun.encode())
        moveLength = moveLength + moveStepDistance
        with open(Config.CurrentSlideBarDistanceFile, 'w') as file:
            file.write(str(moveLength))
            LoggerHelper.app_logger.info('ScanMachine Write length: ' + str(moveLength))
        moveDirection = -1         
        machineAprilTags = SmartCamera.GetMachineAprilTag()
        machine_id = 0
        willScanMachine = None
        if len(machineAprilTags) > 0:
            aprilTagLocation = machineAprilTags
            for machine in machineAprilTags:
                if MachinesDistance.get(str(machine.tag_id)) == None:
                    willScanMachine = machine
                else:
                    moveStepDistance = -280
                    break
            if willScanMachine != None:
                aprilTag_center_x = round(willScanMachine.center[0]) # x_center
                machine_id = willScanMachine.tag_id
                if int(machine_id) >= 190 and int (machine_id) != 586:
                    slider_ratio = 2.8
                    long_keyboard_flag = True
                    min_keyboard_color = SmartCamera.GetColorLocation("Yellow")
                    if min_keyboard_color != None or min_keyboard_color == False:
                        min_color_x,min_color_y,min_color_w,min_color_h = min_keyboard_color
                        if willScanMachine.center[0] < min_color_x and abs(willScanMachine.center[1] - min_color_y) < 20:
                            if int(min_color_w) >= 44:
                                print(min_keyboard_color)
                            else:
                                moveStepDistance = -10
                else:
                    #print('识别小键盘！！！可以同时识别到两个二维码，判断二维码所在位置')
                    allAprilTag = SmartCamera.GetMachineAprilTag()
                    right_tag = SmartCamera.GetAprilTagBydTagId(allAprilTag, 586)
                    left_tag = SmartCamera.GetAprilTagBydTagId(allAprilTag, machine_id)
                    if left_tag != None :
                        print('Machine tag center x {}'.format(left_tag.center[0]))   
                        if int(machine_id) >= 90:                
                            moveStepDistance = -round((left_tag.center[0]-450) / slider_ratio)
                        else:
                            moveStepDistance = -round((left_tag.center[0]-370) / slider_ratio)
                        print('Move Step Distance: {}'.format(moveStepDistance))
                        if str(machine_id) in MachinesDistance:
                            moveStepDistance = -280
                        elif str(machine_id) not in MachinesDistance:
                            saveMachineValue = str(machine_id) +":" + str(moveLength + moveStepDistance)
                            MachinesDistance[str(machine_id)] = str(moveLength + moveStepDistance)
                            with open(Config.SlideBarDistanceFile, 'a') as file:
                                file.write(str(saveMachineValue))
                                file.write("\r\n")
                        if abs(int(moveStepDistance)) < 18:
                            moveStepDistance = -280
                        willMoveTotalLen = abs(moveStepDistance + moveLength)
                        if willMoveTotalLen > abs(Config.SlideTotalLength):
                            break

                    if right_tag != None :
                        print('right tag center x {}'.format(right_tag.center[0]))
                        LoggerHelper.app_logger.info('right tag center x {}'.format(right_tag.center[0]))
                    if left_tag != None and right_tag != None:
                        print('left tag center x {}'.format(left_tag.center[0]))
                        LoggerHelper.app_logger.info('left tag center x {}'.format(left_tag.center[0]))
        else:
             moveStepDistance = -20
        COMM.write(continueRun.encode()) 
    SlideRailSerialClose()
    LoggerHelper.app_logger.info('Scan Result {}'.format(str(MachinesDistance)))


def MoveSlideRail(distance):
    global COMM
    try:
        SlideRailSerialOpen()
        sendStr = "CJXCGX{0}F8000$".format(distance)
        COMM.write(sendStr.encode())
        moveTime = abs(distance / 100) * 2 + 2
        time.sleep(moveTime)
        SlideRailSerialClose()
        time.sleep(0.5)
    except Exception as e:
        LoggerHelper.app_logger.info('MoveSlideRail Failed: ' + str(e))
        return False
    return True

def GoToMachineByIndex(machineIndex):
    allMachinseLength = []
    currentLength = 0
    targetLength = 0
    machinesLength = {}
    
    RoboticArm.GotoZero()

    with open(Config.CurrentSlideBarDistanceFile, 'r') as file:
        currentLength = float(file.read())

    if os.path.exists(Config.SlideBarDistanceFile) == False:
        return False

    with open(Config.SlideBarDistanceFile, 'r') as file:
        allMachinseLength = file.readlines()
    for line in allMachinseLength:
        if line != "" and line != '\n' and line != '\r':
            id,length = line.replace('\n',"").split(":")
            machinesLength[str(id)] = float(length)
       
    if machineIndex in machinesLength:
        targetLength = float(machinesLength[machineIndex]) - currentLength
        if float(targetLength) == 0.0:
            print('The Current Loaction is Target location, donot need move')
            LoggerHelper.app_logger.info('The Current Loaction is Target location, donot need move')
            Config.CurrentSliderIsTargetMachineFlag = True
            return True
        
        Config.CurrentSliderIsTargetMachineFlag == False

        movesliderResult = MoveSlideRail(targetLength)
        if movesliderResult:
            currentLength = str(machinesLength[machineIndex])
            with open(Config.CurrentSlideBarDistanceFile, 'w') as file:
                file.write(currentLength)
            print('Move the slide Succeed!')
            return True
        else:
            print('Move the slide Failed!')
            return False
    else:
        print('The Machine {} is not in the List!'.format(machineIndex))
        return False

if __name__ == '__main__':
    MoveSlideRail(50)