# 2 types of measurements:

- temperature ramp
- temperature steps

# Always:

Need a log --> quantities (temperature, lockin output) should be measured continuously and saved in a log file (with threading/queueing, probably queueing is better)
And plotted in real time (for further version, have the possibility to change plot between time/temperature/something else dynamically?)

Data from config need to be in a header.

Temps en valeur absolue / enregistrer en format exponentiel / delimiter = , (dans np.savetxt)
extension CSV --> colorie les colonnes


# Config file:

  Lakeshore Channel: 1
  Ramp: yes/no
  Log_delay: 1s or different
  For Ramp: ramp_start_point - ramp_end_point - ramp_speed - ramp_delay --> add possibility to have multiple arrays (sequence)
  For Steps:  start point - end point - number of steps --> add possibility to have multiple arrays? (sequence)
              Averaging (in s)- 


# Steps for Ramp:

  Set temperature to starting point
  Wait for stable (set time? Condition?)
  Start the ramp
  Loop to save the data with a set delay --> Ends when the ramp is complete (condition?)


# Steps for steps:

  Loop over the temperature array:
    Set temperature to starting point
    Wait for stable
    Loop to get the data, average it over the averaging parameter
    Save the data



Objectif: mesurer et plot en temps réel les datas et la température en fonction du temps
          sauvegarder dans le log
