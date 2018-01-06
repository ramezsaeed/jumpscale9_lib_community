from js9 import j


class WinConsoleFactory:

    def get(self):
        return WinConsole()


class WinConsole:
    """
    methods to work with console on windows
    """

    def __init__(self):
        """
        """
        self.__jslocation__ = "j.tools.winconsole"
        if not j.core.platformtype.myplatform.isWindows:
            raise j.exceptions.RuntimeError("Only supported on windows.")
        self.configpath = j.sal.fs.joinPaths(j.dirs.TMPDIR, "consolecfg", str(
            j.data.idgenerator.generateRandomInt(1, 1000)) + ".xml")
        self.config = """

<?xml version="1.0"?>
<settings>
    <console change_refresh="10" refresh="100" rows="36" columns="121" buffer_rows="1000" buffer_columns="0" init_dir="" start_hidden="0" save_size="1" shell="">
        <colors>
            <color id="0" r="0" g="0" b="0"/>
            <color id="1" r="0" g="0" b="128"/>
            <color id="2" r="0" g="150" b="0"/>
            <color id="3" r="0" g="150" b="150"/>
            <color id="4" r="170" g="25" b="25"/>
            <color id="5" r="128" g="0" b="128"/>
            <color id="6" r="128" g="128" b="0"/>
            <color id="7" r="192" g="192" b="192"/>
            <color id="8" r="128" g="128" b="128"/>
            <color id="9" r="0" g="100" b="255"/>
            <color id="10" r="0" g="255" b="0"/>
            <color id="11" r="0" g="255" b="255"/>
            <color id="12" r="255" g="50" b="50"/>
            <color id="13" r="255" g="0" b="255"/>
            <color id="14" r="255" g="255" b="0"/>
            <color id="15" r="255" g="255" b="255"/>
        </colors>
    </console>
    <appearance>
        <font name="Courier New" size="10" bold="0" italic="0" smoothing="0">
            <color use="0" r="0" g="0" b="0"/>
        </font>
        <window title="Console" icon="" use_tab_icon="1" use_console_title="0" show_cmd="1" show_cmd_tabs="1" use_tab_title="1" trim_tab_titles="20" trim_tab_titles_right="0"/>
        <controls show_menu="1" show_toolbar="1" show_statusbar="1" show_tabs="1" hide_single_tab="1" show_scrollbars="1" flat_scrollbars="0" tabs_on_bottom="0"/>
        <styles caption="1" resizable="1" taskbar_button="1" border="1" inside_border="2" tray_icon="1">
            <selection_color r="255" g="255" b="255"/>
        </styles>
        <position x="-1" y="-1" dock="-1" snap="0" z_order="0" save_position="0"/>
        <transparency type="0" active_alpha="255" inactive_alpha="255" r="0" g="0" b="0"/>
    </appearance>
    <behavior>
        <copy_paste copy_on_select="1" clear_on_copy="1" no_wrap="1" trim_spaces="1" copy_newline_char="1" sensitive_copy="1"/>
        <scroll page_scroll_rows="0"/>
        <tab_highlight flashes="3" stay_highligted="1"/>
    </behavior>
    <hotkeys use_scroll_lock="1">
        <hotkey ctrl="1" shift="0" alt="0" extended="0" code="83" command="settings"/>
        <hotkey ctrl="0" shift="0" alt="0" extended="0" code="112" command="help"/>
        <hotkey ctrl="0" shift="0" alt="1" extended="0" code="115" command="exit"/>
        <hotkey ctrl="1" shift="0" alt="0" extended="0" code="112" command="newtab1"/>
        <hotkey ctrl="1" shift="0" alt="0" extended="0" code="113" command="newtab2"/>
        <hotkey ctrl="1" shift="0" alt="0" extended="0" code="114" command="newtab3"/>
        <hotkey ctrl="1" shift="0" alt="0" extended="0" code="115" command="newtab4"/>
        <hotkey ctrl="1" shift="0" alt="0" extended="0" code="116" command="newtab5"/>
        <hotkey ctrl="1" shift="0" alt="0" extended="0" code="117" command="newtab6"/>
        <hotkey ctrl="1" shift="0" alt="0" extended="0" code="118" command="newtab7"/>
        <hotkey ctrl="1" shift="0" alt="0" extended="0" code="119" command="newtab8"/>
        <hotkey ctrl="1" shift="0" alt="0" extended="0" code="120" command="newtab9"/>
        <hotkey ctrl="1" shift="0" alt="0" extended="0" code="121" command="newtab10"/>
        <hotkey ctrl="1" shift="0" alt="0" extended="0" code="49" command="switchtab1"/>
        <hotkey ctrl="1" shift="0" alt="0" extended="0" code="50" command="switchtab2"/>
        <hotkey ctrl="1" shift="0" alt="0" extended="0" code="51" command="switchtab3"/>
        <hotkey ctrl="1" shift="0" alt="0" extended="0" code="52" command="switchtab4"/>
        <hotkey ctrl="1" shift="0" alt="0" extended="0" code="53" command="switchtab5"/>
        <hotkey ctrl="1" shift="0" alt="0" extended="0" code="54" command="switchtab6"/>
        <hotkey ctrl="1" shift="0" alt="0" extended="0" code="55" command="switchtab7"/>
        <hotkey ctrl="1" shift="0" alt="0" extended="0" code="56" command="switchtab8"/>
        <hotkey ctrl="1" shift="0" alt="0" extended="0" code="57" command="switchtab9"/>
        <hotkey ctrl="1" shift="0" alt="0" extended="0" code="48" command="switchtab10"/>
        <hotkey ctrl="1" shift="0" alt="0" extended="0" code="9" command="nexttab"/>
        <hotkey ctrl="1" shift="1" alt="0" extended="0" code="9" command="prevtab"/>
        <hotkey ctrl="1" shift="0" alt="0" extended="0" code="87" command="closetab"/>
        <hotkey ctrl="1" shift="0" alt="0" extended="0" code="82" command="renametab"/>
        <hotkey ctrl="1" shift="0" alt="0" extended="0" code="67" command="copy"/>
        <hotkey ctrl="1" shift="0" alt="0" extended="1" code="46" command="clear_selection"/>
        <hotkey ctrl="1" shift="0" alt="0" extended="0" code="86" command="paste"/>
        <hotkey ctrl="0" shift="0" alt="0" extended="0" code="0" command="stopscroll"/>
        <hotkey ctrl="0" shift="0" alt="0" extended="0" code="0" command="scrollrowup"/>
        <hotkey ctrl="0" shift="0" alt="0" extended="0" code="0" command="scrollrowdown"/>
        <hotkey ctrl="0" shift="0" alt="0" extended="0" code="0" command="scrollpageup"/>
        <hotkey ctrl="0" shift="0" alt="0" extended="0" code="0" command="scrollpagedown"/>
        <hotkey ctrl="0" shift="0" alt="0" extended="0" code="0" command="scrollcolleft"/>
        <hotkey ctrl="0" shift="0" alt="0" extended="0" code="0" command="scrollcolright"/>
        <hotkey ctrl="0" shift="0" alt="0" extended="0" code="0" command="scrollpageleft"/>
        <hotkey ctrl="0" shift="0" alt="0" extended="0" code="0" command="scrollpageright"/>
        <hotkey ctrl="1" shift="1" alt="0" extended="0" code="112" command="dumpbuffer"/>
        <hotkey ctrl="0" shift="0" alt="0" extended="0" code="0" command="activate"/>
    </hotkeys>
    <mouse>
        <actions>
            <action ctrl="0" shift="0" alt="0" button="1" name="copy"/>
            <action ctrl="0" shift="0" alt="0" button="1" name="select"/>
            <action ctrl="0" shift="0" alt="0" button="3" name="paste"/>
            <action ctrl="1" shift="0" alt="0" button="1" name="drag"/>
            <action ctrl="0" shift="0" alt="0" button="2" name="menu"/>
        </actions>
    </mouse>
    <tabs>
$tabs
    </tabs>
</settings>


        """
        self.config = self.config.replace("$BASEDIR", j.dirs.JSBASEDIR)
        self.tabs = []
        self.tabCmd = []
        self.addTab("console", "", "")
        self.addTab("jshell", "", "jshell.bat")

    def writeConfig(self):
        tabs = ""
        for tab in self.tabs:
            tabs += "%s\n" % tab
        config = self.config.replace("$tabs", tabs)
        j.sal.fs.createDir(j.sal.fs.getDirName(self.configpath))
        j.sal.fs.writeFile(self.configpath, config)

    def addTab(self, name, startdir, cmd):
        if startdir == "":
            # startdir=j.dirs.JSBASEDIR
            startdir = j.sal.fs.getcwd()

        C = """
        <tab title="$name" use_default_icon="0">
            <console shell="$cmd" init_dir="$BASEDIR" run_as_user="0" user=""/>
            <cursor style="0" r="255" g="255" b="255"/>
            <background type="0" r="0" g="0" b="0">
                <image file="" relative="0" extend="0" position="0">
                    <tint opacity="0" r="0" g="0" b="0"/>
                </image>
            </background>
        </tab>"""
        C = C.replace("$name", name)
        C = C.replace("$BASEDIR", startdir)
        C = C.replace("$cmd", cmd)
        self.tabs.append(C)
        cmd2 = "%s\\%s" % (startdir, cmd)
        self.tabCmd.append([name, startdir, cmd2])

    def start(self):
        self.writeConfig()
        cwd = j.sal.fs.getcwd()
        j.sal.fs.changeDir(j.sal.fs.joinPaths(j.dirs.JSBASEDIR, "appsbin", "console"))
        cmd = "start console.exe -c \"%s\"" % self.configpath.replace("\\\\", "\\")
        for name, startdir, cmd2 in self.tabCmd:
            # startdir=startdir.replace("/","\\")
            # startdir=startdir.replace("\\\\","\\")
            cmd += " -t %s " % (name)

        # j.sal.process.execute(cmd)
        j.sal.process.executeWithoutPipe(cmd)
        j.sal.fs.changeDir(cwd)
