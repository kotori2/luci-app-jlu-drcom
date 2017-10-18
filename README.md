# luci-app-jlu-drcom
# 简介
本软件包是基于 [jlu-drcom-client](https://github.com/drcoms/jlu-drcom-client) 开发的吉大Dr.com工具的LuCI界面。方便使用OpenWrt的同学使用。
# 编译
将该项目复制到OpenWrt源码的`package`目录下，执行
``` 
make V=s package/luci-app-jlu-drcom/compile
```
即可编译出软件包。你也可以从本项目的release页面下载预编译软件包。
# 依赖
本项目的依赖项为python-light，Python内需包含`subprocess socket hashlib struct`等库。