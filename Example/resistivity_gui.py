from PyQt5.QtWidgets import QApplication
from resistivity.View.mainwindow import MainWindow
from resistivity.Model.log_measure import LogMeasure
from qt_material import apply_stylesheet

resist = LogMeasure('Config.yml')
resist.load_config()

app = QApplication([])
win = MainWindow(resist)

win.show()
apply_stylesheet(app, theme='dark_teal.xml')
app.exec()
