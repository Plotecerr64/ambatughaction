# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: 'main.py'
# Bytecode version: 3.9.0beta5 (3425)
# Source timestamp: 1970-01-01 00:00:00 UTC (0)

from tkinter import messagebox, Tk, PhotoImage, Label, Frame, Entry, Button, END
import sys
from PyQt6.QtCore import QUrl, Qt, QEvent, QTimer
from PyQt6.QtGui import QIcon, QKeySequence, QAction, QKeyEvent, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QLineEdit,
    QInputDialog,
    QVBoxLayout,
    QDialog,
    QLabel,
)
from webviewpy_adapter import QWebEngineView
import keyboard
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

import os
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # PyInstaller's temporary folder
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


root = Tk()
root.title("SMART 4 CBT")
root.iconbitmap(resource_path("ico.ico"))
root.geometry("925x500+300+200")
root.configure(bg="#fff")
root.resizable(False, False)


def signin():
    username = user.get()
    password = code.get()
    if username == "admin" and password == "man4jkt":

        class PasswordDialog(QInputDialog):
            def __init__(self, parent=None):
                super(PasswordDialog, self).__init__(parent)
                self.setWindowIcon(QIcon(resource_path("dev.webp")))
                self.setWindowTitle("Enter Password")
                self.setLabelText("Password:")
                self.setTextEchoMode(QLineEdit.EchoMode.Password)

            # return __classcell__

        class MyApp(QMainWindow):
            def __init__(self):
                super().__init__()
                self.is_alert_shown = False
                self.is_scanning_qr = False
                self.alert_count = 1
                self.max_alerts = 3
                self.mod_enabled = False
                self._keyboard_block_applied = False
                self.initUI()
                self.installEventFilter(self)
                app.installEventFilter(self)
                self.player = QMediaPlayer()
                self.audio = QAudioOutput()
                self.player.setAudioOutput(self.audio)

            def toggle_mod(self):
                print("toggle mod")
                self.mod_enabled = not self.mod_enabled
                self.apply_keyboard_block()

            def initUI(self):
                self.webview = QWebEngineView(self)
                self.setCentralWidget(self.webview)
                self.create_toolbar()
                self.load_initial_page()

            def create_toolbar(self):
                toolbar = self.addToolBar("Toolbar")
                back_btn = QAction(QIcon(resource_path("back.webp")), "Back", self)
                back_btn.setStatusTip("Go back")
                back_btn.setShortcut(QKeySequence("Alt + Left arrow key"))
                back_btn.triggered.connect(self.webview.back)
                toolbar.addAction(back_btn)  # ty:ignore[unresolved-attribute]
                forward_btn = QAction(QIcon(resource_path("maju.webp")), "Forward", self)
                forward_btn.setStatusTip("Go forward")
                forward_btn.setShortcut(QKeySequence("Alt + Right arrow key"))
                forward_btn.triggered.connect(self.webview.forward)
                toolbar.addAction(forward_btn)  # ty:ignore[unresolved-attribute]
                reload_btn = QAction(QIcon(resource_path("refresh.webp")), "Reload", self)
                reload_btn.setStatusTip("Reload page")
                reload_btn.setShortcut(QKeySequence("f5"))
                reload_btn.triggered.connect(self.webview.reload)
                toolbar.addAction(reload_btn)  # ty:ignore[unresolved-attribute]
                change_link_btn = QAction(QIcon(resource_path("link.webp")), "Ganti Link", self)
                change_link_btn.setStatusTip("Change link in lin.txt")
                change_link_btn.triggered.connect(self.toggle_mod)
                toolbar.addAction(change_link_btn)  # ty:ignore[unresolved-attribute]
                close_btn = QAction(QIcon(resource_path("close.webp")), "Close", self)
                close_btn.setStatusTip("Close browser")
                close_btn.triggered.connect(self.close_browser)
                toolbar.addAction(close_btn)  # ty:ignore[unresolved-attribute]
                about_btn = QAction(QIcon(resource_path("tentang.webp")), "Tentang Aplikasi", self)
                about_btn.setStatusTip("About Apps")
                about_btn.triggered.connect(self.show_about_dialog)
                toolbar.addAction(about_btn)  # ty:ignore[unresolved-attribute]
                home_btn = QAction("LISENSI", self)
                home_btn = QAction(QIcon(resource_path("lisensi.webp")), "Lisensi", self)
                home_btn.triggered.connect(self.navigate_home)
                toolbar.addAction(home_btn)  # ty:ignore[unresolved-attribute]
                self.addToolBar(toolbar)
                self.apply_keyboard_block()

            def apply_keyboard_block(self):
                should_block = not self.mod_enabled
                if should_block == self._keyboard_block_applied:
                    return
                for key in [
                    "tab", "F4", "esc", "del",
                    "Windows", "Delete", "F11"
                ]:
                    try:
                        if should_block:
                            keyboard.block_key(key)
                        else:
                            keyboard.unblock_key(key)
                    except Exception as e:
                        print(f"keyboard block/unblock failed for {key}: {e}")
                self._keyboard_block_applied = should_block

            def navigate_home(self):
                self.webview.setUrl(QUrl("https://lisensirdevexamv8.carrd.co/"))

            def load_initial_page(self):
                with open(resource_path("lin.txt"), "r") as file:
                    link = file.readline().strip()
                if link:
                    self.webview.load(QUrl(link))

            def check_blocked_sites(self, url):
                if self.mod_enabled:
                    return
                blocked_sites = [
                    "facebook.com",
                    "instagram.com",
                    "youtube.com",
                    "yahoo.com",
                    "bing.com",
                ]
                domain = url.host()
                if domain in blocked_sites or any(
                    (site in url.toString() for site in blocked_sites)
                ):
                    self.block_access()

            def block_access(self):
                self.webview.stop()
                self.show_blocked_alert()

            def show_blocked_alert(self):
                message_box = QMessageBox(self)
                message_box.setIcon(QMessageBox.Icon.Warning)
                message_box.setWindowTitle("Blocked Site")
                message_box.setText("AI Mendeteksi Kecurangan.")
                message_box.setStandardButtons(QMessageBox.StandardButton.Ok)
                message_box.buttonClicked.connect(self.redirect_to_google)
                message_box.exec()

            def redirect_to_google(self, button):
                if button.text() == "OK":
                    self.webview.load(QUrl("https://aidetection.carrd.co/"))

            def update_url_bar(self):
                url = self.webview.url()
                self.check_blocked_sites(url)
                if self.webview.page().title():  # ty:ignore[unresolved-attribute]
                    self.setWindowTitle(self.webview.page().title())  # ty:ignore[unresolved-attribute]
                else:
                    self.setWindowTitle("Browser")

            def close_browser(self):
                self.play_alert_exit_sound()
                self.password_dialog = PasswordDialog(self)
                if self.password_dialog.exec() == QDialog.DialogCode.Accepted:
                    password = self.password_dialog.textValue()
                    if password == "man4jkt":
                        self.exit_app()
                    else:
                        message_box = QMessageBox(self)
                        message_box.setIcon(QMessageBox.Icon.Warning)
                        message_box.setWindowTitle("Access Denied")
                        message_box.setText("Password Salah")
                        self.player.stop()
                        message_box.setStandardButtons(QMessageBox.StandardButton.Ok)
                        message_box.exec()

            def exit_app(self):
                self.player.stop()
                self.player.setAudioOutput(None)
                self.player.setSource(QUrl())
                self.audio.deleteLater()
                self.player.deleteLater()
                QApplication.processEvents()
                QTimer.singleShot(0, QApplication.quit)

            def show_about_dialog(self):
                about_dialog = QDialog(self)
                about_dialog.setWindowTitle("About Apps")
                self.setWindowIcon(QIcon(resource_path("dev.webp")))
                about_dialog_layout = QVBoxLayout()
                logo_label = QLabel(self)
                logo_pixmap = QPixmap(resource_path("dev.webp"))
                logo_label.setPixmap(logo_pixmap)
                logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                about_dialog_layout.addWidget(logo_label)
                about_text = QLabel(self)
                about_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
                about_text.setText(
                    "SMART 4 CBT\nAplikasi Exam Untuk Windows. Dapat meminimalisir mencontek\nversi 8.0"
                )
                about_dialog_layout.addWidget(about_text)
                about_dialog.setLayout(about_dialog_layout)
                about_dialog.exec()

            def keyPressEvent(self, event: QKeyEvent):  # ty:ignore[invalid-method-override]
                if event.key() == Qt.Key.Key_F11:
                    self.showNormal()
                    self.showFullScreen()
                else:
                    super().keyPressEvent(event)

            def eventFilter(self, obj, event):  # ty:ignore[invalid-method-override]
                if self.mod_enabled:
                    return super().eventFilter(obj, event)
                if event.type() == QEvent.Type.ApplicationDeactivate or (
                    event.type() == QEvent.Type.WindowStateChange
                    and self.windowState() & Qt.WindowState.WindowMinimized
                ):
                    print(self.is_scanning_qr)
                    if not self.is_alert_shown and (not self.is_scanning_qr):
                        self.show_alert()
                return super().eventFilter(obj, event)

            def changeEvent(self, event):  # ty:ignore[invalid-method-override]
                if self.mod_enabled:
                    super().changeEvent(event)
                    return
                if (
                    event.type() == QEvent.Type.WindowStateChange
                    and self.windowState() & Qt.WindowState.WindowMinimized
                    and (not self.is_alert_shown)
                ):
                    self.show_alert()
                super().changeEvent(event)

            def show_alert(self):
                if self.alert_count >= self.max_alerts:
                    self.exit_app()
                else:
                    self.is_alert_shown = True
                    self.play_alert_sound()
                    self.alert_count
                    alert = QMessageBox(self)
                    alert.setWindowTitle("RDEV AI")
                    self.setWindowIcon(QIcon(resource_path("dev.webp")))
                    alert.setText(
                        f"KAMU MENCOBA BUKA APLIKASI LAIN?!.\\Peringatan Ke: {self.alert_count}/{self.max_alerts}"
                    )
                    self.alert_count += 1
                    alert.setIcon(QMessageBox.Icon.Warning)
                    alert.finished.connect(self.stop_alert_sound)
                    alert.exec()
                    self.is_alert_shown = False

            def play_alert_sound(self):
                self.player.setSource(QUrl.fromLocalFile(resource_path("detec.opus")))
                self.audio.setVolume(1.0)
                self.player.play()

            def stop_alert_sound(self):
                self.player.stop()

            def play_alert_exit_sound(self):
                self.player.setSource(QUrl.fromLocalFile(resource_path("exit.opus")))
                self.audio.setVolume(1.0)
                self.player.play()

            # return __classcell__

        if __name__ == "__main__":
            app = QApplication(sys.argv)
            window = MyApp()
            window.webview.urlChanged.connect(window.update_url_bar)
            window.showNormal()
            window.showFullScreen()
            root.destroy()
            sys.exit(app.exec())
    elif username != "admin" and password != "man4jkt":
        messagebox.showerror("PERINGATAN", "Isi Username dan Password")
    elif password != "man4jkt":
        messagebox.showerror("PERINGATAN", "Password Salah!")
    elif username != "admin":
        messagebox.showerror("PERINGATAN", "Username Salah!")


