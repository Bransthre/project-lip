#Packages
import threading
import time
import datetime
import re
import random
import tkinter as tk
from tkinter import ttk
from . import global_database
from . import notif_agent
from . import ei_database as ei_ds
from . import planner_database as pl_db

# General usage display function
def get_dialogue_line(dialogue_file, ind, replace_txt = ('',)):
    """
    Provides the ind_th line of dialogue from the file address marked by
    dialogue_file, while keywords in the dialogue line have substitute values
    marked by replace_txt.

    Args:
        dialogue_file (str): The file address of the .txt dialogue_file.
        ind (int): The index of the target line in .txt of dialogue_file.
        replace_txt (tuple): The substitute values for keywords in the dialogue
        message.
    
    Returns:
        str: The line of dialogue message to be displayed on interface via some
        other functions below.
    """
    selected_line = dialogue_file[ind]
    line_raw = global_database.transform_msg(selected_line, replace_txt)
    return line_raw.replace(r'\n', '\n')

def roll_new_text(screen, strvar, display_txt, delay = 10):
    """
    Displays a character-by-character introductory animation on interface screen
    for the dialogue message, display_txt, contained by strvar. The animation
    character appearance interval is marked by delay in miliseconds, by default
    25ms per character.

    Args:
        screen (tKinter interface): The screen that display_txt's char-by-char
        animation will be displayed on.
        strvar (tKinter StringVar): The strvar on the screen that will contain
        the displayed animation and message. 
        display_txt (str): The dialogue line to be displayed in animation.
        delay (int): The interval by which characters appear.
    """
    strvar.set("")
    def roll_new_txt_nest(display_txt):
        if display_txt:
            curr_txt = strvar.get()
            strvar.set(curr_txt + display_txt[0])
            screen.after(delay, roll_new_txt_nest, display_txt[1:])
    
    roll_new_txt_nest(display_txt)

# Setup Screen
class SetupScreen():
    """
    This is a Screen marking the setup of the entire management system, as well
    as a collector of global attributes via inputs from the gui units.
    """
    def __init__(self):
        """
        Constructor Method
        """
        self.message_ind = 0
        dialogue_file_address = (
            global_database.CWD + r"/function_backend/dialogue_setup.txt"
        )
        self.dialogue_file = open(
            dialogue_file_address,
            mode = 'r'
        ).readlines()
        self.dialogue_length = len(self.dialogue_file)
        
        self.init_screen = init_screen = tk.Tk()
        init_screen.title("Initializing...")
        init_screen.geometry("800x750")
        init_screen.resizable(0, 0)

        validate_dig = lambda input: (input.isdigit() or input == '')
        self.valid_dig = init_screen.register(validate_dig)

        init_screen.dialogue_frame = df = tk.Frame(init_screen)
        init_screen.df_strvar = tk.StringVar(
            master = df,
            value = ''
        )
        init_screen.df_lbl = tk.Label(
            master = df, 
            textvariable = init_screen.df_strvar, 
            height = 30
        )
        init_screen.df_btn = tk.Button(
            master = df,
            text = "Continue",
            command = self.change_txt
        )
        init_screen.df_entry = tk.Entry(
            master = df,
            width = 100,
            state = 'disabled'
        )
        df.pack()

        init_screen.df_lbl.grid(row = 0, column = 0, padx = 5, pady = 5)
        self.init_screen.df_btn.grid(row = 2, column = 0, padx = 5, pady = 5)

    def change_txt(self):
        """
        Main method for text changing events in the SetupScreen class, mainly
        triggered via buttons.
        """
        self.dialogue_gui_event()
        display_txt = self.dialogue_txt_event()
        self.init_screen.df_strvar.set('')
        self.init_screen.df_btn.grid_remove()
        self.init_screen.df_entry.delete(0, tk.END)

        roll_new_text(self.init_screen,
                      self.init_screen.df_strvar,
                      display_txt
                     )
        revive_btn = lambda: self.init_screen.df_btn.grid(row = 2,
                                                          column = 0,
                                                          padx = 5,
                                                          pady = 5
                                                         )
        self.init_screen.after(4 * len(display_txt), revive_btn)
        self.message_ind += 1
    
    def dialogue_txt_event(self):
        """
        Main handler of specific events based on some dialogue lines' related
        text inputs.

        Returns:
            str: A transformed version of message.
        """
        msg = get_dialogue_line(self.dialogue_file, self.message_ind)
        if self.message_ind == 7:
            user_name = self.init_screen.df_entry.get()
            global_database.set_global_attr('user_name', user_name)
            replacement = get_dialogue_line(self.dialogue_file, 19)
            msg = get_dialogue_line(self.dialogue_file, 
                                    self.message_ind,
                                    replace_txt = (replacement,)
                                   )
        elif self.message_ind == 10:
            check_interval = self.init_screen.df_entry.get()
            global_database.set_global_attr('checkin_interval', check_interval)
            msg = get_dialogue_line(self.dialogue_file, self.message_ind)
        
        return msg

    def dialogue_gui_event(self):
        """
        Main event handler for gui related events during the dialogue, such as
        component changes.
        """
        if self.message_ind == 5:
            self.init_screen.df_entry.grid(row = 1, column = 0, padx=5, pady=5)
        elif self.message_ind == 6:
            self.init_screen.df_entry.config(state = 'normal')
        elif self.message_ind == 9:
            self.init_screen.df_entry.config(validate = 'key',
                                             validatecommand = (self.valid_dig, 
                                                                '%P'
                                                               )
                                            )
            self.init_screen.df_entry.config(state = 'normal')
        elif self.message_ind == 17:
            self.init_screen.title("Lip")
        elif self.message_ind == 18:
            destroy_window = lambda: self.init_screen.destroy()
            self.init_screen.df_entry.grid_remove()
            self.init_screen.df_btn.config(command = destroy_window)
            ei_ds.emo_tbl_setup()
            pl_db.database_setup()
            global_database.set_global_attr('setup', 'TRUE')
            global_database.set_global_attr('tts', 'TRUE')
        else:
            self.init_screen.df_entry.config(state = 'disabled')

