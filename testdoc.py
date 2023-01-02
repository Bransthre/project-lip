import function_backend.planner_database as planner_database
import datetime as datetime
import function_backend.ei_decision_tree as ei_dt
import function_backend.ei_database as ei_ds
import random
import function_backend.gui as gui
import function_backend.global_database as global_database
import threading
import function_backend.notif_agent as notif_agent
import function_backend.intervention_agent as in_ag

def test_planner_database():
    planner_database.database_setup("test_table")

    print(planner_database.get_all_events("test_table"))
    print("Expected empty table")
    planner_database.create_event("Test", "test category", "Testing", 
                                  2021, 12, 21, None, None, 
                                  tbl_name="test_table")
    print(planner_database.get_all_events("test_table"))
    print("expected: an event row")

    update_dict = {k: v for k, v in zip(
            planner_database.events_col_names[1:],
            ['Test 2', 'test category', 'Testing', 2021, 12, 21, 17, 50]
            )
        }
    planner_database.update_event(update_dict, "Test", None, 
                                  2021, 12, 21, None, None, 
                                  tbl_name="test_table")
    print(planner_database.get_all_events("test_table"))
    print("expected: an updated event row")
    planner_database.remove_event("Test 2", 
                                  2021, 12, 21, 17, 50, tbl_name="test_table")
    print(planner_database.get_all_events("test_table"))
    print("expected: an empty table")
    planner_database.clear_all_events("test_table")

    print("\n\nAll tests passed in test_planner_database\n\n")

def test_event_notification():
    planner_database.database_setup("test_table")
    planner_database.create_event("18:20", "test category", "Testing", 
                                  2021, 12, 21, 18, 20, tbl_name="test_table")
    planner_database.create_event("18:30", "test category", "Testing", 
                                  2021, 12, 21, 18, 30, tbl_name="test_table")
    planner_database.create_event("23:50", "test category", "Testing", 
                                  2021, 12, 21, 23, 50, tbl_name="test_table")
    print(planner_database.get_all_events("test_table"))

    notif_agent.push_event_notification(
        datetime.datetime(2021, 12, 21, 18, 0), 
        50, 
        tbl_name="test_table"
        )
    planner_database.clear_all_events("test_table")

    print("\n\nAll tests passed in test_event_notification\n\n")

def test_pomodoro():
    notif_agent.push_pomodoro_notification(1, "1", 1)
    print("\n\nAll tests passed in test_pomodoro\n\n")

def test_device_check():
    notif_agent.push_pc_stat_notification()
    print("\n\nAll tests passed in test_device_check\n\n")

def test_ei_decision_tree():
    print("Test ei decision agent starts")
    ei_ds.clear_all_logs("test_table")
    ei_ds.emo_tbl_setup("test_table")
    noise = lambda: random.randint(-5, 5) / 10
    rta = lambda: random.randint(100, 160)
    rtb = lambda: random.randint(140, 180)
    rtc = lambda: random.randint(150, 300)
    rtd = lambda: random.randint(100, 300)
    rda = lambda: max(1, random.randint(1, 3) + noise())
    rdb = lambda: min(5, random.randint(3, 5) + noise())
    day = lambda: min(6, round(random.randint(0, 6) + noise()))
    #'''
    today = datetime.datetime.now()
    print("creating data")
    for _ in range(16):
        ei_ds.create_entry('emo type a', rta(), day(), 'ucb', rda(), rda(), rda(), today, "test_table")
        ei_ds.create_entry('emo type b', rtb(), day(), 'ucla', rdb(), rdb(), rdb(), today, "test_table")
        ei_ds.create_entry('emo type c', rtc(), day(), 'uci', rdb(), rdb(), rda(), today, "test_table")
        ei_ds.create_entry('emo type d', rtd(), day(), 'ucsd', rdb(), rda(), rda(), today, "test_table")
    for _ in range(10):
        ei_ds.create_entry('emo type a', rta(), day(), 'ucla', rda(), rda(), rda(), today, "test_table")
        ei_ds.create_entry('emo type b', rtb(), day(), 'uci', rdb(), rdb(), rdb(), today, "test_table")
        ei_ds.create_entry('emo type c', rtc(), day(), 'ucsd', rdb(), rdb(), rda(), today, "test_table")
        ei_ds.create_entry('emo type d', rtd(), day(), 'ucb', rdb(), rda(), rda(), today, "test_table")
    for _ in range(4):
        ei_ds.create_entry('emo type a', rta(), day(), 'ucb', rda(), rda(), rda(), today, "test_table")
        ei_ds.create_entry('emo type b', rtb(), day(), 'uci', rdb(), rdb(), rdb(), today, "test_table")
        ei_ds.create_entry('emo type c', rtc(), day(), 'ucla', rdb(), rdb(), rda(), today, "test_table")
        ei_ds.create_entry('emo type d', rtd(), day(), 'ucsd', rdb(), rda(), rda(), today, "test_table")
    cutoff_col = 6
    sample_data = ei_ds.get_sample_data("test_table", cutoff_col)
    print(sample_data)
    for train_ratio in range(5, 10):
        for depths in range(3, 6):
            for conf in range(15, 105, 15):
                #Best parameter: ratio 7, depths 5
                decision_tree = ei_dt.DecisionTree(max_depth = depths, verbose = False)
                training_set = sample_data.sample(frac = train_ratio / 10)
                testing_set = sample_data.drop(training_set.index)
                ei_dt.DecisionTree.fill_decision_tree(decision_tree, training_set, training_set)
                ei_dt.DecisionTree.post_prune(decision_tree, training_set, confidence_lvl = conf)
                
                solutions = testing_set['emotion']
                test_params = testing_set.filter(ei_ds.emo_col_names[cutoff_col:])
                test_predictions = test_params.apply(lambda row: ei_dt.DecisionTree.predict(decision_tree, row), axis = 1)
                
                print(f'accuracy is {(solutions == test_predictions).mean()} for training_ratio {train_ratio}, depth {depths}, confidence level {conf}')

