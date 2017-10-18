#!/usr/bin/env python
# -*- coding: utf-8 -*-
import socket, struct, time
from hashlib import md5
import sys
import os
import random
import time

# CONFIG
#load config from /etc/config/jlu-drcom
confile = open("/etc/config/jlu-drcom", "r")
conf = confile.read()
confile.close()
confs = conf.split("\n")
for i in confs:
	if i.find("mac") > 0:
		s = i.find("'")
		mac = i[s+1:s+18]
		mac = mac.split(":")
		mac = int("".join(mac), 16)
	if i.find("name") > 0:
		s = i.find("'")
		host_name = i[s+1:-1]
	if i.find("os") > 0:
		s = i.find("'")
		host_os = i[s+1:-1]
	if i.find("ip") > 0:
		s = i.find("'")
		host_ip = i[s+1:-1]
	if i.find("username") > 0:
		s = i.find("'")
		username = i[s+1:-1]
	if i.find("password") > 0:
		s = i.find("'")
		password = i[s+1:-1]
	if i.find("reconnect") > 0:
		s = i.find("'")
		reconnect = i[s+1:-1]
	
server = '10.100.61.3'
#username=''#用户名
#password=''#密码
#host_ip = ''#ip地址
#mac = 0x000000000000#mac地址
#host_name = 'Computer'#计算机名
#host_os = 'Windows 10'#操作系统
CONTROLCHECKSTATUS = '\x20'
ADAPTERNUM = '\x03'
IPDOG = '\x01'
PRIMARY_DNS = '10.10.10.10'
dhcp_server = '0.0.0.0'
AUTH_VERSION = '\x68\x00'
KEEP_ALIVE_VERSION = '\xdc\x02'
# CONFIG_END

nic_name = '' #Indicate your nic, e.g. 'eth0.2'.nic_name
bind_ip = '0.0.0.0'
#print("Waiting router to boot...")
#time.sleep(10)

class ChallengeException (Exception):
	def __init__(self):
		pass

class LoginException (Exception):
	def __init__(self):
		pass

def bind_nic():
	try:
		import fcntl
		def get_ip_address(ifname):
			s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			return socket.inet_ntoa(fcntl.ioctl(
				s.fileno(),
				0x8915,  # SIOCGIFADDR
				struct.pack('256s', ifname[:15])
			)[20:24])
		return get_ip_address(nic_name)
	except ImportError as e:
		print('Indicate nic feature need to be run under Unix based system.')
		return '0.0.0.0'
	except IOError as e:
		print(nic_name + 'is unacceptable !')
		return '0.0.0.0'
	finally:
		return '0.0.0.0'

if nic_name != '':
	bind_ip = bind_nic()

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((bind_ip, 61440))

s.settimeout(3)
SALT = ''
IS_TEST = True
# specified fields based on version
CONF = "/etc/drcom.conf"
UNLIMITED_RETRY = True
EXCEPTION = False
DEBUG = True #log saves to file
LOG_PATH = '/var/log/drcom_client.log'
if IS_TEST:
	DEBUG = True
	LOG_PATH = 'drcom_client.log'


def log(*args, **kwargs):
	s = ' '.join(args)
	print(s)
	if DEBUG:
		with open(LOG_PATH,'a') as f:
			f.write(s + '\n')

def challenge(svr,ran):
	while True:
		t = struct.pack("<H", int(ran)%(0xFFFF))
		s.sendto("\x01\x02"+t+"\x09"+"\x00"*15, (svr, 61440))
		
		data, address = s.recvfrom(1024)
		log('[challenge] recv',data.encode('hex'))
		
		
		#log('[challenge] timeout, retrying...')
		#	continue
		
		if address == (svr, 61440):
			break
		else:
			continue
	log('[DEBUG] challenge:\n' + data.encode('hex'))
	if data[0] != '\x02':
		raise ChallengeException
	log('[challenge] challenge packet sent.')
	return data[4:8]

def md5sum(s):
	m = md5()
	m.update(s)
	return m.digest()

def dump(n):
	s = '%x' % n
	if len(s) & 1:
		s = '0' + s
	return s.decode('hex')