# Main Screen
class MainScreen(tk.Tk):
    """
    The Main Screen, great container interface of this management system.
    """
    def __init__(self):
        """
        Constructor method.
        """
        super().__init__()
        self.title('Lip, Interface')
        self.geometry('1200x600')
        self.resizable(0, 0)
        self.rowconfigure(0, minsize = 800, weight = 1)
        self.columnconfigure(1, minsize = 800, weight = 1)
        OptionsWindow(self)
    
    def push_survey_action(self, is_short = False):
        survey_screen = SurveyScreen(self, is_short = is_short)
        survey_screen.mainloop()

class OptionsWindow(ttk.LabelFrame):
    """
    The Option Menu of functionalities for this management system, at the left
    side of homescreen.
    """
    def __init__(self, master):
        """
        Constructor Method.
        """
        super().__init__(master)
        self['text'] = 'Menu'
        self.selected_value = tk.IntVar()
        home_btn = ttk.Radiobutton(
            self, 
            text = 'Home', 
            value = 0,
            variable = self.selected_value,
            command = self.change_frame
        )
        planner_btn = ttk.Radiobutton(
            self, 
            text = 'Event Planner', 
            value = 1,
            variable = self.selected_value,
            command = self.change_frame
        )
        pomodoro_btn = ttk.Radiobutton(
            self, 
            text = 'Pomodoro', 
            value = 2,
            variable = self.selected_value,
            command = self.change_frame
        )
        setting_btn = ttk.Radiobutton(
            self, 
            text = 'Settings', 
            value = 3,
            variable = self.selected_value,
            command = self.change_frame
        )
        home_btn.grid(row = 0, column = 0, sticky = 'ew')
        planner_btn.grid(row = 1, column = 0, sticky = 'ew')
        pomodoro_btn.grid(row = 2, column = 0, sticky = 'ew')
        setting_btn.grid(row = 3, column = 0, sticky = 'ew')
        self.grid(column = 0, row = 0, sticky = 'ns')
        self.frames = [
            HomeScreen(master),
            PlannerScreen(master),
            PomodoroScreen(master),
            SettingsScreen(master)
        ]
        self.change_frame()
    
    def change_frame(self):
        """
        Event handler for changing the right side screen ("frame") corresponding
        to the option chosen at the left side screen (option menu).
        """
        chosen_frame = self.frames[self.selected_value.get()]
        chosen_frame.reset()
        chosen_frame.tkraise()

