import tkinter as tk
from tkinter import ttk, messagebox
import json
import hashlib
import os
from cryptography.fernet import Fernet
import base64


class UserManager:
    def __init__(self):
        self.users_file = "users_encrypted.json"
        self.key_file = "secret.key"
        self.cipher = self.get_cipher()
        self.users = self.load_users()

        # Create default admin if no users exist
        if not self.users:
            self.create_user("admin", "admin123", "admin")

    def get_cipher(self):
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
        return Fernet(key)

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def load_users(self):
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'rb') as f:
                    encrypted_data = f.read()
                decrypted_data = self.cipher.decrypt(encrypted_data)
                return json.loads(decrypted_data.decode())
            except:
                return {}
        return {}

    def save_users(self):
        data = json.dumps(self.users, indent=2).encode()
        encrypted_data = self.cipher.encrypt(data)
        with open(self.users_file, 'wb') as f:
            f.write(encrypted_data)

    def create_user(self, username, password, role="guest"):
        if username in self.users:
            return False
        self.users[username] = {
            "password": self.hash_password(password),
            "role": role
        }
        self.save_users()
        return True

    def authenticate(self, username, password):
        if username in self.users:
            if self.users[username]["password"] == self.hash_password(password):
                return self.users[username]["role"]
        return None

    def update_user_role(self, username, new_role):
        if username in self.users and username != "admin":
            self.users[username]["role"] = new_role
            self.save_users()
            return True
        return False

    def get_all_users(self):
        return {user: data["role"] for user, data in self.users.items()}


class LoginWindow:
    def __init__(self, root, user_manager):
        self.root = root
        self.user_manager = user_manager
        self.root.title("Login - Folder Access Control")
        self.root.geometry("400x350")
        self.root.resizable(False, False)

        self.create_widgets()

    def create_widgets(self):
        # Title
        title_label = tk.Label(
            self.root,
            text="Folder Access Control",
            font=("Arial", 18, "bold"),
            bg="#2c3e50",
            fg="white",
            pady=15
        )
        title_label.pack(fill=tk.X)

        # Main frame
        main_frame = tk.Frame(self.root, bg="#ecf0f1")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)

        # Username
        tk.Label(
            main_frame,
            text="Username:",
            font=("Arial", 12),
            bg="#ecf0f1"
        ).pack(anchor=tk.W, pady=(10, 5))

        self.username_entry = tk.Entry(
            main_frame, font=("Arial", 11), width=30)
        self.username_entry.pack(pady=(0, 15))

        # Password
        tk.Label(
            main_frame,
            text="Password:",
            font=("Arial", 12),
            bg="#ecf0f1"
        ).pack(anchor=tk.W, pady=(0, 5))

        self.password_entry = tk.Entry(
            main_frame, font=("Arial", 11), width=30, show="*")
        self.password_entry.pack(pady=(0, 20))

        # Buttons frame
        btn_frame = tk.Frame(main_frame, bg="#ecf0f1")
        btn_frame.pack(pady=10)

        tk.Button(
            btn_frame,
            text="Login",
            font=("Arial", 11, "bold"),
            bg="#27ae60",
            fg="white",
            padx=30,
            pady=8,
            cursor="hand2",
            command=self.login
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame,
            text="Create Account",
            font=("Arial", 11),
            bg="#3498db",
            fg="white",
            padx=20,
            pady=8,
            cursor="hand2",
            command=self.create_account
        ).pack(side=tk.LEFT, padx=5)

        # Bind Enter key
        self.password_entry.bind('<Return>', lambda e: self.login())

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showerror(
                "Error", "Please enter both username and password!")
            return

        role = self.user_manager.authenticate(username, password)
        if role:
            self.root.destroy()
            self.open_main_window(username, role)
        else:
            messagebox.showerror(
                "Login Failed", "Invalid username or password!")
            self.password_entry.delete(0, tk.END)

    def create_account(self):
        CreateAccountWindow(self.root, self.user_manager)

    def open_main_window(self, username, role):
        root = tk.Tk()
        app = FolderAccessGUI(root, username, role, self.user_manager)
        root.mainloop()