def ror(md5, pwd):
	ret = ''
	for i in range(len(pwd)):
		x = ord(md5[i]) ^ ord(pwd[i])
		ret += chr(((x<<3)&0xFF) + (x>>5))
	return ret

def keep_alive_package_builder(number,random,tail,type=1,first=False):
	data = '\x07'+ chr(number) + '\x28\x00\x0b' + chr(type)
	if first :
		data += '\x0f\x27'
	else:
		data += KEEP_ALIVE_VERSION
	data += '\x2f\x12' + '\x00' * 6
	data += tail
	data += '\x00' * 4
	#data += struct.pack("!H",0xdc02)
	if type == 3:
		foo = ''.join([chr(int(i)) for i in host_ip.split('.')]) # host_ip
		#CRC
		# edited on 2014/5/12, filled zeros to checksum
		# crc = packet_CRC(data+foo)
		crc = '\x00' * 4
		#data += struct.pack("!I",crc) + foo + '\x00' * 8
		data += crc + foo + '\x00' * 8
	else: #packet type = 1
		data += '\x00' * 16
	return data

# def packet_CRC(s):
#	 ret = 0
#	 for i in re.findall('..', s):
#		 ret ^= struct.unpack('>h', i)[0]
#		 ret &= 0xFFFF
#	 ret = ret * 0x2c7
#	 return ret

def keep_alive2(*args):
	#first keep_alive:
	#number = number (mod 7)
	#status = 1: first packet user sended
	#		 2: first packet user recieved
	#		 3: 2nd packet user sended
	#		 4: 2nd packet user recieved
	#   Codes for test
	tail = ''
	packet = ''
	svr = server
	ran = random.randint(0,0xFFFF)
	ran += random.randint(1,10)   
	# 2014/10/15 add by latyas, maybe svr sends back a file packet
	svr_num = 0
	packet = keep_alive_package_builder(svr_num,dump(ran),'\x00'*4,1,True)
	while True:
		log('[keep-alive2]',time.strftime('[%Y-%m-%d %H:%M:%S]',time.localtime(time.time())), ' send1',packet.encode('hex'))
		s.sendto(packet, (svr, 61440))
		data, address = s.recvfrom(1024)
		log('[keep-alive2] recv1',data.encode('hex'))
		if data.startswith('\x07\x00\x28\x00') or data.startswith('\x07' + chr(svr_num)  + '\x28\x00'):
			break
		elif data[0] == '\x07' and data[2] == '\x10':
			log('[keep-alive2]',time.strftime('[%Y-%m-%d %H:%M:%S]',time.localtime(time.time())), ' recv file, resending..')
			svr_num = svr_num + 1
			packet = keep_alive_package_builder(svr_num,dump(ran),'\x00'*4,1, False)
		else:
			log('[keep-alive2]',time.strftime('[%Y-%m-%d %H:%M:%S]',time.localtime(time.time())), ' recv1/unexpected',data.encode('hex'))
	#log('[keep-alive2] recv1',data.encode('hex'))
	
	ran += random.randint(1,10)   
	packet = keep_alive_package_builder(svr_num, dump(ran),'\x00'*4,1,False)
	log('[keep-alive2]',time.strftime('[%Y-%m-%d %H:%M:%S]',time.localtime(time.time())), ' send2',packet.encode('hex'))
	s.sendto(packet, (svr, 61440))
	while True:
		data, address = s.recvfrom(1024)
		if data[0] == '\x07':
			svr_num = svr_num + 1
			break
		else:
			log('[keep-alive2]',time.strftime('[%Y-%m-%d %H:%M:%S]',time.localtime(time.time())), ' recv2/unexpected',data.encode('hex'))
	log('[keep-alive2] recv2',data.encode('hex'))
	tail = data[16:20]
	

	ran += random.randint(1,10)   
	packet = keep_alive_package_builder(svr_num,dump(ran),tail,3,False)
	log('[keep-alive2]',time.strftime('[%Y-%m-%d %H:%M:%S]',time.localtime(time.time())), ' send3',packet.encode('hex'))
	s.sendto(packet, (svr, 61440))
	while True:
		data, address = s.recvfrom(1024)
		if data[0] == '\x07':
			svr_num = svr_num + 1
			break
		else:
			log('[keep-alive2]',time.strftime('[%Y-%m-%d %H:%M:%S]',time.localtime(time.time())), ' recv3/unexpected',data.encode('hex'))
	log('[keep-alive2]',time.strftime('[%Y-%m-%d %H:%M:%S]',time.localtime(time.time())), ' recv3',data.encode('hex'))
	tail = data[16:20]
	log("[keep-alive2]",time.strftime('[%Y-%m-%d %H:%M:%S]',time.localtime(time.time())), " keep-alive2 loop was in daemon.")
	
	i = svr_num
	err_count = 0
	while True:
		try:
			ran += random.randint(1,10)   
			packet = keep_alive_package_builder(i,dump(ran),tail,1,False)
			#log('DEBUG: keep_alive2,packet 4\n',packet.encode('hex'))
			log('[keep_alive2]',time.strftime('[%Y-%m-%d %H:%M:%S]',time.localtime(time.time())), ' send',str(i),packet.encode('hex'))
			s.sendto(packet, (svr, 61440))
			data, address = s.recvfrom(1024)
			log('[keep_alive2]',time.strftime('[%Y-%m-%d %H:%M:%S]',time.localtime(time.time())), ' recv',data.encode('hex'))
			tail = data[16:20]
			#log('DEBUG: keep_alive2,packet 4 return\n',data.encode('hex'))
		
			ran += random.randint(1,10)   
			packet = keep_alive_package_builder(i+1,dump(ran),tail,3,False)
			#log('DEBUG: keep_alive2,packet 5\n',packet.encode('hex'))
			s.sendto(packet, (svr, 61440))
			log('[keep_alive2]',time.strftime('[%Y-%m-%d %H:%M:%S]',time.localtime(time.time())), ' send',str(i+1),packet.encode('hex'))
			data, address = s.recvfrom(1024)
			log('[keep_alive2]',time.strftime('[%Y-%m-%d %H:%M:%S]',time.localtime(time.time())), ' recv',data.encode('hex'))
			tail = data[16:20]
			#log('DEBUG: keep_alive2,packet 5 return\n',data.encode('hex'))
			i = (i+2) % 0xFF
			time.sleep(20)
			keep_alive1(*args)
			err_count = 0
		except:
			err_count += 1
			if err_count >= 5:
				log('[keep_alive2]', time.strftime('[%Y-%m-%d %H:%M:%S]',time.localtime(time.time())), "FATAL ERROR: CONNECTION ERROR.")
				exit()

	