class HomeScreen(ttk.Frame):
    """
    The Homescreen of this management system; the default opened window.
    """
    def __init__(self, container):
        """
        Constructor method.

        Args:
            container (tK.tk): The master (container) of this frame.
        """
        super().__init__(container)
        self.container = container
        self.display_lbl = ttk.Label(self, text = 'home')
        self.display_lbl.grid(column = 0, row = 0)
        print(container)
        self.survey_init_btn = ttk.Button(
            self,
            text = 'initiate survey',
            command = lambda: self.push_survey()
        )
        self.survey_init_btn.grid(column = 0, row = 1)
        self.grid(column = 1, row = 0, sticky = 'nsew')
        self.survey_init_btn = ttk.Button(
            self,
            text = 'initiate short survey',
            command = lambda: self.push_survey(is_short = True)
        )
        self.survey_init_btn.grid(column = 0, row = 2)
    
    def reset(self):
        """
        Incomplete.

        Args:
            param (type): description
        
        Returns:
            type: description
        """
        self.display_lbl.txt = ''
    
    def push_survey(self, is_short = False):
        '''
        thread_notif = threading.Thread(
            target = lambda: notif_agent.push_survey_notif(
                self.container,
                is_short = is_short
            )
        )
        thread_notif.start()
        '''
        notif_agent.push_survey_notif(
            self.container,
            is_short = is_short
        )

