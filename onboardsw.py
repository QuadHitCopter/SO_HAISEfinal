import json
import pickle

import csv
import os
import threading
import sys
import socket
import subprocess

from datetime import datetime, date
from time import sleep
from datetime import datetime

sys.path.append("/home/haise/Downloads/RPI-ADXL345")
import adxl345

from ina219 import INA219
from ina219 import DeviceRangeError
from mpu6050 import  mpu6050

#adafruit try mpu6050
import time
import board
import adafruit_mpu6050


IP_GS = '192.168.0.16'

#obtener directorio
path_now = os.path.realpath(os.path.dirname(__file__))

#CREACIÓN DE ARCHIVO DE REGISTRO

tm_dic_BASE = { #Keys para generar archivo de registro
							"time": datetime.now(), #tiempo de toma de datos
							"last_com":None, #ultimo comando recibido
							"last_com_date": None, #Fecha ultimo comando recibido
							"v5":0, # linea de 5 volts
							"i5":0, #corriente en 5 volts
							"p5":0, #potencia en 5 volts
							"v3":0, #linea de 3.3 volts
							"i3":0, #corriente en 3.3 volts
							"p3":0, #potencia en 3.3V
							"bat":0,# voltaje de batería
							"sun":0, # voltaje de LDR
							"acce_1_x":0,
							"acce_1_y":0,
							"acce_1_z":0,
							"acce_2_x":0,
							"acce_2_y":0,
							"acce_2_z":0,
							"gyro_X":0,
							"gyro_Y":0,
							"gyro_Z":0,
							"temp":0
							}
now = datetime.now()
current_time = now.strftime("%d_M%m_%Y-%H_m%M") #obtener fecha y hora
#crear nombre de archivo para registros
TM_file_new = path_now + f'/TM{current_time}.csv'

with open(TM_file_new, 'w', newline='') as f: # crea archivo
    writer = csv.writer(f)
    writer.writerow(tm_dic_BASE.keys())

def register_file_update(tm_dic): #actualiza el archivo
	with open(TM_file_new, 'a', newline='') as f2:
		writer2 = csv.writer(f2)
		writer2.writerow(tm_dic.values())    
#############################################	

class TELEMETRY():
	def __init__(self):
		self.TM_recorded = None

TM_RCRD = TELEMETRY()

class HAISE_state():
	def __init__(self,end_check_com,last_com, take_pic,linked):
		self.endCheck= end_check_com
		self.last_com = last_com
		self.v5line = 0
		self.i5line = 0
		self.p5line = 0
		self.v3line = 0
		self.i3line = 0
		self.p3line = 0
		self.batline = 0
		self.sunline = 0
		self.acce1x = 0
		self.acce1y = 0
		self.acce1z = 0
		self.acce2x = 0
		self.acce2y = 0
		self.acce2z = 0
		self.gyro_X = 0
		self.gyro_Y = 0
		self.gyro_Z = 0
		self.temp = 0


		self.TAKE_PIC = take_pic
		self.LINKED = linked
		self.ALIVE_FLAG=True
		self.ALIVE_SAT = True
		self.SEND_TM = False
		self.SEARCHING = True
		self.GS_FOUND = False

HS = HAISE_state("init",{
							"command":"init",
							"rec_date":"now"
							},
							take_pic=False,
							linked = False
							)
def clear():
		#os.system("clear")
		#print("\n\n\n")
		pass

