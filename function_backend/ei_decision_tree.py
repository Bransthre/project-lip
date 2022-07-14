"""
This file implements the overall architecture for C4.5 algorithm's decision-
making computations and algorithm, via implementing the DecisionTree object.
"""

#Packages
from . import ei_database as ei_ds
from . import global_database as gl_ds
import random as random
import pandas as pd
import scipy.stats as st
import numpy as np
import math
np.seterr(all="ignore")

#Classes
class DecisionTree():
    """
    This class represents a decision tree to be used for the implementation of 
    the C4.5 algorithm.
    """
    
    def __init__(self, min_sample = 2, max_depth = None, verbose = False):
        """
        This function is the consturctor of a DecisionTree object.
        
        Args:
            min_sample (int): The minimum sample needed for a training set to be
            partitionable.
            max_depth (int): The maximum depth allowed for the DecisionTree 
            object.
            verbose (Boolean): A boolean value indicating whether the verbose
            function should be opened or not.
        """
        self.children = {}
        self.decision = None
        self.split_attr = None
        self.threshold = None
        self.min_sample = min_sample
        self.max_depth = max_depth
        self.verbose = verbose      

    def fill_decision_tree(
            self, training_set,
            curr_depth = 1, sample_cls_name = 'emotion'
        ):
        """
        This function fills a decision tree object based on the provided 
        dataset.
        
        Args:
            training_set (DataFrame): a pandas Dataframe of the training
            set, but will be used for partition when filling the decision tree.
            curr_depth (int): the current depth of a decision tree.
            sample_cls_name (str): The column name of class that the decisions 
            trees will classify objects for.
        """
        sample_class = training_set[sample_cls_name]
        if curr_depth == self.max_depth or len(training_set) < self.min_sample:
            self.decision = get_majority_class(sample_class)
        elif len(sample_class.unique()) == 1:
            self.decision = get_majority_class(sample_class)
        else:
            decision_params = get_best_split_attr(training_set, sample_cls_name)
            self.split_attr = decision_params[0]
            self.threshold = decision_params[1]
            branch_names = decision_params[2]
            all_branch_names = decision_params[3]
            
            if self.verbose:
                print(
                    f'created tree with split {self.split_attr}, \
                    threshold {self.threshold}, \
                    depth {curr_depth} / {self.max_depth}'
                )
                print('\n========\n')
            
            for v in all_branch_names:
                inds = branch_names == v
                if len(training_set[inds]) > 0:
                    self.children[v] = DecisionTree(
                        self.min_sample, 
                        self.max_depth, 
                        self.verbose
                    )
                    self.children[v].fill_decision_tree(
                        training_set[inds],
                        curr_depth + 1, 
                        sample_cls_name
                    )
                else:
                    self.children[v] = DecisionTree(
                        self.min_sample, 
                        1,
                        self.verbose
                    )
                    self.children[v].fill_decision_tree(
                        training_set,
                        1, 
                        sample_cls_name
                    )
    
    def post_prune(
            self, training_set,
            confidence_lvl = 0.15, sample_class_name = 'emotion'
        ):
        """
        This function performs a bottom-up postpruning for the Decision Tree
        object based on the C4.5 implementation. Due to the post-pruning
        measure being overly aggressive and the satisfaction with processing
        time without help from post-pruning, this function is not used.
        Note: It was recommended to use a confidence level of 0.25 in some 
        papers, and that option turned to be quite aggressive.
        
        Args:
            training_set (DataFrame): a pandas DataFrame representing a SQL
            database of testing set data.
            confidence_lvl (double): The confidence level used for the 
            confidence interval, in between 0 and 1. A 75% confidence interval
            is represented with the value of 0.75, which is default.
            sample_class_name (str): The column name of class that the decisions 
            trees will classify objects for.
        """
        
        z = st.norm.ppf(0.5 * (1 - confidence_lvl))
        confid_lvl_errors = np.array([])
        testing_class = training_set[sample_class_name]
        node_freqs = testing_class.value_counts(normalize = True)
        node_max_cls = node_freqs.idxmax()
        node_min_error = 1 - node_freqs.max()
        training_set_length = len(training_set.index)
        
        for attr_val, b in self.children.items():
            branch_attr = training_set[self.split_attr]
            if not pd.api.types.is_string_dtype(branch_attr):
                branch_attr = branch_attr >= self.threshold
                branch_attr[branch_attr] = "greater"
                branch_attr[branch_attr == False] = "less"
            branch_test_inds = branch_attr == attr_val
            branch_training_set = training_set.loc[branch_test_inds]
            n = len(branch_training_set)
            if n == 0:
                return
            
            f = 1
            b.post_prune(branch_training_set, confidence_lvl, sample_class_name)
            branch_sample_class = branch_training_set[sample_class_name]
            child_freqs = branch_sample_class.value_counts(normalize = True)
            if node_max_cls in child_freqs.index.values:
                f -= child_freqs[node_max_cls]
            z_sq = z ** 2
            confid_lvl_upp_est = (
                f + z_sq / (2 * n) + 
                z * math.sqrt(f / n - (f ** 2) / n + z_sq / (4 * (n ** 2)))
            ) / (1 + z_sq / n) * (n / training_set_length)
            confid_lvl_errors = np.append(confid_lvl_errors, confid_lvl_upp_est)
        
        if self.verbose:
            print(f"LOG: Pruning Error: {np.sum(confid_lvl_errors)}")
        if node_min_error < np.sum(confid_lvl_errors):
            self.decision = node_max_cls
            self.children = {}
            self.split_attr = None
            self.threshold = None

    def predict(self, sample):
        """
        This function returns the result of the prediction/classification for
        the provided sample using the decision tree.
        
        Args:
            sample (Series): A pandas Series that stands for the sample being
            predicted/classified for.
        
        Returns:
            str: The class that this sample is predicted/classified to.
        """
        
        if self.verbose:
            print(f"""
            children: {[k for k in self.children]}, 
            attribute: {self.split_attr},
            threshold: {self.threshold},
            decision: {self.decision},
            """)
        
        if self.decision is not None:
            return self.decision
        
        attr_val = sample[self.split_attr]
        if isinstance(attr_val, str):
            if attr_val in self.children.keys():
                child = self.children[attr_val]
            else:
                child = random.choice(list(self.children.items()))[1]
        else:
            assert self.threshold is not None, f"""
            attr_val: {attr_val}
            children: {[k for k in self.children]}, 
            attribute: {self.split_attr},
            threshold: {self.threshold},
            decision: {self.decision}
            """
            if attr_val > self.threshold and 'greater' in self.children.keys():
                child = self.children['greater']
            else:
                child = self.children['less']
        
        return child.predict(sample)

