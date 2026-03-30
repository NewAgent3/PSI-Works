import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import json


class SteamClone:
    def __init__(self, root):
        self.root = root
        self.root.title("PyGames Library")
        self.root.geometry("1000x650")
        self.root.configure(bg="#1b2838")

        # Sample data
        self.user = {
            "name": "Player",
            "level": 15,
            "balance": 50.00
        }

        self.library_games = [
            {"name": "Portal 2", "hours": 124.5,
                "last_played": "2025-12-10", "installed": True},
            {"name": "Half-Life 3", "hours": 89.2,
                "last_played": "2025-12-11", "installed": True},
            {"name": "Team Fortress 2", "hours": 456.8,
                "last_played": "2025-12-09", "installed": False},
            {"name": "Dota 2", "hours": 1234.5,
                "last_played": "2025-12-12", "installed": True},
        ]

        self.store_games = [
            {"name": "Cyberpunk 2077", "price": 59.99,
                "discount": 0, "rating": "Very Positive"},
            {"name": "Red Dead Redemption 2", "price": 59.99,
                "discount": 50, "rating": "Overwhelmingly Positive"},
            {"name": "Elden Ring", "price": 59.99,
                "discount": 20, "rating": "Very Positive"},
            {"name": "Baldur's Gate 3", "price": 59.99,
                "discount": 0, "rating": "Overwhelmingly Positive"},
            {"name": "Stardew Valley", "price": 14.99,
                "discount": 25, "rating": "Overwhelmingly Positive"},
        ]

        self.friends = [
            {"name": "GamerTag123", "status": "Online", "game": "Playing Dota 2"},
            {"name": "ProPlayer99", "status": "Offline",
                "game": "Last online 2 hours ago"},
            {"name": "CasualGamer", "status": "Online", "game": "Playing Portal 2"},
        ]

        self.current_view = "library"
        self.setup_ui()

    def setup_ui(self):
        # Top bar
        top_frame = tk.Frame(self.root, bg="#171a21", height=50)
        top_frame.pack(fill=tk.X, side=tk.TOP)
        top_frame.pack_propagate(False)

        # Menu buttons
        menu_btns = [
            ("STORE", lambda: self.switch_view("store")),
            ("LIBRARY", lambda: self.switch_view("library")),
            ("COMMUNITY", lambda: self.switch_view("community")),
            ("PROFILE", lambda: self.switch_view("profile"))
        ]

        for text, cmd in menu_btns:
            btn = tk.Button(top_frame, text=text, command=cmd,
                            bg="#171a21", fg="white", font=("Arial", 10, "bold"),
                            relief=tk.FLAT, padx=20, cursor="hand2")
            btn.pack(side=tk.LEFT, padx=5, pady=10)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#2a475e"))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg="#171a21"))

        # User info
        user_label = tk.Label(top_frame, text=f"👤 {self.user['name']} | Lv.{self.user['level']} | ${self.user['balance']:.2f}",
                              bg="#171a21", fg="white", font=("Arial", 10))
        user_label.pack(side=tk.RIGHT, padx=20, pady=10)

        # Main content area
        self.content_frame = tk.Frame(self.root, bg="#1b2838")
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.show_library()

    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def switch_view(self, view):
        self.current_view = view
        self.clear_content()
        if view == "library":
            self.show_library()
        elif view == "store":
            self.show_store()
        elif view == "community":
            self.show_community()
        elif view == "profile":
            self.show_profile()

    def show_library(self):
        title = tk.Label(self.content_frame, text="MY GAMES",
                         bg="#1b2838", fg="white", font=("Arial", 20, "bold"))
        title.pack(anchor=tk.W, pady=(0, 10))

        # Game list with scrollbar
        list_frame = tk.Frame(self.content_frame, bg="#1b2838")
        list_frame.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(list_frame, bg="#1b2838", highlightthickness=0)
        scrollbar = tk.Scrollbar(
            list_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#1b2838")

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)

        for game in self.library_games:
            self.create_library_item(scrollable_frame, game)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_library_item(self, parent, game):
        frame = tk.Frame(parent, bg="#16202d", relief=tk.RAISED, bd=1)
        frame.pack(fill=tk.X, pady=5, padx=5)

        # Game info
        info_frame = tk.Frame(frame, bg="#16202d")
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH,
                        expand=True, padx=15, pady=10)

        name_label = tk.Label(info_frame, text=game["name"],
                              bg="#16202d", fg="white", font=("Arial", 14, "bold"))
        name_label.pack(anchor=tk.W)

        stats = f"⏱ {game['hours']} hours | Last played: {game['last_played']}"
        stats_label = tk.Label(info_frame, text=stats,
                               bg="#16202d", fg="#8f98a0", font=("Arial", 9))
        stats_label.pack(anchor=tk.W)

        status = "✓ Installed" if game["installed"] else "Not installed"
        status_label = tk.Label(info_frame, text=status,
                                bg="#16202d", fg="#5cb85c" if game["installed"] else "#d9534f",
                                font=("Arial", 9))
        status_label.pack(anchor=tk.W)

        # Buttons
        btn_frame = tk.Frame(frame, bg="#16202d")
        btn_frame.pack(side=tk.RIGHT, padx=15, pady=10)

        if game["installed"]:
            play_btn = tk.Button(btn_frame, text="▶ PLAY",
                                 bg="#5cb85c", fg="white", font=("Arial", 10, "bold"),
                                 relief=tk.FLAT, padx=20, pady=5, cursor="hand2",
                                 command=lambda: self.launch_game(game["name"]))
            play_btn.pack()
        else:
            install_btn = tk.Button(btn_frame, text="↓ INSTALL",
                                    bg="#2a475e", fg="white", font=("Arial", 10, "bold"),
                                    relief=tk.FLAT, padx=20, pady=5, cursor="hand2",
                                    command=lambda: self.install_game(game["name"]))
            install_btn.pack()

    def show_store(self):
        title = tk.Label(self.content_frame, text="STORE",
                         bg="#1b2838", fg="white", font=("Arial", 20, "bold"))
        title.pack(anchor=tk.W, pady=(0, 10))

        # Featured section
        featured = tk.Label(self.content_frame, text="Featured & Recommended",
                            bg="#1b2838", fg="#66c0f4", font=("Arial", 14, "bold"))
        featured.pack(anchor=tk.W, pady=(0, 10))

        # Store list
        list_frame = tk.Frame(self.content_frame, bg="#1b2838")
        list_frame.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(list_frame, bg="#1b2838", highlightthickness=0)
        scrollbar = tk.Scrollbar(
            list_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#1b2838")

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)

        for game in self.store_games:
            self.create_store_item(scrollable_frame, game)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_store_item(self, parent, game):
        frame = tk.Frame(parent, bg="#16202d", relief=tk.RAISED, bd=1)
        frame.pack(fill=tk.X, pady=5, padx=5)

        # Game info
        info_frame = tk.Frame(frame, bg="#16202d")
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH,
                        expand=True, padx=15, pady=10)

        name_label = tk.Label(info_frame, text=game["name"],
                              bg="#16202d", fg="white", font=("Arial", 14, "bold"))
        name_label.pack(anchor=tk.W)

        rating_label = tk.Label(info_frame, text=f"👍 {game['rating']}",
                                bg="#16202d", fg="#66c0f4", font=("Arial", 9))
        rating_label.pack(anchor=tk.W)

        # Price
        price_frame = tk.Frame(frame, bg="#16202d")
        price_frame.pack(side=tk.RIGHT, padx=15, pady=10)

        if game["discount"] > 0:
            discount_label = tk.Label(price_frame, text=f"-{game['discount']}%",
                                      bg="#4c6b22", fg="#beee11", font=("Arial", 12, "bold"),
                                      padx=5)
            discount_label.pack(side=tk.LEFT, padx=5)

            original = tk.Label(price_frame, text=f"${game['price']:.2f}",
                                bg="#16202d", fg="#8f98a0", font=("Arial", 10),
                                relief=tk.FLAT)
            original.pack(side=tk.LEFT)
            original.config(font=("Arial", 10, "overstrike"))

            final_price = game["price"] * (1 - game["discount"] / 100)
            price_label = tk.Label(price_frame, text=f"${final_price:.2f}",
                                   bg="#16202d", fg="#beee11", font=("Arial", 12, "bold"))
            price_label.pack(side=tk.LEFT, padx=5)
        else:
            price_label = tk.Label(price_frame, text=f"${game['price']:.2f}",
                                   bg="#16202d", fg="white", font=("Arial", 12, "bold"))
            price_label.pack(side=tk.LEFT, padx=5)

        buy_btn = tk.Button(price_frame, text="🛒 ADD TO CART",
                            bg="#2a475e", fg="white", font=("Arial", 9, "bold"),
                            relief=tk.FLAT, padx=15, pady=5, cursor="hand2",
                            command=lambda: self.add_to_cart(game["name"]))
        buy_btn.pack(side=tk.LEFT, padx=5)

    def show_community(self):
        title = tk.Label(self.content_frame, text="FRIENDS & COMMUNITY",
                         bg="#1b2838", fg="white", font=("Arial", 20, "bold"))
        title.pack(anchor=tk.W, pady=(0, 20))

        for friend in self.friends:
            frame = tk.Frame(self.content_frame, bg="#16202d",
                             relief=tk.RAISED, bd=1)
            frame.pack(fill=tk.X, pady=5, padx=5)

            info_frame = tk.Frame(frame, bg="#16202d")
            info_frame.pack(side=tk.LEFT, fill=tk.BOTH,
                            expand=True, padx=15, pady=10)

            status_color = "#5cb85c" if friend["status"] == "Online" else "#8f98a0"
            status_icon = "🟢" if friend["status"] == "Online" else "⚫"

            name_label = tk.Label(info_frame, text=f"{status_icon} {friend['name']}",
                                  bg="#16202d", fg="white", font=("Arial", 12, "bold"))
            name_label.pack(anchor=tk.W)

            game_label = tk.Label(info_frame, text=friend["game"],
                                  bg="#16202d", fg="#8f98a0", font=("Arial", 9))
            game_label.pack(anchor=tk.W)

            btn_frame = tk.Frame(frame, bg="#16202d")
            btn_frame.pack(side=tk.RIGHT, padx=15, pady=10)

            msg_btn = tk.Button(btn_frame, text="💬",
                                bg="#2a475e", fg="white", font=("Arial", 12),
                                relief=tk.FLAT, padx=10, pady=2, cursor="hand2",
                                command=lambda n=friend["name"]: messagebox.showinfo("Message", f"Chat with {n}"))
            msg_btn.pack(side=tk.LEFT, padx=2)

            invite_btn = tk.Button(btn_frame, text="🎮",
                                   bg="#2a475e", fg="white", font=("Arial", 12),
                                   relief=tk.FLAT, padx=10, pady=2, cursor="hand2",
                                   command=lambda n=friend["name"]: messagebox.showinfo("Invite", f"Invite {n} to game"))
            invite_btn.pack(side=tk.LEFT, padx=2)

    def show_profile(self):
        title = tk.Label(self.content_frame, text="PROFILE",
                         bg="#1b2838", fg="white", font=("Arial", 20, "bold"))
        title.pack(anchor=tk.W, pady=(0, 20))

        profile_frame = tk.Frame(
            self.content_frame, bg="#16202d", relief=tk.RAISED, bd=1)
        profile_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Avatar placeholder
        avatar = tk.Label(profile_frame, text="👤", bg="#16202d",
                          fg="white", font=("Arial", 60))
        avatar.pack(pady=20)

        name = tk.Label(profile_frame, text=self.user["name"],
                        bg="#16202d", fg="white", font=("Arial", 18, "bold"))
        name.pack()

        level = tk.Label(profile_frame, text=f"Level {self.user['level']}",
                         bg="#16202d", fg="#66c0f4", font=("Arial", 14))
        level.pack(pady=5)

        # Stats
        stats_frame = tk.Frame(profile_frame, bg="#16202d")
        stats_frame.pack(pady=20)

        total_games = len(self.library_games)
        total_hours = sum(g["hours"] for g in self.library_games)

        stat1 = tk.Label(stats_frame, text=f"Games Owned\n{total_games}",
                         bg="#16202d", fg="white", font=("Arial", 12), padx=30)
        stat1.pack(side=tk.LEFT)

        stat2 = tk.Label(stats_frame, text=f"Total Hours\n{total_hours:.1f}",
                         bg="#16202d", fg="white", font=("Arial", 12), padx=30)
        stat2.pack(side=tk.LEFT)

        stat3 = tk.Label(stats_frame, text=f"Wallet\n${self.user['balance']:.2f}",
                         bg="#16202d", fg="#5cb85c", font=("Arial", 12), padx=30)
        stat3.pack(side=tk.LEFT)

    def launch_game(self, game_name):
        messagebox.showinfo("Launch", f"Launching {game_name}...")

    def install_game(self, game_name):
        messagebox.showinfo("Install", f"Installing {game_name}...")

    def add_to_cart(self, game_name):
        messagebox.showinfo("Cart", f"Added {game_name} to cart!")


if __name__ == "__main__":
    root = tk.Tk()
    app = SteamClone(root)
    root.mainloop()
