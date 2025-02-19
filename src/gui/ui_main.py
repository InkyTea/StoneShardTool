import sys
import threading
from PyQt5 import QtCore
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QApplication, QMainWindow
from gui import Ui_untitled
from PyQt5.QtCore import QObject, pyqtSignal
from folder_backup_restore import AutoBackup
# 重定向print输出
class EmittingStream(QObject):
    textWritten = pyqtSignal(str)

    def write(self, text):
        self.textWritten.emit(str(text))

    def flush(self):
        pass

class Ui_Main():
    def __init__(self) -> None:
        self.app = QApplication(sys.argv)
        self.main_win = QMainWindow()
        self.ui = Ui_untitled.Ui_MainWindow()
        self.ui.setupUi(self.main_win)
        self.auto_backup = AutoBackup()
        self.add_event()
        self.init_set()
        self.main_win.show()
        sys.exit(self.app.exec_())

    def init_set(self):
        self.stdout_redirect = EmittingStream()
        self.stdout_redirect.textWritten.connect(self.ui.plainTextEdit.insertPlainText)
        sys.stdout = self.stdout_redirect
    
    def add_event(self):
        self.ui.pushButton.clicked.connect(self.onBtnClickStart)
        self.ui.pushButton_2.clicked.connect(self.onBtnClickStart1)

    def onBtnClickStart(self, _):
        t = threading.Thread(target=self.auto_backup.main)
        t.start()

    def onBtnClickStart1(self, _):
        t = threading.Thread(target=self.auto_backup.upload)
        t.start()