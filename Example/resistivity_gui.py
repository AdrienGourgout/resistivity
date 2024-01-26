from PyQt5.QtWidgets import QApplication
from resistivity.View.mainwindow import MainWindow
from resistivity.Model.resistivity import Resistivity

resist = Resistivity('Example\Config.yml')
resist.load_config()
resist.load_instruments()

app = QApplication([])
win = MainWindow(resist)

win.show()
app.exec()
