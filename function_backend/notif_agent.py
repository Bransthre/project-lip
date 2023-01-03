#Packages
import threading
import subprocess
import psutil
import os
import time
import datetime
from gtts import gTTS
from playsound import playsound
import pyttsx3
import winsdk.windows.ui.notifications as notification
import winsdk.windows.data.xml.dom as dom
from . import global_database as gl_ds
from . import planner_database as pl_db
from . import gui
from . import intervention_agent as in_ag
ICON_PATH = gl_ds.ICON_PATH

#TODO: homescreen revival mechanics or make it non-closeable
EXPIRATION_TIME = 10
notification.ToastNotification.ExpirationTime = EXPIRATION_TIME
notification_manager, notifier = None, None

def push_main(homescreen):
    """
    The main method to push notifications with, involving an ongoing loop of
    notifications based on interval-related global attributes for user survey
    and intervention chronological metrics.

    Args:
        homescreen (tK.tk): The homescreen of current management system.
    """
    global notification_manager, notifier
    notification_manager = notification.ToastNotificationManager
    notifier = notification_manager.create_toast_notifier()
    device_check_interval = gl_ds.get_global_attr("checkin_interval")
    ei_survey_interval = device_check_interval * 2
    ei_check_interval = device_check_interval * 3
    curr_device_intv = device_check_interval
    curr_survey_intv = ei_survey_interval
    curr_ei_intv = ei_check_interval
    while True:
        slept_time = min(curr_device_intv, curr_ei_intv, curr_survey_intv)
        time.sleep(int(slept_time * 60))
        curr_device_intv -= slept_time
        curr_survey_intv -= slept_time
        curr_ei_intv -= slept_time   
        if curr_ei_intv <= 0:
            push_survey_notif(homescreen, is_short = True)
            curr_ei_intv = ei_check_interval
        elif curr_survey_intv <= 0:
            push_survey_notif(homescreen)
            curr_survey_intv = ei_survey_interval
        if curr_device_intv <= 0:
            current_datetime = datetime.datetime.now()
            push_pc_stat_notification()
            push_event_notification(
                current_datetime, 
                device_check_interval * 2
            )
            curr_device_intv = device_check_interval

def notif_tts(notif_msg):
    #TODO: Try out Azure's version of tts API for a perhaps more "humanic" voice
    if gl_ds.get_global_attr("tts"):
        audio_path = gl_ds.CWD + r'/images/notif_Temp.mp3'
        speaker = gTTS(notif_msg, lang = 'en', tld = 'com')
        speaker.save(audio_path)
        playsound(audio_path)
        os.remove(audio_path)

def notif_tts_pyttsx(notif_msg):
    if gl_ds.get_global_attr("tts"):
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        engine.setProperty('voice', voices[2].id)
        engine.say(notif_msg)
        engine.runAndWait()
        engine.stop()

def get_net_attribute(net_stat, attr):
    """
    This function returns the attribute of a network provided a message from the
    cmd prompt.
    
    Args:
        net_stat (str): Status message regarding device internet status using
        cmd prompt results.
        attr (str): Attribute needed to attain from the status message.
    
    Returns:
        str: A line of message for the network attributes of this computer.
    """
    attr_msg = str(net_stat)[str(net_stat).find(attr):]
    return attr_msg[attr_msg.find(":") + 2: attr_msg.find(r"\r\n")]

def get_net_status_check():
    """
    This function returns a message for the internet portion of device status
    check.

    Returns:
        str: A line of message for the network status of this computer.
    """
    net_stat_checker = r"netsh wlan show interfaces"
    net_stat_result = subprocess.check_output(net_stat_checker)
    wifi_name = gl_ds.get_global_attr('wifi_name')
    net_notif_msg = ""
    if not b"disconnected" in net_stat_result:
        net_ssid = get_net_attribute(net_stat_result, "SSID")
        net_name = get_net_attribute(net_stat_result, "Name")
        net_notif_msg = (
            f"For now, this computer is connected to {net_name}: "
            f"{net_ssid}."
        )
    elif not wifi_name is None:
        net_connect_cmd = f"netsh wlan connect name={wifi_name}"
        subprocess.run(net_connect_cmd)
        net_notif_msg = f"I'll connect this offline computer to {wifi_name}."
    return net_notif_msg

def get_battery_status_check():
    """
    This function returns a message for the internet portion of device status
    check.

    Returns:
        str: A line of message for the battery status of this computer.
    """
    def convert_time_format(seconds):
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return f'{hours} hr {minutes} min {seconds} sec'

    battery_stat = psutil.sensors_battery()
    battery_percent = battery_stat.percent
    battery_plug = "charging" if battery_stat.power_plugged else "not charging"
    battery_time = "can, in my calculation, last another "
    battery_time += convert_time_format(battery_stat.secsleft)
    
    if battery_plug == "charging":
        return f"Your battery ({battery_percent}%) is {battery_plug}."
    else:
        return f"Your battery ({battery_percent}%) {battery_time}."