def test_setup_screen():
    global_database.global_tbl_setup()
    window = gui.SetupScreen()
    window.init_screen.mainloop()

def delete_tables():
    ei_ds.delete_tbl()
    ei_ds.delete_tbl("test_table")

def launch_survey_window():
    homescreen = gui.MainScreen()
    thread_notif = threading.Thread(
        target = lambda: notif_agent.push_survey_notif(homescreen)
    )
    thread_notif.start()
    homescreen.mainloop()

def launch_main_window():
    homescreen = gui.MainScreen()
    homescreen.mainloop()

'''
This is the old version of training and testing model.
def check_curr_data_complicacy():
    cutoff_col = 6
    curr_class = 'user_valence'
    for train_ratio in range(4, 5):
        for depth in range(3, 8):
            for conf in range(0, 95, 15):
            #conf = 0
                accuracy = 0
                num_iter = 7
                for _ in range(num_iter):
                    sample_data = ei_ds.get_sample_data("emotion_data", cutoff_col)
                    decision_tree = ei_dt.DecisionTree(max_depth = depth, verbose = False)
                    training_set = sample_data.sample(frac = 7 / 10)
                    testing_set = sample_data.drop(training_set.index)
                    ei_dt.DecisionTree.fill_decision_tree(decision_tree, training_set, sample_cls_name = curr_class)
                    if conf:
                        ei_dt.DecisionTree.post_prune(decision_tree, training_set, confidence_lvl = conf / 100, sample_class_name = curr_class)
                    solutions = testing_set[curr_class]
                    test_params = testing_set.filter(ei_ds.emo_col_names[cutoff_col:])
                    test_predictions = test_params.apply(lambda row: ei_dt.DecisionTree.predict(decision_tree, row), axis = 1)
                    accuracy += (solutions == test_predictions).mean()
                print(
                    f'for training ratio {7 / 10}, tree depth {depth}, post-prune confidence level {conf}%: '
                    f'accuracy is {round(accuracy / num_iter * 100, 2)}% '
                )
'''
def check_current_data_model():
    target_classes = ['user_valence', 'user_activation', 'emotion']
    for target_class in target_classes:
        print("Currently tuning on class: ", target_class)
        for tr in range(70, 90, 5):
            print(f"Training Ratio: {tr}%")
            model = ei_dt.train_model(target_class, True, tr / 100)

#execute section
'''import function_backend.ei_ml_detection as testing_package
testing_row = (100, 1, "Study Space", 2, 3, 3)
test_row = testing_package.prepare_dataset("emotion", ei_ds.convert_tuple_to_series(testing_row))
print(test_row)
model = testing_package.train_model("emotion", True)
print(model.predict(test_row))
print(in_ag.get_intervention_dialogues()[model.predict(test_row)[0]])
notif_agent.push_interventions(testing_row)'''
print(ei_ds.get_today_data_properties())