class PlannerScreen(ttk.Frame):
    """
    The right-side screen corresponding to the planner functionality.
    """
    def __init__(self, container):
        """
        Constructor method.

        Args:
            container (tK.tk): The master (container) of this frame.
        """
        super().__init__(container)
        self.display_lbl = ttk.Label(self, text = 'planner')
        self.display_lbl.grid(column = 0, row = 0)
        self.event_log_lbl = ttk.Label(self, text = 'Event Log:')
        self.event_log_lbl.grid(column = 0, row = 1, sticky = "ew")
        self.event_display_canvas = self.EventLogBoard(self, self.EventRow)
        self.event_display_canvas.grid(
            column = 0,
            row = 2,
            padx = (10, 0),
            pady = (10, 0),
            sticky="ew"
        )
        self.event_edit_window_lbl = ttk.Label(self, text = 'Event Entry:')
        self.event_edit_window_lbl.grid(column = 0, row = 3, sticky = "ew")
        self.edit_event_canvas = self.EventWriterWindow(self)
        self.edit_event_canvas.grid(
            column = 0,
            row = 4,
            padx = (10, 0),
            pady = (10, 0),
            sticky="ew"
        )
        self.grid(column = 1, row = 0, sticky = 'nsew')
            
    def reset(self):
        """
        Incomplete

        Args:
            param (type): description
        
        Returns:
            type: description
        """
        self.display_lbl.txt = ''
        self.edit_event_canvas.update_entry_board()
    
    class EventLogBoard(tk.Canvas):
        def __init__(self, container, eventRow):
            super().__init__(
                container,
                borderwidth = 5,
                width = 200,
                height = 50
            )
            self.eventRow = eventRow
            self.container = container
            self.elog_dict = {}
            self.scroll_bar = ttk.Scrollbar(
                self,
                orient = 'vertical',
                command=self.yview
            )
            self.build_event_board()
            self.scroll_bar.grid(
                column = 1,
                row = 0,
                sticky = "ns",
                rowspan = self.row_cnter + 1
            )
        
        def build_event_board(self):
            self.clear_board()
            # at above, did not use self.delete("all") because it doesn't work
            instruction_lbl = ttk.Label(
                self,
                text = "The event details recorded on my side are listed here",
            )
            instruction_lbl.grid(
                column = 0,
                row = 0,
                padx = (5, 5),
                pady = (2, 2),
                sticky = "e"
            )
            all_events = pl_db.get_all_events()
            self.row_cnter = 0
            for event in all_events:
                self.elog_dict[event[0]] = self.eventRow(self, event)
                self.row_cnter += 1
        
        def clear_board(self):
            for rows in self.elog_dict.values():
                rows.event_lbl.grid_remove()
            self.elog_dict = {}
        
        def update_event_gui(self, event_params):
            self.container.edit_event_canvas.update_event_gui(event_params)
        
        def delete_event_gui(self, event_params):
            event_params = event_params[0:1] + event_params[3:]
            pl_db.remove_event(*event_params)
            self.build_event_board()
    
    class EventRow():
        def __init__(self, master, event_params):
            self.master = master
            event_msg = self.get_event_msg(event_params)
            self.event_lbl = ttk.Label(
                self.master,
                text = event_msg
            )
            self.event_lbl.grid(
                column = 0,
                row = self.master.row_cnter + 1,
                padx = (5, 5),
                pady = (2, 2),
                sticky = "e"
            )
            self.event_r_clk_menu = tk.Menu(self.master, tearoff = 0)
            self.event_r_clk_menu.add_command(
                label = "Update",
                command = lambda: self.master.update_event_gui(event_params[1:])
            )
            self.event_r_clk_menu.add_separator()
            self.event_r_clk_menu.add_command(
                label = "Delete",
                command = lambda: self.master.delete_event_gui(event_params[1:])
            )
            self.event_lbl.bind("<Button-3>", self.menu_open)
        
        def get_event_msg(self, event):
            event_name, event_type, event_desc, event_yr, event_mn, \
                    event_day, event_hr, event_min = event[1:]
            if not event_mn // 10:
                event_mn = "0" + str(event_mn)
            if not event_day // 10:
                event_day = "0" + str(event_day)
            if not event_hr // 10:
                event_hr = "0" + str(event_hr)
            if not event_min // 10:
                event_min = "0" + str(event_min)
            return (
                f"Your {event_type} event: {event_name}: {event_desc}, "
                f"comes: {event_yr}/{event_mn}/{event_day}, "
                f"{event_hr}:{event_min}"
            )
        
        def menu_open(self, event):
            try:
                self.event_r_clk_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.event_r_clk_menu.grab_release()

    class EventWriterWindow(tk.Canvas):
        def __init__(self, container):
            super().__init__(container)
            self.container = container
            self.entry_attr_names = pl_db.events_col_names[1:][:]
            self.entry_map = {
                name: ttk.Entry(self, width = 16) for name in self.entry_attr_names
            }
            self.scroll_bar = ttk.Scrollbar(
                self,
                orient = 'horizontal',
                command=self.xview
            )
            self.build_board()
            self.scroll_bar.grid(
                column = 0,
                row = 2,
                sticky = "ew",
                columnspan = self.col_cnter + 1
            )
            self.create_btn = ttk.Button(
                self,
                text = "Create Event",
                command = self.create_event_gui
            )
            self.update_btn = ttk.Button(self, text = "Update Event")
            self.create_btn.grid(
                column = 0,
                row = 3,
                sticky = "ew"
            )
        
        def build_board(self):
            self.col_cnter = 0
            for p in self.entry_map.items():
                instruction_lbl = ttk.Label(self, text = p[0])
                instruction_lbl.grid(
                    column = self.col_cnter, 
                    row = 0, 
                    sticky = "ew"
                )
                p[1].grid(
                    column = self.col_cnter,
                    row = 1,
                    padx = (5, 5),
                    sticky = "ew"
                )
                self.col_cnter += 1
            self.update_entry_board()
        
        def validate_entry_content(self):
            for p in self.entry_map.items():
                if p[1].get() == "":
                    return False
                if p[0] in self.entry_attr_names[4:]:
                    if not p[1].get().isdigit():
                        return False
            return True
        
        def update_entry_board(self, event_default_params = None):
            if event_default_params:
                while len(event_default_params) < 8:
                    event_default_params.append(0)
            def_param_ind = 0
            for p in self.entry_map.items():
                p[1].delete(0, tk.END)
                if event_default_params:
                    p[1].insert(tk.END, event_default_params[def_param_ind])
                else:
                    if p[0] == "event_yr":
                        p[1].insert(tk.END, str(datetime.datetime.now().year))
                    elif p[0] == "event_month":
                        p[1].insert(tk.END, str(datetime.datetime.now().month))
                    elif p[0] == "event_day":
                        p[1].insert(tk.END, str(datetime.datetime.now().day))
                    elif p[0] == "event_hr":
                        p[1].insert(
                            tk.END,
                            str((datetime.datetime.now().hour + 1) % 24)
                        )
                    elif p[0] == "event_min":
                        p[1].insert(tk.END, str(datetime.datetime.now().minute))
                def_param_ind += 1

        def create_event_gui(self, event_params = None, mode = 'c'):
            if not self.validate_entry_content():
                return
            if mode == 'c':
                entry_contents = [
                    self.entry_map.get(attr_name).get()
                    for attr_name in self.entry_attr_names
                ]
                for e in entry_contents:
                    if e.isdigit():
                        e = int(e)
                    else:
                        e = e.replace("\n", "  ")
                pl_db.create_event(*entry_contents)
            elif mode == 'u' and len(event_params) == 8:
                event_params = list(event_params)
                entry_contents = {
                    attr_name : self.entry_map.get(attr_name).get()
                    for attr_name in self.entry_attr_names
                }
                for e in entry_contents.values():
                    if e.isdigit():
                        e = int(e)
                    else:
                        e = e.replace("\n", "  ")
                up_par = [entry_contents] + event_params[0:1] + event_params[3:]
                pl_db.update_event(*up_par)
                self.update_btn.grid_remove()
            else:
                raise Exception("There is no such mode for this function.")
            self.container.event_display_canvas.build_event_board()
            self.update_entry_board()
        
        def update_event_gui(self, event_params):
            self.update_entry_board(event_params)
            self.update_btn.config(
                command = lambda: self.create_event_gui(
                    event_params = event_params,
                    mode = 'u'
                )
            )
            self.update_btn.grid(
                column = 0,
                row = 3,
                sticky = "ew"
            )