def push_pc_stat_notification():
    """
    This function pushes notifications to the client regarding a periodic event 
    about the device status checkup.
    """
    network_stat = get_net_status_check()
    battery_stat = get_battery_status_check()
    message_subject = f'Your Device Tracing Status'
    message_body = f"{network_stat}\n{battery_stat}"
    message_xml = f"""
    <toast launch="app-defined-string">
    
        <header
            id = "device"
            title = "Device Notifications"
            arguments = ""
        />
        
        <visual>
            <binding template="ToastGeneric">
                <text hint-maxLines="1">{message_subject}</text>
                <text>{message_body}</text>
                <text placement="attribution">Via Project L.</text>
                <image placement="appLogoOverride" hint-crop="circle" \
                    src="{ICON_PATH}"/>
            </binding>
        </visual>

        <audio src="ms-winsoundevent:Notification.Mail"/>
    </toast>
    """
    message_doc = dom.XmlDocument()
    message_doc.load_xml(message_xml)
    notifier.show(notification.ToastNotification(message_doc))
    notif_tts("Hi, here is a device status update!")

def get_event_notification(event_properties):
    """
    This function serves to format the contents of a notification
    based on the given properties of an event.

    Args:
        event_properties (tuple): A tuple whose first element is an XML 
        string representing a row in the SQL database of events that 
        conveys information about an upcoming event, and the second being
        the total length of the notification message excluding XML labeling.
    
    Returns:
        tuple: A tuple containing the notification message and its length.
    """
    prop_dict = {k:v for k, v in zip(pl_db.events_col_names, event_properties)}
    event_contents = f'{prop_dict["event_type"]}: {prop_dict["event_name"]}'
    event_timing = ''
    if prop_dict["event_hr"] != -1:
        event_timing = f' at {prop_dict["event_hr"]}:{prop_dict["event_min"]}'
    msg_title = (
        f'Lip (Reminder): Upcoming {prop_dict["event_type"]}:'
        f'{prop_dict["event_name"]}'
    )
    msg_body = f'Your {event_contents} is happening {event_timing}!'
    message_xml = f"""
    <toast launch="app-defined-string">
    
        <header
            id = "events"
            title = "Event Notifications"
            arguments = ""
        />
        
        <visual>
            <binding template="ToastGeneric">
                <text hint-maxLines="1">{msg_title}</text>
                <text>{msg_body}</text>
                <text placement="attribution">Via Project L.</text>
                <image placement="appLogoOverride" hint-crop="circle" \
                    src="{ICON_PATH}"/>
            </binding>
        </visual>

        <audio src="ms-winsoundevent:Notification.Mail"/>
    </toast>
    """
    return message_xml, len(msg_title + msg_body)

def push_event_notification(current_time, distance, tbl_name = 'events'):
    """
    This function pushes notifications to the client for events that
    are DISTANCE minutes away from the given CURRENT_TIME.

    Args:
        current_time (datetime object): A datetime object representing the 
        current time
        distance (int): An integer representing the range of time from 
        CURRENT_TIME in minutes which the events will be notified for the user
    """    
    all_events = pl_db.get_all_events(tbl_name)
    def time_distance_filter(event):
        event_time = datetime.datetime(
            event[4], 
            event[5], 
            event[6], 
            0 if event[7] == "NULL" else event[7], 
            0 if event[8] == "NULL" else event[8]
        )
        time_delta = (event_time - current_time)
        return 0 <= time_delta.seconds / 60 <= distance and not time_delta.days
    
    filtered_events = filter(time_distance_filter, all_events)
    for event in filtered_events:
        message_info = get_event_notification(event)
        message_doc = dom.XmlDocument()
        message_doc.load_xml(message_info[0])
        duration = message_info[1] // 25 + 3
        notification.ToastNotification.ExpirationTime = duration
        notifier.show(notification.ToastNotification(message_doc))
        notif_tts("Hi, " + str(message_info[1]))
        notification.ToastNotification.ExpirationTime = EXPIRATION_TIME

