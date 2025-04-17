#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk
import time
import threading
import math
import os
import subprocess
from tkinter import messagebox
import sys

# Try to import notify2, but provide fallbacks if not available
try:
    import notify2
    HAS_NOTIFY2 = True
except ImportError:
    HAS_NOTIFY2 = False

# Helper function to create a label with a shadow effect.
def create_shadow_label(parent, text, font, fg, bg, offset=(2,2), shadow_color="black"):
    container = tk.Frame(parent, bg=bg)
    shadow = tk.Label(container, text=text, font=font, fg=shadow_color, bg=bg)
    shadow.place(x=offset[0], y=offset[1])
    label = tk.Label(container, text=text, font=font, fg=fg, bg=bg)
    label.place(x=0, y=0)
    container.update_idletasks()
    container.config(width=label.winfo_width() + offset[0], height=label.winfo_height() + offset[1])
    return container

class CircularProgressBar(tk.Canvas):
    def __init__(self, parent, size=300, **kwargs):
        super().__init__(parent, width=size, height=size, highlightthickness=0, **kwargs)
        self.size = size
        # Dark background for the progress area
        self.configure(bg='#1e1e1e')
        self.angle = 0

    def draw(self, percent=0, time_text="00:00"):
        self.delete("all")
        padding = 10
        # Draw the progress arc only if percent > 0
        if percent > 0:
            start_angle = 90
            angle = -360 * (percent / 100)
            self.create_arc(padding, padding, self.size - padding, self.size - padding,
                            start=start_angle, extent=angle,
                            outline="#3498db", width=8, style="arc")
        # Always display the time text in the center
        self.create_text(self.size / 2, self.size / 2, text=time_text,
                         font=('Helvetica', 48, 'bold'), fill='white')

class ModernEntry(tk.Frame):
    def __init__(self, parent, label_text, **kwargs):
        # Use a slightly larger font (12 instead of 10) for the label.
        super().__init__(parent, bg='#1e1e1e')
        # Increased padding by about 10%
        self.container = tk.Frame(self, bg='#1e1e1e', padx=6, pady=6)
        self.container.pack(fill=tk.X, expand=True)
        shadow_label = create_shadow_label(self.container, label_text,
                                           font=('Helvetica', 12),
                                           fg='white',
                                           bg='#1e1e1e',
                                           offset=(1,1),
                                           shadow_color="black")
        shadow_label.pack(anchor='w', pady=(0,6))
        self.entry = tk.Entry(self.container, **kwargs)
        self.entry.configure(
            relief=tk.FLAT,
            bg='#333333',
            fg='white',
            insertbackground='white',
            font=('Helvetica', 12),
            bd=0,
            highlightthickness=1,
            highlightcolor='#3498db',
            highlightbackground='#333333'
        )
        # Increase the internal vertical padding and external padding by about 10%
        self.entry.pack(fill=tk.X, pady=(6,7), ipady=4, padx=4)
        
    def get(self):
        return self.entry.get()
        
    def delete(self, first, last):
        return self.entry.delete(first, last)
        
    def insert(self, index, string):
        return self.entry.insert(index, string)

class NotificationEntry:
    def __init__(self, percentage, message):
        self.percentage = percentage
        self.message = message
        self.triggered = False  # To track if notification has been fired

