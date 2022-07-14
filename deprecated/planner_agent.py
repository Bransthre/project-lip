#Packages
import datetime
from notif_agent import notif_tts
import planner_database as pl_db
import winsdk.windows.ui.notifications as notification
import winsdk.windows.data.xml.dom as dom
from global_database import ICON_PATH

#Establishing notification agent
notification_manager = notification.ToastNotificationManager
notifier = notification_manager.create_toast_notifier()

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
    notif_tts("Hi, " + msg_body)
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
    notif_tts("Hi, Your Pomodoro Clock has been updated!")
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
    notification.ToastNotification.ExpirationTime = 15
    notifier.show(notification.ToastNotification(message_doc))