import re
def checksum(s):
	ret = 1234
	for i in re.findall('....', s):
		ret ^= int(i[::-1].encode('hex'), 16)
	ret = (1968 * ret) & 0xffffffff
	return struct.pack('<I', ret)

def mkpkt(salt, usr, pwd, mac):
	data = '\x03\x01\x00'+chr(len(usr)+20)
	data += md5sum('\x03\x01'+salt+pwd)
	data += usr.ljust(36, '\x00')
	data += CONTROLCHECKSTATUS
	data += ADAPTERNUM
	data += dump(int(data[4:10].encode('hex'),16)^mac).rjust(6,'\x00') #mac xor md51
	data += md5sum("\x01" + pwd + salt + '\x00'*4) #md52
	data += '\x01' # number of ip
	#data += '\x0a\x1e\x16\x11' #your ip address1, 10.30.22.17
	data += ''.join([chr(int(i)) for i in host_ip.split('.')]) #x.x.x.x -> 
	data += '\00'*4 #your ipaddress 2
	data += '\00'*4 #your ipaddress 3
	data += '\00'*4 #your ipaddress 4
	data += md5sum(data + '\x14\x00\x07\x0b')[:8] #md53
	data += IPDOG
	data += '\x00'*4 #delimeter
	data += host_name.ljust(32, '\x00')
	data += ''.join([chr(int(i)) for i in PRIMARY_DNS.split('.')]) #primary dns
	data += ''.join([chr(int(i)) for i in dhcp_server.split('.')]) #DHCP server
	data += '\x00\x00\x00\x00' #secondary dns:0.0.0.0
	data += '\x00' * 8 #delimeter
	data += '\x94\x00\x00\x00' # unknow
	data += '\x06\x00\x00\x00' # os major
	data += '\x02\x00\x00\x00' # os minor
	data += '\xf0\x23\x00\x00' # OS build
	data += '\x02\x00\x00\x00' #os unknown
	data += '\x44\x72\x43\x4f\x4d\x00\xcf\x07\x68'
	data += '\x00' * 55#unknown string
	data += '\x33\x64\x63\x37\x39\x66\x35\x32\x31\x32\x65\x38\x31\x37\x30\x61\x63\x66\x61\x39\x65\x63\x39\x35\x66\x31\x64\x37\x34\x39\x31\x36\x35\x34\x32\x62\x65\x37\x62\x31'
	data += '\x00' * 24
	data += AUTH_VERSION
	data += '\x00' + chr(len(pwd))
	data += ror(md5sum('\x03\x01'+salt+pwd), pwd)
	data += '\x02\x0c'
	data += checksum(data+'\x01\x26\x07\x11\x00\x00'+dump(mac))
	data += '\x00\x00' #delimeter
	data += dump(mac)
	if (len(pwd) / 4) != 4:
		data += '\x00' * (len(pwd) / 4)#strange。。。
	data += '\x60\xa2' #unknown, filled numbers randomly =w=
	data += '\x00' * 28
	log('[mkpkt]',data.encode('hex'))
	return data

