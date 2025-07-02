

import customtkinter as ctk
from tkinter import messagebox, filedialog
import settings_manager as sm
import vpn_manager as vm
import wol_manager as wm
import rdp_manager as rm
import icon_manager as im
import threading
import time
from datetime import datetime
from PIL import Image
from tkinter import PhotoImage

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
        self.grid_rowconfigure(0, weight=1)

        self.tab_view = ctk.CTkTabview(self, anchor="w")
        self.tab_view.pack(expand=True, fill="both", padx=10, pady=10)

        self.home_tab = self.tab_view.add("Home")
        self.settings_tab = self.tab_view.add("Settings")

        self.create_home_tab()
        self.create_settings_tab()
        self.log("Application started.")

    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert(ctk.END, f"[{timestamp}] {message}\n")
        self.log_textbox.configure(state="disabled")
        self.log_textbox.see(ctk.END)

    def create_home_tab(self):
        self.home_tab.grid_columnconfigure(1, weight=1)
        self.home_tab.grid_rowconfigure(0, weight=1)

        control_frame = ctk.CTkFrame(self.home_tab, width=250)
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

        log_frame = ctk.CTkFrame(self.home_tab)
        log_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        log_frame.grid_rowconfigure(1, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(log_frame, text="Activity Log", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, pady=10)
        self.log_textbox = ctk.CTkTextbox(log_frame, state="disabled", wrap="word")
        self.log_textbox.grid(row=1, column=0, padx=10, pady=(0,10), sticky="nsew")

    def create_settings_tab(self):
        self.settings_tab.grid_columnconfigure(0, weight=1)

        wg_frame = ctk.CTkFrame(self.settings_tab)
        wg_frame.pack(pady=10, padx=10, fill="x")
        ctk.CTkLabel(wg_frame, text="WireGuard Config Path:").pack(side="left", padx=10)
        self.wg_path_entry = ctk.CTkEntry(wg_frame, width=300)
        self.wg_path_entry.insert(0, self.settings.get('wireguard_config_path', ''))
        self.wg_path_entry.pack(side="left", expand=True, fill="x", padx=5)
        ctk.CTkButton(wg_frame, text="Browse...", command=self.browse_wg_config).pack(side="left")

        host_mgmt_frame = ctk.CTkFrame(self.settings_tab)
        host_mgmt_frame.pack(pady=10, padx=10, fill="both", expand=True)
        ctk.CTkLabel(host_mgmt_frame, text="Host Profiles", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)

        self.host_listbox = ctk.CTkTextbox(host_mgmt_frame, height=150, wrap="none")
        self.host_listbox.pack(pady=5, padx=10, fill="x")
        self.update_host_listbox()

        edit_frame = ctk.CTkFrame(host_mgmt_frame)
        edit_frame.pack(pady=5, padx=10, fill="x")
        edit_frame.grid_columnconfigure(1, weight=1)

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
        btn_frame.pack(pady=5, padx=10, fill="x")
        ctk.CTkButton(btn_frame, text="Add", command=self.add_host).pack(side="left", expand=True, padx=5)
        ctk.CTkButton(btn_frame, text="Update", command=self.update_host).pack(side="left", expand=True, padx=5)
        ctk.CTkButton(btn_frame, text="Remove", command=self.remove_host).pack(side="left", expand=True, padx=5)
        ctk.CTkButton(self.settings_tab, text="Save All Settings", command=self.save_settings).pack(pady=10, padx=10)

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
        self.host_listbox.configure(state="disabled")
        self.update_host_dropdown()

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

if __name__ == "__main__":
    app = App()
    app.mainloop()
