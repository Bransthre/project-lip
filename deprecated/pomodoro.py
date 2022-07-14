#Packages
import time
import notif_agent

def pomodoro_clock(
        work_interval, rest_interval, sect_cnt, pomodoro_screen, 
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
    work_msg = work_msg or f"Work period, number {max_cnt - sect_cnt}, starts."
    rest_msg = rest_msg or f"Work period, number {max_cnt - sect_cnt}, ends."
    while sect_cnt:
        notif_agent.push_pomodoro_notification(
            sect_cnt, 
            work_msg, 
            work_interval
        )
        countdown(work_interval * 60, time_display_lbl)
        notif_agent.push_pomodoro_notification(
            sect_cnt, 
            rest_msg, 
            rest_interval
        )
        countdown(rest_interval * 60, time_display_lbl)
        sect_cnt -= 1
    pomodoro_screen.update_after_clock()
    

def countdown(time_length, time_display_lbl):
    while time_length:
        min, sec = divmod(time_length, 60)
        if not min // 10:
            min = "0" + str(min)
        if not sec // 10:
            sec = "0" + str(sec)
        time_display_lbl.config(text = f"Remaining time: {min}:{sec}")
        time.sleep(1)
        time_length -= 1