"""
Utility Functions that would be employed by methods in the DecisionTree class:
"""

def get_majority_class(sample_col):
    """
    This function returns the majority class of an attribute column. If there
    are multiple, return one of the majority values randomly.
    
    Args:
        sample_col (Series): A pandas Series that represents a column to find
        the majority value from.
        
    Returns:
        any: the majority value of a column.
    """
    if len(sample_col) == 0: return None
    freq = sample_col.value_counts()
    majorities = freq.keys()[freq == freq.max()]
    return majorities[random.randint(0, len(majorities) - 1)]

def get_entropy(frequencies):
    """
    This function returns the entropy of a state given a probability model
    FREQUENCY; represented by an array of probability distribution.
    
    Args:
        frequencies (series): A pandas Series whose contents sum up to 1
    
    Returns:
        double: the entropy of the state given the probability model argument.
    """
    return -1 * sum([f * math.log(f, 2) for f in frequencies if f > 0])

def get_attr_entropy(sample_attr, sample_class):
    """
    This function returns the entropy of a state if a sample space is being
    partitioned based on the values of an attribute.
    
    Args:
        sample_attr (series): A pandas Series representing the attribute column
        of the database.
        sample_class (series): A pandas Series representing the class column of
        the database.
    
    Returns:
        double: the entropy of the state given the portions of database for 
        partitioning.
    """
    def get_entropy_by_name(name):
        indices = sample_attr == name
        attr_classes = sample_class[indices]
        class_freq = get_entropy(attr_classes.value_counts(normalize = True))
        attr_coeff = len(sample_attr[indices]) / len(sample_attr)
        return class_freq * attr_coeff
    
    return sum([get_entropy_by_name(name) for name in sample_attr.unique()])

