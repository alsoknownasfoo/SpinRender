"""
SpinRender Dependency Check Dialog (Bootstrap Version)
Uses only standard wxPython controls to avoid dependencies on PyYAML/Theme.
"""
import wx
import threading
import logging

logger = logging.getLogger("SpinRender")

class DependencyCheckDialog(wx.Dialog):
    """
    Standard wxPython dialog for dependency checking and installation.
    Used during bootstrap when PyYAML might be missing.
    """

    def __init__(self, parent, dep_status, checker):
        super().__init__(
            parent,
            title="SpinRender - Setup Required",
            size=(500, 600),
            style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP
        )

        self.dep_status = dep_status
        self.checker = checker
        
        # UI state
        self.current_dep_index = 0
        self.num_deps = 0
        
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer, self.timer)

        self.build_ui()
        self.Centre()

    def build_ui(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Header
        header_txt = wx.StaticText(self, label="Setup Required")
        header_font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        header_font.SetPointSize(14)
        header_font.SetWeight(wx.FONTWEIGHT_BOLD)
        header_txt.SetFont(header_font)
        main_sizer.Add(header_txt, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 20)

        # Message
        msg = wx.StaticText(self, label="SpinRender requires the following dependencies to function:")
        main_sizer.Add(msg, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 20)

        # Dependency List
        list_panel = wx.Panel(self)
        list_sizer = wx.BoxSizer(wx.VERTICAL)
        
        for dep_name, is_found in self.dep_status.items():
            row = wx.Panel(list_panel)
            row_sizer = wx.BoxSizer(wx.HORIZONTAL)
            
            lbl = wx.StaticText(row, label=dep_name)
            status_txt = "OK" if is_found else "MISSING"
            status_color = wx.Colour(0, 150, 0) if is_found else wx.Colour(200, 0, 0)
            
            status_lbl = wx.StaticText(row, label=status_txt)
            status_lbl.SetForegroundColour(status_color)
            
            row_sizer.Add(lbl, 1, wx.ALIGN_CENTER_VERTICAL)
            row_sizer.Add(status_lbl, 0, wx.ALIGN_CENTER_VERTICAL)
            row.SetSizer(row_sizer)
            
            list_sizer.Add(row, 0, wx.EXPAND | wx.BOTTOM, 10)
            
        list_panel.SetSizer(list_sizer)
        main_sizer.Add(list_panel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 30)

        main_sizer.AddSpacer(20)

        # Progress Area
        self.progress_panel = wx.Panel(self)
        self.progress_panel.Hide()
        progress_sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.progress_gauge = wx.Gauge(self.progress_panel, range=100, size=(-1, 15))
        progress_sizer.Add(self.progress_gauge, 0, wx.EXPAND | wx.BOTTOM, 5)
        
        self.progress_status = wx.StaticText(self.progress_panel, label="Initializing...")
        progress_sizer.Add(self.progress_status, 0, wx.EXPAND | wx.BOTTOM, 5)
        
        self.progress_log = wx.TextCtrl(
            self.progress_panel, 
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL
        )
        progress_sizer.Add(self.progress_log, 1, wx.EXPAND)
        
        self.progress_panel.SetSizer(progress_sizer)
        main_sizer.Add(self.progress_panel, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 30)

        # Footer
        footer_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.close_btn = wx.Button(self, label="Exit", id=wx.ID_CANCEL)
        self.install_btn = wx.Button(self, label="Install Dependencies", id=wx.ID_OK)
        self.install_btn.SetDefault()
        
        footer_sizer.Add(self.close_btn, 0, wx.RIGHT, 10)
        footer_sizer.Add(self.install_btn, 0)
        
        main_sizer.Add(footer_sizer, 0, wx.ALL | wx.ALIGN_RIGHT, 20)

        self.SetSizer(main_sizer)
        
        self.install_btn.Bind(wx.EVT_BUTTON, self.on_install)
        self.close_btn.Bind(wx.EVT_BUTTON, self.on_close)

    def on_timer(self, event):
        val = self.progress_gauge.GetValue()
        limit = (self.current_dep_index * 100) + 95
        if val < limit:
            self.progress_gauge.SetValue(val + 1)

    def on_close(self, event):
        self.EndModal(wx.ID_CANCEL)

    def on_install(self, event):
        if not self.checker.missing_deps:
            self.EndModal(wx.ID_OK)
            return

        self.install_btn.Enable(False)
        self.close_btn.Enable(False)
        
        self.progress_panel.Show()
        self.progress_log.Clear()
        self.Layout()

        self.num_deps = len(self.checker.missing_deps)
        self.progress_gauge.SetRange(self.num_deps * 100)
        self.progress_gauge.SetValue(0)
        
        self.timer.Start(100)

        thread = threading.Thread(target=self._run_install_thread)
        thread.daemon = True
        thread.start()

    def _run_install_thread(self):
        num_deps = len(self.checker.missing_deps)
        for i, dep_name in enumerate(self.checker.missing_deps):
            self.current_dep_index = i
            is_last = (i == num_deps - 1)
            wx.CallAfter(self.progress_status.SetLabel, f"Installing {dep_name}...")
            
            def log_callback(message):
                wx.CallAfter(self._append_log, message)
                if is_last and "Successfully installed" in message:
                    wx.CallAfter(self.progress_gauge.SetValue, num_deps * 100)
                    wx.CallAfter(self.progress_status.SetLabel, "Installation complete.")

            self.checker.install_dependency(dep_name, callback=log_callback)
            wx.CallAfter(self.progress_gauge.SetValue, (i + 1) * 100)

        wx.CallAfter(self._on_install_finished)

    def _append_log(self, message):
        self.progress_log.AppendText(message + "\n")
        self.progress_log.ShowPosition(self.progress_log.GetLastPosition())

    def _on_install_finished(self):
        self.timer.Stop()
        self.progress_gauge.SetValue(self.num_deps * 100)
        
        self.dep_status = self.checker.check_all()
        if not self.checker.missing_deps:
            self.EndModal(wx.ID_OK)
        else:
            self.install_btn.Enable(True)
            self.close_btn.Enable(True)
            self.progress_status.SetLabel("Some installations failed.")
            self.Layout()
