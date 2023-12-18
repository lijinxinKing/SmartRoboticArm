import sys
import time
import cv2
import numpy as np
import sys,os,cv2,math
import redis,uuid,base64

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Config import Config
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from appium.webdriver.common.touch_action import TouchAction
from selenium.webdriver.common.by import By
from appium.options.common import AppiumOptions
from Logger import LoggerHelper

option = AppiumOptions()

desired_caps = {
    'platformName': 'Android',
    'platformVersion': '8.1.0',
    'deviceName': 'HLTE700T',
    'appPackage': 'com.tuya.smartiot',
    'appActivity': 'com.smart.ThingSplashActivity',
    'skipServerInstallation': False,
    'skipDeviceInitialization': True,
    'dontStopAppOnReset': True,
    'noReset': True
}

option.set_capability('platformName','android')
option.set_capability('platformVersion','8.1.0')
option.set_capability('deviceName','HLTE700T')
option.set_capability('appPackage','com.tuya.smartiot')
option.set_capability('appActivity','com.smart.ThingSplashActivity')
option.set_capability('skipServerInstallation',False)
option.set_capability('skipDeviceInitialization',True)
option.set_capability('dontStopAppOnReset',True)
option.set_capability('noReset',True)
option.set_capability('newCommandTimeout',100)

app_started = False
color_threshold = 500

def startApp():
    try:
        if Config.AndroidDriver == None:
            Config.AndroidDriver = webdriver.Remote('http://127.0.0.1:4724/wd/hub',desired_capabilities=desired_caps)
            Config.AndroidDriver.implicitly_wait(5)
        if 'appContext' in Config.AndroidDriver.session:
            Config.AndroidDriver.execute_script('mobile: activateApp', {'bundleId': Config.AndroidDriver.session['appContext']})
        else:
            Config.AndroidDriver.session['appContext'] = Config.AndroidDriver.current_package
        print('Start Android App Succeed')
    except Exception as e:
        print('Start Android App Failed')
        time.sleep(1)
    
def closeAPP():
    try:
        if Config.AndroidDriver != None:
            Config.AndroidDriver.quit()
            Config.AndroidDriver = None
        else:
            pass
    except:
        print('Quit Android App Failed')

def ClickBegin(arg):
    global color_threshold
    if "Press" in arg:
        arg_parts = arg.split(" ")
        arg1 = arg_parts[1].strip()
        try:
            text_element = Config.AndroidDriver.find_element(By.XPATH, f"//*[@text='{arg1}']/..")
            target_button = text_element.find_element(By.ID, 'com.tuya.smartiot:id/switchButton')
            button_location = target_button.location
            button_size = target_button.size
            screenshot_path = r"smartFingure_screenshot.png"
            Config.AndroidDriver.get_screenshot_as_file(screenshot_path)
            screenshot = cv2.imread(screenshot_path)
            button_x, button_y = button_location['x'], button_location['y']
            button_width, button_height = button_size['width'], button_size['height']
            button_area = screenshot[button_y:button_y + button_height, button_x:button_x + button_width]
            average_color_per_row = np.average(button_area, axis=0)
            average_color = np.average(average_color_per_row, axis=0)  
            if(sum(average_color) > color_threshold): #已经按下
                TouchAction(Config.AndroidDriver).tap(target_button).perform()
                time.sleep(1)
            print('Smart Finger Run Succeed ！')
            return True
        except:
            print('Smart Finger Run Failed！')
            return False

def PressSmartFingure(fingureName):
    if Config.AndroidDriver != None:
        closeAPP()
    startApp()
    global color_threshold
    color_threshold = 600
    if ClickBegin("Press "+fingureName) == False:
        return False
    closeAPP()
    return True

def ReleaseSmartFingure(fingureName):
    startApp()
    global color_threshold
    color_threshold = 500
    if ClickBegin("Press "+fingureName) == False:
        return False
    closeAPP()
    return True

if __name__ == '__main__':
    PressSmartFingure("gaming-Y770SIN")#区分大小写
    ReleaseSmartFingure("gaming-Y770SIN")#区分大小写