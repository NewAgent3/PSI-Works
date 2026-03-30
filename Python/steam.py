import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import random
import os
import sys
import subprocess

# ================= STEAM ETA ================= #


class SteamETA:
    def __init__(self):
        self.samples = []
        self.last_eta = None
        self.calculating_until = time.time() + random.uniform(2, 5)

    def update(self, speed_mb, remaining_gb):
        if time.time() < self.calculating_until:
            return "Calculating..."

        self.samples.append(speed_mb)
        if len(self.samples) > 30:
            self.samples.pop(0)

        avg_speed = max(sum(self.samples) / len(self.samples), 0.5)
        eta_seconds = (remaining_gb * 1024) / avg_speed

        if self.last_eta:
            delta = eta_seconds - self.last_eta
            eta_seconds = self.last_eta + max(min(delta, 5), -5)

        self.last_eta = eta_seconds
        return self.format(eta_seconds)

    def format(self, seconds):
        seconds = int(seconds)

        if seconds < 60:
            return "< 1 minute"

        minutes = seconds // 60
        if minutes < 60:
            return f"{minutes} minutes"

        hours = minutes // 60
        if hours < 24:
            return f"{hours} hours"

        return f"{hours // 24} days"

# ================= DATA ================= #


FAKE_DISK_SPACE = 500.0

GAMES = {
    "Half-Life 3": {
        "size": 45,
        "desc": "The legendary return of Gordon Freeman in a physics-driven narrative FPS.",
        "features": ["Story Rich", "Advanced AI", "Physics-Based Combat"],
        "tags": ["FPS", "Sci-Fi", "Singleplayer"],
        "reviews": "Overwhelmingly Positive (98%)",
        "achievements": ["Wake Up", "Crowbar Only", "Lambda Survivor"],
        "dlc": ["Soundtrack", "Developer Commentary"],
        "updates": ["Day-One Patch", "Physics Stability Update"]
    },
    "Cyberpunk 2077": {
        "size": 70,
        "desc": "An open-world RPG set in Night City.",
        "features": ["Open World", "RPG Choices", "Multiple Endings"],
        "tags": ["RPG", "Cyberpunk"],
        "reviews": "Very Positive (84%)",
        "achievements": ["Legend of Night City"],
        "dlc": ["Phantom Liberty"],
        "updates": ["2.0 Overhaul"]
    },
    "Elden Ring": {
        "size": 60,
        "desc": "A vast fantasy world forged by Miyazaki and George R. R. Martin.",
        "features": ["Souls Combat", "Open World"],
        "tags": ["Souls-like", "Fantasy"],
        "reviews": "Overwhelmingly Positive (95%)",
        "achievements": ["Elden Lord"],
        "dlc": ["Shadow of the Erdtree"],
        "updates": ["Balance Patch"]
    }
}

FRIENDS = [
    "Alex is playing Elden Ring",
    "Maria unlocked an achievement",
    "João came online",
    "Sofia installed Cyberpunk 2077",
    "Pedro is playing Half-Life 3"
]

download_history = []

# ================= DOWNLOAD TASK ================= #


class DownloadTask(threading.Thread):
    def __init__(self, game, ui):
        super().__init__(daemon=True)
        self.game = game
        self.data = GAMES[game]
        self.ui = ui
        self.downloaded = 0.0
        self.speed = random.uniform(6, 22)
        self.running = True
        self.paused = False
        self.eta = SteamETA()

    def run(self):
        size = self.data["size"]
        self.ui.set_status(self, "Downloading")

        while self.downloaded < size and self.running:
            time.sleep(0.1)
            if self.paused:
                continue

            if random.random() < 0.04:
                self.ui.set_status(self, "Network busy")
                time.sleep(random.uniform(1, 2))
                self.ui.set_status(self, "Downloading")

            self.speed = max(1, self.speed + random.uniform(-2, 2))
            self.downloaded += self.speed / 1024

            percent = min((self.downloaded / size) * 100, 100)
            eta_text = self.eta.update(self.speed, size - self.downloaded)

            self.ui.update_progress(self, percent, self.speed, eta_text)

        if self.running:
            self.install()

    def install(self):
        self.ui.set_status(self, "Installing")
        for i in range(100):
            time.sleep(0.03)
            self.ui.update_install(self, i + 1)

        self.ui.set_status(self, "Cloud Sync")
        time.sleep(random.uniform(1, 2))
        self.ui.complete(self)
        download_history.append(self.game)

# ================= GUI ================= #


class SteamGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Steam")
        self.geometry("1200x700")
        self.configure(bg="#1b2838")
        self.tasks = {}
        self.big_picture = False
        self.create_ui()
        self.update_friends()

    def create_ui(self):
        tk.Label(self, text="STEAM", font=("Arial", 30, "bold"),
                 fg="white", bg="#1b2838").pack(pady=5)

        self.disk = tk.Label(self, text=f"Disk Space: {FAKE_DISK_SPACE:.1f} GB",
                             fg="#c7d5e0", bg="#1b2838")
        self.disk.pack()

        main = tk.Frame(self, bg="#1b2838")
        main.pack(fill=tk.BOTH, expand=True)

        # Store list
        left = tk.Frame(main, bg="#1b2838")
        left.pack(side=tk.LEFT, padx=10)

        self.listbox = tk.Listbox(left, width=35, height=10,
                                  bg="#2a475e", fg="white")
        self.listbox.pack()

        for g in GAMES:
            self.listbox.insert(tk.END, f"{g} ({GAMES[g]['size']} GB)")

        tk.Button(left, text="Store Page", command=self.open_store,
                  bg="#2a475e", fg="white").pack(pady=2)

        tk.Button(left, text="Download", command=self.start_download,
                  bg="#5c7e10", fg="white").pack()

        tk.Button(left, text="Big Picture Mode", command=self.toggle_big_picture,
                  bg="#2a475e", fg="white").pack(pady=5)

        # Friends
        right = tk.Frame(main, bg="#1b2838")
        right.pack(side=tk.RIGHT, padx=10)

        tk.Label(right, text="Friends Activity",
                 fg="white", bg="#1b2838").pack()

        self.friends_box = tk.Listbox(right, width=30, height=12,
                                      bg="#2a475e", fg="#c7d5e0")
        self.friends_box.pack()

        # Downloads
        self.downloads = tk.Frame(self, bg="#1b2838")
        self.downloads.pack(fill=tk.BOTH, expand=True)

    # ---------- Store Page ---------- #

    def open_store(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        game = self.listbox.get(sel).split(" (")[0]
        data = GAMES[game]

        win = tk.Toplevel(self)
        win.title(game)
        win.configure(bg="#1b2838")

        tk.Label(win, text=game, font=("Arial", 22, "bold"),
                 fg="white", bg="#1b2838").pack()

        tk.Label(win, text=data["desc"], wraplength=520,
                 fg="#c7d5e0", bg="#1b2838").pack(pady=5)

        for section, items in data.items():
            if section in ("desc", "size"):
                continue
            tk.Label(win, text=section.capitalize(),
                     fg="white", bg="#1b2838",
                     font=("Arial", 12, "bold")).pack(anchor="w", padx=10)
            for i in items:
                tk.Label(win, text=f"• {i}",
                         fg="#c7d5e0", bg="#1b2838").pack(anchor="w", padx=20)

        tk.Label(win, text=f"Reviews: {data['reviews']}",
                 fg="#9fb4c7", bg="#1b2838").pack(pady=5)

    # ---------- Downloads ---------- #

    def start_download(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        game = self.listbox.get(sel).split(" (")[0]
        size = GAMES[game]["size"]

        global FAKE_DISK_SPACE
        if size > FAKE_DISK_SPACE:
            messagebox.showerror("Disk Full", "Not enough disk space!")
            return

        FAKE_DISK_SPACE -= size
        self.disk.config(text=f"Disk Space: {FAKE_DISK_SPACE:.1f} GB")

        frame = tk.Frame(self.downloads, bg="#2a475e")
        frame.pack(fill=tk.X, padx=10, pady=4)

        tk.Label(frame, text=game,
                 bg="#2a475e", fg="white").pack(anchor="w")

        bar = ttk.Progressbar(frame, length=700)
        bar.pack()

        info = tk.Label(frame, text="Queued",
                        bg="#2a475e", fg="#c7d5e0")
        info.pack(anchor="w")

        play = tk.Button(frame, text="Play",
                         command=lambda g=game: self.launch_game(g),
                         bg="#5c7e10", fg="white", state=tk.DISABLED)
        play.pack(anchor="e")

        task = DownloadTask(game, self)
        self.tasks[task] = (bar, info, play)
        task.start()

    def update_progress(self, task, percent, speed, eta):
        bar, info, _ = self.tasks[task]
        bar["value"] = percent
        info.config(text=f"{percent:.1f}% | {speed:.1f} MB/s | ETA: {eta}")

    def update_install(self, task, percent):
        bar, info, _ = self.tasks[task]
        bar["value"] = percent
        info.config(text=f"Installing... {percent}%")

    def set_status(self, task, text):
        _, info, _ = self.tasks[task]
        info.config(text=text)

    def complete(self, task):
        bar, info, play = self.tasks[task]
        bar["value"] = 100
        info.config(text="Ready to Play ✔")
        play.config(state=tk.NORMAL)

    # ---------- Launch ---------- #

    def launch_game(self, game):
        image = f"{game}.mp4"
        if not os.path.exists(image):
            messagebox.showerror("Launch Error",
                                 f"Missing file:\n{image}")
            return

        if sys.platform.startswith("win"):
            os.startfile(image)
        elif sys.platform == "darwin":
            subprocess.call(["open", image])
        else:
            subprocess.call(["xdg-open", image])

    # ---------- Misc ---------- #

    def toggle_big_picture(self):
        self.big_picture = not self.big_picture
        self.attributes("-fullscreen", self.big_picture)

    def update_friends(self):
        self.friends_box.delete(0, tk.END)
        random.shuffle(FRIENDS)
        for f in FRIENDS[:4]:
            self.friends_box.insert(tk.END, f)
        self.after(5000, self.update_friends)

# ================= RUN ================= #


if __name__ == "__main__":
    SteamGUI().mainloop()