def get_gain_ratio(sample_attr, sample_class):
    """
    This function returns the gain ratio of partitioning a training set with an
    attribute according to the C4.5 algorithm standards.
    
    Args:
        sample_attr (series): A pandas Series representing the attribute column
        of the database.
        sample_class (series): A pandas Series representing the class column of
        the database.
    
    Returns:
        double: the gain ratio of the state given the portions of database for 
        partitioning.
    """
    class_freq = sample_class.value_counts(normalize = True)
    info_emo = get_entropy(class_freq)
    info_attr_emo = get_attr_entropy(sample_attr, sample_class)
    info_gain = info_emo - info_attr_emo
    splt_entropy = get_entropy(sample_attr.value_counts(normalize = True))
    if splt_entropy == 0: splt_entropy = 1
    gain_ratio = info_gain / splt_entropy
    
    return gain_ratio

def get_best_split_attr(train_set, sample_cls_name):
    """
    This function finds the best attribute to partition a training set by 
    based on which method of partitioning would grant the maximum gain ratio.
    
    Args:
        sample_data (DataFrame): A pandas DataFrame representing information
        captured from the SQL database
        sample_cls_name (str): The column name of class that the decisions trees
        will classify objects for.
        
    Returns:
        tuple: A tuple of the best attribute to split by, the threshold of the
        attribute if continuous, and the attribute column of the database, which
        is formatted into a string format if the attribute is continuous.
    """
    branch_names = all_branch_names = pd.Series(dtype='str')
    attr_names = train_set.keys()[train_set.keys() != sample_cls_name]
    sample_class = train_set[sample_cls_name]
    max_gain_ratio = 0
    best_split_attr = None
    best_threshold = None
    
    for attr in attr_names:
        if pd.api.types.is_string_dtype(train_set[attr]):
            attr_gain_ratio = get_gain_ratio(train_set[attr], sample_class)
            if attr_gain_ratio > max_gain_ratio or best_threshold is None:
                best_split_attr = attr
                best_threshold = None
                max_gain_ratio = attr_gain_ratio
                branch_names = train_set[attr][train_set[attr] != None]
                all_branch_names = branch_names.unique()
        else:
            sorted_data = train_set.sort_values(attr)
            sorted_attr = sorted_data[attr]
            sorted_class = sorted_data[sample_cls_name]
            for i in range(0, len(sorted_attr) - 2):
                if sorted_class.iat[i] != sorted_class.iat[i + 1]:
                    curr_threshold = (sorted_attr.iat[i] + \
                        sorted_attr.iat[i + 1]) / 2
                    val_lbls = train_set[attr] > curr_threshold
                    val_lbls[val_lbls] = "greater"
                    val_lbls[val_lbls == False] = "less"
                    attr_gain_ratio = get_gain_ratio(val_lbls, sample_class)
                    if attr_gain_ratio > max_gain_ratio or best_threshold is None:
                        best_split_attr = attr
                        best_threshold = curr_threshold
                        max_gain_ratio = attr_gain_ratio
                        branch_names = val_lbls[val_lbls != None]
                        all_branch_names = branch_names.unique()
    
    return (best_split_attr, best_threshold, branch_names, all_branch_names)

