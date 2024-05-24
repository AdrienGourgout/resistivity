"""
View.py holds the code for a gui for MultiPyVu.Server

@author: djackson
"""


import sys
import io
from enum import IntEnum, auto
import logging
import tkinter as tk
from tkinter import font
from PIL import ImageTk, Image

from .__version import __version__ as mpv_version
from .project_vars import SERVER_NAME
from .IView import IView
from .IController import IController


class TextWidgetHandler(logging.Handler):
    def __init__(self, text_widget: tk.Text):
        '''
        Configure a handler for info messages to the std.out
        '''
        super().__init__()
        self.text_widget = text_widget
        self.log_name = 'TkinterGui'
        self.formatter = logging.Formatter('%(asctime)s - %(message)s',
                            '%m-%d %H:%M')
        self.setFormatter(self.formatter)
        self.set_name(self.log_name)
        self.logger = logging.getLogger(SERVER_NAME)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(self)

    def emit(self, record):
        msg = self.format(record)
        self.text_widget.config(state='normal')
        self.text_widget.insert("end", msg + "\n")
        self.text_widget.see("end")  # Auto-scroll to the end
        self.text_widget.config(state='disabled')

    def stop(self):
        '''
        Remove the handler.
        '''
        self.close()
        self.logger.removeHandler(self)


class StdoutRedirector(io.TextIOBase):
    '''
    This is used to redirect stdout to the gui
    '''
    def __init__(self, text_widget: tk.Text):
        self.text_widget = text_widget
        # Redirect sys.stdout to the custom redirector
        sys.stdout = self

    def write(self, string):
        '''
        Overwrite the io.TextIOBase.write command to go to the text_widget
        '''
        self.text_widget.config(state='normal')
        self.text_widget.insert("end", string)
        self.text_widget.see("end")  # Auto-scroll to the end
        self.text_widget.config(state='disabled')
        return len(string)

    def stop(self):
        sys.stdout = sys.__stdout__


class RedirectOutputToGui():
    def __init__(self, text_widget: tk.Text):
        '''
        Redirect stdio and INFO logging handlers to the gui

        Parameters:
        -----------
        text_widget: tkinter.Text
            The text widget target
        '''
        self.stdio = StdoutRedirector(text_widget)
        self.handler = TextWidgetHandler(text_widget)

    def stop(self):
        '''
        Stop redirecting output to the gui
        '''
        self.stdio.stop()
        self.handler.stop()


