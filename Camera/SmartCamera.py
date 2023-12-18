
import cv2
import pupil_apriltags as apriltag
import numpy as np
import os,sys
import subprocess
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Config import Config
from Logger import LoggerHelper
# Define color thresholds
color_thresholds = {
    'red': (np.array([0, 43, 46]), np.array([10, 255, 255])),
    'blue': (np.array([100, 43, 46]), np.array([124, 255, 255])),
    'green': (np.array([35, 43, 46]), np.array([77, 255, 255])),
    'yellow': (np.array([26, 43, 46]), np.array([34, 255, 255])),
    'purple': (np.array([125, 43, 46]), np.array([155, 255, 255]))
}

lower_red = np.array([0, 43, 46])  # 红色低阈值
upper_red = np.array([10, 255, 255])  # 红色高阈值

lower_blue = np.array([100, 43, 46])  # 蓝色低阈值
upper_blue = np.array([124, 255, 255])  # 蓝色高阈值

lower_green = np.array([35, 43, 46])
upper_green = np.array([77, 255, 255])

lower_yellow = np.array([26, 43, 46])
upper_yellow = np.array([34, 255, 255])

ZERO = [235.55, 18, 130.0, 0.0]
#紫色
lower_purple = np.array([125, 43, 46])
upper_purple = np.array([155, 255, 255])

ZERO = [235.55, 18, 130.0, 0.0]
resultMsg = ""
getAllTags = []
getMachineAprilTag = []

def RestartCameraExe():
    from Common import CommonHelper
    result = CommonHelper.ClickTaskBar()
    if result == False:
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        print(desktop_path)
        exe_path = desktop_path + "\\" + "Camera.exe"
        subprocess.Popen(exe_path)
        time.sleep(3)
        os.system("c:\\windows\\System32\\taskkill /F /IM Camera.exe")
        time.sleep(3)
    # desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    # exe_path = desktop_path + "\\" + "Camera.exe"
    # if os.path.exists(exe_path) == False:
    #     current_directory = os.path.dirname(os.path.abspath(__file__))
    #     parent_directory = os.path.dirname(current_directory)
    #     exe_path = os.path.join(parent_directory, "Camera.exe")
    # subprocess.Popen(exe_path)
    # time.sleep(3)
    # os.system("c:\\windows\\System32\\taskkill /F /IM Camera.exe")
    # time.sleep(3)

def get_camera_frame():
    initialize_camera()
    ret, frame = Config.Camera.read()
    if not ret:
        RestartCameraExe()
        return None
    return frame
   
def initialize_camera():
    if Config.Camera is None:
        Config.Camera = cv2.VideoCapture(1, cv2.CAP_DSHOW)
        Config.Camera.set(3, Config.resolutionRatio_Width)
        Config.Camera.set(4, Config.resolutionRatio_Height)
        cv2.waitKey(1500)

def capture_frame(retries=5):
    frame = None
    initialize_camera()
    for i in range(retries):
        ret, frame = Config.Camera.read()
        if ret:
            break
        else:
            Config.Camera = cv2.VideoCapture(1, cv2.CAP_DSHOW)
            cv2.waitKey(1500)
    return frame

