--
-- Copyright (C) 2017 scsz <lijun00326@gmail.com>
--
-- This is free software, licensed under the GNU Affero General Public License v3.0
-- See /LICENSE for more information.
--

local m, s ,o

m = Map("jlu-drcom", translate("Dr.com"), translate("Dr.com Client for JLU"))

s = m:section(TypedSection, "general", translate("General Setting") )
s.anonymous = true

o = s:option(Value, "mac", translate("MAC adress"))
o.datatype = "macaddr"

o = s:option(Value, "name", translate("Computer name"))
o.default = "My Computer"

o = s:option(Value, "os", translate("Operating system"))
o.default = "Windows 10"

o = s:option(Value, "ip", translate("IP adress"))
o.datatype = "ipaddr"
o.placeholder = translate("The static adress used in WAN.")

o = s:option(Value, "username", translate("Username"))

o = s:option(Value, "password", translate("Password"))
o.password = true

o = s:option(Flag, "reconnect", translate("Reconnect on error"))
o.default = 1

local apply = luci.http.formvalue("cbi.apply")
if apply then
	io.popen("/etc/init.d/drcom stop")
	io.popen("/etc/init.d/drcom start")
end

s = m:section(TypedSection, "general", translate("Log"))
s.anonymous = true
o = s:option(TextValue,"log")
o.readonly = true
o.rows = 30
o.cfgvalue = function()
	return luci.sys.exec("tail -n 100 /tmp/drcom.log")
end

s = m:section(TypedSection, "general", translate("Daemon log"))
s.anonymous = true
o = s:option(TextValue,"daemon_log")
o.readonly = true
o.rows = 15
o.cfgvalue = function()
	return luci.sys.exec("tail -n 100 /tmp/drdaemon.log")
end

return m
