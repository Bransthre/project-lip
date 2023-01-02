from . import ei_database as ei_ds
from . import ei_ml_detection as ei_dt
from . import global_database as gl_ds
import random
import datetime

def get_intervention_dialogues():
    dialogue_file = open(gl_ds.CWD + r'/function_backend/dialogue_eii.txt', encoding="utf-8")
    dialogue_lines = dialogue_file.readlines()
    dialogue_dict = {}
    curr_attr = ""
    for line in dialogue_lines:
        processed_line = line[:-1]
        if processed_line[0] == "@":
            curr_attr = processed_line[1:]
            dialogue_dict[curr_attr] = []
        else:
            dialogue_dict[curr_attr].append(gl_ds.transform_msg(processed_line))
    return dialogue_dict

def get_intervention_texts(row):
    data_row = ei_ds.convert_tuple_to_series(row)
    dialogue_lines = get_intervention_dialogues()
    return (
        get_notification_doc('Lip EI Unit:', emotion_interventions(data_row, dialogue_lines)),
        get_notification_doc('Lip EI Unit:', special_interventions(dialogue_lines))
    )

def emotion_interventions(row, custom_dict = None):
    print("DEBUG: currently dealing with emotion")
    print(f"{row} as row for prediction")
    if custom_dict is None:
        custom_dict = get_intervention_dialogues()
    model_emo = ei_dt.train_model(target_class = "emotion", verbose = True)
    emo_status = model_emo.predict(ei_dt.prepare_dataset("emotion", row))
    return custom_dict[emo_status[0]]

def special_interventions(custom_dict = None):
    print("DEBUG: currently dealing with special")
    fun_value = random.randint(1, 100)
    if 85 <= fun_value <= 90:
        return ['rr']
    elif fun_value == 99:
        return ['bb']
    today = datetime.datetime.today()
    data_status_today = ei_ds.get_today_data_properties()
    all_sp_intervents = []
    line_dict = get_intervention_dialogues()
    if 3 <= data_status_today['work_time'] < 5:
        all_sp_intervents.append(line_dict['work_3'][0])
    elif 5 <= data_status_today['work_time'] < 7:
        all_sp_intervents.append(line_dict['work_5'][0])
    elif 7 <= data_status_today['work_time'] < 9:
        all_sp_intervents.append(line_dict['work_7'][0])
    elif 9 <= data_status_today['work_time']:
        all_sp_intervents.append(line_dict['work_9'][0])
    if 7 <= today.hour <= 10:
        all_sp_intervents.append(line_dict['morning'][0])
    elif 12 <= today.hour <= 14:
        all_sp_intervents.append(line_dict['noon'][0])
    elif 17 <= today.hour <= 19:
        all_sp_intervents.append(line_dict['evening'][0])
    if 2 <= data_status_today['rest_num'] < 4:
        all_sp_intervents.append(line_dict['rest_2'][0])
    elif 4 <= data_status_today['rest_num']:
        all_sp_intervents.append(line_dict['rest_4'][0])
    if data_status_today['neg_val'] >= 3:
        all_sp_intervents.append(line_dict['neg_val'][0])
    if data_status_today['neg_act'] >= 3:
        all_sp_intervents.append(line_dict['neg_act'][0])
    return all_sp_intervents

def get_notification_doc(title, message):
    msg_body = 'Keep working on it!'
    if message:
        msg_body = random.choice(message)
    notif_doc_text = f"""
    <toast launch="app-defined-string">
    
        <header
            id = "device"
            title = "Device Notifications"
            arguments = ""
        />
        
        <visual>
            <binding template="ToastGeneric">
                <text hint-maxLines="1">{title}</text>
                <text>{msg_body}</text>
                <text placement="attribution">Via Project L.</text>
                <image placement="appLogoOverride" hint-crop="circle" \
                    src="{gl_ds.ICON_PATH}"/>
            </binding>
        </visual>

        <audio src="ms-winsoundevent:Notification.Mail"/>
    </toast>
    """
    return notif_doc_text, msg_body