class ViewTk(IView):
    TK_RUNNING = False
    pad = 7
    _border_width_main_frames = 3
    _thin_border = 1

    class start_button_text(IntEnum):
        start = auto()
        idle = auto()
        stop = auto()
    start_button_enum = start_button_text

    def __init__(self, controller: IController):
        self._controller = controller

        self.gui = tk.Tk()
        self.gui.title(f'MultiPyVu Server {mpv_version}')
        self.gui.protocol("WM_DELETE_WINDOW", self.quit_gui)

        # this gets instantiated when the server starts
        self.redirector = None

    def create_display(self):
        '''
        Create the Server window
        '''
        # add the QD font
        font_location = self._controller.absolute_path('font/Play-Regular.ttf')
        # qd_font_large = font.Font(family=font_location, size=30)
        qd_font_small = font.Font(family=font_location, size=15)
        qd_font_status = font.Font(family=font_location, size=12)

        # create the header
        frm_header = tk.Frame(
            master=self.gui,
            background='white',
            border=self._border_width_main_frames,
            relief=tk.RAISED,
            padx=10,
            pady=self.pad,
            )
        file_image = Image.open(self._controller.absolute_path('images/QD_logo.jpg'))
        logo_img = ImageTk.PhotoImage(file_image)
        panel = tk.Label(master=frm_header,
                         image=logo_img,
                         )
        panel.grid(row=0, column=0)
        frm_header.pack()

        # create the main info frame
        frm_info = tk.Frame(
            master=self.gui,
            background=self.qd_red,
            border=self._border_width_main_frames,
            relief=tk.SUNKEN,
            padx=self.pad,
            pady=self.pad,
            )

        # create an indicator light to show if connected
        self.frm_connected = tk.Frame(
            master=frm_info,
            background=self.qd_red,
            padx=self.pad,
            pady=self.pad,
            )
        self._var_connected = tk.BooleanVar(value=False)
        self.lbl_connected_indicator = tk.Label(
            master=self.frm_connected,
            width=2,
            height=1,
            padx=self.pad,
        )
        self.lbl_connected = tk.Label(
            master=self.frm_connected,
            font=qd_font_small,
            padx=self.pad,
        )
        self.lbl_connected_indicator.pack(fill=tk.BOTH, side=tk.LEFT)
        self.lbl_connected.pack(fill=tk.BOTH, side=tk.LEFT)
        # update the light indicator (and add the frame if needed)
        self.set_connection_status(False)

        # start server button
        self.btn_start = tk.Button(
            master=frm_info,
            font=qd_font_small,
            padx=self.pad,
            pady=self.pad,
            width=10,
            command=lambda: self._start_btn_action()
        )
        self.btn_start.grid(row=0, column=2, sticky='e')
        btn_txt = self._get_start_btn_txt(self.start_button_enum.start)
        self.btn_start.config(text=btn_txt)

        # ip address
        frm_ip_address = tk.Frame(master=frm_info,
                                  background=self.qd_red,
                                  padx=self.pad,
                                  pady=self.pad,
                                  )
        self.ent_ip = tk.Entry(master=frm_ip_address,
                               font=qd_font_small,
                               width=15,
                               border=self._thin_border,
                               relief=tk.SUNKEN,
                               )
        self.ent_ip.pack(fill=tk.BOTH, side=tk.LEFT)
        # localhost checkbox
        self._var_localhost = tk.BooleanVar(value=True)
        self.ch_localhost = tk.Checkbutton(
            master=frm_ip_address,
            font=qd_font_small,
            text='localhost',
            variable=self._var_localhost,
            onvalue=True,
            offvalue=False,
            command=lambda: self._set_localhost(),
        )
        self._set_localhost()
        self.ch_localhost.pack(fill=tk.BOTH, side=tk.LEFT)
        # scaffolding indicator
        # self.scaffolding = tk.BooleanVar(value=False)
        # self.chk_scaffolding = tk.Radiobutton(
        #     master=frm_ip_address,
        #     text="Scaffolding",
        #     variable=self.scaffolding,
        #     value=True,
        #     command=self._controller.
        # )
        frm_ip_address.grid(row=1, column=0, sticky='w')

        # flavor name
        # create a frame so that the alignment matches other widgets
        frm_flavor = tk.Frame(
            master=frm_info,
            background=self.qd_red,
            padx=self.pad,
            pady=self.pad,
            )
        self.lbl_flavor = tk.Label(
            master=frm_flavor,
            font=qd_font_small,
            text='',
            width=17,
            relief=tk.SUNKEN,
            padx=self.pad,
            pady=self.pad,
        )
        self.lbl_flavor.pack()
        frm_flavor.grid(row=2, column=0, sticky='w')

        # Output the command line info to the gui
        frm_readback = tk.Frame(master=frm_info,
                                background=self.qd_red,
                                padx=self.pad,
                                pady=self.pad,
                                )
        lbl_readback_title = tk.Label(master=frm_readback,
                                      font=qd_font_small,
                                      background='white',
                                      fg=self.qd_black,
                                      text='Server Status',
                                      border=self._thin_border,
                                      padx=self.pad,
                                      pady=self.pad,
                                      )
        self.txt_readback = tk.Text(
            master=frm_readback,
            font=qd_font_status,
            background='white',
            fg=self.qd_black,
            width=50,
            height=7,
            state="disabled",
            )
        # Create vertical scroll bar and link it to the Text widget
        self.vertical_scrollbar = tk.Scrollbar(master=frm_readback,
                                               command=self.txt_readback.yview)
        self.txt_readback.configure(yscrollcommand=self.vertical_scrollbar.set)
        self.vertical_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        lbl_readback_title.pack(fill=tk.BOTH)
        self.txt_readback.pack()
        frm_readback.grid(row=3, column=0, sticky='w')

        # Quit button
        btn_quit = tk.Button(
            master=frm_info,
            font=qd_font_small,
            text='Quit',
            padx=self.pad,
            pady=self.pad,
            command=lambda: self.quit_gui()
        )
        btn_quit.grid(row=3, column=2, sticky='se')

        frm_info.pack()

        self.start_gui()

    def _set_localhost(self):
        # remove the current text
        self.ent_ip.delete(0, tk.END)
        # set the text
        if self._var_localhost.get():
            self.ent_ip.insert(0, 'localhost')
        else:
            self.ent_ip.insert(0, self._controller.ip_address)

    def _get_ip_address(self) -> str:
        return self.ent_ip.get()

    def get_connection_status(self):
        return self._var_connected.get()

    def set_connection_status(self, connected: bool):
        '''
        Update the connection toggle.  The toggle is hidden
        if the Server isn't running, so this also adds
        the frm_connected frame to the gui.
        '''
        self._var_connected.set(connected)
        if self._controller.model is None:
            # hide the connection frame
            self.frm_connected.grid_remove()
        else:
            self.frm_connected.grid(row=0, column=0, sticky='w')
            if connected:
                # turn the indicator light on
                self.lbl_connected_indicator.config(bg='green')
                self.lbl_connected.config(text='Connected')
            else:
                # turn the indicator light off
                self.lbl_connected_indicator.config(bg='grey')
                self.lbl_connected.config(text='Idle')

    def _get_start_btn_txt(self, btn_enum: start_button_enum) -> str:
        if btn_enum == self.start_button_enum.start:
            return 'Start Server'
        elif btn_enum == self.start_button_enum.idle:
            return 'Waiting for Client'
        elif btn_enum == self.start_button_enum.stop:
            return 'Close Server'
        else:
            raise ValueError('Unknown option')

    def _start_btn_action(self):
        '''
        Toggle between this button starting/stopping the server
        '''
        if self._controller.model is None:
            # the model has not been instantiated, so
            # instantiate the Server
            instance = self._controller.start_server(self._get_ip_address())
            # since the model was nothing, we need to call to
            # redirect the output at this point because instantiating
            # the Server wipes out the logging handlers
            self.redirector = RedirectOutputToGui(self.txt_readback)
            # check if an instance was returned
            if instance is None:
                print('Failed to start the server.  Check the IP address')
                self._controller.stop_server()
                return None
            # change the button text to stop
            btn_txt = self._get_start_btn_txt(self.start_button_enum.stop)
            self.btn_start.config(text=btn_txt)
            # show the connection status indicator
            self.frm_connected.grid(row=0, column=0, sticky='w')
            self.set_connection_status(False)
        else:
            # the model exists, so
            # stop the server
            self._controller.stop_server()
            # change the button text to start
            btn_txt = self._get_start_btn_txt(self.start_button_enum.start)
            self.btn_start.config(text=btn_txt)
            # hide the connection status indicator
            self.frm_connected.grid_remove()

    @property
    def mvu_flavor(self):
        return self.lbl_flavor['text']

    @mvu_flavor.setter
    def mvu_flavor(self, flavor):
        self.lbl_flavor.config(text=flavor)
        self.lbl_flavor['text'] = flavor

    def start_gui(self):
        self.TK_RUNNING = True
        self.gui.mainloop()

    def quit_gui(self):
        if self.TK_RUNNING:
            self._controller.stop_server()
            if self.redirector is not None:
                self.redirector.stop()
                self.redirector = None
            self.gui.destroy()
        self.TK_RUNNING = False
