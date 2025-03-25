import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from tkcalendar import DateEntry
import pytz
import csv
import os

# Timezones
TIMEZONES = {
    "EST": "US/Eastern",
    "CST": "America/Chicago",
    "IST": "Asia/Kolkata"
}

meetings = []

def save_meetings_to_csv():
    with open("meetings.csv", mode='w', newline='') as file:
        writer = csv.writer(file)
        #writer.writerow(["Title", "EST", "CST", "IST"])
        writer.writerow(["Title", "DateTime", "TimeZone"])
        for title, dt, tz in meetings:
            #writer.writerow([title, times["EST"], times["CST"], times["IST"]])
            writer.writerow([title, dt.strftime("%Y-%m-%d %I:%M %p"), tz])

def load_meetings_from_csv():
    if not os.path.exists("meetings.csv"):
        return
    with open("meetings.csv", mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            title = row["Title"]
            dt = datetime.strptime(row["DateTime"], "%Y-%m-%d %I:%M %p")
            tz = row["TimeZone"]
            meetings.append((title, dt, tz))

def convert_time(meeting_time, base_tz):
    base = pytz.timezone(TIMEZONES[base_tz])
    local_dt = base.localize(meeting_time)
    conversions = {}
    for label, tz in TIMEZONES.items():
        target = pytz.timezone(tz)
        conversions[label] = local_dt.astimezone(target).strftime('%Y-%m-%d %I:%M %p')
    return conversions

def add_meeting():
    title = title_entry.get()
    date_str = date_var.get()
    hour = hour_combo.get()
    minute = minute_combo.get()
    ampm = ampm_combo.get()
    base_tz = tz_combo.get()

    if not title or not date_str or not hour or not minute or not ampm:
        messagebox.showerror("Missing Info", "Please fill in all fields.")
        return

    try:
        time_str = f"{hour}:{minute} {ampm}"
        meeting_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %I:%M %p")
    except ValueError as ve:
        messagebox.showerror("Invalid Format", f"Check date/time format: {ve}")
        return
    except Exception as e:
        messagebox.showerror("Error", f"Unexpected error: {e}")
        return

    meetings.append((title, meeting_time, base_tz))
    save_meetings_to_csv()
    update_meeting_list()
    clear_fields()

def update_meeting_list():
    meeting_list.delete(*meeting_list.get_children())

    # Sort by datetime (in CST timezone)
    def sort_key(item):
        title, dt, tz = item
        local = pytz.timezone(TIMEZONES[tz]).localize(dt)
        return local.astimezone(pytz.timezone("America/Chicago"))

    sorted_meetings = sorted(meetings, key=sort_key)

    for title, dt, tz in sorted_meetings:
        converted_times = convert_time(dt, tz)
        meeting_list.insert('', 'end', values=(title, converted_times["EST"], converted_times["CST"], converted_times["IST"]))


def clear_fields():
    title_entry.delete(0, tk.END)
    date_var.set('')
    hour_combo.set("01")
    minute_combo.set("00")
    ampm_combo.set("AM")

def delete_meeting():
    selected = meeting_list.focus()
    if not selected:
        messagebox.showwarning("No Selection", "Please select a meeting to delete.")
        return

    confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this meeting?")
    if not confirm:
        return

    try:
        del meetings[meeting_list.index(selected)]
        update_meeting_list()
        save_meetings_to_csv()
        clear_fields()
    except Exception as e:
        messagebox.showerror("Error", f"Could not delete: {e}")


# GUI setup
root = tk.Tk()
root.title("Meeting Scheduler")

# Fix macOS theme rendering for calendar
style = ttk.Style(root)
style.theme_use('clam')

# Meeting Title
tk.Label(root, text="Meeting Title").grid(row=0, column=0, sticky="w")
title_entry = tk.Entry(root, bg='white', fg='black')
title_entry.grid(row=0, column=1, sticky="ew", columnspan=2)

# Date Picker
tk.Label(root, text="Date").grid(row=1, column=0, sticky="w")
date_var = tk.StringVar()
date_entry = DateEntry(
    root,
    textvariable=date_var,
    date_pattern='yyyy-mm-dd',
    foreground='black',
    background='white',
    borderwidth=2
)
date_entry.grid(row=1, column=1, columnspan=2, sticky="ew")
date_var.set('')

# Time Picker
tk.Label(root, text="Time").grid(row=2, column=0, sticky="w")
hour_combo = ttk.Combobox(root, values=[f"{h:02}" for h in range(1, 13)], width=3, state="readonly")
hour_combo.grid(row=2, column=1, sticky="w")
hour_combo.set("01")

minute_combo = ttk.Combobox(root, values=["00", "15", "30", "45"], width=3, state="readonly")
minute_combo.grid(row=2, column=1)
minute_combo.set("00")

ampm_combo = ttk.Combobox(root, values=["AM", "PM"], width=3, state="readonly")
ampm_combo.grid(row=2, column=1, sticky="e")
ampm_combo.set("AM")

# Time Zone
tk.Label(root, text="Base Time Zone").grid(row=3, column=0, sticky="w")
tz_combo = ttk.Combobox(root, values=list(TIMEZONES.keys()), state="readonly")
tz_combo.grid(row=3, column=1, columnspan=2, sticky="ew")
tz_combo.set("CST")

# Buttons
tk.Button(root, text="Add Meeting", command=add_meeting).grid(row=4, column=0, columnspan=2, pady=10)
tk.Button(root, text="Delete Meeting", command=delete_meeting).grid(row=4, column=2, pady=10)

# Table
columns = ("Title", "EST", "CST", "IST")
meeting_list = ttk.Treeview(root, columns=columns, show="headings")
for col in columns:
    meeting_list.heading(col, text=col)
meeting_list.grid(row=5, column=0, columnspan=3, sticky="nsew")

root.columnconfigure(1, weight=1)
root.columnconfigure(2, weight=1)

# Load and Run
load_meetings_from_csv()
update_meeting_list()
root.mainloop()