class PomodoroScreen(ttk.Frame):
    """
    The right-side screen corresponding to the pomodoro clock functionality.
    """
    def __init__(self, container):
        """
        Constructor method.

        Args:
            container (tK.tk): The master (container) of this frame.
        """
        super().__init__(container)
        self.display_lbl = ttk.Label(self, text = 'pomodoro')
        self.time_input_lbl = ttk.Label(
            self,
            text = 'Input the time length (int) of your work section at right:'
        )
        self.time_input_entry = ttk.Entry(self, width = 5)
        self.rest_input_lbl = ttk.Label(
            self,
            text = 'Input the time length (int) of your rest section at right:'
        )
        self.rest_input_entry = ttk.Entry(self, width = 5)
        self.time_section_cnt_lbl = ttk.Label(
            self,
            text = 'Input the number of your work section you want at right:'
        )
        self.time_section_cnt_entry = ttk.Entry(self, width = 5)
        self.start_btn = ttk.Button(
            self,
            text = "start timer",
            command = self.start_clock
        )
        self.display_lbl.grid(column = 0, row = 0)
        self.time_input_lbl.grid(column = 0, row = 1)
        self.time_input_entry.grid(column = 1, row = 1)
        self.rest_input_lbl.grid(column = 0, row = 2)
        self.rest_input_entry.grid(column = 1, row = 2)
        self.time_section_cnt_lbl.grid(column = 0, row = 3)
        self.time_section_cnt_entry.grid(column = 1, row = 3)
        self.start_btn.grid(column = 0, row = 4)
        self.time_input_entry.insert(tk.END, "25")
        self.rest_input_entry.insert(tk.END, "5")
        self.time_section_cnt_entry.insert(tk.END, "2")
        self.time_display_lbl = ttk.Label(self, text = "")
        self.grid(column = 1, row = 0, sticky = 'nsew')
        self.clock = self.PomodoroClock()
        self.entries = [
            self.time_input_entry,
            self.rest_input_entry,
            self.time_section_cnt_entry
        ]
    
    def reset(self):
        """
        Incomplete

        Args:
            param (type): description
        
        Returns:
            type: description
        """
        self.display_lbl.txt = ''
    
    def validate_entry_input(self):
        for entry in self.entries:
            if not entry.get().isdigit():
                return False
        return True

    def start_clock(self):
        """
        The method that launches a separate thread for the pomodoro clock
        functionality to be ran in parallel, via a trigger from button that
        triggers this event.
        """
        if not self.validate_entry_input():
            raise Exception("Entry contents not numeric, they invalid :/")
        clock_inputs = []
        for entry in self.entries:
            clock_inputs.append(int(entry.get()))
            entry.config(state = "disabled")
        self.time_display_lbl.grid(column = 0, row = 4)
        clock_inputs.append(self)
        self.clock_thread = threading.Thread(
            target = lambda: self.clock.pomodoro_clock(*clock_inputs)
        )
        self.clock_thread.start()
    
    def update_after_clock(self):
        self.time_display_lbl.grid_remove()
        for entry in self.entries:
            entry.config(state = "enabled")
    
    class PomodoroClock():
        def pomodoro_clock(
            self, work_interval, rest_interval, sect_cnt, pomodoro_screen, 
            work_msg = None, rest_msg = None
        ):
            """
            This function is a pomodoro timer that counts WORK_INTERVAL
            amount of minutes, then REST_INTERVAL amount of minutes, in
            interleaving manner until they are both called REPETITION times.

            Args:
                work_interval (float): A floating point representing the amount
                of time this function will count for in a first interval.
                rest_interval (float): A floating point representing the amount
                of time this function will count for in a second interval.
                repetition (int): The amount of times both intervals will be called.
            """
            time_display_lbl = pomodoro_screen.time_display_lbl
            max_cnt = sect_cnt
            while sect_cnt:
                work_msg = work_msg or \
                    f"Work period, number {max_cnt - sect_cnt}, starts."
                rest_msg = rest_msg or \
                    f"Work period, number {max_cnt - sect_cnt}, ends."
                notif_agent.push_pomodoro_notification(
                    sect_cnt, 
                    work_msg, 
                    work_interval
                )
                self.countdown(work_interval * 60, time_display_lbl)
                notif_agent.push_pomodoro_notification(
                    sect_cnt, 
                    rest_msg, 
                    rest_interval
                )
                self.countdown(rest_interval * 60, time_display_lbl)
                sect_cnt -= 1
            pomodoro_screen.update_after_clock()

        def countdown(self, time_length, time_display_lbl):
            while time_length:
                min, sec = divmod(time_length, 60)
                if not min // 10:
                    min = "0" + str(min)
                if not sec // 10:
                    sec = "0" + str(sec)
                time_display_lbl.config(text = f"Remaining time: {min}:{sec}")
                time.sleep(1)
                time_length -= 1

