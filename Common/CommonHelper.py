import socket,requests
import serial,time
import redis,json,cv2,os
import sys,os,cv2,math
import redis,uuid,base64
import pyautogui

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Config import Config
from Camera import SmartCamera
from Logger import LoggerHelper

PictureData = []
index_key_Data = []
machineIndex = ""

def GetLocalIP():
    """
    查询本机内网IP
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

def getDeviceName(comName):
    deviceName = ''
    com_list = serial.tools.list_ports.comports()
    for com in com_list:
        if comName in str(com):
            deviceName = com.device
            print('{} Com Name {}'.format(comName,deviceName))
    return deviceName

CenterKey_location = {}

def GetKeyLocationFromRedis(planId,deviceName,KeyValue):
    try:
        key = planId + ":" + deviceName + "," + str(KeyValue)
        location = CenterKey_location.get(key)
        if location != None:
            return location
        pool = redis.ConnectionPool(host='10.119.96.35',port=6379,password='',db=4)  
        r = redis.Redis(connection_pool=pool)
        data = r.get(key)
        if data == None:
            key = planId + ":" + deviceName + "," + str(KeyValue).upper()
            data = r.get(key)
        if data !=None:
            value = json.loads(data)
            CenterKey_location[key] = value
            return value
    except Exception as e:
        LoggerHelper.app_logger.error(str(e))
    return None

def GetKeyboardLocation(machine_id, keyboardCode,PlanId):
    frame = None

    SmartCamera.RestartCameraExe()
    current_directory = os.path.dirname(os.path.abspath(__file__))    
    parent_directory = os.path.dirname(current_directory)  # 获取当前目录的父目录
    target_path = 'KeyboardLayout\\{}\\Keyboard_layout_{}.jpg'.format(PlanId,str(machine_id))
    target_path = os.path.join(parent_directory,target_path)

    Config.Camera = cv2.VideoCapture(1, cv2.CAP_DSHOW)
    Config.Camera.set(3, Config.resolutionRatio_Width)
    Config.Camera.set(4, Config.resolutionRatio_Height)
    cv2.waitKey(1500)
    for i in range(0, 5): 
        ret, frame = Config.Camera.read()
        if ret == False or frame is None:
            SmartCamera.RestartCameraExe()
            Config.Camera = cv2.VideoCapture(1, cv2.CAP_DSHOW)
            Config.Camera.set(3, Config.resolutionRatio_Width)
            Config.Camera.set(4, Config.resolutionRatio_Height)
            cv2.waitKey(1500)
            ret, frame = Config.Camera.read()
            if ret == False or frame is None:
                continue
        else:
            if os.path.exists(target_path):
                os.remove(target_path)
            cv2.imwrite(target_path, frame)
            image = cv2.imread(target_path)
            if SmartCamera.is_blurry(image):
                LoggerHelper.app_logger.info("is blurry")
            else:
                LoggerHelper.app_logger.info("is clear")
                break

    data = None
    with open(target_path, "rb") as f:
        tk = f.read()
        image = base64.b64encode(tk)
        data ={"image": image.decode("utf-8")}
    try:
        jsonFileName = "KeyboardLayout\\{}\\data_{}_temp.json".format(PlanId,machine_id)
        current_directory = os.path.dirname(os.path.abspath(__file__))
        parent_directory = os.path.dirname(current_directory)
        jsonFileName = os.path.join(parent_directory,jsonFileName)

        url = "http://10.119.96.106:58083/"
        print('{} Get Keyboard Location'.format(keyboardCode))
        resp = requests.post(url+"image/segment?code={}&keyboard=1&show=1&name=keyboard&async=1".format(keyboardCode), json=data)
        print("Request url is " + str(resp))
        json_data = json.loads(resp.text)
        getLocation = url+json_data['taskid']
        print(getLocation)
        while True:
            resp = requests.get(getLocation)
            print(resp.status_code)
            if resp.status_code != 404:
                print(resp.text)
                with open(jsonFileName, 'w') as f:
                    f.write(resp.text)
                print("Finished")
                break
            print(resp.text)
            time.sleep(5)
        return True
    except:
        print('发送请求失败')
        return False
    
def ClickTaskBar():
    # 读取任务栏的屏幕截图
    try:
        screen_width, screen_height = pyautogui.size()
        screenshot = pyautogui.screenshot(region=(0, 10, screen_width, screen_height))  
        # 这里根据你的屏幕分辨率和任务栏位置进行调整
        current_directory = os.path.dirname(os.path.abspath(__file__))
        # 保存屏幕截图
        screenshot.save(os.path.join(current_directory,'taskbar_screenshot.png'))
        screenshot = cv2.imread(os.path.join(current_directory,'taskbar_screenshot.png'))
        # 读取任务栏图标的截图作为模板
        icon_template = cv2.imread( os.path.join(current_directory,'icon_template.png'))
        # 模板匹配
        result = cv2.matchTemplate(screenshot, icon_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        # 获取匹配位置
        top_left = max_loc
        bottom_right = (top_left[0] + icon_template.shape[1], top_left[1] + icon_template.shape[0])
        # 在原始截图中绘制矩形框来标记图标位置
        #cv2.rectangle(screenshot, top_left, bottom_right, (0, 255, 0), 2)
        if top_left != None and bottom_right != None:
            height = abs(bottom_right[1] - top_left[1])/2
            width = abs(bottom_right[0] - top_left[0])/2
            print((top_left[0] + width,top_left[1] + height))
            pyautogui.click(top_left[0] + width,top_left[1] + height)
            time.sleep(10)
            LoggerHelper.app_logger.info("Click taskbar succefully")
            if check_process_exists("Camera.exe"):
                os.system("c:\\windows\\System32\\taskkill /F /IM Camera.exe")
            else:
                pyautogui.leftClick(top_left[0] + width,top_left[1] + height)
                time.sleep(3)
                os.system("c:\\windows\\System32\\taskkill /F /IM Camera.exe")
            time.sleep(0.5)
            return True
    except Exception as e:
        print(str(e))
        return False
    
def check_process_exists(process_name):
    import psutil
    processes = list(psutil.process_iter())
    for process in processes:
        if process.name() == process_name:
            return True
    return False
        
def GetKeyboardData(fileIndex,PlanId):
    global PictureData
    current_directory = os.path.dirname(os.path.abspath(__file__)) 
    fileName = "KeyboardLayout\\{}\\data_{}_temp.json".format(PlanId,fileIndex)
    parent_directory = os.path.dirname(current_directory)
    fileName = os.path.join(parent_directory,fileName)
    with open(fileName,"r") as f:
        data = json.load(f)
    PictureData = data

def GetBaseArrowLocation(keyName,layoutId,PlanId):
    arrowKeys = ['UpArrow']
    if  'Arrow' in keyName:
        cr_x,cr_y,cr_w,cr_h = GetKeyLocation('CTRL_R', layoutId,PlanId)
        for key in arrowKeys:
         arrow_Location = GetKeyLocation(key, layoutId,PlanId)
         if arrow_Location  != None:
            l_x,l_y,l_w,l_h = arrow_Location
            if l_x > cr_x:
                if keyName == 'DownArrow':
                    arrow_Location = l_x, l_y + 40, cr_w, cr_h
                    return arrow_Location
                elif keyName == 'LeftArrow':
                    arrow_Location = l_x - 40, l_y + 40, cr_w, cr_h
                    return arrow_Location
                elif keyName == 'RightArrow':
                    arrow_Location = l_x + 40, l_y + 40, cr_w, cr_h
                    return arrow_Location
                
def GetKeyLocation(key_name, machine_index,PlanId):
    GetKeyboardData(machine_index,PlanId)
    layout_data = PictureData["data"]
    variations = [
        key_name,
        "[" + key_name + "]",
        str(key_name).upper(),
        str(key_name).lower(),
        "[" + str(key_name).upper() + "]",
        "[" + str(key_name).lower() + "]"
    ]

    for variation in variations:
        key_location = layout_data.get(variation, None)
        if key_location is not None:
            return key_location

    for key in key_name:
        key_location = layout_data.get(str(key).lower(), None)
        if key_location is not None:
            return key_location
    return None

# def GetAllKeysLocation():
#     GetKeyboardData(machineIndex)
#     layout_data = PictureData["data"]
#     return layout_data

def GetKeyNameRowCol(i,j,machineIndex,PlanId):
    current_directory = os.path.dirname(os.path.abspath(__file__))
    parent_directory = os.path.dirname(current_directory)
    fileName = "KeyboardLayout\\{}.json".format(machineIndex)
    fileName = os.path.join(parent_directory,fileName)
    if os.path.exists(fileName) == False:
        fileName = "KeyboardLayout\\US{}.json".format(machineIndex)
        fileName = os.path.join(parent_directory,fileName)
    with open(fileName,"r") as f:
        data = json.load(f)
    index_key_Data = data["keys"]
    col_count = len(index_key_Data[i])
    if j < col_count:
        if (index_key_Data[i][j]) == "" and index_key_Data[i][j-1] != "":
            return index_key_Data[i][j-1]
    else:
        return None
    return index_key_Data[i][j]

def get_boundary_value(machineIndex,PlanId):
    current_directory = os.path.dirname(os.path.abspath(__file__))
    parent_directory = os.path.dirname(current_directory)
    fileName = "KeyboardLayout\\{}.json".format(machineIndex)
    fileName = os.path.join(parent_directory,fileName)
    if os.path.exists(fileName) == False:
        fileName = "KeyboardLayout\\US{}.json".format(machineIndex)
        fileName = os.path.join(parent_directory,fileName)
    with open(fileName,"r") as f:
        data = json.load(f)
    index_key_Data = data["keys"]
    firstKey = index_key_Data[0][0]
    col_count = len(index_key_Data[0])
    firstRow_lastCol = index_key_Data[0][col_count-1]
    min_x = GetKeyLocation(firstKey,machineIndex,PlanId)[0]
    min_y_1 = GetKeyLocation(firstKey,machineIndex,PlanId)[1]
    max_x = GetKeyLocation(firstRow_lastCol,machineIndex,PlanId)[0]
    min_y_2 = GetKeyLocation(firstRow_lastCol,machineIndex,PlanId)[1]
    min_y = min_y_1
    if min_y < min_y_2:
        min_y = min_y_2
    return (min_x,max_x,min_y)

def GetRowColByKeyName(key_name,machineIndex,PlanId):
    current_directory = os.path.dirname(os.path.abspath(__file__))
    parent_directory = os.path.dirname(current_directory)
    fileName = "KeyboardLayout\\{}.json".format(machineIndex)
    file_name = os.path.join(parent_directory,fileName)
    if os.path.exists(file_name) == False:
        fileName = "KeyboardLayout\\US{}.json".format(machineIndex)
        fileName = os.path.join(parent_directory,fileName)
    with open(fileName,"r") as f:
        data = json.load(f)
    index_key_Data = data["keys"]
    j = 0
    i = 0
    flag = False
    for items in index_key_Data:
        for item in items:
            if len(key_name) == 1 and len(item) <= 2:
                if str(key_name).lower() in str(item).lower():
                    flag = True
                    break
            elif len(key_name) > 1 and len(item) > 1:
                if str(key_name).lower() in str(item).lower():
                    flag = True
                    break
            j = j + 1
        if flag:
            break
        i = i + 1
        j = 0
        if i >=6 :
            return None
    return (i,j)

if __name__ == '__main__':
    from RoboticArm import RoboticArm
    #RoboticArm.GotoZero()
    GetKeyboardLocation('7','7')