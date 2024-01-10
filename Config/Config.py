Camera = None
SmartArm = None
AndroidDriver = None

#机器AprilTag ID 和 键盘中心点色块所在的按键位置
Machines_center = {'6':'j','7':'j','5':'k','1':'j'}
Special_Distance = {'5':-44}
#机器上粘贴二维码的距离，可以为机器AprilTag ID,Value 为 距离
machine_len = {'6':159,'7':201,'5':159,'1':200}
#智能手指Name和测试机DeviceName 的对应关系 注：区分大小写
SmartFingureMachine = {'LAPTOP-T7SDIEJE':'gaming-Y770SIN','LAPTOP-TE3RNLJ7':'gaming-770aa','LAPTOP-TUOVIH6V':'gaming-y560','LAPTOP-2ME3TH16':'gaming-L380AN'}
#机械臂识别的ID和测试机DeviceName 的对应关系 注：区分大小写
SmartArmMachine = {'LAPTOP-T7SDIEJE':'7','LAPTOP-TE3RNLJ7':'6','LAPTOP-TUOVIH6V':'5','LAPTOP-2ME3TH16':'1'}


ZERO = [235.55, 18, 130.0, 0.0]
# 摄像头的宽和高的值
resolutionRatio_Width = 1280
resolutionRatio_Height = 720
c_x = resolutionRatio_Width/2
c_y = resolutionRatio_Height/2
SliderNotLaunch = "The Slider Not Launch,Failed"
ScanMachineFinished = "Scan Machines Finished,Successful"
CurrentSlideBarDistanceFile = "C:\\CurrentSlideBarDistanceFile.txt"
SlideBarDistanceFile = "C:\\SlideBarDistanceFile.txt"
#要判断一下滑轨的移动方向
SlideTotalLength = -1650
Long_Keyboard_Flag = False
# Key:机器AprilTag ID，Value: layoutId，考虑到，不同的机器 可能存在一样的layout，
# 不添加key 和value 的对应关系 则 代表 key 和value 为一个值
Machine_Code_Dic={'5':5}
# 摄像头的宽和高的值
resolutionRatio_Width = 1280
resolutionRatio_Height = 720
machine_ratio = {}
end_left_distance = 60
end_up_distance = 40
end_high_distance = 102
#102
min_keyboard = [['Num Lock','/','*','-'],
                ['7','8','9','+'],
                ['4','5','6',''],
                ['1','2','3','Enter'],
                ['0','','.','']]
CurrentSliderIsTargetMachineFlag = False
