import adxl345
import time
import os
def clear():
	os.system("clear")

accelerometer = adxl345.ADXL345(i2c_port=1, address=0x53)
accelerometer.load_calib_value()
accelerometer.set_data_rate(data_rate=adxl345.DataRate.R_100)
accelerometer.set_range(g_range=adxl345.Range.G_16, full_res=True)
accelerometer.measure_start()

accelerometer.calibrate()	# Calibrate only one time

n = 0
while(True) and n<5:
    clear()
    n = n+0.25
    x, y, z = accelerometer.get_3_axis_adjusted()
    print('x: ', x, 'y: ', y, 'z: ', z,"\n")#
    print('pitch: ',"\n", accelerometer.get_pitch())
    #print('roll: ',"\n", accelerometer.get_roll())
    #print('yaw: ',"\n", accelerometer.get_yaw())


    time.sleep(0.25)