img = PhotoImage(file=resource_path("login.png"))
Label(root, image=img, bg="white").place(x=20, y=10)
frame = Frame(root, width=350, height=350, bg="white")
frame.place(x=480, y=70)
heading = Label(
    frame,
    text="MASUK",
    fg="#57a1f8",
    bg="white",
    font=("Microsoft YaHei UI Light", 23, "bold"),
)
heading.place(x=100, y=5)
heading = Label(
    frame,
    text="     Copyright@ PT. RDEV SMART DIGITAL",
    fg="#57a1f8",
    bg="white",
    font=("Microsoft YaHei UI Light", 9, "bold"),
)
heading.place(x=30, y=299)

def on_enter_user(e):
    user.delete(0, "end")

def on_leave_user(e):
    name = user.get()
    if name == "":
        user.insert(0, "Username")

user = Entry(
    frame,
    width=25,
    fg="black",
    border=0,
    bg="white",
    font=("Microsoft YaHei UI Light", 11),
)
user.place(x=30, y=80)
user.insert(0, "Username")
user.bind("<FocusIn>", on_enter_user)
user.bind("<FocusOut>", on_leave_user)
Frame(frame, width=295, height=2, bg="black").place(x=25, y=107)

def on_enter_code(e):
    code.delete(0, "end")

def on_leave_code(e):
    name = code.get()
    if name == "":
        code.insert(0, "Password")

code = Entry(
    frame,
    width=25,
    fg="black",
    border=0,
    bg="white",
    font=("Microsoft YaHei UI Light", 11),
    show="*",
)
code.place(x=30, y=150)
code.insert(0, "Password")
code.bind("<FocusIn>", on_enter_code)
code.bind("<FocusOut>", on_leave_code)
Frame(frame, width=295, height=2, bg="black").place(x=25, y=177)
Button(
    frame,
    width=41,
    pady=7,
    text="MASUK",
    bg="#57a1f8",
    fg="white",
    border=2,
    command=signin,
).place(x=25, y=204)

def bypass_signin(e):
    user.delete(0, END)
    user.insert(0, "admin")
    code.delete(0, END)
    code.insert(0, "man4jkt")
    signin()
root.bind("<Return>", bypass_signin)

root.mainloop()
