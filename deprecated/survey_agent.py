import time
from notif_agent import notif_tts
import gui
import winsdk.windows.ui.notifications as notification
import winsdk.windows.data.xml.dom as dom
from global_database import ICON_PATH

#Establishing notification agent
notification_manager = notification.ToastNotificationManager
notifier = notification_manager.create_toast_notifier()

def push_survey_notif(homescreen, is_short = False):
    """
    Method to push the survey notifications and launch the survey window.

    Args:
        homescreen (tK.tk): The homescreen of current management system.
    """
    survey_title = "Check-in Survey"
    if is_short:
        survey_title = "Instant Check-in Survey"
    msg_title = f"Lip (Survey): {survey_title} ready!"
    msg_body = "Another survey has been prepared ฅ(=･ω･=)ฅ."
    notif_tts(f"Hi, here is a {survey_title} I just prepared!")
    notifString = (
        f"""
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
                <image placement="appLogoOverride" hint-crop="circle" src="{ICON_PATH}"/>
            </binding>
        </visual>
    """
    r"""
        <audio src="ms-winsoundevent:Notification.Mail"/>

        <actions>
                
            <action
                content="Launch Survey"
                arguments=""
                activationType="foreground"/>
        </actions>

    </toast>
    """
    )
    xDoc = dom.XmlDocument()
    xDoc.load_xml(notifString)
    survey_notif = notification.ToastNotification(xDoc)
    survey_task = 1
    def push_survey(sender, lorem):
        nonlocal survey_task
        survey_screen = gui.SurveyScreen(is_short = is_short)
        survey_task = survey_screen
        survey_screen.mainloop()
    activated_token = survey_notif.add_activated(push_survey)
    notifier.show(survey_notif)
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
