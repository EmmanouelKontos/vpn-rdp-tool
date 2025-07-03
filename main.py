import customtkinter as ctk
from tkinter import messagebox, filedialog
import settings_manager as sm
import vpn_manager as vm
import wol_manager as wm
import rdp_manager as rm
import icon_manager as im
import update_manager as um
import threading
import time
from datetime import datetime
from PIL import Image
from tkinter import PhotoImage
import os
import sys
import subprocess
import platform

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Universal VPN & RDP Tool")
        self.geometry("800x600")
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # Load Icons
        self.icons = {name: ctk.CTkImage(Image.open(path)) for name, path in im.get_all_icons().items()}
        try:
            app_icon_path = im.get_app_icon()
            self.app_icon = PhotoImage(file=app_icon_path)
            self.wm_iconphoto(True, self.app_icon)
        except Exception as e:
            print(f"Error setting application icon: {e}")


        self.settings = sm.load_settings()
        self.vpn_active = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1) # Row for tab_view
        self.grid_rowconfigure(1, weight=0) # Row for status bar

        self.tab_view = ctk.CTkTabview(self, anchor="w")
        self.tab_view.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Status Bar
        self.status_bar = ctk.CTkFrame(self)
        self.status_bar.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.status_bar.grid_columnconfigure(0, weight=1)
        self.version_label = ctk.CTkLabel(self.status_bar, text=f"Version: {um.CURRENT_VERSION}", font=ctk.CTkFont(size=12))
        self.version_label.grid(row=0, column=0, padx=10, pady=5, sticky="e")

        self.home_tab = self.tab_view.add("Home")
        self.settings_tab = self.tab_view.add("Settings")

        self.create_home_tab()
        self.create_settings_tab()
        self.log("Application started.")
        self.after(100, self.check_for_updates_on_startup) # Check for updates shortly after startup

    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert(ctk.END, f"[{timestamp}] {message}\n")
        self.log_textbox.configure(state="disabled")
        self.log_textbox.see(ctk.END)

    def create_home_tab(self):
        self.home_tab.grid_columnconfigure(0, weight=0) # Control frame, fixed size
        self.home_tab.grid_columnconfigure(1, weight=1) # Log frame, expands
        self.home_tab.grid_rowconfigure(0, weight=1)

        control_frame = ctk.CTkFrame(self.home_tab)
        control_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ns")

        ctk.CTkLabel(control_frame, text="Controls", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        ctk.CTkLabel(control_frame, text="Select Host:").pack(padx=10, pady=(10,0), anchor="w")
        self.host_variable = ctk.StringVar()
        self.host_dropdown = ctk.CTkOptionMenu(control_frame, variable=self.host_variable, values=[h['name'] for h in self.settings.get('hosts', [])])
        self.host_dropdown.pack(fill="x", padx=10, pady=5)

        self.vpn_status_label = ctk.CTkLabel(control_frame, text="VPN: Disconnected", text_color="red")
        self.vpn_status_label.pack(pady=10)

        self.connect_btn = ctk.CTkButton(control_frame, text="Connect VPN", image=self.icons['connect'], command=self.toggle_vpn_connection)
        self.connect_btn.pack(fill="x", padx=10, pady=5)

        self.wake_btn = ctk.CTkButton(control_frame, text="Wake Host", image=self.icons['wake'], command=self.wake_host)
        self.wake_btn.pack(fill="x", padx=10, pady=5)

        self.rdp_btn = ctk.CTkButton(control_frame, text="Launch RDP", image=self.icons['rdp'], command=self.launch_rdp)
        self.rdp_btn.pack(fill="x", padx=10, pady=5)
        
        self.progress_bar = ctk.CTkProgressBar(control_frame, mode='indeterminate')
        self.download_progress_bar = ctk.CTkProgressBar(control_frame, mode='determinate')
        self.download_percentage_label = ctk.CTkLabel(control_frame, text="")

        log_frame = ctk.CTkFrame(self.home_tab)
        log_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        log_frame.grid_rowconfigure(1, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(log_frame, text="Activity Log", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, pady=10)
        self.log_textbox = ctk.CTkTextbox(log_frame, state="disabled", wrap="word")
        self.log_textbox.grid(row=1, column=0, padx=10, pady=(0,10), sticky="nsew")

    def create_settings_tab(self):
        self.settings_tab.grid_columnconfigure(0, weight=1)
        self.settings_tab.grid_rowconfigure(0, weight=0) # For wg_frame
        self.settings_tab.grid_rowconfigure(1, weight=1) # For host_mgmt_frame
        self.settings_tab.grid_rowconfigure(2, weight=0) # For bottom_buttons_frame

        wg_frame = ctk.CTkFrame(self.settings_tab)
        wg_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        wg_frame.grid_columnconfigure(1, weight=1) # Make entry expand
        ctk.CTkLabel(wg_frame, text="WireGuard Config Path:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.wg_path_entry = ctk.CTkEntry(wg_frame)
        self.wg_path_entry.insert(0, self.settings.get('wireguard_config_path', ''))
        self.wg_path_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(wg_frame, text="Browse...", command=self.browse_wg_config).grid(row=0, column=2, padx=5, pady=5)

        host_mgmt_frame = ctk.CTkFrame(self.settings_tab)
        host_mgmt_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        host_mgmt_frame.grid_rowconfigure(1, weight=1) # Make listbox expand
        host_mgmt_frame.grid_rowconfigure(2, weight=0) # For edit_frame
        host_mgmt_frame.grid_rowconfigure(3, weight=0) # For btn_frame
        host_mgmt_frame.grid_columnconfigure(0, weight=1) # Make content expand
        ctk.CTkLabel(host_mgmt_frame, text="Host Profiles", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, pady=5)

        self.host_listbox = ctk.CTkTextbox(host_mgmt_frame, wrap="none")
        self.host_listbox.grid(row=1, column=0, pady=5, padx=10, sticky="nsew")
        self.host_listbox.bind("<<ListboxSelect>>", self.on_host_select)
        self.update_host_listbox()

        edit_frame = ctk.CTkFrame(host_mgmt_frame)
        edit_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        edit_frame.grid_columnconfigure(1, weight=1) # Make entry fields expand

        ctk.CTkLabel(edit_frame, text="Name:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.name_entry = ctk.CTkEntry(edit_frame)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkLabel(edit_frame, text="IP Address:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.ip_entry = ctk.CTkEntry(edit_frame)
        self.ip_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkLabel(edit_frame, text="MAC Address:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.mac_entry = ctk.CTkEntry(edit_frame)
        self.mac_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkLabel(edit_frame, text="RDP User:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.user_entry = ctk.CTkEntry(edit_frame)
        self.user_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        btn_frame = ctk.CTkFrame(host_mgmt_frame)
        btn_frame.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        btn_frame.grid_columnconfigure((0,1,2), weight=1) # Make buttons expand
        ctk.CTkButton(btn_frame, text="Add", command=self.add_host).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(btn_frame, text="Update", command=self.update_host).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(btn_frame, text="Remove", command=self.remove_host).grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        
        # New frame for Save and Update Check buttons
        bottom_buttons_frame = ctk.CTkFrame(self.settings_tab)
        bottom_buttons_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        bottom_buttons_frame.grid_columnconfigure((0,1), weight=1)
        ctk.CTkButton(bottom_buttons_frame, text="Save All Settings", command=self.save_settings).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(bottom_buttons_frame, text="Check for Updates", command=self.check_for_updates_gui).grid(row=0, column=1, padx=5, pady=5, sticky="ew")

    def browse_wg_config(self):
        filepath = filedialog.askopenfilename(title="Select WireGuard Configuration File")
        if filepath:
            self.wg_path_entry.delete(0, ctk.END)
            self.wg_path_entry.insert(0, filepath)
            self.log(f"Selected WireGuard config: {filepath}")

    def update_host_listbox(self):
        self.host_listbox.configure(state="normal")
        self.host_listbox.delete("1.0", ctk.END)
        for host in self.settings.get('hosts', []):
            self.host_listbox.insert(ctk.END, f"{host['name']} ({host['ip_address']})\n")
        self.update_host_dropdown()

    def on_host_select(self, event=None):
        # This event is for the Textbox, we need to get the selected line
        selected_index = self.host_listbox.index(ctk.INSERT).split('.')[0]
        if selected_index:
            try:
                selected_index = int(selected_index) - 1 # Convert to 0-based index
                if 0 <= selected_index < len(self.settings.get('hosts', [])):
                    host = self.settings.get('hosts', [])[selected_index]
                    self.name_entry.delete(0, ctk.END)
                    self.name_entry.insert(0, host.get('name', ''))
                    self.ip_entry.delete(0, ctk.END)
                    self.ip_entry.insert(0, host.get('ip_address', ''))
                    self.mac_entry.delete(0, ctk.END)
                    self.mac_entry.insert(0, host.get('mac_address', ''))
                    self.user_entry.delete(0, ctk.END)
                    self.user_entry.insert(0, host.get('rdp_user', ''))
            except (ValueError, IndexError):
                pass # Ignore errors if the line is invalid or out of range

    def update_host_dropdown(self):
        host_names = [h['name'] for h in self.settings.get('hosts', [])]
        if not host_names:
            host_names = ["No hosts configured"]
        self.host_dropdown.configure(values=host_names)
        if len(host_names) > 1:
            self.host_dropdown.set(host_names[0])

    def add_host(self):
        host = {
            "name": self.name_entry.get(), "ip_address": self.ip_entry.get(),
            "mac_address": self.mac_entry.get(), "rdp_user": self.user_entry.get()
        }
        if all(host.values()):
            self.settings.setdefault('hosts', []).append(host)
            self.update_host_listbox()
            self.clear_host_entries()
            self.log(f"Added host: {host['name']}")
        else:
            messagebox.showerror("Error", "All host fields are required.")

    def update_host(self):
        selected_host_name = self.host_variable.get()
        if not selected_host_name or selected_host_name == "No hosts configured":
            messagebox.showerror("Error", "No host selected to update.")
            return
        for i, host in enumerate(self.settings.get('hosts', [])):
            if host['name'] == selected_host_name:
                updated_host = {
                    "name": self.name_entry.get(), "ip_address": self.ip_entry.get(),
                    "mac_address": self.mac_entry.get(), "rdp_user": self.user_entry.get()
                }
                self.settings['hosts'][i] = updated_host
                self.update_host_listbox()
                self.clear_host_entries()
                self.log(f"Updated host: {updated_host['name']}")
                return

    def remove_host(self):
        selected_host_name = self.host_variable.get()
        if not selected_host_name or selected_host_name == "No hosts configured":
            messagebox.showerror("Error", "No host selected to remove.")
            return
        self.settings['hosts'] = [h for h in self.settings.get('hosts', []) if h['name'] != selected_host_name]
        self.update_host_listbox()
        self.log(f"Removed host: {selected_host_name}")

    def clear_host_entries(self):
        self.name_entry.delete(0, ctk.END)
        self.ip_entry.delete(0, ctk.END)
        self.mac_entry.delete(0, ctk.END)
        self.user_entry.delete(0, ctk.END)

    def save_settings(self):
        self.settings['wireguard_config_path'] = self.wg_path_entry.get()
        sm.save_settings(self.settings)
        self.log("Settings saved successfully.")
        messagebox.showinfo("Success", "Settings have been saved.")

    def get_selected_host(self):
        selected_host_name = self.host_variable.get()
        if selected_host_name == "No hosts configured": return None
        return next((h for h in self.settings.get('hosts', []) if h['name'] == selected_host_name), None)

    def toggle_vpn_connection(self):
        if self.vpn_active:
            self.disconnect_vpn()
        else:
            self.connect_vpn()

    def connect_vpn(self):
        config_path = self.settings.get('wireguard_config_path')
        if not config_path:
            messagebox.showerror("Error", "WireGuard config path not set in Settings.")
            return
        self.log("VPN connection process started...")
        self.progress_bar.pack(fill="x", padx=10, pady=5)
        self.progress_bar.start()
        self.connect_btn.configure(state="disabled")
        
        threading.Thread(target=self._execute_vpn_connect, args=(config_path,), daemon=True).start()

    def _execute_vpn_connect(self, config_path):
        success, message = vm.connect_vpn(config_path)
        self.after(100, self.on_vpn_connect_done, success, message)

    def on_vpn_connect_done(self, success, message):
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.connect_btn.configure(state="normal")
        self.log(message)
        if success:
            self.vpn_active = True
            self.vpn_status_label.configure(text="VPN: Connected", text_color="green")
            self.connect_btn.configure(text="Disconnect VPN", image=self.icons['disconnect'])
        else:
            self.vpn_status_label.configure(text="VPN: Failed", text_color="red")
            messagebox.showerror("VPN Error", message)

    def disconnect_vpn(self):
        config_path = self.settings.get('wireguard_config_path')
        self.log("VPN disconnection process started...")
        success, message = vm.disconnect_vpn(config_path)
        self.log(message)
        if success:
            self.vpn_active = False
            self.vpn_status_label.configure(text="VPN: Disconnected", text_color="red")
            self.connect_btn.configure(text="Connect VPN", image=self.icons['connect'])
        else:
            messagebox.showerror("VPN Error", message)

    def wake_host(self):
        host = self.get_selected_host()
        if not host:
            messagebox.showerror("Error", "No host selected.")
            return
        self.log(f"Sending Wake-on-LAN packet to {host['name']} ({host['mac_address']})...")
        success, message = wm.wake_host(host['mac_address'])
        self.log(message)
        if success:
            messagebox.showinfo("Wake-on-LAN", f"Magic packet sent to {host['name']}.")
        else:
            messagebox.showerror("Wake-on-LAN Error", message)

    def launch_rdp(self):
        host = self.get_selected_host()
        if not host:
            messagebox.showerror("Error", "No host selected.")
            return
        self.log(f"Launching RDP for {host['name']} at {host['ip_address']}...")
        success, message = rm.launch_rdp(host['ip_address'], host.get('rdp_user'))
        self.log(message)
        if not success:
            messagebox.showerror("RDP Error", message)

    def check_for_updates_on_startup(self):
        self.log("Checking for updates...")
        threading.Thread(target=self._check_for_updates_thread, args=(True,), daemon=True).start()

    def check_for_updates_gui(self):
        self.log("Manually checking for updates...")
        threading.Thread(target=self._check_for_updates_thread, args=(False,), daemon=True).start()

    def _check_for_updates_thread(self, startup_check=False):
        update_available, latest_version, assets = um.check_for_updates()
        if update_available:
            self.after(100, self._handle_update_available, latest_version, assets)
        else:
            if not startup_check:
                self.after(100, lambda: messagebox.showinfo("No Updates", "You are running the latest version."))
            self.log("No updates available.")

    def _handle_update_available(self, latest_version, assets):
        self.log(f"Update available! Latest version: {latest_version}")
        response = messagebox.askyesno("Update Available",
                                       f"A new version ({latest_version}) is available. Do you want to download it now?")
        if response:
            self.log("Downloading update...")
            self.download_progress_bar.pack(fill="x", padx=10, pady=5)
            self.download_percentage_label.pack(pady=(0,5))
            self.download_progress_bar.set(0)
            threading.Thread(target=self._download_update_thread, args=(assets,), daemon=True).start()

    def _update_download_progress_gui(self, downloaded, total):
        if total > 0:
            progress = downloaded / total
            percentage = int(progress * 100)
            self.download_progress_bar.set(progress)
            self.download_percentage_label.configure(text=f"Downloading: {percentage}%")
        else:
            self.download_percentage_label.configure(text="Downloading...")

    def _download_update_thread(self, assets):
        asset_to_download = um.get_appropriate_asset(assets)
        if asset_to_download:
            download_path = os.path.join(os.path.expanduser("~"), asset_to_download['name'])
            success, error_message = um.download_asset(asset_to_download['browser_download_url'], download_path, self._update_download_progress_gui)
            
            self.after(100, self.download_progress_bar.pack_forget)
            self.after(100, self.download_percentage_label.pack_forget)

            if success:
                self.log(f"Update downloaded to {download_path}")
                self.after(100, lambda: self._prompt_for_update_and_restart(download_path))
            else:
                self.after(100, lambda: messagebox.showerror("Download Failed",
                                                           f"Failed to download update: {error_message}"))
                self.log(f"Update download failed: {error_message}")
        else:
            self.after(100, lambda: messagebox.showerror("Update Error",
                                                       "No appropriate update file found for your operating system."))
            self.log("No appropriate update file found.")

    def _prompt_for_update_and_restart(self, downloaded_path):
        response = messagebox.askyesno("Update Ready",
                                       "Update downloaded. Do you want to install it now and restart the application?")
        if response:
            self._perform_self_update(downloaded_path)
        else:
            messagebox.showinfo("Update Deferred", "Update will be installed on next manual restart.")

    def _perform_self_update(self, downloaded_path):
        current_executable = sys.executable if not getattr(sys, 'frozen', False) else sys.argv[0]
        
        # For PyInstaller bundled app, sys.executable points to the bootloader, sys.argv[0] is the executable itself
        if getattr(sys, 'frozen', False):
            current_executable = sys.argv[0]
        else:
            # If not frozen, we are running from source, so we don't self-update the script itself
            messagebox.showinfo("Self-Update", "Self-update is only available for packaged executables.")
            return

        # Create a temporary script to perform the update
        if platform.system() == "Windows":
            updater_script_content = f"""
@echo off
set "current_exe_path={current_executable}"
set "downloaded_exe_path={downloaded_path}"
set "old_exe_path=%current_exe_path%.old"

REM Give the current app a moment to close
timeout /t 3 /nobreak >NUL

REM Rename the old executable to release file lock
move /Y "%current_exe_path%" "%old_exe_path%"

REM Move the new executable into place
move /Y "%downloaded_exe_path%" "%current_exe_path%"

REM Start the new executable
start "" "%current_exe_path%"

REM Clean up old executable and updater script
del "%old_exe_path%"
del "%~f0"
"""
            updater_script_path = os.path.join(os.path.dirname(current_executable), "update.bat")
        else: # Linux
            updater_script_content = f"""
#!/bin/bash
sleep 5
mv -f "{downloaded_path}" "{current_executable}"
chmod +x "{current_executable}"
exec "{current_executable}" &
rm -- "$0"
"""
            updater_script_path = os.path.join(os.path.dirname(current_executable), "update.sh")
            os.chmod(updater_script_path, 0o755) # Make executable

        with open(updater_script_path, "w") as f:
            f.write(updater_script_content)

        self.log(f"Executing update script: {updater_script_path}")
        
        # Execute the updater script and exit the current application
        try:
            if platform.system() == "Windows":
                subprocess.Popen([updater_script_path], shell=True, creationflags=subprocess.DETACHED_PROCESS)
            else:
                subprocess.Popen([updater_script_path], shell=True, preexec_fn=os.setsid)
        except Exception as e:
            self.log(f"Error launching updater script: {e}")
            messagebox.showerror("Update Error", f"Failed to launch updater script: {e}")
        
        self.destroy() # Close the current application
        sys.exit() # Ensure the process exits

if __name__ == "__main__":
    app = App()
    app.mainloop()