class SettingsScreen(ttk.Frame):
    """
    The right-side screen corresponding to the settings window functionality
    that permits customized running options and global attribute modifications.
    """
    def __init__(self, container):
        """
        Constructor method.

        Args:
            container (tK.tk): The master (container) of this frame.
        """
        super().__init__(container)
        self.display_lbl = ttk.Label(self, text = 'settings')
        self.display_lbl.grid(column = 0, row = 0)
        self.attr_settings_canvas = tk.Canvas(self, borderwidth = 5)
        self.scroll_bar = ttk.Scrollbar(
            self.attr_settings_canvas,
            orient = 'vertical',
            command=self.attr_settings_canvas.yview
        )
        self.attr_table_items = {
            name: 
            [
                ttk.Label(self.attr_settings_canvas, text = name), 
                ttk.Label(
                    self.attr_settings_canvas,
                    text = f"Currently {global_database.get_global_attr(name)}"
                ),
                tk.Entry(self.attr_settings_canvas, width = 15),
                tk.Button(
                    self.attr_settings_canvas,
                    text = f"Change Value for {name}"
                )
            ]
            for name in global_database.get_all_attr_names()
        }
        row_cnter = 0
        for name in self.attr_table_items.keys():
            attr_gui_elems = self.attr_table_items.get(name)
            attr_gui_elems[3].config(command = self.update_event_handler(name))
            for col_cnt in range(len(attr_gui_elems)):
                attr_gui_elems[col_cnt].grid(
                    column = col_cnt,
                    row = row_cnter + 1,
                    sticky = "ew"
                )
            row_cnter += 1
        self.scroll_bar.grid(
            column = 4,
            row = 0,
            sticky = "ns",
            rowspan = row_cnter + 1
        )
        self.attr_settings_canvas.grid(
            column = 0,
            row = 1,
            padx = (10, 0),
            pady = (10, 0)
        )
        self.grid(column = 1, row = 0, sticky = 'nsew')
    
    def reset(self):
        """
        Incomplete

        Args:
            param (type): description
        
        Returns:
            type: description
        """
        self.display_lbl.txt = ''
    
    def update_event_handler(self, attr_name):
        """
        An event handling function when global attributes are to be updated.

        Args:
            attr_name (str): the name of the attribute to be changed.

        Returns:
            function: An argument-less lambda function to be called by the
            associated button that invoked this handler.
        """        
        def update_event_handler_helper(attr_name):   
            attr_val_container = self.attr_table_items.get(attr_name)[2]
            attr_val = attr_val_container.get()
            attr_val = attr_val.replace(" ", "").replace("\n", "")
            if not attr_val:
                raise Exception("Please enter an appropriate value for update.")
            elif attr_val.isdigit():
                attr_val = int(attr_val)
            elif attr_val.lower() == "true" or attr_val.lower() == "false":
                attr_val = attr_val.upper()
            else:
                try:
                    attr_val = float(attr_val)
                except ValueError:
                    attr_val = attr_val
            global_database.set_global_attr(attr_name, attr_val)
            self.attr_table_items.get(attr_name)[1].config(
                text = f"Currently {global_database.get_global_attr(attr_name)}"
            )
            attr_val_container.delete(0, tk.END)
        return lambda: update_event_handler_helper(attr_name)

#Survey Screen
class SurveyScreen(tk.Toplevel):
    """
    The great interface container for emotional survey-related options of this
    management system.
    """
    def __init__(self, master, is_short = False):
        """
        Constructor method.

        Args:
            master (tK.tk): The mainscreen of current management system.
        """
        super().__init__(master)
        self.title('Lip (Survey Interface)')
        self.geometry('800x750')
        self.resizable(0, 0)
        self.survey_window = SurveyWindow(self, is_short = is_short)
        self.survey_window.pack()

