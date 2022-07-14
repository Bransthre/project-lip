#Packages
import subprocess
import psutil
import global_database
import winsdk.windows.ui.notifications as notification
import winsdk.windows.data.xml.dom as dom
from global_database import ICON_PATH

#Establishing notification agent
notification_manager = notification.ToastNotificationManager
notifier = notification_manager.create_toast_notifier()

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
    wifi_name = global_database.get_global_attr('wifi_name')
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
    notif_tts("Hi, here is a device status update!")
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
    notification.ToastNotification.ExpirationTime = 20
    notifier.show(notification.ToastNotification(message_doc))