def com_ss():
	global HS
	#socket telecomandos
	while True and HS.ALIVE_FLAG:
		if HS.GS_FOUND:
			try:
				bb = False
				attemps = 0
				while True:
					try:
						s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
						#print("a")
						s.connect((IP_GS, 4000))
						try:
							sleep(0.1)
							s.settimeout(1.0)
							receive = s.recv(1024)
							s.settimeout(None)
							print("Enlace establecido \n")
							HS.LINKED=True
							bb = True
							break
						except Exception as e:
							s.close()

							HS.LINKED = False
							receive = False
							if str(e) == "[Errno 104] Connection reset by peer":
								HS.GS_FOUND = False
								HS.SEARCHING = True
								break

							pass
					except:
						attemps +=1
						sleep(0.1)
						print(f"Attempting connection ... {attemps}")
						if attemps > 10:
							HS.GS_FOUND = False
							HS.SEARCHING = True
							break



				com_t = 0
				while receive and com_t!="end" and bb:
					clear()
					try:
						receive = s.recv(1024)
					except Exception as e:
						HS.GS_FOUND = False
						HS.SEARCHING = True
						print("Estación terrestre perdida")
						break
					time = str(datetime.now())[0:-4]
					com_t = receive.decode() # Recibir telecomando
					HS.endCheck = com_t
					if com_t != "end":
							com_dic= {
									"command":com_t,
									"rec_date":time
									}
							com_json = json.dumps(com_dic,indent = 1)
							with open("coms.json","w") as updating:
									updating.write(com_json)
							HS.last_com=com_dic
							print(HS.last_com)
							if com_t =="TAKE_PIC":
								HS.TAKE_PIC=True
							elif com_t == "KILL_OS":
								HS.ALIVE_FLAG = False
								print(HS.ALIVE_FLAG)
								print("KILL")
								break
							elif com_t == "KILL_SAT":
								HS.ALIVE_FLAG = False
								HS.ALIVE_SAT = False
								break
							elif com_t == "GET_TM":
								HS.SEND_TM = True

					else:
						print("Enlace cerrado")
						HS.LINKED = False
						s.close()
					sleep(0.1)
				s.close()
				if com_t == "end":
					s.close()
				HS.LINKED= False
				sleep(1)
			except Exception as e:
				#print(e)
				pass
		sleep(0.1)

def telemetry_update():
	global TM_RCRD,HS
	while True and HS.ALIVE_FLAG:

		tm_dic = {
								"time": datetime.now().strftime("%d-%m-%Y %H:%M:%S.%f")[0:-3], #tiempo de toma de datos now.strftime("%d_M%m_%Y-%H_m%M")
								"last_com":HS.last_com["command"], #ultimo comando recibido
								"last_com_date": HS.last_com["rec_date"],
								"v5":HS.v5line, # linea de 5 volts
								"i5":HS.i5line, #corriente 5V
								"p5":HS.p5line, #potencia en 5V
								"v3":HS.v3line, #linea de 3.3 volts
								"i3":HS.i3line, #corriente 3.3V
								"p3":HS.p3line, #potencia en 3.3V
								"bat":HS.batline,# voltaje de batería
								"sun":HS.sunline, # voltaje de LDR
								# aceleraciones y velocidades angular de acce1=adxl345, acce2= mpu6050
								"acce_1_x":HS.acce1x, 
								"acce_1_y":HS.acce1y,
								"acce_1_z":HS.acce1z,
								"acce_2_x":HS.acce2x,
								"acce_2_y":HS.acce2y,
								"acce_2_z":HS.acce2z,
								"gyro_X":HS.gyro_X,
								"gyro_Y":HS.gyro_Y,
								"gyro_Z":HS.gyro_Z,
								"temp":HS.temp
								}
		TM_RCRD.TM_recorded = tm_dic
		register_file_update(tm_dic)
		sleep(0.2)

def TM_channel():
	global HS
	while True and HS.ALIVE_FLAG:
		if HS.GS_FOUND:
			try:
				cc = True
				attemps = 0
				if HS.LINKED:
					#socket telemetría
					s2 = socket.socket(socket.AF_INET,
					  	socket.SOCK_STREAM)
					while cc and attemps < 20:
						try:
							s2.connect((IP_GS, 4500))
							cc = False
						except:
							attemps +=1
							pass
					while   not cc and HS.ALIVE_FLAG:
						if not HS.LINKED:
							break
						tm_data = TM_RCRD.TM_recorded

						coded_tm = pickle.dumps(tm_data)
						s2.send(coded_tm) #Enviar telemetría
						sleep(0.05)
					s2.close()
				sleep(0.2)
			except Exception as e:
				#print(e)
				pass

