from PyQt5.QtWidgets import QApplication
from resistivity.View.mainwindow import MainWindow
from resistivity.Model.resistivity import Resistivity

resist = Resistivity('Config.yml')
resist.load_config()

app = QApplication([])
win = MainWindow(resist)

win.show()
app.exec()
