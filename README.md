# project-lip
An Incomplete Introduction to this project.\
You will see a lot of things in parentheses, which shows the status quo of the project, as I'm only able to work on this project during parts of break between semesters.

## Main (vague) Objective of this Project, and Project Statement
Under constrained knowledge and abilities, create (the foundations of) a virtual personal intelligent assistant that can offer mental care via EMI messages to prevent burnout, which is a prevalent problem for 21st century and especially the university I study at.\
The three main challenges this project attempts to overcome is hugely inspired by another report in 2003, "Affective Computing: Challenges", which is a follow up from the report "Affective Computing":
1. How can an application communicate to its users?
2. How can emotional data be sampled from users during work?
3. How can the data of a user's current status and amount of activity in a day be parametrized to predict a user's current emotion?

While a README is not the best place to address the project's solution, I will briefly address them here, and attach a finished article later when at spare time.

The application communicates to its users via the idea of EMI (which was chosen after reviewing some related research); it sends messages that offer specific hints or advices (which is not its best version now) to ``navigate'' users onto a more mentally active, less troubled state (defined as positive valence, nonnegative activation).

The application samples data of a user's current status and degree of activity in a day primarily via survey interfaces (represented in GUI), and new integrations to sample emotion-related data from text and facial expression is currently being developed.\
The facial expression recognition Google Colab notebook is currently very chaotic, but put [here](https://colab.research.google.com/drive/1RwUzk1kRx_CIAJGToNWCTRNeadY6mpOV?usp=sharing) outside the repository.\
Its best performance on the FER 2013 dataset is currently at 68% validation accuracy.

The application predicts a user's current emotion as it uses user-labeled data (labeled during a proportion of surveys), where the feature of each datapoint is noted by the aforementioned parameteres (mainly degree of activity, and time), and the response variable is a two dimensional point of emotion formed by its valence and activation based on the Dimensional Theory of Emotion.\
Alternative approach involves a hierarchical classifier where emotions are classified first into seven larger categories, but that would require far more data than what user-labeled datasets can provide.

## Roles of Each Folders
`databases`: data used for settings customization and affective computing related mesaures.\
`deprecated`: some infrastructures and architectures that were deprecated for obsolescence.\
`function_backend`: most of the backend files are gathered here. Among which, there are some hand-built implementations of SQL <-> Pandas data conversion and C4.5 Decision Trees that can be further expanded into a Random Forest Classifier. Machine learning infrastructures in this repository (except hte notebook) are built primarily during freshman year upon self-studying and referencing related literature.


## Why ``Lip''
Lip is the fundamental element of human verbal interaction, so the project is equivalent of a foundational work in my understanding of HCI (as I have not the opportunity to enroll in related courseworks yet).