def measure_ADXL345():
	global HS
	#Lectura del ADXL345
	accelerometer = adxl345.ADXL345(i2c_port=1, address=0x53)
	accelerometer.load_calib_value()
	accelerometer.set_data_rate(data_rate=adxl345.DataRate.R_100)
	accelerometer.set_range(g_range=adxl345.Range.G_16, full_res=True)
	accelerometer.measure_start()
	sensor = mpu6050(0x68) # Lecutra del  MPU6050

	i2c = board.I2C()
	mpu = adafruit_mpu6050.MPU6050(i2c)

	while True and HS.ALIVE_FLAG:
		x, y, z = accelerometer.get_3_axis_adjusted()
		x2, y2, z2 = mpu.acceleration
		gx , gy, gz = mpu.gyro
		temp2 = mpu.temperature

		HS.acce1x = str(x)[0:-13]
		HS.acce1y = str(y)[0:-13]
		HS.acce1z = str(z)[0:-13]

		accel_data = sensor.get_accel_data(g=True)
		gyro_data = sensor.get_gyro_data()
		temp = sensor.get_temp()
		#libreria mpu6050
		#HS.acce2x = str(accel_data['x'])[0:-9]
		#HS.acce2y = str(accel_data['y'])[0:-9]
		#HS.acce2z = str(accel_data['z'])[0:-9]
		#HS.gyro_X = str(gyro_data['x'])[0:-13]
		#HS.gyro_Y = str(gyro_data['y'])[0:-13]
		#HS.gyro_Z = str(gyro_data['z'])[0:-13]
		HS.temp = str(temp)[0:-13]
		#libreria adafruit de su mpu6050
		HS.acce2x = str(x2/9.807)[0:-9]
		HS.acce2y = str(y2/9.807)[0:-9]
		HS.acce2z = str(z2/9.807)[0:-9]
		HS.gyro_X = str(gx)[0:-13]
		HS.gyro_Y = str(gy)[0:-13]
		HS.gyro_Z = str(gz)[0:-13]
		#HS.temp = str(temp2)[0:-13]


		sleep(0.1)


def measure_Power():
	global HS
	# identificadores
	# ad5v = 0x45
	# adbat = 0x40
	# ad_3v = 0x44
	# ad_sol = 0x41
	def read(ina):
		b_v = ina.voltage()
		try:
				b_c = ina.current()
				b_p = ina.power()
		except DeviceRangeError as e:
				print(e)
		return b_v, b_c, b_p
	SHUNT_OHMS = 0.1
	max_AMP = 1.0
	ad5v = 0x40
	adbat = 0x41
	ad_3v = 0x45
	ad_sol = 0x44
	ina_5v = INA219(SHUNT_OHMS,max_AMP,address=ad5v)
	ina_5v.configure(ina_5v.RANGE_16V)
	ina_bat = INA219(SHUNT_OHMS,max_AMP,address=adbat)
	ina_bat.configure(ina_bat.RANGE_16V)
	ina_3v = INA219(SHUNT_OHMS,max_AMP,address=ad_3v)
	ina_3v.configure(ina_3v.RANGE_16V)
	ina_sol = INA219(SHUNT_OHMS,max_AMP,address=ad_sol)
	ina_sol.configure(ina_bat.RANGE_16V)
	while True and HS.ALIVE_FLAG:
		V5_line = read(ina_5v)
		bat_line =read(ina_bat)
		v3_line =read(ina_3v)
		sol_line = read(ina_sol)

		HS.v5line = V5_line[0]
		HS.i5line = str(V5_line[1])[0:-11]
		HS.p5line = str(V5_line[2])[0:-11]
		HS.batline = bat_line[0]
		bat_i = str(bat_line[1])[0:-11]
		bat_p = str(bat_line[2])[0:-11]
		HS.v3line = v3_line[0]
		HS.i3line = str(v3_line[1])[0:-11]
		HS.p3line = str(v3_line[2])[0:-11]
		HS.sunline = sol_line[0]
		if bat_line[0]< 3.2:
			HS.ALIVE_FLAG = False
			HS.ALIVE_SAT = False
		sleep(0.1)
	pass

