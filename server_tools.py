import tkinter as tk
import ttkbootstrap as ttk
import urllib
import requests
import sqlite3
import threading
import subprocess
import os
import asyncio
import aiohttp

main = ttk.Window(themename='yeti')
main.title("markrainey.me Server Tools")
text_padding = 5
#database = r'.\server_database.db'
global loggedIn
#Main Screen Contents
greeting = ttk.Label(text="Please Select an Option")
greeting.pack(padx=text_padding, pady=text_padding)

import sqlite3
import os

DATABASE_FILE = os.path.abspath("server_database.db") 

def init_database():
    if not os.path.exists(DATABASE_FILE):
        print("Initializing database...")
        try:
            conn = sqlite3.connect(DATABASE_FILE)
            c = conn.cursor()

            c.execute('''
                CREATE TABLE Settings (
                    Key TEXT DEFAULT ""
                )
            ''')
            
            c.execute('INSERT INTO Settings (Key) VALUES ("")')
            
            conn.commit()
            conn.close()
            print("Database initialized successfully.")
        except sqlite3.Error as e:
            print(f"Error initializing database: {e}")
    else:
        print("Database already exists.")

init_database()

with sqlite3.connect(DATABASE_FILE) as conn:
    conn.execute("PRAGMA journal_mode=DELETE")

def checkLogIn():
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute("SELECT Key FROM Settings")
    data = c.fetchall()  
    conn.close()
    if data and data[0][0]:
        return True
    else:
        return False
    
def updateButtons():
    login_Button.pack_forget()
    download_Button.pack_forget()
    files_Button.pack_forget()
    settings_Button.pack_forget()
    logout_Button.pack_forget()

    if checkLogIn():
        download_Button.pack(padx=text_padding, pady=text_padding)
        files_Button.pack(padx=text_padding, pady=text_padding)
        settings_Button.pack(padx=text_padding, pady=text_padding)
        logoutstatus.pack_forget()
        logout_Button.pack(padx=text_padding, pady=text_padding)
    else:
        login_Button.pack(padx=text_padding, pady=text_padding)
        logoutstatus.pack(padx=text_padding, pady=text_padding)

