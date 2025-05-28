import sys
import subprocess
import ctypes  # Windows 需要 ctypes 來暫停/繼續
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QLineEdit

class CommandRunner(QThread):
    output_signal = pyqtSignal(str)

    def __init__(self, command, user_input):
        super().__init__()
        self.command = command
        self.user_input = user_input
        self.process = None  # 用來保存 subprocess 進程

    def run(self):
        self.process = subprocess.Popen(
            self.command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, bufsize=1, universal_newlines=True
        )

        if self.user_input:
            self.process.stdin.write(self.user_input + "\n")
            self.process.stdin.flush()

        while self.process.poll() is None:  # 持續監控
            line = self.process.stdout.readline()
            if line:
                self.output_signal.emit(line.strip())
                self.process.stdout.flush()

            err = self.process.stderr.readline()
            if err:
                self.output_signal.emit(err.strip())
                self.process.stderr.flush()

        self.process.stdout.close()
        self.process.stderr.close()
        self.process.wait()

    def pause_process(self):
        if self.process:
            ctypes.windll.kernel32.SuspendThread(self.process._handle)  # Windows: 暫停進程

    def resume_process(self):
        if self.process:
            ctypes.windll.kernel32.ResumeThread(self.process._handle)  # Windows: 繼續進程

    def restart_process(self, cmd, prompt):
        if self.process:
            self.process.kill()  # 停止舊進程
        self.command = cmd
        self.user_input = prompt
        self.start()  # 重新啟動新進程

class OpenManusApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("OpenManus 控制台")
        self.setGeometry(200, 200, 500, 400)

        layout = QVBoxLayout()

        # 指令輸入框
        self.prompt_input = QLineEdit(self)
        self.prompt_input.setPlaceholderText("輸入指令 (例如: go to YT)")
        layout.addWidget(self.prompt_input)

        # 按鈕區
        self.run_button = QPushButton("🚀 執行 OpenManus", self)
        self.run_button.clicked.connect(self.run_script)
        layout.addWidget(self.run_button)

        self.pause_button = QPushButton("⏸️ 暫停", self)
        self.pause_button.clicked.connect(self.pause_script)
        layout.addWidget(self.pause_button)

        self.resume_button = QPushButton("▶️ 繼續", self)
        self.resume_button.clicked.connect(self.resume_script)
        layout.addWidget(self.resume_button)

        self.restart_button = QPushButton("🔄 重新開始", self)
        self.restart_button.clicked.connect(self.restart_script)
        layout.addWidget(self.restart_button)

        # CMD 監視器
        self.cmd_output = QTextEdit(self)
        self.cmd_output.setReadOnly(True)
        layout.addWidget(self.cmd_output)

        self.setLayout(layout)
        self.command_runner = None  # 存儲執行狀態

    def run_script(self):
        prompt = self.prompt_input.text()
        cmd = "conda activate open_manus && cd /d C:\\Users\\laixi\\OpenManus && python main.py"

        self.command_runner = CommandRunner(cmd, prompt)
        self.command_runner.output_signal.connect(self.update_output)
        self.command_runner.start()

    def pause_script(self):
        if self.command_runner:
            self.command_runner.pause_process()

    def resume_script(self):
        if self.command_runner:
            self.command_runner.resume_process()

    def restart_script(self):
        prompt = self.prompt_input.text()
        cmd = "conda activate open_manus && cd /d C:\\Users\\laixi\\OpenManus && python main.py"
        if self.command_runner:
            self.command_runner.restart_process(cmd, prompt)

    def update_output(self, text):
        self.cmd_output.append(text)
        self.cmd_output.update()

# 啟動應用
app = QApplication(sys.argv)
window = OpenManusApp()
window.show()
sys.exit(app.exec())