def save_image(frame, file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
    cv2.imwrite(file_path, frame)

def GetColorLocation(color_type):
    font = cv2.FONT_HERSHEY_SIMPLEX
    #if Config.Camera is None:
    Config.Camera = cv2.VideoCapture(1, cv2.CAP_DSHOW)
    Config.Camera.set(3, Config.resolutionRatio_Width)
    Config.Camera.set(4, Config.resolutionRatio_Height)
    ret, frame = Config.Camera.read()  # 读取一帧
    if ret == False:
        RestartCameraExe()
    else:
        ret, frame = Config.Camera.read()
        if ret == False:
            RestartCameraExe()
            Config.Camera = cv2.VideoCapture(1, cv2.CAP_DSHOW)
            ret, frame = Config.Camera.read()  # 读取一帧
            if ret:
                return False
    Config.Camera.set(3, Config.resolutionRatio_Width)
    Config.Camera.set(4, Config.resolutionRatio_Height)
    while ret == False:
        cv2.waitKey(500)
        Config.Camera = cv2.VideoCapture(1, cv2.CAP_DSHOW)

        Config.Camera.set(3, Config.resolutionRatio_Width)
        Config.Camera.set(4, Config.resolutionRatio_Height)
        ret, frame = Config.Camera.read()  # 读取一帧
        if ret == False:
            RestartCameraExe()

    y = int(frame.shape[0] / 2)
    x = int(frame.shape[1] / 2)
    point_size = 1
    point_color = (0, 0, 255)  # BGR
    thickness = 2
    lower_color = None
    upper_color = None
    # 画点
    match str(color_type).lower():
        case 'yellow':
            lower_color = lower_yellow
            upper_color = upper_yellow
            pass
        case 'green':
            lower_color = lower_green
            upper_color = upper_green
            pass
        case 'red':
            lower_color = lower_red
            upper_color = upper_red
            pass
        case 'blue':
            lower_color = lower_blue
            upper_color = upper_blue
            pass
        case 'purple':
            lower_color = lower_purple
            upper_color = upper_purple
            pass
    point = (x, y)  # 点的坐标。画点实际上就是画半径很小的实心圆。
    cv2.circle(frame, point, point_size, point_color, thickness)
    hsv_img = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)  # 根据颜色范围删选
    mask_ = cv2.inRange(hsv_img, lower_color, upper_color)
    mask_ = cv2.medianBlur(mask_, 7)
    contours3, hierarchy3 = cv2.findContours(
        mask_, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    MaxBox = 0
    MaxX = 0
    MaxY = 0
    MaxW = 0
    MaxH = 0
    for cnt3 in contours3:
        (x3, y3, w3, h3) = cv2.boundingRect(cnt3)
        currentBox = w3 * h3
        if currentBox > MaxBox:
            MaxBox = currentBox
            MaxX = x3
            MaxY = y3
            MaxW = w3
            MaxH = h3
            setStr = "["+str(x3)+" "+str(y3)+" "+" "+str(w3)+" "+str(h3) + "]"
            cv2.putText(frame, setStr, (x3-w3, y3 + h3),
                        font, 0.3, (255, 255, 0), 1)
            now_f = "KeyboardLayout\\{}\\{}.jpg".format(color_type,time.strftime("%Y-%m-%d-%H_%M_%S",time.localtime(time.time())))                
            if os.path.exists(now_f):
                os.remove(now_f)
            cv2.imwrite(now_f,frame) #保存图片

    result = (MaxX, MaxY, MaxW, MaxH)
    print('\'{}\' color location {}'.format(color_type,result))
    return result

def GetAprilTagBydTagId(allAprilTag: [], tag_id):
    for tag in allAprilTag:
        if str(tag.tag_id) == str(tag_id):
            return tag
        
def GetMachineAprilTag():
    i = 0
    if Config.Camera == None:
        Config.Camera = cv2.VideoCapture(1,cv2.CAP_DSHOW)
        Config.Camera.set(3,Config.resolutionRatio_Width)
        Config.Camera.set(4,Config.resolutionRatio_Height)
   
    flag = Config.Camera.isOpened()
    if flag == False:
        Config.Camera = cv2.VideoCapture(1,cv2.CAP_DSHOW)
        Config.Camera.set(3,Config.resolutionRatio_Width)
        Config.Camera.set(4,Config.resolutionRatio_Height)
    getAllTags = []
    while i < 10:
        try:
            cv2.waitKey(200)
            ret, frame = Config.Camera.read()
            if ret == False:
                Config.Camera = cv2.VideoCapture(1,cv2.CAP_DSHOW)
                Config.Camera.set(3,Config.resolutionRatio_Width) #设置分辨率
                Config.Camera.set(4,Config.resolutionRatio_Height)
                ret, frame = Config.Camera.read()
                cv2.waitKey(200)
            if ret:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                at_detector = apriltag.Detector(families='tag36h11') # 创建一个apriltag检测器
                tags = at_detector.detect(gray)
                if len(tags) > 0:
                    for tag in tags:
                        if tag.tag_id != 586:
                             getAllTags.append(tag)
                else:
                    time.sleep(0.5)
                if len(getAllTags) > 0:
                    Config.Camera.release()
                    break
            else:
                RestartCameraExe()
            i = i + 1
        except:
            print("Error")
    Config.Camera.release()
    if len(getAllTags) > 0:
        print(getAllTags[0].center)
        pass
    return getAllTags
 
def GetAllAprilTag(tagCount):
    checkTinmes:int = 5000
    maxLen = -1
    allAprilTags = []
    getAllAprilTag = {}
    returnFlag = False
    f = "GetAprilTag.png"
    cap = cv2.VideoCapture(1,cv2.CAP_DSHOW)
    cap.set(3,Config.resolutionRatio_Width) #设置分辨率
    cap.set(4,Config.resolutionRatio_Height)
    flag = cap.isOpened()
    from RangeSensor import RangeSensor
    currentDistance = RangeSensor.GetCurrentDistance()
    from RoboticArm import RoboticArm
    if currentDistance < 200:
        RoboticArm.ResetToZero()
        cap = cv2.VideoCapture(1,cv2.CAP_DSHOW)
        cap.set(3,Config.resolutionRatio_Width) #设置分辨率
        cap.set(4,Config.resolutionRatio_Height)
        cv2.waitKey(1000)
    while flag and checkTinmes >0:
        ret, frame = cap.read()
        img = frame
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # 创建一个apriltag检测器
        at_detector = None       
        try:
            at_detector = apriltag.Detector(families='tag36h11')
        except Exception as e:
            print(e)
            continue
        # at_detector = apriltag.Detector(families='tag36h11 tag25h9')  #for windows
        # 进行apriltag检测，得到检测到的apriltag的列表
        tags = at_detector.detect(gray)
        print("%d apriltags have been detected."%len(tags))
        if len(tags) >= maxLen:
            maxLen = len(tags)
            allAprilTags = []
            getAllAprilTag = {}
            for tag in tags:            
                cv2.circle(img, tuple(tag.corners[0].astype(int)), 4,(255,0,0), 1) # left-top
                cv2.circle(img, tuple(tag.corners[1].astype(int)), 4,(255,0,0), 1) # right-top
                cv2.circle(img, tuple(tag.corners[2].astype(int)), 4,(255,0,0), 1) # right-bottom
                cv2.circle(img, tuple(tag.corners[3].astype(int)), 4,(255,0,0), 1) # left-bottom
                a = (tuple(tag.corners[3].astype(int))[0], tuple(tag.corners[3].astype(int))[1])
                cv2.putText(img, str(tag.tag_id)+",["+str(round(tag.center[0]))+","+str(round(tag.center[1]))+"]", (a[0]-100, a[1]- 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                if getAllAprilTag.get(tag.tag_id) == None:
                    getAllAprilTag[tag.tag_id] = tag
                    allAprilTags.append(tag)
                    if len(allAprilTags) == tagCount:
                        returnFlag = True
                        break
            if os.path.exists(f):
                os.remove(f)
            cv2.imwrite(f,img) #保存图片
        checkTinmes = checkTinmes - 1
        #cv2.imshow("apriltag_test",img)
        if returnFlag == True:    # Esc key to stop
          break
        elif checkTinmes % 10 == 0:
            RestartCameraExe()
    return allAprilTags
    
def GetAprilTagByTagId(tagId):
    i = 0
    cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
    flag = cap.isOpened()
    getAllTags = []
    while i < 10:
        ret, frame = cap.read()       
        if ret:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            at_detector = apriltag.Detector(families='tag36h11') 
            tags = at_detector.detect(gray)
            if len(tags) > 0:
                for tag in tags:
                    print(tag.tag_id)
                    if tag.tag_id == tagId:
                        print(tag)
                        x = tag.corners[0][0]
                        y = tag.corners[0][1]
                        w = abs(tag.corners[0][0] - tag.corners[2][0])
                        h = abs(tag.corners[0][1] - tag.corners[1][1])
                        ratio = (float(w+h)/2)/9
                        return (x,y,w,h,ratio)
                        getAllTags.append(tag)
            else:
                time.sleep(0.1)
            if len(getAllTags) >= 1:
                cap.release()
                break
            elif len(getAllTags) == 0:
                cap.release()
                RestartCameraExe()
                time.sleep(1)
                cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
                time.sleep(1)
        i = i + 1
    cap.release()
    return None

def GetAprilTagCenterByTagId(tagId):
    i = 0
    cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
    flag = cap.isOpened()
    getAllTags = []
    while i < 10:
        ret, frame = cap.read()       
        if ret:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # 创建一个apriltag检测器
            at_detector = apriltag.Detector(families='tag36h11') 
            tags = at_detector.detect(gray)
            if len(tags) > 0:
                for tag in tags:
                    getAllTags.append(tag)
                    print(tag.tag_id)
                    if tag.tag_id == tagId:
                        return (tag.center)
            else:
                time.sleep(0.1)
            if len(getAllTags) >= 1:
                cap.release()
                break
            elif len(getAllTags) == 0:
                cap.release()
                RestartCameraExe()
                time.sleep(1)
                cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
                time.sleep(1)
        i = i + 1
    cap.release()
    return None

def GetCalibration():
    i = 0
    if Config.Camera == None:
        Config.Camera = cv2.VideoCapture(1, cv2.CAP_DSHOW)
    while i < 10:
        ret, frame = Config.Camera.read()
        if ret:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            at_detector = apriltag.Detector(families='tag36h11') # 创建一个apriltag检测器
            tags = at_detector.detect(gray)
            if len(tags) > 1:
                for tag in tags:
                    if tag.tag_id != 0:
                        getAllTags.append(tag)
            else:
                time.sleep(0.1)
            if len(getAllTags) >= 2:
                #cap.release()
                break
            elif len(getAllTags) == 0:
                Config.Camera.release()
                RestartCameraExe()
                Config.Camera = cv2.VideoCapture(1, cv2.CAP_DSHOW)
                time.sleep(1)
        else:
            Config.Camera = cv2.VideoCapture(1, cv2.CAP_DSHOW)
            ret, frame = Config.Camera.read()
        i = i + 1
    return getAllTags

if __name__=="__main__":
    GetColorLocation('Green')