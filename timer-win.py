import tkinter as tk
from tkinter import ttk
import time
import threading
from tkinter import messagebox
import os
import sys
import math
from plyer import notification  # Cross-platform notifications

# Helper function to get the correct path for resources when packaged as an exe
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

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
        # Reduced window size to ensure it fits on most screens
        self.root.geometry("800x750")
        self.root.configure(bg='#121212')
        
        # Set app icon if available
        try:
            icon_path = resource_path("timer_icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception:
            pass  # If icon loading fails, just use the default icon
        
        self.running = False
        self.work_time = tk.StringVar(value="60")
        self.break_time = tk.StringVar(value="15")
        self.notifications = []
        self.current_timer = None
        self.is_work_period = True
        
        # Create data directory for settings if it doesn't exist
        self.data_dir = os.path.join(os.path.expanduser("~"), "ProductivityTimer")
        os.makedirs(self.data_dir, exist_ok=True)
        
        self._create_ui()
        
    def _create_ui(self):
        # Create a scrollable canvas to ensure everything fits
        canvas_container = tk.Frame(self.root, bg='#121212')
        canvas_container.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        vscrollbar = ttk.Scrollbar(canvas_container, orient="vertical")
        vscrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create canvas with scrollbar
        canvas = tk.Canvas(canvas_container, bg='#121212', yscrollcommand=vscrollbar.set, highlightthickness=0)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure scrollbar to scroll canvas
        vscrollbar.config(command=canvas.yview)
        
        # Create a frame inside the canvas for all content
        main_frame = tk.Frame(canvas, bg='#121212', padx=20, pady=20)
        
        # Create window in canvas for the frame
        canvas_window = canvas.create_window((0, 0), window=main_frame, anchor="nw")
        
        # Configure the canvas to resize with the window
        def configure_canvas(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Resize the window inside canvas to match canvas width
            canvas.itemconfig(canvas_window, width=event.width)
        
        canvas.bind("<Configure>", configure_canvas)
        
        # Circular Progress Bar - with smaller size for compact layout
        self.progress_bar = CircularProgressBar(main_frame, size=250)
        self.progress_bar.pack(pady=15)
        self.progress_bar.draw(0, "00:00")
        
        # Settings Section - More compact
        settings_frame = tk.Frame(main_frame, bg='#1e1e1e', padx=10, pady=10)
        settings_frame.pack(fill=tk.X, pady=10)
        
        self.work_entry = ModernEntry(settings_frame, "Work Time (minutes)",
                                      textvariable=self.work_time)
        self.work_entry.pack(fill=tk.X, pady=5)
        
        self.break_entry = ModernEntry(settings_frame, "Break Time (minutes)",
                                       textvariable=self.break_time)
        self.break_entry.pack(fill=tk.X, pady=5)
        
        # Notifications Section - More compact
        notif_frame = tk.Frame(main_frame, bg='#1e1e1e', padx=10, pady=10)
        notif_frame.pack(fill=tk.X, pady=10)
        
        notif_heading = create_shadow_label(notif_frame, "Notifications",
                                            font=('Helvetica', 12, 'bold'),
                                            fg='white',
                                            bg='#1e1e1e',
                                            offset=(2,2),
                                            shadow_color='black')
        notif_heading.pack(anchor='w', pady=(0,5))
        
        # Use grid layout for better control of notification input fields
        notif_input_frame = tk.Frame(notif_frame, bg='#1e1e1e')
        notif_input_frame.pack(fill=tk.X, pady=5)
        notif_input_frame.grid_columnconfigure(0, weight=3)
        notif_input_frame.grid_columnconfigure(1, weight=3)
        notif_input_frame.grid_columnconfigure(2, weight=1)
        notif_input_frame.grid_columnconfigure(3, weight=1)
        
        self.notification_percentage = ModernEntry(notif_input_frame, "Percentage")
        self.notification_percentage.grid(row=0, column=0, padx=(0,5), pady=5, sticky="ew")
        
        self.notification_message = ModernEntry(notif_input_frame, "Message")
        self.notification_message.grid(row=0, column=1, padx=(0,5), pady=5, sticky="ew")
        
        # Notification buttons
        add_button = tk.Button(notif_input_frame, text="Add", command=self._add_notification,
                               bg='#3498db', fg='white', font=('Helvetica', 11, 'bold'),
                               relief=tk.FLAT, padx=10, pady=5, bd=0, highlightthickness=0)
        add_button.grid(row=0, column=2, padx=(0,5), pady=5)
        
        clear_notif_button = tk.Button(notif_input_frame, text="Clear", command=self._clear_notifications,
                                       bg='#e67e22', fg='white', font=('Helvetica', 11, 'bold'),
                                       relief=tk.FLAT, padx=10, pady=5, bd=0, highlightthickness=0)
        clear_notif_button.grid(row=0, column=3, padx=(0,5), pady=5)
        
        # Notification text area - smaller height
        self.notifications_text = tk.Text(notif_frame, height=4,
                                          bg='#333333', fg='white',
                                          font=('Helvetica', 10),
                                          relief=tk.FLAT,
                                          padx=6, pady=6)
        self.notifications_text.pack(fill=tk.X, pady=5)
        
        # Control buttons - using grid for better alignment
        button_frame = tk.Frame(main_frame, bg='#121212')
        button_frame.pack(fill=tk.X, pady=10)
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)
        
        self.start_button = tk.Button(button_frame, text="Start",
                                      command=self.start_timer,
                                      bg='#3498db', fg='white',
                                      font=('Helvetica', 12, 'bold'),
                                      relief=tk.FLAT, padx=20, pady=8, bd=0, highlightthickness=0)
        self.start_button.grid(row=0, column=0, padx=5, pady=5)
        
        self.stop_button = tk.Button(button_frame, text="Stop",
                                     command=self.stop_timer,
                                     bg='#e74c3c', fg='white',
                                     font=('Helvetica', 12, 'bold'),
                                     relief=tk.FLAT, padx=20, pady=8, bd=0, highlightthickness=0)
        self.stop_button.grid(row=0, column=1, padx=5, pady=5)

        self.reset_button = tk.Button(button_frame, text="Reset",
                                      command=self._reset_all,
                                      bg='#9b59b6', fg='white',
                                      font=('Helvetica', 12, 'bold'),
                                      relief=tk.FLAT, padx=20, pady=8, bd=0, highlightthickness=0)
        self.reset_button.grid(row=0, column=2, padx=5, pady=5)

        self.status_label = create_shadow_label(main_frame, "Ready",
                                                font=('Helvetica', 12),
                                                fg='white',
                                                bg='#121212',
                                                offset=(1,1),
                                                shadow_color='black')
        self.status_label.pack(pady=5)
        
        # Make sure scrolling works with mousewheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    def _clear_notifications(self):
        self.notifications = []
        self.notifications_text.delete('1.0', tk.END)

    def _reset_all(self):
        self.stop_timer()
        self.work_time.set("60")
        self.break_time.set("15")
        self._clear_notifications()
        self.progress_bar.draw(0, "00:00")
        self._update_status("Ready")
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
        self._update_status("Stopped")
        
    def _timer_loop(self):
        while self.running:
            try:
                minutes = int(self.work_time.get()) if self.is_work_period else int(self.break_time.get())
                seconds = minutes * 60
                total_seconds = seconds
                tolerance = (100 / total_seconds) / 2.0
                
                # Update status at start of timer
                current_mode = "Work" if self.is_work_period else "Break"
                self._update_status(f"{current_mode} in progress")
                
                for remaining in range(seconds, -1, -1):
                    if not self.running:
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
                                notif.triggered = True
                    time.sleep(1)
                period_type = "Work" if self.is_work_period else "Break"
                self._send_notification(f"{period_type} period completed!")
                if self.is_work_period:
                    self._update_status(f"Work period complete! Taking a break.")
                else:
                    self._update_status(f"Break complete! Starting work period.")
                self.is_work_period = not self.is_work_period
            except ValueError:
                self._send_notification("Please enter valid numbers for timer settings!")
                self.stop_timer()
                break
    
    def _update_status(self, message):
        # Safely update the status label
        if hasattr(self, 'status_label') and self.status_label.winfo_exists():
            self.status_label.destroy()
        
        self.status_label = create_shadow_label(self.root, message,
                                                font=('Helvetica', 12),
                                                fg='white',
                                                bg='#121212',
                                                offset=(1,1),
                                                shadow_color='black')
        self.status_label.pack(pady=5)
    
    def _send_notification(self, message):
        try:
            # Use plyer for notifications
            notification.notify(
                title="Productivity Timer",
                message=message,
                app_name="Productivity Timer",
                timeout=10
            )
        except Exception as e:
            # Fallback to tkinter messagebox if plyer fails
            self.root.after(0, lambda: messagebox.showinfo("Productivity Timer", message))
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ProductivityTimer()
    app.run()