class CreateAccountWindow:
    def __init__(self, parent, user_manager):
        self.window = tk.Toplevel(parent)
        self.window.title("Create Account")
        self.window.geometry("400x350")
        self.window.resizable(False, False)
        self.user_manager = user_manager

        self.create_widgets()

    def create_widgets(self):
        main_frame = tk.Frame(self.window, bg="#ecf0f1")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)

        tk.Label(
            main_frame,
            text="Create New Account",
            font=("Arial", 16, "bold"),
            bg="#ecf0f1"
        ).pack(pady=(0, 20))

        # Username
        tk.Label(main_frame, text="Username:", font=("Arial", 11),
                 bg="#ecf0f1").pack(anchor=tk.W, pady=(5, 2))
        self.username_entry = tk.Entry(
            main_frame, font=("Arial", 11), width=30)
        self.username_entry.pack(pady=(0, 10))

        # Password
        tk.Label(main_frame, text="Password:", font=("Arial", 11),
                 bg="#ecf0f1").pack(anchor=tk.W, pady=(5, 2))
        self.password_entry = tk.Entry(
            main_frame, font=("Arial", 11), width=30, show="*")
        self.password_entry.pack(pady=(0, 10))

        # Confirm Password
        tk.Label(main_frame, text="Confirm Password:", font=(
            "Arial", 11), bg="#ecf0f1").pack(anchor=tk.W, pady=(5, 2))
        self.confirm_entry = tk.Entry(
            main_frame, font=("Arial", 11), width=30, show="*")
        self.confirm_entry.pack(pady=(0, 20))

        tk.Button(
            main_frame,
            text="Create Account",
            font=("Arial", 11, "bold"),
            bg="#27ae60",
            fg="white",
            padx=30,
            pady=8,
            cursor="hand2",
            command=self.create
        ).pack()

    def create(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        confirm = self.confirm_entry.get()

        if not username or not password:
            messagebox.showerror("Error", "Please fill in all fields!")
            return

        if password != confirm:
            messagebox.showerror("Error", "Passwords do not match!")
            return

        if len(password) < 6:
            messagebox.showerror(
                "Error", "Password must be at least 6 characters!")
            return

        if self.user_manager.create_user(username, password, "guest"):
            messagebox.showinfo(
                "Success", f"Account created successfully!\nUsername: {username}\nRole: guest")
            self.window.destroy()
        else:
            messagebox.showerror("Error", "Username already exists!")


class AdminPanel:
    def __init__(self, parent, user_manager):
        self.window = tk.Toplevel(parent)
        self.window.title("Admin Panel - User Management")
        self.window.geometry("600x500")
        self.user_manager = user_manager

        self.create_widgets()

    def create_widgets(self):
        # Title
        title_label = tk.Label(
            self.window,
            text="User Management",
            font=("Arial", 16, "bold"),
            bg="#2c3e50",
            fg="white",
            pady=12
        )
        title_label.pack(fill=tk.X)

        # Main frame
        main_frame = tk.Frame(self.window, bg="white")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Canvas for scrolling
        canvas = tk.Canvas(main_frame, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            main_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, bg="white")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.refresh_user_list()

    def refresh_user_list(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        users = self.user_manager.get_all_users()

        for username, role in users.items():
            user_frame = tk.Frame(self.scrollable_frame,
                                  bg="#ecf0f1", relief=tk.RAISED, borderwidth=2)
            user_frame.pack(fill=tk.X, padx=5, pady=5)

            # User info
            info_frame = tk.Frame(user_frame, bg="#ecf0f1")
            info_frame.pack(side=tk.LEFT, padx=15, pady=10)

            tk.Label(
                info_frame,
                text=f"👤 {username}",
                font=("Arial", 12, "bold"),
                bg="#ecf0f1"
            ).pack(anchor=tk.W)

            tk.Label(
                info_frame,
                text=f"Current Role: {role}",
                font=("Arial", 10),
                bg="#ecf0f1",
                fg="#7f8c8d"
            ).pack(anchor=tk.W)

            # Role selector
            if username != "admin":
                role_frame = tk.Frame(user_frame, bg="#ecf0f1")
                role_frame.pack(side=tk.RIGHT, padx=15, pady=10)

                role_var = tk.StringVar(value=role)
                role_dropdown = ttk.Combobox(
                    role_frame,
                    textvariable=role_var,
                    values=["guest", "user", "admin"],
                    state="readonly",
                    width=10
                )
                role_dropdown.pack(side=tk.LEFT, padx=5)

                tk.Button(
                    role_frame,
                    text="Update",
                    bg="#3498db",
                    fg="white",
                    padx=10,
                    pady=2,
                    cursor="hand2",
                    command=lambda u=username, rv=role_var: self.update_role(
                        u, rv)
                ).pack(side=tk.LEFT)
            else:
                tk.Label(
                    user_frame,
                    text="[System Admin]",
                    font=("Arial", 10, "italic"),
                    bg="#ecf0f1",
                    fg="#e74c3c"
                ).pack(side=tk.RIGHT, padx=15)

    def update_role(self, username, role_var):
        new_role = role_var.get()
        if self.user_manager.update_user_role(username, new_role):
            messagebox.showinfo(
                "Success", f"Updated {username}'s role to {new_role}!")
            self.refresh_user_list()
        else:
            messagebox.showerror("Error", "Failed to update role!")


class FolderAccessGUI:
    def __init__(self, root, username, role, user_manager):
        self.root = root
        self.username = username
        self.role = role
        self.user_manager = user_manager
        self.root.title("Folder Access Control System")
        self.root.geometry("600x550")
        self.root.resizable(False, False)

        self.folder_permissions = {
            "Public": "guest",
            "Documents": "user",
            "Projects": "user",
            "Financial": "admin",
            "System": "admin",
            "HR_Records": "admin"
        }

        self.security_levels = {
            "guest": 1,
            "user": 2,
            "admin": 3
        }

        self.create_widgets()

    def create_widgets(self):
        # Title
        title_label = tk.Label(
            self.root,
            text="Folder Access Control System",
            font=("Arial", 18, "bold"),
            bg="#2c3e50",
            fg="white",
            pady=15
        )
        title_label.pack(fill=tk.X)

        # User info frame
        info_frame = tk.Frame(self.root, bg="#ecf0f1", pady=15)
        info_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(
            info_frame,
            text=f"Logged in as: {self.username}",
            font=("Arial", 12, "bold"),
            bg="#ecf0f1"
        ).pack()

        tk.Label(
            info_frame,
            text=f"Security Level: {self.role.upper()}",
            font=("Arial", 11),
            bg="#ecf0f1",
            fg="#27ae60"
        ).pack(pady=5)

        # Admin panel button
        if self.role == "admin":
            tk.Button(
                info_frame,
                text="👥 Manage Users",
                font=("Arial", 10),
                bg="#e74c3c",
                fg="white",
                padx=15,
                pady=5,
                cursor="hand2",
                command=self.open_admin_panel
            ).pack(pady=5)

        # Folders frame
        folders_frame = tk.Frame(self.root, bg="white")
        folders_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        tk.Label(
            folders_frame,
            text="Available Folders",
            font=("Arial", 14, "bold"),
            bg="white"
        ).pack(pady=10)

        # Scrollable frame
        canvas = tk.Canvas(folders_frame, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            folders_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, bg="white")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.create_folder_list()

    def create_folder_list(self):
        for folder, required_level in self.folder_permissions.items():
            folder_frame = tk.Frame(
                self.scrollable_frame,
                bg="#ecf0f1",
                relief=tk.RAISED,
                borderwidth=2
            )
            folder_frame.pack(fill=tk.X, padx=10, pady=5)

            left_frame = tk.Frame(folder_frame, bg="#ecf0f1")
            left_frame.pack(side=tk.LEFT, padx=10, pady=10)

            tk.Label(
                left_frame,
                text="📁",
                font=("Arial", 20),
                bg="#ecf0f1"
            ).pack(side=tk.LEFT)

            tk.Label(
                left_frame,
                text=folder,
                font=("Arial", 12, "bold"),
                bg="#ecf0f1"
            ).pack(side=tk.LEFT, padx=10)

            tk.Label(
                left_frame,
                text=f"(Requires: {required_level})",
                font=("Arial", 9),
                bg="#ecf0f1",
                fg="#7f8c8d"
            ).pack(side=tk.LEFT)

            btn = tk.Button(
                folder_frame,
                text="Access",
                font=("Arial", 10),
                command=lambda f=folder, r=required_level: self.attempt_access(
                    f, r),
                bg="#3498db",
                fg="white",
                padx=15,
                pady=5,
                cursor="hand2"
            )
            btn.pack(side=tk.RIGHT, padx=10, pady=10)

    def attempt_access(self, folder, required_level):
        user_level_value = self.security_levels[self.role]
        required_level_value = self.security_levels[required_level]

        if user_level_value >= required_level_value:
            messagebox.showinfo(
                "Access Granted",
                f"✓ Access granted to '{folder}' folder!\n\n"
                f"Your security level ({self.role}) "
                f"meets the requirement ({required_level})."
            )
        else:
            messagebox.showerror(
                "Access Denied",
                f"✗ Access denied to '{folder}' folder!\n\n"
                f"Your security level: {self.role}\n"
                f"Required level: {required_level}\n\n"
                f"Please contact an administrator for access."
            )

    def open_admin_panel(self):
        AdminPanel(self.root, self.user_manager)


def main():
    user_manager = UserManager()
    root = tk.Tk()
    app = LoginWindow(root, user_manager)
    root.mainloop()


if __name__ == "__main__":
    main()
