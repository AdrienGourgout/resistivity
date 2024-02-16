from PyQt5.QtWidgets import QApplication
from resistivity.View.mainwindow import MainWindow
from resistivity.Model.log_measure import LogMeasure

resist = LogMeasure('Config.yml')
resist.load_config()

app = QApplication([])
win = MainWindow(resist)

win.show()
app.exec()
