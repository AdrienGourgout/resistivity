from resistivity.Model.resistivity import Resistivity
from time import sleep
import pyqtgraph as pg


Meas = Resistivity('ASRL4::INSTR', )
Meas.start_logging()

# PlotWidget = pg.plot(title="Plotting T vs t")
# while Meas.log_thread.is_alive():
#     PlotWidget.plot(Meas.exptime, Meas.temperature_log, clear=True)
#     pg.QtGui.QGuiApplication.processEvents()
#     sleep(.1)


sleep(15)

Meas.stop_logging()