#socket imagenes
def take_pic():
	global HS
	while True and HS.ALIVE_FLAG:
		if HS.GS_FOUND:
			try:
				while HS.endCheck!="end" and HS.LINKED and HS.ALIVE_FLAG:
					if HS.TAKE_PIC:
						subprocess.run(["raspistill","-rot","270","-o","image.jpg","-w","1920","-h","1080"])
						s3 = socket.socket(socket.AF_INET,
								socket.SOCK_STREAM)
						dd = True
						attemps = 0
						while dd and attemps < 20:
							try:
								s3.connect((IP_GS, 3000))

								dd = False
							except:
								attemps +=1
								#print(attemps)
								pass
						#im = open("c:/Users/Robocop/Desktop/HAISE/imagen.jpg","rb")
						im = open("image.jpg","rb")

						for i in im:
							s3.send(i)

						HS.TAKE_PIC=False
						#print("image sent")
						sleep(0.5)
						s3.close()
				sleep(1)
			except Exception as e:
				#print(e)
				pass
		sleep(0.1)

# Enviar toda la telemetría registrada desde que se encendió el satelite.
def send_all_TM():
	global HS
	while True and HS.ALIVE_FLAG:
		if HS.GS_FOUND:
			try:
				cc = True
				attemps = 0
				if HS.SEND_TM and HS.LINKED:
					#socket telemetría
					s_tm = socket.socket(socket.AF_INET,
					  	socket.SOCK_STREAM)
					while cc and attemps < 20:
						try:
							s_tm.connect((IP_GS,7000))
							cc=False
						except Exception as e:
							attemps +=1
							#print (e)
							if attemps>20:
								HS.SEND_TM = False
					with open(TM_file_new, "r") as f:
						reader = csv.reader(f)
						for i, line in enumerate(reader):
							s_tm.send(pickle.dumps(line))
					s_tm.close()
					HS.SEND_TM = False
			except Exception as e:
				#print(e)
				pass
			sleep(1)
		sleep(0.1)





def try_something():
	global IP_GS, addr
	while True and HS.ALIVE_FLAG:
		if HS.SEARCHING:
			try:
				print("Buscando estación terresre")
				socket_GS = socket.socket(socket.AF_INET,
								socket.SOCK_STREAM)
				socket_GS.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
				print(1)
				socket_GS.bind(('', 8200))
				
				print(2)
				socket_GS.listen(1)
				print(3)
				d, addr = socket_GS.accept()
				print(4)
				IP_GS = addr[0]
				telem_1 = d.recv(2048)
				socket_GS.close()
				HS.SEARCHING = False
				HS.GS_FOUND = True
				print("Estación terrestre encontrada")
			except Exception as e:
				print("Error try_something", e)
				socket_GS.close()
				pass

		sleep(1)



if __name__== "__main__":
	#Threads para multiprocesos
	t_coms = threading.Thread(target=com_ss)
	t_coms.daemon = True

	t_tm_up = threading.Thread(target=telemetry_update)
	t_tm_up.daemon = True

	t_tm_send = threading.Thread(target=TM_channel)
	t_tm_send.daemon = True

	t_camera = threading.Thread(target=take_pic)
	t_camera.daemon = True

	t_all_TM = threading.Thread(target=send_all_TM)
	t_all_TM.daemon = True

	t_power = threading.Thread(target=measure_Power)
	t_power.daemon = True
	t_ADXL = threading.Thread(target=measure_ADXL345)
	t_ADXL.daemon = True
	t_searching = threading.Thread(target = try_something)
	t_searching.daemon = True

	t_searching.start()
	sleep(0.2)

	t_coms.start()
	sleep(0.2)
	t_tm_up.start()
	t_tm_send.start()
	t_camera.start()
	t_all_TM.start()
	t_power.start()
	t_ADXL.start()

	t_searching.join()
	sleep(0.2)

	t_coms.join()
	sleep(0.2)
	t_tm_up.join()
	t_tm_send.join()
	t_camera.join()
	t_all_TM.join()
	t_power.join()
	t_ADXL.join()
	if not HS.ALIVE_SAT:
		print("Power Off")
		sleep(5)
		os.system("sudo shutdown now")
	sys.exit()


