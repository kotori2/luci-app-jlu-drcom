--
-- Copyright (C) 2017 scsz <lijun00326@gmail.com>
--
-- This is free software, licensed under the GNU Affero General Public License v3.0
-- See /LICENSE for more information.
--

module("luci.controller.jlu-drcom", package.seeall)

function index()
    if not nixio.fs.access("/etc/config/jlu-drcom") then
        return
    end
    entry({"admin","services","jlu-drcom"}, cbi("jlu-drcom"), _("Dr.com"), 60)
end
