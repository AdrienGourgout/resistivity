val:
[1] --> output amplitude/frequency
[1][0][1] --> frequency
[1][0][2] --> amplitude




[2] --> DC
[3] --> x
[4] --> y
[5] --> r
[6] --> theta



Plan:

- Update dictionnaries: Instruments_dict/Variables_dict/Variables
- Makes API for each instruments --> Grab all relevant variables and imput them in the Variables_dict
- Instruments creation: Ask about which quantity is relevant (main window, create pop-up), then load the instrument (log_measure) and make the Variables_dict associated to it (log_measure/window).

 
- Main Window:

Load normal, remove the "variable name" thing? How to differenciate if several same instruments? Add 1,2,3?
When load is pressed, open the sub-window to choose what to measure.
Have checkboxes depending on the instrument, and a validate button.

- log_measure:

Make sure connexion instrument class is instanciated once and only once for each instrument.
Connexion should be in the __init__ of Instruments_reading (do we do one separate for each instrument? Or one file with several classes?)
In the data_dict, put in a dictionnary for each instruments, which will have variable names as keys and variable values as values

- Main window:

Change the graph window. Should have a scroll menu for each instrument, opening another one with all the variables for that instrument that were loaded.
Maybe have a checkbox system, and checking will open another unchecked row automatically? Predetermined number seems silly

