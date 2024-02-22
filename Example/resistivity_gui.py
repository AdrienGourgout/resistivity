from PyQt5.QtWidgets import QApplication
from resistivity.View.mainwindow import MainWindow
from resistivity.Model.log_measure import LogMeasure
from qt_material import apply_stylesheet
import os

log = LogMeasure('Config.yml')
log.load_config()
log.load_instruments()

app = QApplication([])
win = MainWindow(log)

win.show()
apply_stylesheet(app, theme='dark_teal.xml')
app.exec()

# Important in case the user has not clicked on stop before closing the window
log.stop_logging()