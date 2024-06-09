from PyQt5.QtWidgets import QApplication
from resistivity.View.main_window import MainWindow
from resistivity.Experiment.log_measure import LogMeasure
from qt_material import apply_stylesheet
import os

log = LogMeasure('Config.yml')
log.load_config()

app = QApplication([])
win = MainWindow(log)

win.show()
apply_stylesheet(app, theme='dark_teal.xml')
app.exec()