def login(usr, pwd, svr):
	import random
	global SALT
 
	i = 0
	while True:
		salt = challenge(svr,time.time()+random.randint(0xF,0xFF))
		SALT = salt
		packet = mkpkt(salt, usr, pwd, mac)
		log('[login] send',packet.encode('hex'))
		s.sendto(packet, (svr, 61440))
		data, address = s.recvfrom(1024)
		log('[login] recv',data.encode('hex'))
		log('[login] packet sent.')
		if address == (svr, 61440):
			if data[0] == '\x04':
				log('[login] loged in')
				break
			else:
				log('[login] login failed.')
				exit()
				if IS_TEST:
					time.sleep(3)
				else:
					time.sleep(30)
				continue
		else:
			if i >= 5 and UNLIMITED_RETRY == False :
				log('[login] exception occured.')
				sys.exit(1)
			else:
				continue
			
	log('[login] login sent')
	#0.8 changed:
	return data[23:39]
	#return data[-22:-6]

def keep_alive1(salt,tail,pwd,svr):
	foo = struct.pack('!H',int(time.time())%0xFFFF)
	data = '\xff' + md5sum('\x03\x01'+salt+pwd) + '\x00\x00\x00'
	data += tail
	data += foo + '\x00\x00\x00\x00'
	log('[keep_alive1] send',data.encode('hex'))

	s.sendto(data, (svr, 61440))
	while True:
		data, address = s.recvfrom(1024)
		print data.encode('hex')
		if data[0] == '\x07':
			break
		else:
			log('[keep-alive1]recv/not expected',data.encode('hex'))
	log('[keep-alive1] recv',data.encode('hex'))

def empty_socket_buffer():
#empty buffer for some fucking schools
	log('starting to empty socket buffer')
	try:
		while True:
			data, address = s.recvfrom(1024)
			log('recived sth unexpected',data.encode('hex'))
			if s == '':
				break
	except:
		# get exception means it has done.
		log('exception in empty_socket_buffer')
		pass
	log('emptyed')
def daemon():
	with open('/var/run/jludrcom.pid','w') as f:
		f.write(str(os.getpid()))
	
def main():
	if not IS_TEST:
		daemon()
		execfile(CONF, globals())
	log("auth svr:"+server+"\nusername:"+username+"\npassword:"+password+"\nmac:"+str(hex(mac)))
	log(bind_ip)
	while True:
		try:
			package_tail = login(username, password, server)
		except LoginException:
			continue
		log('package_tail',package_tail.encode('hex'))
		#keep_alive1 is fucking bullshit!
		empty_socket_buffer()
		keep_alive1(SALT,package_tail,password,server)
		keep_alive2(SALT,package_tail,password,server)
	
if __name__ == "__main__":
	main()