def login(username, password, widget, window):
    params = {
        'username': username,
        'password': password
    }

    url = f'http://markrainey.me/login'
    try:
        response = requests.post(url,json=params)

        if response.status_code == 200:
            try:
                response_data = response.json()
            except requests.exceptions.JSONDecodeError:
                widget.config(text="Login Failed: Invalid response")
                return

            if response_data.get('access_token'):
                conn = sqlite3.connect(DATABASE_FILE)
                c = conn.cursor()
                c.execute("UPDATE Settings SET Key = ?", (response_data['access_token'],))
                conn.commit()
                conn.close()
                updateButtons()
                window.destroy()
                
            else:
                loggedIn = False
                widget.config(text="Login Failed")
        else:
            widget.config(text=f"Login Failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        widget.config(text=f"Login Failed: {str(e)}")
        return False

def logout(widget):
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute("SELECT Key FROM Settings")
    data = c.fetchall()
    if not data or not data[0][0]:
        widget.config(text="Not Logged In")
        return 
    key = data[0][0]
    conn.close()

    header = {
        'Authorization': f'Bearer {key}'
    }
    try:
        url = f'http://markrainey.me/logout'

        response = requests.post(url, headers=header)

        if response.status_code == 200:
            conn = sqlite3.connect(DATABASE_FILE)
            c = conn.cursor()
            c.execute("UPDATE Settings SET Key = ?", ("",))
            conn.commit()
            conn.close()
            updateButtons()
            widget.config(text="Logged Out")
        else:
            conn = sqlite3.connect(DATABASE_FILE)
            c = conn.cursor()
            c.execute("UPDATE Settings SET Key = ?", ("",))
            conn.commit()
            conn.close()
            updateButtons()
            widget.config(text="Logout Failed / Cleared Database.")
    except requests.exceptions.RequestException as e:
        widget.config(text=f"Logout Failed: {str(e)}")
        return False

def open_login_window():
    global username_box, password_box, loginstatus

    login_window = ttk.Toplevel()
    login_window.title("Log In")

    login_window.bind('<Return>', lambda event: login(username_box.get(), password_box.get(), loginstatus, login_window))

    username_label = ttk.Label(login_window, text="Username").pack(padx=text_padding, pady=text_padding)
    username_box = ttk.Entry(login_window)
    username_box.pack(padx=text_padding, pady=text_padding)
    password_label = ttk.Label(login_window, text="Password").pack(padx=text_padding, pady=text_padding)
    password_box = ttk.Entry(login_window, show="*")
    password_box.pack(padx=text_padding, pady=text_padding)

    loginstatus = ttk.Label(login_window, text="")
    loginstatus.pack(padx=text_padding, pady=text_padding)

    login_button = ttk.Button(login_window, text="Log In", command=lambda: login(username_box.get(), password_box.get(), loginstatus, login_window))
    login_button.pack(padx=text_padding, pady=text_padding)

def download(url, password, text_widget):
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute("SELECT Key FROM Settings")
    data = c.fetchall()
    key = data[0][0]
    conn.close()

    headers = {
        'Authorization': f'Bearer {key}'
    }

    if not password:
        params = {
            "command": f"mega-get {url} E:\media"
        }
    else:
        params = {
            "command": f'mega-get --password="{password}" {url} E:\media'
        }

    url = f'http://markrainey.me/command'

    try:
        # Send POST request
        response = requests.post(url, headers=headers, json=params)

        if response.status_code == 200:
            # Stream and display output
            text_widget.insert(tk.END, "Download Started\n")
            for chunk in response.iter_lines():
                if chunk:
                    decoded_line = chunk.decode('utf-8')
                    text_widget.insert(tk.END, decoded_line + '\n')
                    text_widget.see(tk.END)  # Auto-scroll
            print('ding')
        elif response.status_code == 401:
            conn = sqlite3.connect(DATABASE_FILE)
            c = conn.cursor()
            c.execute("UPDATE Settings SET Key = ?", ("",))
            conn.commit()
            conn.close()
            updateButtons()
            text_widget.insert(tk.END, "Download Failed: Unauthorized\n Cleared Database\n Please Log In Again \n")
            text_widget.see(tk.END)            
        else:
            text_widget.insert(tk.END, f"Download Failed: {response.status_code}\n")
            text_widget.see(tk.END)

    except requests.exceptions.RequestException as e:
        text_widget.insert(tk.END, f"Download Failed: {str(e)}\n")
        text_widget.see(tk.END)

def start_download(url, password, text_widget):
    print("started download")
    # Use a thread to avoid blocking the main UI
    threading.Thread(target=download, args=(url, password, text_widget), daemon=True).start()
    
def open_download_window():
    global url_box, download_status

    download_window = tk.Toplevel()
    download_window.title("Download File")

    url_label = ttk.Label(download_window, text="URL").pack(padx=10, pady=10)
    url_box = ttk.Entry(download_window)
    url_box.pack(padx=10, pady=10)

    password_label = ttk.Label(download_window, text="Password").pack(padx=10, pady=10)
    password_box = ttk.Entry(download_window)
    password_box.pack(padx=10, pady=10)

    download_status = tk.Text(download_window, wrap=tk.WORD, height=10, width=80)
    download_status.pack(padx=10, pady=10)

    download_button = ttk.Button(
        download_window, text="Download",
        command=lambda: start_download(url_box.get(), password_box.get(), download_status)
    )
    download_button.pack(padx=10, pady=10)

def list_media_folder(window, directory):
    # Fetch API Key from DATABASE_FILE
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute("SELECT Key FROM Settings")
    data = c.fetchall()
    conn.close()

    if not data or not data[0][0]:
        return ["Error: Not logged in or API key missing."]

    key = data[0][0]

    headers = {
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json'
    }

    params = {
        "command": f"dir {directory}"
    }

    url = 'http://markrainey.me/command'

    try:
        response = requests.post(url, headers=headers, json=params)

        if response.status_code == 200:
            try:
                # Ensure the response is valid JSON
                response_data = response.text
                return response_data.strip().splitlines()
            except requests.exceptions.JSONDecodeError:
                return [f"Error: Invalid JSON Response from Server - {response.text}"]
        elif response.status_code == 401:
            conn = sqlite3.connect(DATABASE_FILE)
            c = conn.cursor()
            c.execute("UPDATE Settings SET Key = ?", ("",))
            conn.commit()
            conn.close()
            updateButtons()
            window.destroy()
        else:
            return [f"Error: {response.status_code} - {response.text}"]
    except requests.exceptions.RequestException as e:
        return [f"Error: {str(e)}"]




def show_media_window():
    media_window = tk.Toplevel()
    media_window.title("Media Folder Contents")
    media_window.geometry("800x600")

    tree = ttk.Treeview(media_window, columns=("Name", "Size", "Date", "Time"), show="headings")
    tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    tree.heading("Name", text="Name")
    tree.heading("Size", text="Size (Bytes)")
    tree.heading("Date", text="Date")
    tree.heading("Time", text="Time")

    tree.column("Name", width=300)
    tree.column("Size", width=150, anchor=tk.E)
    tree.column("Date", width=100)
    tree.column("Time", width=100)

    # Initialize current directory
    current_directory = "E:\\media"
    lines = list_media_folder(media_window, current_directory)

    def populate_tree(lines):
        tree.delete(*tree.get_children())

        directories = []
        files = []

        for line in lines:
            if not line.strip() or "Directory of" in line or "bytes free" in line or "E is SSD" in line or "is 1CE8-06DD" in line:
                continue

            try:
                if "<DIR>" in line:
                    date, time, _dir, name = line.split(maxsplit=3)
                    directories.append((name, "dir", date, time))
                else:
                    date, time, size, name = line.split(maxsplit=3)
                    files.append((name, size, date, time))
            except ValueError:
                continue

        # Insert directories first
        for name, size, date, time in directories:
            tree.insert("", tk.END, values=(name, size, date, time))

        # Insert files next
        for name, size, date, time in files:
            tree.insert("", tk.END, values=(name, size, date, time))

    populate_tree(lines)

    def onDoubleClick(event):
        nonlocal current_directory

        item = tree.item(tree.selection())
        values = item['values']

        if not values:
            return

        name = values[0][5:].strip()
        print(values)
        if name == "..":
            new_directory = "\\".join(current_directory.split("\\")[:-1])
            if not new_directory or new_directory == "E:":
                new_directory = "E:\\"
        elif values[1] == "DIR".lower():
            new_directory = f"{current_directory}\\{name}"
            print(new_directory)
        else:
            return  # Not a directory, do nothing

        # Fetch the new directory contents
        new_lines = list_media_folder(media_window, f'"{new_directory}"')
        if new_directory == "E:\\":
            current_directory = "E:"
        else:
            current_directory = new_directory

        # Repopulate tree with new directory contents
        populate_tree(new_lines)

    tree.bind("<Double-1>", onDoubleClick)

    scrollbar = ttk.Scrollbar(media_window, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

def restart_mega(widget):
        conn = sqlite3.connect(DATABASE_FILE)
        c = conn.cursor()
        c.execute("SELECT Key FROM Settings")
        data = c.fetchall()
        key = data[0][0]
        conn.close()

        headers = {
            'Authorization': f'Bearer {key}'
        }

        
        params = {
            "process": f"MEGAcmdServer.exe",
            "start_command": f"C:\\Users\\raine\\AppData\\Local\\MEGAcmd\\MEGAcmdServer"
        }

        url = f'http://markrainey.me/restart'

        try:
            # Send POST request
            response = requests.post(url, headers=headers, json=params)

            if response.status_code == 200:
                widget.config(text="Successfully Restarted Server Process")
            else:
                widget.config(text=f"Restart Failed")
        except requests.exceptions.RequestException as e:
            widget.config(text=f"Restart Failed: {str(e)}")
            return False

def open_settings_window():
    global restart_status
    settings_window = tk.Toplevel()
    settings_window.title("Settings")

    restart_mega_button = ttk.Button(settings_window, text="Restart Mega Server", command = lambda: restart_mega(restart_status))
    restart_mega_button.pack(padx=text_padding, pady=text_padding)
    restart_status = ttk.Label(settings_window, text="")
    restart_status.pack(padx=text_padding, pady=text_padding)
    

global loginstatus, logoutstatus, download_Button, files_Button, settings_Button

login_Button = ttk.Button(text="Login", command=open_login_window)
download_Button = ttk.Button(text="Download File", command=open_download_window)
files_Button = ttk.Button(text="View Files", command=show_media_window)
logout_Button = ttk.Button(text="Logout", command=lambda: logout(logoutstatus))
logoutstatus = ttk.Label(main, text="")

settings_Button = ttk.Button(text="Settings", command=open_settings_window)

if checkLogIn() == False:
    login_Button.pack(padx=text_padding, pady=text_padding)
    logoutstatus.pack(padx=text_padding, pady=text_padding)
else:
    download_Button.pack(padx=text_padding, pady=text_padding)
    files_Button.pack(padx=text_padding, pady=text_padding)
    settings_Button.pack(padx=text_padding, pady=text_padding)
    logout_Button.pack(padx=text_padding, pady=text_padding)
    

main.mainloop()
