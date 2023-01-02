import threading
import function_backend.gui as gui
import function_backend.notif_agent as notif_agent
import function_backend.global_database as global_db
import function_backend.ei_database as ei_ds
import function_backend.planner_database as planner_db

global_db.global_tbl_setup()
planner_db.database_setup()
ei_ds.emo_tbl_setup()

if not global_db.get_global_attr('setup'):
    init_screen = gui.SetupScreen().init_screen
    init_screen.mainloop()

homescreen = gui.MainScreen()
thread_notif = threading.Thread(
    target = lambda: notif_agent.push_main(homescreen)
)
thread_notif.start()
homescreen.mainloop()