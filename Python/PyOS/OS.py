"""
pyOS_gui.py

A lightweight "OS"-like GUI desktop written in pure Python (Tkinter).
Designed for Python 3.14 compatibility.

Features:
- Desktop area with a simple taskbar
- "Install Script" action to copy a .py file into the pyos_apps folder
- Lists installed .py scripts (icons on desktop + sidebar)
- Runs installed scripts in a separate subprocess (isolated from main GUI)
- Shows live stdout/stderr from the running script in a window
- Ability to stop running script

Security note: this tool *executes arbitrary Python files* you install. Only run code
from sources you trust. The implementation runs scripts in subprocesses to reduce
accidental interference with the main GUI, but it does NOT fully sandbox or
restrict file/network access.

Usage: python pyOS_gui.py

"""

import os
import sys
import shutil
import subprocess
import threading
import pathlib
import time
from tkinter import Tk, Frame, Label, Button, Listbox, Toplevel, filedialog, messagebox, StringVar, Entry, Scrollbar, RIGHT, Y, BOTH, LEFT, END
import tkinter.scrolledtext as scrolledtext

# ----------------------- Configuration -----------------------
APPS_DIR = os.path.join(os.path.abspath(
    os.path.dirname(__file__)), "pyos_apps")
ICON_SIZE = (64, 64)
WINDOW_TITLE = "pyOS — lightweight Python desktop"

# Ensure apps directory exists
os.makedirs(APPS_DIR, exist_ok=True)

# ----------------------- Utilities -----------------------


def list_installed_scripts():
    """Return list of .py files in the apps directory (sorted)."""
    files = [f for f in os.listdir(APPS_DIR) if f.endswith('.py')]
    files.sort()
    return files


def copy_script_into_apps(src_path, dest_name=None):
    """Copy a .py file into the apps directory. Returns destination path."""
    if not src_path.endswith('.py'):
        raise ValueError("Only .py files can be installed")
    if dest_name is None:
        dest_name = os.path.basename(src_path)
    dest = os.path.join(APPS_DIR, dest_name)
    # avoid overwriting unless user confirms
    if os.path.exists(dest):
        base, ext = os.path.splitext(dest)
        i = 1
        while os.path.exists(f"{base}_{i}{ext}"):
            i += 1
        dest = f"{base}_{i}{ext}"
    shutil.copy2(src_path, dest)
    return dest


# ----------------------- Subprocess runner -----------------------
class ScriptProcess:
    """Manage running a script in a subprocess and stream its output to a text widget."""

    def __init__(self, script_path, output_callback, error_callback, finished_callback):
        self.script_path = script_path
        self.output_callback = output_callback
        self.error_callback = error_callback
        self.finished_callback = finished_callback
        self.proc = None
        self._thread = None
        self._stopped = False

    def start(self):
        def target():
            # Run using the same Python interpreter
            cmd = [sys.executable, self.script_path]
            try:
                self.proc = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
            except Exception as e:
                self.error_callback(f"Failed to start script: {e}\n")
                self.finished_callback()
                return

            # Read stdout/stderr concurrently
            def read_stream(stream, callback):
                for line in iter(stream.readline, ''):
                    if self._stopped:
                        break
                    callback(line)
                stream.close()

            t_out = threading.Thread(target=read_stream, args=(
                self.proc.stdout, self.output_callback), daemon=True)
            t_err = threading.Thread(target=read_stream, args=(
                self.proc.stderr, self.error_callback), daemon=True)
            t_out.start()
            t_err.start()
            # Wait for process to finish
            self.proc.wait()
            # ensure the threads finish reading
            t_out.join(timeout=1)
            t_err.join(timeout=1)
            self.finished_callback()

        self._thread = threading.Thread(target=target, daemon=True)
        self._thread.start()

    def stop(self):
        self._stopped = True
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.terminate()
                # give it a short time then kill
                time.sleep(0.2)
                if self.proc.poll() is None:
                    self.proc.kill()
            except Exception:
                pass