def train_model(target_class, verbose = False, train_ratio = 0.8):
    if verbose:
        print("===================================================")
    original_sample_data = ei_ds.get_sample_data(target_class = target_class)
    sample_data = increase_database_variance(original_sample_data)
    TRAIN_RATIO = train_ratio
    training_set = sample_data.sample(frac = TRAIN_RATIO)
    testing_set = sample_data.drop(training_set.index)
    params = get_optimized_param(training_set, target_class, verbose = verbose)
    model = DecisionTree(max_depth = params[0])
    model.fill_decision_tree(
        training_set,
        sample_cls_name = target_class
    )
    model.post_prune(
        training_set,
        params[1] / 100, 
        sample_class_name=target_class
    )
    y = testing_set[target_class]
    x = testing_set.drop(target_class, axis = 1)
    accuracy = get_accuracy(model, x, y)
    if verbose:
        print(f"Testing set accuracy: {accuracy}")
    #print(f"RESULT_VERBOSE: Testing set accuracy: {accuracy}")
    return model

def get_optimized_param(training_set, target_class, verbose = False):
    DEPTH = random.randint(3, 7)
    CONF_LVL = random.randint(20, 80)
    best_depth, best_conf = DEPTH, CONF_LVL
    current_best = -1
    cwv = "depth"
    conf_increm = 10
    if verbose:
        print(f"Now tuning model for class: {target_class}")
    for epoch in range(10):
        model = DecisionTree(max_depth = DEPTH)
        real_training_set = training_set.sample(frac = 0.9) #9-fold Cross V.
        validation_set = training_set.drop(real_training_set.index)
        model.fill_decision_tree(
            real_training_set,
            sample_cls_name = target_class
        )
        if CONF_LVL:
            model.post_prune(
                real_training_set,
                CONF_LVL / 100,
                sample_class_name = target_class
            )
        y = validation_set[target_class]
        x = validation_set.drop(target_class, axis = 1)
        accuracy = get_accuracy(model, x, y)
        if verbose:
            print(
                f"Epoch {epoch + 1}: \n"
                f"verbose: depth {DEPTH}, confidence level of {CONF_LVL}%, "
                f"with an accuracy of {accuracy}"
            )
        if cwv == "depth":
            if current_best <= accuracy:
                best_depth = DEPTH
                current_best = accuracy
                DEPTH += 1
            else:
                DEPTH -= 1
                cwv = "conf"
        elif cwv == "conf":
            CONF_LVL += (int(current_best <= accuracy) - 0.5) * 2 * conf_increm
            CONF_LVL = min(max(0, CONF_LVL), 100)
            if current_best <= accuracy:
                conf_increm /= 2
                best_depth, best_conf = DEPTH, CONF_LVL
                current_best = accuracy
    if verbose:
        print(
            f"Best pair of parameters was depth {best_depth}, with a "
            f"confidence level {best_conf}%. This accuracy was {current_best}"
        )
    
    #print(
    #    "RESULT_VERBOSE: "
    #    f"Best pair of parameters was depth {best_depth}, with a "
    #    f"confidence level {best_conf}%. This accuracy was {current_best}"
    #)
    return best_depth, best_conf, current_best

def increase_database_variance(emo_df, multiple = 5):
    random_interval = gl_ds.get_global_attr("checkin_interval")
    varied_emo_df = emo_df.copy().sample(
        frac = multiple,
        replace = True,
        ignore_index = True
    )
    varied_emo_df['log_time'] = varied_emo_df['log_time'].apply(
        lambda x: x + random.randint(-1 * random_interval, random_interval)
    )
    for classes in ['social_deg', 'work_deg', 'rest_deg']:
        varied_emo_df[classes] = varied_emo_df[classes].apply(
            lambda x: x + random.randint(-40, 40) / 100
        )
    return varied_emo_df
    
def get_accuracy(model, x, y):
    predicted = x.apply(model.predict, axis = 1)
    predicted, y = predicted.align(y, axis = 0, copy = False)
    accuracy = (predicted == y).mean()
    return accuracy
