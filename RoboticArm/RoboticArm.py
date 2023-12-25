import time,sys,os
import serial,json,redis,math
from pymycobot.ultraArm import ultraArm

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Config import Config
from Common import CommonHelper
from Camera import SmartCamera
from RangeSensor import RangeSensor
from Logger import LoggerHelper

RoboticArmComName = 'USB-SERIAL CH340'

def ResetToZero():
    if Config.SmartArm == None: 
        Config.SmartArm = ultraArm(CommonHelper.getDeviceName(RoboticArmComName), 115200)
    currentLocation = Config.SmartArm.get_coords_info()
    print(currentLocation)
    print(Config.ZERO)
    if currentLocation == Config.ZERO:
        return
    Config.SmartArm.set_coords(Config.ZERO, 40)
    time.sleep(0.5)

def GotoZero():
    try:
        if Config.SmartArm == None:
            Config.SmartArm = ultraArm(CommonHelper.getDeviceName(RoboticArmComName), 115200)
        Config.SmartArm.go_zero()
        Config.SmartArm.set_coords(Config.ZERO)
        time.sleep(1)
    except Exception as e:
        LoggerHelper.app_logger.error('GotoZero() Exception: ' + str(e))
        

def SetRobotForCutLongKey():
    target_x = 0
    target_y = 0
    global move_down_distance
    if Config.SmartArm == None:
        Config.SmartArm = ultraArm(CommonHelper.getDeviceName(RoboticArmComName), 115200)
    time.sleep(1.5)

    haveMoveLeft = 0
    haveMoveRight = 0

    min_x = 900
    max_x = 910
    min_y = 10
    max_y = 30
    if Config.Long_Keyboard_Flag == True:
        min_x = 850
        max_x = 870

    print('Set Green Y Location: ')
    for i in range(0, 25):
        result = SmartCamera.GetColorLocation('Green')
        x, y, w, h = result
        if x <= min_x:
            target_x = 3
            haveMoveLeft = haveMoveLeft + 1
            if haveMoveRight > 2:
                break
        elif x > max_x:
            target_x = -3
            haveMoveRight = haveMoveRight + 1
            if haveMoveLeft > 2:
                break
        else:
            target_x = 0
            break
        coords = Config.SmartArm.get_coords_info()
        move_location = [coords[0], coords[1]-target_x, coords[2], coords[3]]
        Config.SmartArm.set_coords(move_location)
        time.sleep(1.5)

    print('Set Green X Location: ')
    preTargetY = 0
    for i in range(0, 15):
        result = SmartCamera.GetColorLocation('Green')
        x, y, w, h = result
        if y < 20:
            break
        if y < min_y:
            target_y = -3
        elif y > max_y:
            target_y = 3
        else:
            target_y = 0
            break
        if preTargetY != 0 and preTargetY != target_y:
            break
        else:
            preTargetY = target_y
        coords = Config.SmartArm.get_coords_info()
        move_location = [coords[0]-target_y, coords[1], coords[2], coords[3]]
        Config.SmartArm.set_coords(move_location)
        time.sleep(1.5)