def push_pomodoro_notification(cycle_cnt, msg_body, interval):
    """
    This function pushes notifications to the client regarding events that 
    occurred in the pomodoro clock.

    Args:
        repetition_cnt (int): An integer representing the number of times the 
        current pomodoro has activated.
        message_body (str): A string representing the body of message for the 
        pomodoro notification.
        interval (float): A floating point representing the amount of time this
        function will count for in a second interval.
    """
    if interval < 1: time_xml = f"{int(interval * 60)} seconds!"
    else: time_xml = f"{int(interval)} minutes!"
    msg_title = f'Lip (Clock): Your Pomodoro Notification'
    message_xml = f"""
    <toast launch="app-defined-string">
    
        <header
            id = "pomodoro"
            title = "Pomodoro Notifications"
            arguments = ""
        />
        
        <visual>
            <binding template="ToastGeneric">
                <text hint-maxLines="1">{msg_title}</text>
                <text>Repetition: {cycle_cnt}\n{msg_body}, {time_xml}</text>
                <text placement="attribution">Via Project L.</text>
                <image placement="appLogoOverride" hint-crop="circle" \
                    src="{ICON_PATH}"/>
            </binding>
        </visual>

        <audio src="ms-winsoundevent:Notification.Mail"/>
    </toast>
    """
    message_doc = dom.XmlDocument()
    message_doc.load_xml(message_xml)
    notifier.show(notification.ToastNotification(message_doc))
    notif_tts("Hi, Your Pomodoro Clock has been updated!")

def from_notif_push_survey(homescreen, is_short = False):
    """
    Method to push the survey notifications and launch the survey window.

    Args:
        homescreen (tK.tk): The homescreen of current management system.
    """
    survey_title = "Check-in"
    if is_short:
        survey_title = "Instant Check-in"
    msg_title = f"Lip (Survey): {survey_title} ready!"
    msg_body = "ฅ(=･ω･=)ฅ \n    Another survey has been prepared."
    notifString = f"""
    <toast launch = "app-defined-string">

        <header
            id = "surveys"
            title = "Survey Notification"
            arguments = ""
        />

        <visual>
            <binding template="ToastGeneric">
                <text hint-maxLines="1">{msg_title}</text>
                <text>{msg_body}</text>
                <text placement="attribution">Via Project L.</text>
                <image placement="appLogoOverride" hint-crop="circle" \
                    src="{ICON_PATH}"/>
            </binding>
        </visual>
        <audio src="ms-winsoundevent:Notification.Mail"/>
    </toast>
    """
    xDoc = dom.XmlDocument()
    xDoc.load_xml(notifString)
    survey_notif = notification.ToastNotification(xDoc)
    #survey_screen = gui.SurveyScreen(homescreen, is_short = is_short)
    notifier.show(survey_notif)
    notif_tts(f"Hi, here is a {survey_title} I just prepared!")
    #survey_screen.mainloop()

def push_survey_notif(homescreen, is_short = False):
    from_notif_push_survey(homescreen, is_short)
    homescreen.push_survey_action(is_short)

def push_interventions(row):
    intervention_docs = in_ag.get_intervention_texts(row)
    for intervention_doc in intervention_docs:
        message_doc = dom.XmlDocument()
        message_doc.load_xml(intervention_doc[0])
        notifier.show(notification.ToastNotification(message_doc))
        time.sleep(len(intervention_doc[1]) / 11)
        notif_tts(intervention_doc[1])

### Deprecated ###
def __push_survey_notif_btn(homescreen, is_short = False):
    """
    Method to push the survey notifications and launch the survey window.

    Args:
        homescreen (tK.tk): The homescreen of current management system.
    """
    survey_title = "Check-in"
    if is_short:
        survey_title = "Instant Check-in"
    msg_title = f"Lip (Survey): {survey_title} ready!"
    msg_body = "ฅ(=･ω･=)ฅ \n    Another survey has been prepared."
    notifString = f"""
    <toast launch = "app-defined-string">

        <header
            id = "surveys"
            title = "Survey Notification"
            arguments = ""
        />

        <visual>
            <binding template="ToastGeneric">
                <text hint-maxLines="1">{msg_title}</text>
                <text>{msg_body}</text>
                <text placement="attribution">Via Project L.</text>
                <image placement="appLogoOverride" hint-crop="circle" \
                    src="{ICON_PATH}"/>
            </binding>
        </visual>
        <audio src="ms-winsoundevent:Notification.Mail"/>
        <actions>
                
            <action
                content="Launch Survey"
                arguments=""
                activationType="foreground"/>
        </actions>
    </toast>
    """
    xDoc = dom.XmlDocument()
    xDoc.load_xml(notifString)
    survey_notif = notification.ToastNotification(xDoc)
    survey_task = 1
    def push_survey(sender, _):
        nonlocal survey_task
        survey_screen = gui.SurveyScreen(is_short = is_short)
        survey_task = survey_screen
        survey_screen.mainloop()
    activated_token = survey_notif.add_activated(push_survey)
    notifier.show(survey_notif)
    notif_tts(f"Hi, here is a {survey_title} I just prepared!")
    while survey_task:
        try:
            if survey_task == 1:
                time.sleep(10)
                if (survey_task == 1):
                    survey_task = None
            elif (survey_task.state() == 'normal'):
                print("LOG: enter wait")
                time.sleep(10)
        except:
            break;
    survey_notif.remove_activated(activated_token)
