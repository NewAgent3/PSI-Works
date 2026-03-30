import tkinter as tk
from tkinter import filedialog, messagebox
import base64
import subprocess
import os
import sys

INSTALLER_TEMPLATE = r"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import zipfile
import tempfile
import os
import shutil
import base64
import winshell
from win32com.client import Dispatch
import threading

APP_NAME = "{app_name}"
ZIP_DATA = "{zip_data}"
MAIN_EXE = "{main_exe}"


def create_shortcut(target, shortcut_path):
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.Targetpath = target
    shortcut.save()


def extract_zip(temp_dir):
    zip_path = os.path.join(temp_dir, "payload.zip")

    with open(zip_path, "wb") as f:
        f.write(base64.b64decode(ZIP_DATA))

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)


class InstallerGUI:

    def __init__(self, root):
        self.root = root
        root.title(APP_NAME + " Installer")
        root.geometry("420x220")

        tk.Label(root, text="Install " + APP_NAME, font=("Arial", 16)).pack(pady=10)

        self.path_var = tk.StringVar(value=os.path.join(os.environ["PROGRAMFILES"], APP_NAME))

        frame = tk.Frame(root)
        frame.pack(pady=10)

        tk.Entry(frame, textvariable=self.path_var, width=35).pack(side=tk.LEFT)
        tk.Button(frame, text="Browse", command=self.browse).pack(side=tk.LEFT)

        self.progress = ttk.Progressbar(root, length=300, mode="determinate")
        self.progress.pack(pady=15)

        tk.Button(root, text="Install", command=self.start_install).pack()

    def browse(self):
        folder = filedialog.askdirectory()
        if folder:
            self.path_var.set(folder)

    def install(self):

        try:
            self.progress["value"] = 10

            install_dir = self.path_var.get()
            os.makedirs(install_dir, exist_ok=True)

            temp_dir = tempfile.mkdtemp()
            extract_zip(temp_dir)

            self.progress["value"] = 50

            for item in os.listdir(temp_dir):
                s = os.path.join(temp_dir, item)
                d = os.path.join(install_dir, item)

                if os.path.isdir(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, d)

            self.progress["value"] = 80

            exe_path = os.path.join(install_dir, MAIN_EXE)

            desktop = winshell.desktop()
            create_shortcut(exe_path, os.path.join(desktop, APP_NAME + ".lnk"))

            start = winshell.start_menu()
            create_shortcut(exe_path, os.path.join(start, APP_NAME + ".lnk"))

            self.progress["value"] = 100

            messagebox.showinfo("Done", "Installation complete!")

            if os.path.exists(exe_path):
                os.startfile(exe_path)

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def start_install(self):
        threading.Thread(target=self.install).start()


if __name__ == "__main__":
    root = tk.Tk()
    InstallerGUI(root)
    root.mainloop()
"""


# ================= BUILDER GUI =================

class BuilderGUI:

    def __init__(self, root):
        self.root = root
        root.title("Python Installer Builder")
        root.geometry("450x260")

        self.zip_path = tk.StringVar()
        self.main_exe = tk.StringVar()
        self.app_name = tk.StringVar(value="MyApp")

        self.make_field("Zip File", self.zip_path, self.select_zip)
        self.make_field("Main EXE", self.main_exe)
        self.make_field("App Name", self.app_name)

        tk.Button(root, text="Build Installer",
                  command=self.build).pack(pady=15)

    def make_field(self, label, var, cmd=None):
        tk.Label(self.root, text=label).pack()
        frame = tk.Frame(self.root)
        frame.pack()

        tk.Entry(frame, textvariable=var, width=40).pack(side=tk.LEFT)

        if cmd:
            tk.Button(frame, text="Browse", command=cmd).pack(side=tk.LEFT)

    def select_zip(self):
        file = filedialog.askopenfilename(filetypes=[("Zip Files", "*.zip")])
        if file:
            self.zip_path.set(file)

    def build(self):

        if not os.path.exists(self.zip_path.get()):
            messagebox.showerror("Error", "Zip not selected")
            return

        with open(self.zip_path.get(), "rb") as f:
            zip_b64 = base64.b64encode(f.read()).decode()

        code = INSTALLER_TEMPLATE.format(
            zip_data=zip_b64,
            app_name=self.app_name.get(),
            main_exe=self.main_exe.get()
        )

        with open("generated_installer.py", "w", encoding="utf-8") as f:
            f.write(code)

        subprocess.run([
            "pyinstaller",
            "--onefile",
            "--noconsole",
            "generated_installer.py"
        ])

        messagebox.showinfo("Done", "Installer built in dist folder!")


if __name__ == "__main__":
    root = tk.Tk()
    BuilderGUI(root)
    root.mainloop()