# ----------------------- GUI Components -----------------------
class PyOS:
    def __init__(self, root: Tk):
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.geometry('900x600')

        # Layout root: top desktop area and bottom taskbar
        self.desktop = Frame(root, bg='#2e3440')
        self.desktop.pack(fill=BOTH, expand=True)

        self.taskbar = Frame(root, bg='#3b4252', height=30)
        self.taskbar.pack(fill='x', side='bottom')

        # Left sidebar listing installed scripts
        self.sidebar = Frame(self.desktop, bg='#4c566a', width=200)
        self.sidebar.pack(side=LEFT, fill='y')

        Label(self.sidebar, text='Installed Scripts',
              bg='#4c566a', fg='white').pack(padx=6, pady=6)
        self.scripts_listbox = Listbox(self.sidebar)
        self.scripts_listbox.pack(fill='y', expand=True, padx=6, pady=6)
        self.scripts_listbox.bind('<Double-Button-1>', self.on_run_selected)

        install_btn = Button(
            self.sidebar, text='Install Script', command=self.install_script)
        install_btn.pack(fill='x', padx=6, pady=6)

        refresh_btn = Button(self.sidebar, text='Refresh',
                             command=self.refresh_scripts)
        refresh_btn.pack(fill='x', padx=6, pady=(0, 6))

        # Desktop area (center) where icons appear
        self.center_area = Frame(self.desktop, bg='#2e3440')
        self.center_area.pack(fill=BOTH, expand=True)

        # A small status label on taskbar
        self.status_var = StringVar(value='Ready')
        Label(self.taskbar, textvariable=self.status_var,
              bg='#3b4252', fg='white').pack(side=LEFT, padx=8)

        # Start menu / quick actions
        Button(self.taskbar, text='Open Apps Folder',
               command=self.open_apps_folder).pack(side=RIGHT, padx=6)
        Button(self.taskbar, text='About',
               command=self.show_about).pack(side=RIGHT)

        # Keep track of running windows/processes
        # list of dicts: {"win": Toplevel, "proc": ScriptProcess}
        self.running_windows = []

        # initial population
        self.refresh_scripts()

    # ---------------------- Actions ----------------------
    def show_about(self):
        messagebox.showinfo(
            'About pyOS', 'pyOS — lightweight Python desktop\nRun and manage .py scripts from pyos_apps')

    def open_apps_folder(self):
        # Try to open file explorer at APPS_DIR
        try:
            if sys.platform.startswith('darwin'):
                subprocess.Popen(['open', APPS_DIR])
            elif sys.platform.startswith('linux'):
                subprocess.Popen(['xdg-open', APPS_DIR])
            elif sys.platform.startswith('win'):
                subprocess.Popen(['explorer', APPS_DIR])
            else:
                messagebox.showinfo('Open folder', f'Apps folder: {APPS_DIR}')
        except Exception as e:
            messagebox.showinfo(
                'Open folder', f'Apps folder: {APPS_DIR}\n\nCould not open automatically: {e}')

    def refresh_scripts(self):
        self.scripts_listbox.delete(0, END)
        for f in list_installed_scripts():
            self.scripts_listbox.insert(END, f)
        # refresh icons on desktop
        for widget in self.center_area.winfo_children():
            widget.destroy()
        self.populate_desktop_icons()

    def populate_desktop_icons(self):
        # Create a simple icon grid of installed scripts
        scripts = list_installed_scripts()
        cols = 4
        row = 0
        col = 0
        padx = 20
        pady = 20
        for name in scripts:
            icon_frame = Frame(self.center_area, width=120,
                               height=100, bg='#3b4252')
            icon_frame.grid_propagate(False)
            icon_frame.grid(row=row, column=col, padx=padx, pady=pady)
            label = Label(icon_frame, text=name, bg='#3b4252',
                          fg='white', wraplength=110, justify='center')
            label.place(relx=0.5, rely=0.5, anchor='center')
            label.bind('<Double-Button-1>', lambda e,
                       n=name: self.run_script(n))
            col += 1
            if col >= cols:
                col = 0
                row += 1

    def install_script(self):
        # Ask user to pick a .py file to install
        path = filedialog.askopenfilename(
            title='Select Python script to install', filetypes=[('Python files', '*.py')])
        if not path:
            return
        try:
            dest = copy_script_into_apps(path)
            messagebox.showinfo('Installed', f'Installed to: {dest}')
            self.status_var.set(f'Installed {os.path.basename(dest)}')
            self.refresh_scripts()
        except Exception as e:
            messagebox.showerror('Error', f'Failed to install: {e}')

    def on_run_selected(self, event):
        sel = self.scripts_listbox.curselection()
        if not sel:
            return
        name = self.scripts_listbox.get(sel[0])
        self.run_script(name)

    def run_script(self, script_name):
        script_path = os.path.join(APPS_DIR, script_name)
        if not os.path.exists(script_path):
            messagebox.showerror('Not found', f'{script_name} not found')
            return
        # Create a run window showing stdout/stderr
        win = Toplevel(self.root)
        win.title(f'Running: {script_name}')
        win.geometry('700x400')

        txt = scrolledtext.ScrolledText(win, state='normal')
        txt.pack(fill=BOTH, expand=True)

        btn_frame = Frame(win)
        btn_frame.pack(fill='x')
        stop_btn = Button(btn_frame, text='Stop', command=lambda: proc.stop())
        stop_btn.pack(side=LEFT, padx=6, pady=6)
        open_btn = Button(btn_frame, text='Open Location',
                          command=lambda: self.open_file_location(script_path))
        open_btn.pack(side=LEFT, padx=6)

        def append_out(line):
            txt.insert(END, line)
            txt.see('end')

        def append_err(line):
            txt.insert(END, line)
            txt.see('end')

        def finished():
            append_out('\n[Process finished]\n')
            self.status_var.set(f'Finished {script_name}')

        proc = ScriptProcess(script_path, output_callback=append_out,
                             error_callback=append_err, finished_callback=finished)
        self.running_windows.append({'win': win, 'proc': proc})

        # When the user closes the window, ensure we stop the process
        def on_close():
            try:
                proc.stop()
            finally:
                win.destroy()
        win.protocol('WM_DELETE_WINDOW', on_close)

        self.status_var.set(f'Running {script_name}')
        proc.start()

    def open_file_location(self, path):
        # select the file in explorer if possible
        try:
            if sys.platform.startswith('win'):
                subprocess.Popen(['explorer', '/select,', path])
            elif sys.platform.startswith('darwin'):
                subprocess.Popen(['open', '-R', path])
            else:
                # Try opening the folder
                subprocess.Popen(['xdg-open', os.path.dirname(path)])
        except Exception as e:
            messagebox.showinfo(
                'Open location', f'File at: {path}\nCould not open explorer: {e}')


# ----------------------- Main -----------------------

def main():
    root = Tk()
    app = PyOS(root)
    root.mainloop()


if __name__ == '__main__':
    main()
