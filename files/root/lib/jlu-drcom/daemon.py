#coding=utf8
#
# Copyright (C) 2017 scsz <lijun00326@gmail.com>
#
# This is free software, licensed under the GNU Affero General Public License v3.0
# See /LICENSE for more information.
#

import subprocess
import time

#load config from /etc/config/jlu-drcom
confile = open("/etc/config/jlu-drcom", "r")
conf = confile.read()
confile.close()
confs = conf.split("\n")
for i in confs:
	if i.find("reconnect") > 0:
		s = i.find("'")
		reconnect = int(i[s+1:-1])
		
f = open("/tmp/drcom.log", "w")
process = subprocess.Popen(["python", "-u", "/lib/jlu-drcom/newclient.py"], stdout=f, stderr=f)
while True:
	time.sleep(5)
	print(time.strftime('[%Y-%m-%d %H:%M:%S]',time.localtime(time.time())) + "Process running...")
	if process.poll() != None:
		if reconnect:
			print(time.strftime('[%Y-%m-%d %H:%M:%S]',time.localtime(time.time())) + "Restarting process...")
			process = subprocess.Popen(["python", "-u", "/lib/jlu-drcom/newclient.py"], stdout=f, stderr=f)
		else:
			print(time.strftime('[%Y-%m-%d %H:%M:%S]',time.localtime(time.time())) + "Dr.com down! Do nothing.")
			break