#
# Copyright (C) 2017 scsz <lijun00326@gmail.com>
#
# This is free software, licensed under the GNU Affero General Public License v3.0
# See /LICENSE for more information.
#

include $(TOPDIR)/rules.mk

PKG_NAME:=luci-app-jlu-drcom
PKG_VERSION:=0.1.0
PKG_RELEASE:=0

PKG_LICENSE:=AGPLv3
PKG_LICENSE_FILES:=LICENSE
PKG_MAINTAINER:=scsz

PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_NAME)

include $(INCLUDE_DIR)/package.mk

define Package/$(PKG_NAME)
	SECTION:=luci
	CATEGORY:=LuCI
	SUBMENU:=3. Applications
	TITLE:=LuCI Support for jlu drcom
	PKGARCH:=all
	DEPENDS:=+python-light
endef

define Package/$(PKG_NAME)/description
	LuCI Support for jlu-drcom.
endef

define Build/Prepare
	$(foreach po,$(wildcard ${CURDIR}/files/luci/i18n/*.po), \
		po2lmo $(po) $(PKG_BUILD_DIR)/$(patsubst %.po,%.lmo,$(notdir $(po)));)
endef

define Package/$(PKG_NAME)/conffiles
/etc/config/jlu-drcom
endef

define Build/Configure
endef

define Build/Compile
endef

define Package/$(PKG_NAME)/postinst
#!/bin/sh
chmod 755 /etc/init.d/drcom
exit 0
endef

define Package/$(PKG_NAME)/install
	$(INSTALL_DIR) $(1)/usr/lib/lua/luci/controller
	$(INSTALL_DATA) ./files/luci/controller/jlu-drcom.lua $(1)/usr/lib/lua/luci/controller/
	$(INSTALL_DIR) $(1)/usr/lib/lua/luci/i18n
	$(INSTALL_DATA) $(PKG_BUILD_DIR)/jlu-drcom.*.lmo $(1)/usr/lib/lua/luci/i18n/
	$(INSTALL_DIR) $(1)/usr/lib/lua/luci/model/cbi
	$(INSTALL_DATA) ./files/luci/model/cbi/jlu-drcom.lua $(1)/usr/lib/lua/luci/model/cbi/
	$(INSTALL_DIR) $(1)/etc/init.d
	$(INSTALL_DATA) ./files/root/etc/init.d/drcom $(1)/etc/init.d/
	$(INSTALL_DIR) $(1)/lib/jlu-drcom
	$(INSTALL_DATA) ./files/root/lib/jlu-drcom/newclient.py $(1)/lib/jlu-drcom
	$(INSTALL_DATA) ./files/root/lib/jlu-drcom/daemon.py $(1)/lib/jlu-drcom
endef

$(eval $(call BuildPackage,$(PKG_NAME)))