class ProductivityTimer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Productivity Timer")
        self.root.geometry("1100x1000")
        self.root.configure(bg='#121212')
        
        # Initialize notification system
        self.has_notifications = False
        if HAS_NOTIFY2:
            try:
                notify2.init('Productivity Timer')
                self.has_notifications = True
            except Exception:
                pass
        
        # Set up icon if it exists
        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(script_dir, "timer_icon.png")
        if os.path.exists(icon_path):
            try:
                self.root.iconphoto(True, tk.PhotoImage(file=icon_path))
            except Exception:
                pass
        
        self.running = False
        self.work_time = tk.StringVar(value="60")
        self.break_time = tk.StringVar(value="15")
        self.notifications = []
        self.current_timer = None
        self.is_work_period = True
        
        self._create_ui()
        
    def _create_ui(self):
        # Increase main frame padding by about 10%
        main_frame = tk.Frame(self.root, bg='#121212', padx=22, pady=22)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Circular Progress Bar
        self.progress_bar = CircularProgressBar(main_frame)
        self.progress_bar.pack(pady=22)
        self.progress_bar.draw(0, "00:00")
        
        settings_frame = tk.Frame(main_frame, bg='#1e1e1e', padx=11, pady=11)
        settings_frame.pack(fill=tk.X, pady=11)
        
        self.work_entry = ModernEntry(settings_frame, "Work Time (minutes)",
                                      textvariable=self.work_time)
        self.work_entry.pack(fill=tk.X, pady=6)
        
        self.break_entry = ModernEntry(settings_frame, "Break Time (minutes)",
                                       textvariable=self.break_time)
        self.break_entry.pack(fill=tk.X, pady=6)
        
        notif_frame = tk.Frame(main_frame, bg='#1e1e1e', padx=11, pady=11)
        notif_frame.pack(fill=tk.X, pady=11)
        
        notif_heading = create_shadow_label(notif_frame, "Notifications",
                                            font=('Helvetica', 12, 'bold'),
                                            fg='white',
                                            bg='#121212',
                                            offset=(2,2),
                                            shadow_color='black')
        notif_heading.pack(anchor='w', pady=(0,6))
        
        notif_input_frame = tk.Frame(notif_frame, bg='#1e1e1e')
        notif_input_frame.pack(fill=tk.X, pady=6)
        
        self.notification_percentage = ModernEntry(notif_input_frame, "Percentage")
        self.notification_percentage.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,6))
        
        self.notification_message = ModernEntry(notif_input_frame, "Message")
        self.notification_message.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,6))
        
        # Notification buttons with larger padding.
        add_button = tk.Button(notif_input_frame, text="Add", command=self._add_notification,
                               bg='#3498db', fg='white', font=('Helvetica', 12, 'bold'),
                               relief=tk.FLAT, padx=22, pady=6, bd=0, highlightthickness=0)
        add_button.pack(side=tk.LEFT, pady=6)
        
        clear_notif_button = tk.Button(notif_input_frame, text="Clear", command=self._clear_notifications,
                                       bg='#e67e22', fg='white', font=('Helvetica', 12, 'bold'),
                                       relief=tk.FLAT, padx=22, pady=6, bd=0, highlightthickness=0)
        clear_notif_button.pack(side=tk.LEFT, padx=6, pady=6)
        
        self.notifications_text = tk.Text(notif_frame, height=5,
                                          bg='#333333', fg='white',
                                          font=('Helvetica', 10),
                                          relief=tk.FLAT,
                                          padx=6, pady=6)
        self.notifications_text.pack(fill=tk.X, pady=6)
        
        button_frame = tk.Frame(main_frame, bg='#121212')
        button_frame.pack(pady=11)
        
        self.start_button = tk.Button(button_frame, text="Start",
                                      command=self.start_timer,
                                      bg='#3498db', fg='white',
                                      font=('Helvetica', 12, 'bold'),
                                      relief=tk.FLAT, padx=22, pady=8, bd=0, highlightthickness=0)
        self.start_button.pack(side=tk.LEFT, padx=6, pady=10)
        
        self.stop_button = tk.Button(button_frame, text="Stop",
                                     command=self.stop_timer,
                                     bg='#e74c3c', fg='white',
                                     font=('Helvetica', 12, 'bold'),
                                     relief=tk.FLAT, padx=22, pady=8, bd=0, highlightthickness=0)
        self.stop_button.pack(side=tk.LEFT, padx=6, pady=10)

        self.reset_button = tk.Button(button_frame, text="Reset",
                                      command=self._reset_all,
                                      bg='#9b59b6', fg='white',
                                      font=('Helvetica', 12, 'bold'),
                                      relief=tk.FLAT, padx=22, pady=8, bd=0, highlightthickness=0)
        self.reset_button.pack(side=tk.LEFT, padx=6, pady=10)

        self.status_label = create_shadow_label(main_frame, "Ready",
                                                font=('Helvetica', 12),
                                                fg='white',
                                                bg='#121212',
                                                offset=(1,1),
                                                shadow_color='black')
        self.status_label.pack(pady=6)
        
        # Show notification status
        if not self.has_notifications:
            notification_status = create_shadow_label(
                main_frame, 
                "Note: notify2 module not found. Desktop notifications disabled.",
                font=('Helvetica', 10),
                fg='yellow',
                bg='#121212',
                offset=(1,1),
                shadow_color='black'
            )
            notification_status.pack(pady=6)
    
    def _clear_notifications(self):
        self.notifications = []
        self.notifications_text.delete('1.0', tk.END)

    def _reset_all(self):
        self.stop_timer()
        self.work_time.set("60")
        self.break_time.set("15")
        self._clear_notifications()
        self.progress_bar.draw(0, "00:00")
        self.status_label.destroy()
        self.status_label = create_shadow_label(self.root, "Ready",
                                                font=('Helvetica', 12),
                                                fg='white',
                                                bg='#121212',
                                                offset=(1,1),
                                                shadow_color='black')
        self.status_label.pack(pady=6)
        self.is_work_period = True

    def _add_notification(self):
        try:
            percentage = float(self.notification_percentage.get())
            message = self.notification_message.get()
            if 0 <= percentage <= 100 and message:
                notif = NotificationEntry(percentage, message)
                self.notifications.append(notif)
                self.notifications_text.insert(tk.END, f"{percentage}% - {message}\n")
                self.notification_percentage.delete(0, tk.END)
                self.notification_message.delete(0, tk.END)
            else:
                messagebox.showerror("Error", "Please enter valid percentage (0-100) and message")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number for percentage")
    
    def start_timer(self):
        if not self.running:
            self.running = True
            # Reset notification triggers for a new period.
            for notif in self.notifications:
                notif.triggered = False
            self.current_timer = threading.Thread(target=self._timer_loop)
            self.current_timer.daemon = True
            self.current_timer.start()
            self.start_button.config(state='disabled')
            
    def stop_timer(self):
        self.running = False
        self.start_button.config(state='normal')
        if hasattr(self, 'status_label') and self.status_label:
            self.status_label.destroy()
        self.status_label = create_shadow_label(self.root, "Stopped",
                                                font=('Helvetica', 12),
                                                fg='white',
                                                bg='#121212',
                                                offset=(1,1),
                                                shadow_color='black')
        self.status_label.pack(pady=6)
        
    def _timer_loop(self):
        try:
            period_status = create_shadow_label(
                self.root, 
                "Work Period" if self.is_work_period else "Break Period",
                font=('Helvetica', 12, 'bold'),
                fg='#3498db' if self.is_work_period else '#2ecc71',
                bg='#121212',
                offset=(1,1),
                shadow_color='black'
            )
            period_status.pack(pady=6)
            
            while self.running:
                try:
                    minutes = int(self.work_time.get()) if self.is_work_period else int(self.break_time.get())
                    seconds = minutes * 60
                    total_seconds = seconds
                    tolerance = (100 / total_seconds) / 2.0
                    for remaining in range(seconds, -1, -1):
                        if not self.running:
                            if period_status:
                                period_status.destroy()
                            return
                        mins, secs = divmod(remaining, 60)
                        time_text = f"{mins:02d}:{secs:02d}"
                        progress = ((total_seconds - remaining) / total_seconds) * 100
                        self.root.after(0, lambda p=progress, t=time_text: self.progress_bar.draw(p, t))
                        if self.is_work_period:
                            current_percentage = ((total_seconds - remaining) / total_seconds) * 100
                            for notif in self.notifications:
                                if (not notif.triggered and 
                                    abs(current_percentage - notif.percentage) <= tolerance):
                                    self._send_notification(notif.message)
                                    self._flash_screen()
                                    notif.triggered = True
                        time.sleep(1)
                    period_type = "Work" if self.is_work_period else "Break"
                    self._send_notification(f"{period_type} period completed!")
                    self._flash_screen()
                    if self.is_work_period:
                        self._clear_notifications()
                    self.is_work_period = not self.is_work_period
                    if period_status:
                        period_status.destroy()
                    period_status = create_shadow_label(
                        self.root, 
                        "Work Period" if self.is_work_period else "Break Period",
                        font=('Helvetica', 12, 'bold'),
                        fg='#3498db' if self.is_work_period else '#2ecc71',
                        bg='#121212',
                        offset=(1,1),
                        shadow_color='black'
                    )
                    period_status.pack(pady=6)
                except ValueError:
                    self._send_notification("Please enter valid numbers for timer settings!")
                    self.stop_timer()
                    if period_status:
                        period_status.destroy()
                    break
        except Exception as e:
            self.stop_timer()
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            if period_status:
                period_status.destroy()
    
    def _send_notification(self, message):
        # Show notification in a dialog if notify2 is not available
        if not self.has_notifications:
            self.root.after(0, lambda: messagebox.showinfo("Productivity Timer", message))
            return
            
        try:
            notification = notify2.Notification(
                "Productivity Timer",
                message,
                "dialog-information"
            )
            notification.show()
        except Exception:
            # Fallback to message box if notification fails
            self.root.after(0, lambda: messagebox.showinfo("Productivity Timer", message))
    
    def _flash_screen(self):
        try:
            # Fixed xrandr command for screen flashing
            # Get the primary display
            process = subprocess.Popen(
                ["xrandr", "--current"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True
            )
            output, _ = process.communicate()
            
            # Find primary display
            primary_display = None
            for line in output.split('\n'):
                if " connected " in line and "primary" in line:
                    primary_display = line.split()[0]
                    break
            
            if primary_display:
                # Flash the screen
                subprocess.run(["xrandr", "--output", primary_display, "--brightness", "0.1"])
                time.sleep(0.2)
                subprocess.run(["xrandr", "--output", primary_display, "--brightness", "1"])
        except Exception:
            # Silently fail if screen flashing doesn't work
            pass
    
    def run(self):
        self.root.mainloop()

# Create executable detection for proper script location
def get_script_path():
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return base_path

if __name__ == "__main__":
    # Set working directory to script location
    os.chdir(get_script_path())
    
    # Check for dependencies
    if not HAS_NOTIFY2:
        print("Warning: notify2 module not found. Desktop notifications will be disabled.")
        print("To enable notifications, install notify2 with: pip install notify2")
    
    # Run application
    app = ProductivityTimer()
    app.run()
