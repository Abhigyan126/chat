# chat_app.py
import tkinter as tk
from tkinter import messagebox
from database_util import get_collection
from encryption_util import generate_key, load_key, encrypt_message, decrypt_message
import bson
import threading
import time

# Generate encryption key if it doesn't exist
try:
    load_key()
except FileNotFoundError:
    generate_key()

key = load_key()

class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Encrypted Chat Application")
        self.create_menu()

        self.user_collection = get_collection("users")
        self.chat_collection = get_collection("chats")

        self.current_user = None
        self.selected_user = None

        self.login_frame = None
        self.user_selection_frame = None
        self.chat_frame = None

        self.refresh_flag = False

        self.setup_login_screen()

    def create_menu(self):
        menu = tk.Menu(self.root)
        self.root.config(menu=menu)

        file_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Login", command=self.setup_login_screen)
        file_menu.add_command(label="Select User", command=self.setup_user_selection_screen)
        file_menu.add_command(label="Chat", command=self.setup_chat_screen)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

    def setup_login_screen(self):
        self.refresh_flag = False
        self.clear_frames()

        self.login_frame = tk.Frame(self.root)
        self.login_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(self.login_frame, text="Username").pack()
        self.username_entry = tk.Entry(self.login_frame)
        self.username_entry.pack()

        tk.Label(self.login_frame, text="Password").pack()
        self.password_entry = tk.Entry(self.login_frame, show='*')
        self.password_entry.pack()

        tk.Button(self.login_frame, text="Login", command=self.login).pack()
        tk.Button(self.login_frame, text="Register", command=self.register).pack()

    def setup_user_selection_screen(self):
        self.refresh_flag = False
        self.clear_frames()

        self.user_selection_frame = tk.Frame(self.root)
        self.user_selection_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(self.user_selection_frame, text="Select User to Chat With").pack()

        self.user_listbox = tk.Listbox(self.user_selection_frame)
        self.user_listbox.pack()

        for user in self.user_collection.find():
            if user["username"] != self.current_user["username"]:
                self.user_listbox.insert(tk.END, user["username"])

        tk.Button(self.user_selection_frame, text="Select", command=self.select_user).pack()

    def setup_chat_screen(self):
        if not self.selected_user:
            messagebox.showerror("Error", "Please select a user to chat with first.")
            return

        self.refresh_flag = False
        self.clear_frames()

        self.chat_frame = tk.Frame(self.root)
        self.chat_frame.pack(fill=tk.BOTH, expand=True)

        self.chat_log = tk.Text(self.chat_frame)
        self.chat_log.pack()

        self.message_entry = tk.Entry(self.chat_frame)
        self.message_entry.pack()

        tk.Button(self.chat_frame, text="Send", command=self.send_message).pack()

        self.load_chat_log()
        self.start_refresh_thread()

    def clear_frames(self):
        self.refresh_flag = False
        if self.login_frame:
            self.login_frame.destroy()
        if self.user_selection_frame:
            self.user_selection_frame.destroy()
        if self.chat_frame:
            self.chat_frame.destroy()

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        user = self.user_collection.find_one({"username": username, "password": password})
        if user:
            self.current_user = user
            self.setup_user_selection_screen()
        else:
            messagebox.showerror("Error", "Invalid credentials")

    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if self.user_collection.find_one({"username": username}):
            messagebox.showerror("Error", "Username already exists")
        else:
            self.user_collection.insert_one({"username": username, "password": password})
            messagebox.showinfo("Success", "User registered successfully")

    def select_user(self):
        selected_username = self.user_listbox.get(tk.ACTIVE)
        self.selected_user = self.user_collection.find_one({"username": selected_username})
        if self.selected_user:
            self.setup_chat_screen()

    def send_message(self):
        message = self.message_entry.get()
        if message:
            encrypted_message = encrypt_message(message, key)
            self.chat_collection.insert_one({
                "sender_id": self.current_user["_id"],
                "receiver_id": self.selected_user["_id"],
                "message": encrypted_message,
                "timestamp": time.time()
            })
            self.message_entry.delete(0, tk.END)
            self.load_chat_log()

    def load_chat_log(self):
        if not self.chat_log:
            return

        self.chat_log.delete(1.0, tk.END)
        chats = self.chat_collection.find({
            "$or": [
                {"sender_id": self.current_user["_id"], "receiver_id": self.selected_user["_id"]},
                {"sender_id": self.selected_user["_id"], "receiver_id": self.current_user["_id"]}
            ]
        }).sort("timestamp", 1)

        for chat in chats:
            sender = self.user_collection.find_one({"_id": chat["sender_id"]})
            decrypted_message = decrypt_message(chat["message"], key)
            self.chat_log.insert(tk.END, f"{sender['username']}: {decrypted_message}\n")

    def refresh_chat_log(self):
        while self.refresh_flag:
            time.sleep(5)
            if not self.chat_log:
                break
            self.load_chat_log()

    def start_refresh_thread(self):
        self.refresh_flag = True
        refresh_thread = threading.Thread(target=self.refresh_chat_log, daemon=True)
        refresh_thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()
