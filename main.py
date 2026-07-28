import sys
from PyQt6.QtWidgets import QApplication
from stopwatch_app import StopwatchApp

if __name__ == "__main__":

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = StopwatchApp()
    window.show()
    
    sys.exit(app.exec())