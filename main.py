
import time,socket
from Config import Config
from Common import CommonHelper
from RoboticArm import RoboticArm
from SmartSlideRail import SmartSlideRail
from SmartFinger import SmartFinger
from Logger import LoggerHelper

def handle_scan_machines():
    # 处理 ScanMachines 消息的逻辑
    global resultMsg
    RoboticArm.GotoZero()
    SmartSlideRail.ScanAllMachines()
    resultMsg = 'Scan All Machines Successful'

def handle_goto_machine(machine_id,deviceName):
    # 处理 GoToMachine 消息的逻辑
    global resultMsg
    machine_id = Config.SmartArmMachine.get(deviceName)
    gotoMachineReuslt = SmartSlideRail.GoToMachineByIndex(machine_id)
    print('Goto Machine Reuslt {}'.format(gotoMachineReuslt))
    if Config.CurrentSliderIsTargetMachineFlag == True:
        resultMsg = 'Current Slider Location is Target Machine'
    else:
        if gotoMachineReuslt is True:
            layoutId = Config.Machine_Code_Dic.get(machine_id)
            if layoutId == None:
                layoutId = machine_id
            sendImageResult = CommonHelper.GetKeyboardLocation(machine_id,layoutId)
            if sendImageResult:
                resultMsg = 'Send Image Result Successful'
            else:
                resultMsg = 'Send Image Result Failed'               
        elif gotoMachineReuslt == False:
            resultMsg = 'Go To Machine Failed'

def handle_get_image_layout(machine_id):
    # 处理 GetImageLayout 消息的逻辑
    global resultMsg
    layoutId = Config.Machine_Code_Dic.get(machine_id)
    if layoutId == None:
        layoutId = machine_id
    sendImageResult = CommonHelper.GetKeyboardLocation(machine_id,layoutId)
    if sendImageResult:
        resultMsg = 'Send Image Result Successful'
    else:
        resultMsg = 'Send Image Result Failed'

def handle_save_press_keys(deviceName):
    # 处理 SavePressKeys 消息的逻辑
    global resultMsg
    Keys = recv_data.split(':')[1].split('#')[0]
    PlanId = recv_data.split('#')[1].split(',')[0]
    getKeys = Keys.split('*')
    machine_id = Config.SmartArmMachine.get(deviceName)
    for key in getKeys:     
        RoboticArm.PressKey(key,machine_id,PlanId,deviceName,pressTimes = 0,SaveLocation=True)
        resultMsg += 'Save Press Keys {} Successful'.format(key)

def handle_press_key(deviceName):
    # 处理 PressKey 消息的逻辑
    global resultMsg
    Keys = recv_data.split(':')[1].split('#')[0].split('*')
    PlanId = recv_data.split('#')[1].split(',')[0]
    fingerDisplayName = Config.SmartFingureMachine.get(deviceName)
    pressFinger = SmartFinger.PressSmartFingure(fingerDisplayName)
    if pressFinger:
        secondKey = Keys[1]
        machine_id = Config.SmartArmMachine.get(deviceName)
        if "times=" in recv_data:
            pressTimes = recv_data.split('=')[1]
            resultMsg = RoboticArm.PressKey(secondKey,machine_id,PlanId,deviceName,pressTimes)
            time.sleep(int(pressTimes))
        SmartFinger.ReleaseSmartFingure(fingerDisplayName)

if __name__ == "__main__":
    print("CSW QA Smart Arm Automation Test!")
    # 服务器绑定和监听的代码...
    server = socket.socket()
    ip = CommonHelper.GetLocalIP()
    port = 15555
    server.bind ((ip, port))
    server.listen()
    BUFFER_SIZE = 1024
    RoboticArm.GotoZero()

    while True:
        conn, addr = server.accept()
        try:
            print('Test Machine IP：', addr)
            data = conn.recv(BUFFER_SIZE)
            recv_data = str(data, encoding='utf-8').strip()
        except Exception as e:
            LoggerHelper.app_logger.info('Recv Data: {}'.format(recv_data))
            continue

        print('Recv Data: ', recv_data)
        LoggerHelper.app_logger.info('Recv Data: {}'.format(recv_data))
        if ',' in recv_data:
            deviceName = recv_data.split(',')[1].split(' ')[0]
            machine_id = Config.SmartArmMachine.get(deviceName)
        # 根据接收到的消息类型分发到相应的处理函数
        if 'ScanMachines' in recv_data:
            handle_scan_machines()
        elif 'GoToMachine' in recv_data:
            handle_goto_machine(machine_id,deviceName)
        # elif 'GetImageLayout' in recv_data:
        #     handle_get_image_layout(machine_id)
        elif 'SavePressKeys' in recv_data:
            handle_save_press_keys(deviceName)
        elif 'PressKey' in recv_data:
            handle_press_key(deviceName)
        # 这里处理结果并发送回客户端
        try:
            conn.send(resultMsg.encode('utf-8'))
            conn.close()
        except Exception as e:
            print('Socket send failed')