def PressKey(keyName,machine_id,PlanId,deviceName,pressTimes,SaveLocation = False):
    global resultMsg
    coords = Config.SmartArm.get_coords_info()
    layoutId = Config.Machine_Code_Dic.get(machine_id)
    center_Key = Config.Machines_center.get(machine_id)
    center_Key_location = CommonHelper.GetKeyLocationFromRedis(PlanId,deviceName,center_Key)
    if layoutId == None:
        layoutId = machine_id
    min_key_location = None
    long_keyboard_flag = False
    if int(machine_id) >= 90:
        min_key_location = SmartCamera.GetColorLocation('Yellow')
        Config.Long_Keyboard_Flag = True

    upArrow = 'UpArrow'
    upArrow_location = None
    if keyName == 'DownArrow':
         upArrow_location = CommonHelper.GetKeyLocationFromRedis(PlanId,deviceName,upArrow)
    target_Key_location = CommonHelper.GetKeyLocationFromRedis(PlanId,deviceName,keyName)
    
    if target_Key_location == None and upArrow_location != None:
        target_Key_location = [upArrow_location[0]-15,upArrow_location[1],upArrow_location[2]]
    if target_Key_location != None:
        moveCoords_key = [target_Key_location[0],target_Key_location[1],float(target_Key_location[2]) + 10]
        if SaveLocation == False:
            for i in range(0,int(pressTimes)):
                Config.SmartArm.set_coords(moveCoords_key,50)
                Config.SmartArm.set_coords(target_Key_location,50)
                time.sleep(0.05)
                moveCoords_key = [target_Key_location[0],target_Key_location[1],float(target_Key_location[2]) + 10]
                Config.SmartArm.set_coords(moveCoords_key,50)
                time.sleep(0.5)
            #Config.SmartArm.set_coords(ZERO, 40)
        resultMsg = 'Press {} Successful'.format(keyName)    
        print(resultMsg)
        return 'Press {} Successful'.format(keyName)
   
    ratio = Config.machine_ratio.get(machine_id)
    if  ratio is None:
        allAprilTag = SmartCamera.GetAllAprilTag(2)
        left_tag = SmartCamera.GetAprilTagBydTagId(allAprilTag, 586)
        right_tag = SmartCamera.GetAprilTagBydTagId(allAprilTag, machine_id)
        machine_AprilTag_Len = Config.machine_len.get(machine_id)
        ratio = abs((left_tag.center[0]-right_tag.center[0])/machine_AprilTag_Len)
        Config.machine_ratio[machine_id] = ratio
        
    if center_Key_location is None:
        print('PressKey {} center_Key_location is None'.format(center_Key))
        LoggerHelper.app_logger.debug('PressKey {} center_Key_location is None'.format(center_Key))
        (Green_MaxX, Green_MaxY, Green_MaxW,Green_MaxH) = SmartCamera.GetColorLocation('Green')
        green_key_cx = Green_MaxX + Green_MaxW/2
        green_key_cy = Green_MaxY - Green_MaxH/2
        posx = (green_key_cx - Config.c_x) / ratio
        posy = (green_key_cy - Config.c_y) / ratio
        print("key_cx = {}, key_cy = {}".format(green_key_cx, green_key_cy))
        if coords:
            green_moveX = coords[0] - posy
            green_moveY = coords[1] + posx
        before_distance = RangeSensor.GetCurrentDistance()
        print('Machine id {}, Before move distance {}'.format(machine_id ,before_distance))
        press_move_down = 130 - (before_distance - Config.end_high_distance)
        before_move_down = press_move_down + 16
        Config.SmartArm.set_coords([green_moveX-Config.end_up_distance,green_moveY-Config.end_left_distance, before_move_down], 60)
        time.sleep(1.5)
        SetRobotForCutLongKey()
        time.sleep(1.5)
        
        coords = Config.SmartArm.get_coords_info()
        green_moveX = coords[0]
        green_moveY = coords[1]
        press_key_distance = RangeSensor.GetCurrentDistance()
        print('Press key distance {}'.format(press_key_distance))

        down_green_moveZ = press_move_down - 8
        center_press_moveCoords_key = [green_moveX, green_moveY, down_green_moveZ]
        print('Press key {} , Location {}'.format(center_Key,center_press_moveCoords_key))
        center_Key_x, center_Key_y, center_Key_w, center_Key_h = Green_MaxX, Green_MaxY, Green_MaxW, Green_MaxH
        #Config.SmartArm.set_coords(center_press_moveCoords_key, 40)
    else:
        center_press_moveCoords_key = [center_Key_location[0], center_Key_location[1], center_Key_location[2]]
        (Green_MaxX, Green_MaxY, Green_MaxW,Green_MaxH) = SmartCamera.GetColorLocation('Green')
        center_Key_x, center_Key_y, center_Key_w, center_Key_h = Green_MaxX, Green_MaxY, Green_MaxW, Green_MaxH
        green_moveX = center_Key_location[0]
        green_moveY = center_Key_location[1]
        green_key_cx = Green_MaxX + Green_MaxW/2
        green_key_cy = Green_MaxY - Green_MaxH/2
        down_green_moveZ = center_Key_location[2]
        before_move_down = down_green_moveZ + 20

    time.sleep(0.5)
 
    #Space 有时 图形获取的有问题，故用B 去代替，然后减去 B 和 centerKey的 y 值差即为B到space的距离
    preKeyName = keyName
    insteadOfSpace:bool = False
    if keyName == 'Space':
        keyName = 'B'
        insteadOfSpace = True
    
    if 'DownArrow' in keyName:
        arrowLocation = CommonHelper.GetBaseArrowLocation(keyName,machine_id,PlanId)
        key_location_in_pic = arrowLocation
    elif 'UpArrow' in keyName:
        key_x, key_y, key_w, key_h = CommonHelper.GetKeyLocation(keyName, machine_id,PlanId)
        if key_h > 60 :
            key_h = 40
        key_location_in_pic = key_x, key_y, key_w, key_h
    else:
        key_location_in_pic = CommonHelper.GetKeyLocation(keyName, machine_id,PlanId)

    key_x, key_y, key_w, key_h = key_location_in_pic
    center_Key_i, center_Key_j = CommonHelper.GetRowColByKeyName(center_Key, layoutId,PlanId)
    target_Key_i = 0
    target_Key_j = 0
    target_key_row_col =  CommonHelper.GetRowColByKeyName(keyName, layoutId,PlanId)
    if target_key_row_col != None:
        target_Key_i = target_key_row_col[0]
        target_Key_j = target_key_row_col[1]

    same_row_key_name = CommonHelper.GetKeyNameRowCol(target_Key_i, center_Key_j, layoutId,PlanId)
    same_row_result = CommonHelper.GetKeyLocation(same_row_key_name, machine_id,PlanId)
 
    print("################# Press Step #######################")
    if key_location_in_pic != None:
        key_log = "The Key is {}, Location is : {} ".format(keyName, key_location_in_pic)
        print(key_log)
        LoggerHelper.app_logger.info(key_log)
        center_key_log = "The center Key is {}".format((green_key_cx, green_key_cy))
        print(center_key_log)
        LoggerHelper.app_logger.info(center_key_log)
    else:
        return
    setOffset = True
    move_h = 0
    if setOffset:
        offset_x = (key_x - center_Key_x) / ratio
        # pc
        #offset_x = ((key_x) - (center_Key_x)) / ratio + move_w/2 / ratio
        if target_Key_j > center_Key_j + 1:
            offset_x = offset_x + key_w/3/ratio       
        if key_h != center_Key_h:
            move_h = key_h - center_Key_h
        offset_y = (key_y - center_Key_y) / ratio + move_h/2 / ratio
    else:
        offset_x = 0
        offset_y = 0

    min_x,max_x,min_y = CommonHelper.get_boundary_value(machine_id,PlanId)
   
    offset_moveX = green_moveX - offset_y # 控制机械臂上下移动
    min_moveX = green_moveX - (key_y - min_y) / ratio + move_h/2 / ratio

    if offset_moveX < min_moveX:
        LoggerHelper.app_logger.error('reach the limit {} ，min {}'.format(offset_moveX,min_moveX))
        from RoboticArm import RoboticArm
        RoboticArm.GotoZero()
        return 'Press {} Failed'.format(keyName)
    
    offset_moveY = round(green_moveY + offset_x,2) # 控制机械臂左右移动
    min_moveY = green_moveY + (min_x - center_Key_x) / ratio
    max_moveY = green_moveY + (max_x - center_Key_x) / ratio
    if offset_moveY > max_moveY or offset_moveY < min_moveY:
        LoggerHelper.app_logger.error('reach the limit {} ， Max {}, Min {}'.format(offset_moveY,max_moveY,min_moveY))
        from RoboticArm import RoboticArm
        RoboticArm.GotoZero()
        return 'Press {} Failed'.format(keyName)

    compensate_x = (key_x - same_row_result[0])/200 * 3
    offset_moveX = round(offset_moveX - compensate_x,2)
    if target_Key_i == 5 and target_Key_j < 4:
        offset_moveY = offset_moveY - 5
    if target_Key_j < center_Key_j:
        offset_moveY = offset_moveY + 5
        
    if insteadOfSpace:
        offset_xindex = abs(offset_moveX - green_moveX)
        offset_moveX = offset_moveX - abs(offset_xindex)

    moveCoords_key = [offset_moveX, offset_moveY, before_move_down]
    result = math.sqrt(offset_moveX**2+offset_moveY**2+down_green_moveZ**2)
    if result > 340 :#机械臂臂长最大值，达到限位
        offset_moveY = offset_moveY + 3
        offset_moveX = offset_moveX - 3
        moveCoords_key = [offset_moveX, offset_moveY, before_move_down]
    if offset_moveX < 186 :
        offset_moveX = 186.5
        if offset_moveY > 20:
            offset_moveX = 184
        moveCoords_key = [offset_moveX, offset_moveY, before_move_down]

    press_moveCoords_key = [offset_moveX, offset_moveY, down_green_moveZ]
    pressDistance = Config.Special_Distance.get(machine_id)
    if pressDistance != None:
       press_moveCoords_key = [offset_moveX, offset_moveY, pressDistance]
    
    if SaveLocation == False:
        for i in range(0,int(pressTimes)):
            if target_Key_i > 3:
                Config.SmartArm.set_coords(moveCoords_key)
            else:
                Config.SmartArm.set_coords(moveCoords_key,75)
            print("The Target Key is {}, Target Move : {} ".format(keyName, moveCoords_key))
            LoggerHelper.app_logger.info("The Target Key is {}, Target Move : {} ".format(keyName, moveCoords_key))
            time.sleep(0.5)
            print('The Target Key click location is {} '.format(press_moveCoords_key))
            LoggerHelper.app_logger.info('The Target Key click location is {} '.format(press_moveCoords_key))
            Config.SmartArm.set_coords(press_moveCoords_key)
            time.sleep(0.1)
            Config.SmartArm.set_coords(moveCoords_key)
        if target_Key_location == None:
            pool = redis.ConnectionPool(host='10.119.96.35',port=6379,password='',db=4)  
            r = redis.Redis(connection_pool=pool)
            setCenterValue = PlanId+":"+deviceName+","+center_Key

            json_data = json.dumps(center_press_moveCoords_key)
            r.set(setCenterValue, json_data)
            if insteadOfSpace:
                setTargetKeyValue = PlanId + ":" + deviceName + "," + preKeyName
            else:
                setTargetKeyValue = PlanId + ":" + deviceName + "," + keyName
            json_data = json.dumps(press_moveCoords_key)
            r.set(setTargetKeyValue, json_data)
            r.close()
    else:
        pool = redis.ConnectionPool(host='10.119.96.35',port=6379,password='',db=4)  
        r = redis.Redis(connection_pool=pool)
        setCenterValue = PlanId+":"+deviceName+","+center_Key
        json_data = json.dumps(center_press_moveCoords_key)
        r.set(setCenterValue, json_data)
        if insteadOfSpace:
            setTargetKeyValue = PlanId+":"+deviceName+",Space"
        else:
            setTargetKeyValue = PlanId+":"+deviceName+","+keyName
        json_data = json.dumps(press_moveCoords_key)
        r.set(setTargetKeyValue, json_data)
        r.close()
    #Config.SmartArm.set_coords(Config.ZERO, 40)
    return 'Press {} Successful'.format(keyName)

if __name__=="__main__":
    ResetToZero()
    SetRobotForCutLongKey()