class SurveyWindow(ttk.Frame):
    """
    The survey window contained by survey screen for this management system.
    """
    parameters = [
        '', 'log_loc', 'social_deg', 'work_deg', 'rest_deg', 'valence', 
        'activation'
    ]
    def __init__(self, master, is_short = False):
        """
        Constructor method.

        Args:
            master (tK.tk): The master (container) of this frame.
        """
        super().__init__(master)
        self.master = master
        options_list = []
        self.survey_results = {}
        self.parameters = SurveyWindow.parameters[:]
        self.journal_entry = ""
        self.is_short = is_short

        dialogue_file_address = (
            global_database.CWD + r"/function_backend/dialogue_survey.txt"
        )
        options_file_address = (
            global_database.CWD + r"/function_backend/options_survey.txt"
        )
        self.entries_file_address = (
            global_database.CWD + r"/function_backend/log_entries.txt"
        )
        self.dialogue_file = open(
            dialogue_file_address,
            mode = 'r'
        ).readlines()
        self.options_file = open(
            options_file_address,
            mode = 'r'
        ).readlines()
        self.message_ind = 0
        self.question_strvar = tk.StringVar(
            self, 
            value = ''
        )
        self.menu_strvar = tk.StringVar(
            self, 
            value = ''
        )
        self.question_lbl = tk.Label(
            self,
            textvariable = self.question_strvar,
            height = 30
        )
        self.proceed_btn = tk.Button(
            self,
            text = "Continue",
            command = self.initiate_survey
        )
        self.answer_menu = ttk.OptionMenu(
            self, 
            variable = self.menu_strvar,
            command = self.get_menu_answer,
            *options_list
        )
        self.answer_txt = tk.Text(
            self,
            height = 10
        )
        self.question_lbl.grid(row = 0, column = 0, padx = 5, pady = 5)
        self.proceed_btn.grid(row = 2, column = 0, padx = 5, pady = 5)

    def get_survey_options(self, topic):
        """
        A method for accessing the options of a dropdown list in a survey query.

        Args:
            topic (str): The name of the survey topic as noted on the file of
            options_file_address
        
        Returns:
            str[]: A list of options provided for the topic of survey.
        """
        start_ind = 1
        while self.options_file[start_ind] != f'@{topic}' + '\n':
            start_ind += 1
            if start_ind >= len(self.options_file):
                return None
        
        terminal_ind = start_ind + 1
        while self.options_file[terminal_ind] != 'end of article\n':
            terminal_ind += 1
            if terminal_ind >= len(self.options_file):
                return None
        
        optionsList = [s[:-1] for s in self.options_file[start_ind:terminal_ind]]
        for i in range(len(optionsList)):
            if optionsList[i].isnumeric():
                optionsList[i] = int(optionsList[i])
        return optionsList
                
    
    def display_dialogue(self, message_ind = None, increment = True):
        """
        Button trigger progress handler for dialogue display based on the above
        general methods for interfaces, displaying the message_ind index message
        on designated dialogue file while incrementing the interface's current
        target index based on the increment option.

        Args:
            message_ind (int): The index of message currently concerned for.
            increment (bool): description
        """
        self.proceed_btn.grid_remove()
        if message_ind is None:
            message_ind = self.message_ind
        
        display_txt = get_dialogue_line(self.dialogue_file, message_ind)
        roll_new_text(self.master, self.question_strvar, display_txt)
        if increment:
            self.message_ind += 1
        revive_btn = lambda: self.proceed_btn.grid(row = 2, 
                                                   column = 0, 
                                                   padx = 5, 
                                                   pady = 5
                                                  )
        self.master.after(35 * len(display_txt), revive_btn)
        #print(f"LOG: {self.message_ind}")
    
    def get_menu_answer(self, option):
        """
        Extracts the menu option of a user input from an optionMenu as an event
        handler of the interface's dropdown menu and saves it into the interface
        object's survey entry information.

        Args:
            option (Any): the option that user has opted from the optionMenu
        """
        self.proceed_btn.config(state = "active")
        if isinstance(option, str) and option.isdigit():
            option = float(re.findall('\d+')[0])
        self.survey_results[self.parameters[0]] = option

    def initiate_survey(self):
        """
        Button event handler for initiating the survey.
        """
        if self.message_ind == 0:
            now_datetime = datetime.datetime.now()
            log_time = now_datetime.hour * 60 + now_datetime.minute
            log_day = now_datetime.weekday()
            self.survey_results['log_time'] = log_time
            self.survey_results['log_day'] = log_day
            self.question_strvar.set('')
        elif self.message_ind == 1:
            self.proceed_btn.config(command = self.ask_log_params)
            self.answer_menu.grid(row = 1, column = 0, padx = 5, pady = 5)
            self.answer_menu.set_menu("Here is the dropdown list!")
        self.display_dialogue()
    
    def ask_log_params(self):
        """
        Button event handler for overall user parameter related queries.
        """
        self.parameters.pop(0)
        options_list = self.get_survey_options(self.parameters[0])
        self.proceed_btn.config(state = "disabled")
        self.answer_menu.set_menu(*(["Choose from below!"] + options_list[1:]))
        if len(self.parameters[1:]) > 2:
            self.proceed_btn.config(command = self.ask_log_params)
        elif self.is_short:
            self.proceed_btn.config(command = self.ask_end_short_survey)
            pass
        else:
            self.proceed_btn.config(command = self.ask_journal)
        self.display_dialogue()

    def ask_journal(self):
        """
        Button event handler for user journal entry.
        """
        self.answer_menu.grid_remove()
        self.display_dialogue()
        if self.message_ind < 9:
            return
        elif self.message_ind == 9:
            self.message_ind += 1
            self.answer_menu.grid_remove()
            self.answer_txt.grid(row = 1, column = 0, padx = 5, pady = 5)
            #prompt_list = self.get_survey_options("prompts")[1:]
            #self.jounral_ind = random.randint(0, len(prompt_list) - 1)
            #self.question_strvar.set(prompt_list[self.jounral_ind])
            self.proceed_btn.config(command = self.ask_emotion)
            self.skip_btn = ttk.Button(
                text = "Skip Journal Entry",
                command = self.ask_emotion
            )
            self.skip_btn.grid(row = 3, column = 0, sticky = "ew")

    def ask_emotion(self):
        """
        Button event handler for user emotion parameter.
        """
        self.journal_entry = self.answer_txt.get("1.0", tk.END)
        self.skip_btn.grid_remove()
        self.answer_txt.grid_remove()
        self.answer_menu.grid_remove()
        self.display_dialogue()
        if self.message_ind == 14 or self.message_ind == 17:
            self.parameters.pop(0)
            self.proceed_btn.config(state = "disabled")
            self.answer_menu.grid(row = 1, column = 0, padx = 5, pady = 5)
            if self.message_ind == 14:
                options_list = self.get_survey_options("valence")
            else:
                options_list = self.get_survey_options("activation")
                self.proceed_btn.config(command = self.ask_end_survey)
            self.answer_menu.set_menu(*(["Choose from below!"] + options_list[1:]))
    
    def ask_end_survey(self):
        """
        Button event handler for terminating the survey.
        """
        self.answer_menu.grid_remove()
        self.display_dialogue()
        if self.message_ind == 18:
            #print("LOG: reach end of survey.")
            self.upload_survey_results()
            self.proceed_btn.config(command = self.end_survey)
    
    def ask_end_short_survey(self):
        """
        Button event handler for terminating the short survey.
        """
        self.answer_menu.grid_remove()
        self.display_dialogue()
        row = (
            self.survey_results['log_time'],
            self.survey_results['log_day'],
            self.survey_results['log_loc'],
            self.survey_results['social_deg'],
            self.survey_results['work_deg'],
            self.survey_results['rest_deg']
        )
        self.proceed_btn.config(command = lambda: self.end_short_survey(row))
    
    def end_survey(self):
        """
        Button event handler for terminating the survey window.
        """
        self.master.destroy()
    
    def end_short_survey(self, row):
        """
        Button event handler for terminating the short survey window.
        """
        self.end_survey()
        threading.Thread(
            target = lambda: notif_agent.push_interventions(row)
        ).start()
    
    def upload_survey_results(self):
        """
        Method to upload the survey results onto the local database.
        """
        status_dict = {
            "negative": -1,
            "neutral": 0,
            "positive": 1
        }
        now = datetime.datetime.now()
        emotion = f"{self.survey_results['valence']}{self.survey_results['activation']}"
        ei_ds.create_entry(
            emotion,
            self.survey_results['log_time'],
            self.survey_results['log_day'],
            self.survey_results['log_loc'],
            self.survey_results['social_deg'],
            self.survey_results['work_deg'],
            self.survey_results['rest_deg'],
            datetime.datetime.now(),
            valence = status_dict[self.survey_results['valence']],
            activate = status_dict[self.survey_results['activation']]
        )

        if self.journal_entry != "":
            with open(self.entries_file_address, 'a') as f:
                f.write(
                    f"@{now.year}-{now.month}-{now.day}-"
                    f"{self.survey_results['log_time']}-\n"
                )
                f.write(self.journal_entry)
                f.write(
                    f"#{self.survey_results['valence']}|"
                    f"{self.survey_results['activation']}|\n"
                )
                f.write("\n")
