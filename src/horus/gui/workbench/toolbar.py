# -*- coding: utf-8 -*-
# This file is part of the Horus Project

__author__ = 'Jesús Arroyo Torrens <jesus.arroyo@bq.com>'
__copyright__ = 'Copyright (C) 2014-2016 Mundo Reader S.L.'
__license__ = 'GNU General Public License v2 http://www.gnu.org/licenses/gpl2.html'

import wx._core

from horus.util import resources

from horus.gui.engine import driver
from horus.engine.driver.board import WrongFirmware, BoardNotConnected
from horus.engine.driver.camera import WrongCamera, CameraNotConnected, InvalidVideo


class Toolbar(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        # Element
        self.toolbar = wx.ToolBar(self)
        self.toolbar.SetDoubleBuffered(True)
        self.toolbar_scan = wx.ToolBar(self)
        self.toolbar_scan.SetDoubleBuffered(True)
        self.combo = wx.ComboBox(self, -1, style=wx.CB_READONLY)

        # Layout
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.toolbar, 0, wx.ALL | wx.EXPAND, 1)
        hbox.Add(self.toolbar_scan, 0, wx.ALL | wx.EXPAND, 1)
        hbox.Add((0, 0), 1, wx.ALL | wx.EXPAND, 1)
        hbox.Add(self.combo, 0, wx.ALL, 10)
        self.SetSizer(hbox)
        self.Layout()


class ToolbarConnection(Toolbar):

    def __init__(
            self, parent, on_connect_callback=None, on_disconnect_callback=None):

        Toolbar.__init__(self, parent)

        self.on_connect_callback = on_connect_callback
        self.on_disconnect_callback = on_disconnect_callback

        # Elements
        self.connect_tool = self.toolbar.AddLabelTool(
            wx.NewId(), _("Connect"),
            wx.Bitmap(resources.get_path_for_image("connect.png")), shortHelp=_("Connect"))
        self.disconnect_tool = self.toolbar.AddLabelTool(
            wx.NewId(), _("Disconnect"),
            wx.Bitmap(resources.get_path_for_image("disconnect.png")), shortHelp=_("Disconnect"))
        self.toolbar.Realize()

        self._enable_tool(self.connect_tool, True)
        self._enable_tool(self.disconnect_tool, False)

        # Events
        self.Bind(wx.EVT_TOOL, self.on_connect_tool_clicked, self.connect_tool)
        self.Bind(wx.EVT_TOOL, self.on_disconnect_tool_clicked, self.disconnect_tool)

    def on_connect_tool_clicked(self, event):
        driver.set_callbacks(lambda: wx.CallAfter(self.before_connect),
                             lambda r: wx.CallAfter(self.after_connect, r))
        driver.connect()

    def on_disconnect_tool_clicked(self, event):
        driver.disconnect()
        self.update_status(driver.is_connected)

    def before_connect(self):
        self._enable_tool(self.connect_tool, False)
        self.GetParent().enable_gui(False)
        driver.board.set_unplug_callback(None)
        driver.camera.set_unplug_callback(None)
        self.wait_cursor = wx.BusyCursor()

    def after_connect(self, response):
        ret, result = response
        if not ret:
            if isinstance(result, WrongFirmware):
                self._show_message(_(result), wx.ICON_INFORMATION,
                                   _("Board has a wrong firmware or an invalid Baud Rate.\n"
                                     "Please select your Board and press Upload Firmware"))
                self.update_status(False)
                self.GetParent().on_preferences(None)
            elif isinstance(result, BoardNotConnected):
                self._show_message(_(result), wx.ICON_INFORMATION,
                                   _("Board is not connected.\n"
                                     "Please connect your board and select a valid Serial Name"))
                self.update_status(False)
                self.GetParent().on_preferences(None)
            elif isinstance(result, WrongCamera):
                self._show_message(_(result), wx.ICON_INFORMATION,
                                   _("You probably have selected a wrong camera.\n"
                                     "Please select other Camera Id"))
                self.update_status(False)
                self.GetParent().on_preferences(None)
            elif isinstance(result, CameraNotConnected):
                self._show_message(_(result), wx.ICON_ERROR,
                                   _("Please plug your camera and try to connect again"))
            elif isinstance(result, InvalidVideo):
                self._show_message(_(result), wx.ICON_ERROR,
                                   _("Unplug and plug your camera USB cable "
                                     "and try to connect again"))

        self.update_status(driver.is_connected)
        self.GetParent().enable_gui(True)
        del self.wait_cursor

    def update_status(self, status):
        self._enable_tool(self.connect_tool, not status)
        self._enable_tool(self.disconnect_tool, status)
        if status:
            if self.on_connect_callback is not None:
                self.on_connect_callback()
            callback = self.GetParent().on_board_unplugged
            driver.board.set_unplug_callback(lambda: wx.CallAfter(callback))
            callback = self.GetParent().on_camera_unplugged
            driver.camera.set_unplug_callback(lambda: wx.CallAfter(callback))
        else:
            if self.on_disconnect_callback is not None:
                self.on_disconnect_callback()
            driver.board.set_unplug_callback(None)
            driver.camera.set_unplug_callback(None)

    def _show_message(self, title, style, desc):
        dlg = wx.MessageDialog(self, desc, title, wx.OK | style)
        dlg.ShowModal()
        dlg.Destroy()

    def _enable_tool(self, item, enable):
        self.toolbar.EnableTool(item.GetId(), enable)

    def scanning_mode(self, enable):
        if enable:
            self.toolbar_scan.Show()
        else:
            self.toolbar_scan.Hide()
