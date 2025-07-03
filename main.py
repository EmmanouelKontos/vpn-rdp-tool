import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTabWidget, QTextEdit, QComboBox,
    QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QEvent
from PyQt6.QtGui import QIcon, QPixmap, QMouseEvent

import settings_manager as sm
import vpn_manager as vm
import wol_manager as wm
import rdp_manager as rm
import icon_manager as im
import update_manager as um
import os
import platform
import threading
import time
import subprocess
from datetime import datetime

class Worker(QThread):
    finished = pyqtSignal(object) # Use object to emit any type of result

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        result = self.func(*self.args, **self.kwargs)
        self.finished.emit(result)

class HostSelectionItem(QWidget):
    clicked = pyqtSignal(object)

    def __init__(self, host_data, icon_path, parent=None):
        super().__init__(parent)
        self.host_data = host_data
        self.is_selected = False

        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.setContentsMargins(10, 10, 10, 10)

        self.icon_label = QLabel()
        try:
            pixmap = QPixmap(icon_path)
            if pixmap.isNull():
                raise ValueError(f"Failed to load pixmap from {icon_path}")
        except Exception as e:
            print(f"Error loading icon {icon_path}: {e}")
            pixmap = QPixmap() # Fallback to empty pixmap
        self.icon_label.setPixmap(pixmap.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.icon_label)

        self.name_label = QLabel(host_data['name'])
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.name_label)

        self.setFixedSize(100, 100) # Fixed size for the item

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.host_data)
            super().mousePressEvent(event)

    def set_selected(self, selected: bool):
        self.is_selected = selected
        self.setProperty("selected", selected)
        self.style().polish(self) # Re-polish to apply stylesheet based on property

class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Universal VPN & RDP Tool")
        self.setGeometry(100, 100, 900, 700)
        self.setMinimumSize(700, 500)

        self.settings = sm.load_settings()
        self.vpn_active = False
        self.current_selected_host = None # To store the currently selected host object
        self.host_dropdown = None # Initialize host_dropdown
        self.host_buttons = [] # To keep track of HostSelectionItem widgets

        # Load Icons
        self.icons = {}
        for name, path in im.get_all_icons().items():
            self.icons[name] = QIcon(path)
        try:
            app_icon_path = im.get_app_icon()
            self.setWindowIcon(QIcon(app_icon_path))
        except Exception as e:
            print(f"Error setting application icon: {e}")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)

        self.home_tab = QWidget()
        self.settings_tab = QWidget()

        self.tab_widget.addTab(self.home_tab, "Home")
        self.tab_widget.addTab(self.settings_tab, "Settings")

        self.create_home_tab()
        self.create_settings_tab()
        self.apply_stylesheet()

        # Status Bar
        self.status_bar = QLabel(f"Version: {um.CURRENT_VERSION}")
        self.status_bar.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.main_layout.addWidget(self.status_bar)

        self.log("Application started.")
        # self.check_for_updates_on_startup() # Re-enable after update manager is integrated

    def apply_stylesheet(self):
        appearance_mode = self.settings.get("appearance_mode", "System")
        if appearance_mode == "Dark":
            # Dark Glassy Theme
            stylesheet = """
                QMainWindow {
                    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2c3e50, stop:1 #34495e);
                    color: #ecf0f1;
                }
                QTabWidget::pane {
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    background-color: rgba(0, 0, 0, 0.3); /* Semi-transparent background */
                    border-radius: 8px;
                }
                QTabWidget::tab-bar {
                    left: 10px;
                }
                QTabBar::tab {
                    background: rgba(255, 255, 255, 0.1);
                    color: #ecf0f1;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-bottom-left-radius: 5px;
                    border-bottom-right-radius: 5px;
                    padding: 10px 25px;
                    margin-right: 2px;
                }
                QTabBar::tab:selected {
                    background: rgba(255, 255, 255, 0.2);
                    border-color: rgba(255, 255, 255, 0.3);
                    border-bottom-color: rgba(255, 255, 255, 0.0); /* Make selected tab look like it's part of the pane */
                }
                QPushButton {
                    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #3498db, stop:1 #2980b9);
                    color: white;
                    border: 1px solid #2980b9;
                    padding: 10px 20px;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2980b9, stop:1 #3498db);
                    border: 1px solid #3498db;
                }
                QPushButton:pressed {
                    background-color: #2980b9;
                }
                QLineEdit, QTextEdit, QComboBox {
                    background-color: rgba(255, 255, 255, 0.1);
                    color: #ecf0f1;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    padding: 8px;
                    border-radius: 5px;
                }
                QLabel {
                    color: #ecf0f1;
                }
                QMessageBox {
                    background-color: #2c3e50;
                    color: #ecf0f1;
                }
                QMessageBox QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    padding: 8px 15px;
                    border-radius: 3px;
                }
                QTableWidget {
                    background-color: rgba(0, 0, 0, 0.2);
                    alternate-background-color: rgba(0, 0, 0, 0.1);
                    color: #ecf0f1;
                    gridline-color: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 5px;
                }
                QHeaderView::section {
                    background-color: rgba(255, 255, 255, 0.15);
                    color: #ecf0f1;
                    padding: 5px;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                }
                QTableWidget::item:selected {
                    background-color: rgba(52, 152, 219, 0.5); /* Blue selection with transparency */
                    color: white;
                }
                QProgressBar {
                    text-align: center;
                    color: white;
                    border-radius: 5px;
                    background-color: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }
                QProgressBar::chunk {
                    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2ecc71, stop:1 #27ae60);
                    border-radius: 5px;
                }
                HostSelectionItem {
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 8px;
                    background-color: rgba(255, 255, 255, 0.05);
                }
                HostSelectionItem:hover {
                    border: 1px solid rgba(255, 255, 255, 0.4);
                    background-color: rgba(255, 255, 255, 0.1);
                }
                HostSelectionItem[selected="true"] {
                    border: 2px solid #3498db;
                    background-color: rgba(52, 152, 219, 0.2);
                }
            """
        elif appearance_mode == "Light":
            # Light Glassy Theme
            stylesheet = """
                QMainWindow {
                    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ecf0f1, stop:1 #bdc3c7);
                    color: #2c3e50;
                }
                QTabWidget::pane {
                    border: 1px solid rgba(0, 0, 0, 0.1);
                    background-color: rgba(255, 255, 255, 0.7); /* Semi-transparent background */
                    border-radius: 8px;
                }
                QTabWidget::tab-bar {
                    left: 10px;
                }
                QTabBar::tab {
                    background: rgba(255, 255, 255, 0.7);
                    color: #2c3e50;
                    border: 1px solid rgba(0, 0, 0, 0.2);
                    border-bottom-left-radius: 5px;
                    border-bottom-right-radius: 5px;
                    padding: 10px 25px;
                    margin-right: 2px;
                }
                QTabBar::tab:selected {
                    background: rgba(255, 255, 255, 0.9);
                    border-color: rgba(0, 0, 0, 0.3);
                    border-bottom-color: rgba(255, 255, 255, 0.0); /* Make selected tab look like it's part of the pane */
                }
                QPushButton {
                    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #3498db, stop:1 #2980b9);
                    color: white;
                    border: 1px solid #2980b9;
                    padding: 10px 20px;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2980b9, stop:1 #3498db);
                    border: 1px solid #3498db;
                }
                QPushButton:pressed {
                    background-color: #2980b9;
                }
                QLineEdit, QTextEdit, QComboBox {
                    background-color: rgba(255, 255, 255, 0.7);
                    color: #2c3e50;
                    border: 1px solid rgba(0, 0, 0, 0.2);
                    padding: 8px;
                    border-radius: 5px;
                }
                QLabel {
                    color: #2c3e50;
                }
                QMessageBox {
                    background-color: #ecf0f1;
                    color: #2c3e50;
                }
                QMessageBox QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    padding: 8px 15px;
                    border-radius: 3px;
                }
                QTableWidget {
                    background-color: rgba(255, 255, 255, 0.6);
                    alternate-background-color: rgba(255, 255, 255, 0.5);
                    color: #2c3e50;
                    gridline-color: rgba(0, 0, 0, 0.1);
                    border: 1px solid rgba(0, 0, 0, 0.1);
                    border-radius: 5px;
                }
                QHeaderView::section {
                    background-color: rgba(0, 0, 0, 0.1);
                    color: #2c3e50;
                    padding: 5px;
                    border: 1px solid rgba(0, 0, 0, 0.1);
                }
                QTableWidget::item:selected {
                    background-color: rgba(52, 152, 219, 0.5); /* Blue selection with transparency */
                    color: white;
                }
                QProgressBar {
                    text-align: center;
                    color: #2c3e50;
                    border-radius: 5px;
                    background-color: rgba(0, 0, 0, 0.1);
                    border: 1px solid rgba(0, 0, 0, 0.2);
                }
                QProgressBar::chunk {
                    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2ecc71, stop:1 #27ae60);
                    border-radius: 5px;
                }
                HostSelectionItem {
                    border: 1px solid rgba(0, 0, 0, 0.2);
                    border-radius: 8px;
                    background-color: rgba(255, 255, 255, 0.7);
                }
                HostSelectionItem:hover {
                    border: 1px solid rgba(0, 0, 0, 0.4);
                    background-color: rgba(255, 255, 255, 0.9);
                }
                HostSelectionItem[selected="true"] {
                    border: 2px solid #3498db;
                    background-color: rgba(52, 152, 219, 0.2);
                }
            """
        else: # System or default to Dark
            stylesheet = """
                QMainWindow {
                    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2c3e50, stop:1 #34495e);
                    color: #ecf0f1;
                }
                QTabWidget::pane {
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    background-color: rgba(0, 0, 0, 0.3); /* Semi-transparent background */
                    border-radius: 8px;
                }
                QTabWidget::tab-bar {
                    left: 10px;
                }
                QTabBar::tab {
                    background: rgba(255, 255, 255, 0.1);
                    color: #ecf0f1;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-bottom-left-radius: 5px;
                    border-bottom-right-radius: 5px;
                    padding: 10px 25px;
                    margin-right: 2px;
                }
                QTabBar::tab:selected {
                    background: rgba(255, 255, 255, 0.2);
                    border-color: rgba(255, 255, 255, 0.3);
                    border-bottom-color: rgba(255, 255, 255, 0.0); /* Make selected tab look like it's part of the pane */
                }
                QPushButton {
                    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #3498db, stop:1 #2980b9);
                    color: white;
                    border: 1px solid #2980b9;
                    padding: 10px 20px;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2980b9, stop:1 #3498db);
                    border: 1px solid #3498db;
                }
                QPushButton:pressed {
                    background-color: #2980b9;
                }
                QLineEdit, QTextEdit, QComboBox {
                    background-color: rgba(255, 255, 255, 0.1);
                    color: #ecf0f1;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    padding: 8px;
                    border-radius: 5px;
                }
                QLabel {
                    color: #ecf0f1;
                }
                QMessageBox {
                    background-color: #2c3e50;
                    color: #ecf0f1;
                }
                QMessageBox QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    padding: 8px 15px;
                    border-radius: 3px;
                }
                QTableWidget {
                    background-color: rgba(0, 0, 0, 0.2);
                    alternate-background-color: rgba(0, 0, 0, 0.1);
                    color: #ecf0f1;
                    gridline-color: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 5px;
                }
                QHeaderView::section {
                    background-color: rgba(255, 255, 255, 0.15);
                    color: #ecf0f1;
                    padding: 5px;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                }
                QTableWidget::item:selected {
                    background-color: rgba(52, 152, 219, 0.5); /* Blue selection with transparency */
                    color: white;
                }
                QProgressBar {
                    text-align: center;
                    color: white;
                    border-radius: 5px;
                    background-color: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }
                QProgressBar::chunk {
                    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2ecc71, stop:1 #27ae60);
                    border-radius: 5px;
                }
                HostSelectionItem {
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 8px;
                    background-color: rgba(255, 255, 255, 0.05);
                }
                HostSelectionItem:hover {
                    border: 1px solid rgba(255, 255, 255, 0.4);
                    background-color: rgba(255, 255, 255, 0.1);
                }
                HostSelectionItem[selected="true"] {
                    border: 2px solid #3498db;
                    background-color: rgba(52, 152, 219, 0.2);
                }
            """
        self.setStyleSheet(stylesheet)

    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_textbox.append(f"[{timestamp}] {message}")

    def create_home_tab(self):
        layout = QHBoxLayout(self.home_tab)

        # Control Frame
        control_frame = QWidget()
        control_layout = QVBoxLayout(control_frame)
        control_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        control_layout.addWidget(QLabel("Controls"))
        # Host Selection
        self.host_selection_container = QWidget()
        self.host_selection_layout = QVBoxLayout(self.host_selection_container) # This will hold either buttons or dropdown
        control_layout.addWidget(QLabel("Select Host:"))
        control_layout.addWidget(self.host_selection_container)

        self.selected_host_label = QLabel("Selected Host: None")
        control_layout.addWidget(self.selected_host_label)

        self.vpn_status_label = QLabel("VPN: Disconnected")
        control_layout.addWidget(self.vpn_status_label)

        self.connect_btn = QPushButton(self.icons['connect'], "Connect VPN")
        self.connect_btn.clicked.connect(self.toggle_vpn_connection)
        control_layout.addWidget(self.connect_btn)

        self.wake_btn = QPushButton(self.icons['wake'], "Wake Host")
        self.wake_btn.clicked.connect(self.wake_host)
        control_layout.addWidget(self.wake_btn)

        self.rdp_btn = QPushButton(self.icons['rdp'], "Launch RDP")
        self.rdp_btn.clicked.connect(self.launch_rdp)
        control_layout.addWidget(self.rdp_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Downloading: %p%")
        self.progress_bar.hide() # Hidden by default
        control_layout.addWidget(self.progress_bar)

        # Log Frame
        log_frame = QWidget()
        log_layout = QVBoxLayout(log_frame)
        log_layout.addWidget(QLabel("Activity Log"))
        self.log_textbox = QTextEdit()
        self.log_textbox.setReadOnly(True)
        log_layout.addWidget(self.log_textbox)

        layout.addWidget(control_frame, 2) # Control frame takes 2 parts of space
        layout.addWidget(log_frame, 1)    # Log frame takes 1 part of space

        self.update_host_selection()

    def create_settings_tab(self):
        layout = QVBoxLayout(self.settings_tab)

        # WireGuard Config Path
        wg_frame = QWidget()
        wg_layout = QHBoxLayout(wg_frame)
        wg_layout.addWidget(QLabel("WireGuard Config Path:"))
        self.wg_path_entry = QLineEdit(self.settings.get('wireguard_config_path', ''))
        wg_layout.addWidget(self.wg_path_entry)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_wg_config)
        wg_layout.addWidget(browse_btn)
        layout.addWidget(wg_frame)

        # Host Profiles
        host_mgmt_frame = QWidget()
        host_mgmt_layout = QVBoxLayout(host_mgmt_frame)
        host_mgmt_layout.addWidget(QLabel("Host Profiles"))

        self.host_table = QTableWidget()
        self.host_table.setColumnCount(4)
        self.host_table.setHorizontalHeaderLabels(["Name", "IP Address", "MAC Address", "RDP User"])
        self.host_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.host_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.host_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.host_table.itemSelectionChanged.connect(self.on_host_select)
        host_mgmt_layout.addWidget(self.host_table)

        edit_frame = QWidget()
        edit_layout = QHBoxLayout(edit_frame)
        edit_layout.addWidget(QLabel("Name:"))
        self.name_entry = QLineEdit()
        edit_layout.addWidget(self.name_entry)
        edit_layout.addWidget(QLabel("IP Address:"))
        self.ip_entry = QLineEdit()
        edit_layout.addWidget(self.ip_entry)
        edit_layout.addWidget(QLabel("MAC Address:"))
        self.mac_entry = QLineEdit()
        edit_layout.addWidget(self.mac_entry)
        edit_layout.addWidget(QLabel("RDP User:"))
        self.user_entry = QLineEdit()
        edit_layout.addWidget(self.user_entry)
        host_mgmt_layout.addWidget(edit_frame)

        btn_frame = QWidget()
        btn_layout = QHBoxLayout(btn_frame)
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_host)
        btn_layout.addWidget(add_btn)
        update_btn = QPushButton("Update")
        update_btn.clicked.connect(self.update_host)
        btn_layout.addWidget(update_btn)
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self.remove_host)
        btn_layout.addWidget(remove_btn)
        host_mgmt_layout.addWidget(btn_frame)

        layout.addWidget(host_mgmt_frame, 1)

        # Save and Update Check buttons
        bottom_buttons_frame = QWidget()
        bottom_buttons_layout = QHBoxLayout(bottom_buttons_frame)
        save_settings_btn = QPushButton("Save All Settings")
        save_settings_btn.clicked.connect(self.save_settings)
        bottom_buttons_layout.addWidget(save_settings_btn)
        check_updates_btn = QPushButton("Check for Updates")
        check_updates_btn.clicked.connect(self.check_for_updates_gui)
        bottom_buttons_layout.addWidget(check_updates_btn)
        layout.addWidget(bottom_buttons_frame)

        # Appearance Mode Setting
        appearance_mode_frame = QWidget()
        appearance_mode_layout = QHBoxLayout(appearance_mode_frame)
        appearance_mode_layout.addWidget(QLabel("Appearance Mode:"))
        self.appearance_mode_optionemenu = QComboBox()
        self.appearance_mode_optionemenu.addItems(["Light", "Dark", "System"])
        self.appearance_mode_optionemenu.currentTextChanged.connect(self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.setCurrentText(self.settings.get("appearance_mode", "System"))
        appearance_mode_layout.addWidget(self.appearance_mode_optionemenu)
        layout.addWidget(appearance_mode_frame)

        self.update_host_table()

    def change_appearance_mode_event(self, new_appearance_mode: str):
        self.settings["appearance_mode"] = new_appearance_mode
        sm.save_settings(self.settings)
        self.apply_stylesheet()

    def browse_wg_config(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Select WireGuard Configuration File")
        if filepath:
            self.wg_path_entry.setText(filepath)
            self.log(f"Selected WireGuard config: {filepath}")

    def update_host_table(self):
        self.host_table.setRowCount(0) # Clear existing rows
        for row_num, host in enumerate(self.settings.get('hosts', [])):
            self.host_table.insertRow(row_num)
            self.host_table.setItem(row_num, 0, QTableWidgetItem(host.get('name', '')))
            self.host_table.setItem(row_num, 1, QTableWidgetItem(host.get('ip_address', '')))
            self.host_table.setItem(row_num, 2, QTableWidgetItem(host.get('mac_address', '')))
            self.host_table.setItem(row_num, 3, QTableWidgetItem(host.get('rdp_user', '')))

    def on_host_select(self):
        selected_items = self.host_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            host = self.settings.get('hosts', [])[row]
            self.name_entry.setText(host.get('name', ''))
            self.ip_entry.setText(host.get('ip_address', ''))
            self.mac_entry.setText(host.get('mac_address', ''))
            self.user_entry.setText(host.get('rdp_user', ''))

    def update_host_selection(self):
        # Clear existing widgets in the layout
        while self.host_selection_layout.count():
            item = self.host_selection_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        hosts = self.settings.get('hosts', [])
        self.host_buttons = [] # Clear previous host buttons

        if not hosts:
            no_hosts_label = QLabel("No hosts configured. Go to Settings to add some.")
            self.host_selection_layout.addWidget(no_hosts_label)
            self.current_selected_host = None
            self.selected_host_label.setText("Selected Host: None")
            self.host_dropdown = None # Ensure dropdown is None if no hosts
            return

        if len(hosts) <= 5:
            self.host_dropdown = None # Ensure dropdown is None if using buttons
            # Use a QHBoxLayout for the buttons to arrange them horizontally
            buttons_h_layout = QHBoxLayout()
            buttons_h_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            for host in hosts:
                icon_path = im.create_icon('pc', im.draw_pc_icon) # Get the actual path for the icon
                host_item = HostSelectionItem(host, icon_path)
                host_item.clicked.connect(self._select_host_by_item)
                buttons_h_layout.addWidget(host_item)
                self.host_buttons.append(host_item)
            self.host_selection_layout.addLayout(buttons_h_layout)

            # Select the first host by default if none is selected
            if self.current_selected_host is None and hosts:
                self.current_selected_host = hosts[0]
                self.selected_host_label.setText(f"Selected Host: {hosts[0]['name']}")
                self.log(f"Host selected: {hosts[0]['name']}")

            # Set the selected state for the appropriate HostSelectionItem
            for item in self.host_buttons:
                if self.current_selected_host and item.host_data['name'] == self.current_selected_host['name']:
                    item.set_selected(True)
                else:
                    item.set_selected(False)

        else:
            # Display as dropdown
            self.host_dropdown = QComboBox()
            self.host_dropdown.addItems([h['name'] for h in hosts])
            self.host_dropdown.currentTextChanged.connect(self._select_host_by_dropdown)
            self.host_selection_layout.addWidget(self.host_dropdown)
            # Select the first host by default if none is selected
            if self.current_selected_host is None and hosts:
                self.host_dropdown.setCurrentText(hosts[0]['name'])
            elif self.current_selected_host:
                # Ensure dropdown reflects current_selected_host if it was set by buttons previously
                self.host_dropdown.setCurrentText(self.current_selected_host['name'])

    def _select_host_by_item(self, host_data):
        # Deselect all other items
        for item in self.host_buttons:
            if item.host_data['name'] != host_data['name']:
                item.set_selected(False)
            else:
                item.set_selected(True)
        self.current_selected_host = host_data
        self.selected_host_label.setText(f"Selected Host: {host_data['name']}")
        self.log(f"Host selected: {host_data['name']}")
        self.host_selection_container.style().polish(self.host_selection_container) # Re-polish container to update styles

    

    def add_host(self):
        host = {
            "name": self.name_entry.text(), "ip_address": self.ip_entry.text(),
            "mac_address": self.mac_entry.text(), "rdp_user": self.user_entry.text()
        }
        if all(host.values()):
            self.settings.setdefault('hosts', []).append(host)
            self.update_host_table()
            self.update_host_selection()
            self.clear_host_entries()
            self.log(f"Added host: {host['name']}")
        else:
            QMessageBox.warning(self, "Error", "All host fields are required.")

    def update_host(self):
        selected_host_name = self.name_entry.text()
        if not selected_host_name or selected_host_name == "No hosts configured":
            QMessageBox.warning(self, "Error", "No host selected to update.")
            return
        for i, host in enumerate(self.settings.get('hosts', [])):
            if host['name'] == selected_host_name:
                updated_host = {
                    "name": self.name_entry.text(), "ip_address": self.ip_entry.text(),
                    "mac_address": self.mac_entry.text(), "rdp_user": self.user_entry.text()
                }
                self.settings['hosts'][i] = updated_host
                self.update_host_table()
                self.update_host_selection()
                self.clear_host_entries()
                self.log(f"Updated host: {updated_host['name']}")
                return

    def remove_host(self):
        selected_host_name = self.name_entry.text()
        if not selected_host_name or selected_host_name == "No hosts configured":
            QMessageBox.warning(self, "Error", "No host selected to remove.")
            return
        self.settings['hosts'] = [h for h in self.settings.get('hosts', []) if h['name'] != selected_host_name]
        self.update_host_table()
        self.update_host_selection()
        self.log(f"Removed host: {selected_host_name}")

    def clear_host_entries(self):
        self.name_entry.clear()
        self.ip_entry.clear()
        self.mac_entry.clear()
        self.user_entry.clear()

    def save_settings(self):
        self.settings['wireguard_config_path'] = self.wg_path_entry.text()
        sm.save_settings(self.settings)
        self.log("Settings saved successfully.")
        QMessageBox.information(self, "Success", "Settings have been saved.")

    def get_selected_host(self):
        return self.current_selected_host

    def toggle_vpn_connection(self):
        if self.vpn_active:
            self.disconnect_vpn()
        else:
            self.connect_vpn()

    def connect_vpn(self):
        config_path = self.settings.get('wireguard_config_path')
        if not config_path:
            QMessageBox.warning(self, "Error", "WireGuard config path not set in Settings.")
            return
        self.log("VPN connection process started...")
        self.connect_btn.setEnabled(False)
        
        self.vpn_worker = Worker(vm.connect_vpn, config_path)
        self.vpn_worker.finished.connect(self.on_vpn_connect_done)
        self.vpn_worker.start()

    def on_vpn_connect_done(self, success, message):
        self.connect_btn.setEnabled(True)
        self.log(message)
        if success:
            self.vpn_active = True
            self.vpn_status_label.setText("VPN: Connected")
            self.vpn_status_label.setStyleSheet("color: green;")
            self.connect_btn.setText("Disconnect VPN")
            self.connect_btn.setIcon(self.icons['disconnect'])
        else:
            self.vpn_status_label.setText("VPN: Failed")
            self.vpn_status_label.setStyleSheet("color: red;")
            QMessageBox.critical(self, "VPN Error", message)

    def disconnect_vpn(self):
        config_path = self.settings.get('wireguard_config_path')
        self.log("VPN disconnection process started...")
        self.connect_btn.setEnabled(False)
        
        self.vpn_worker = Worker(vm.disconnect_vpn, config_path)
        self.vpn_worker.finished.connect(self.on_vpn_disconnect_done)
        self.vpn_worker.start()

    def on_vpn_disconnect_done(self, success, message):
        self.connect_btn.setEnabled(True)
        self.log(message)
        if success:
            self.vpn_active = False
            self.vpn_status_label.setText("VPN: Disconnected")
            self.vpn_status_label.setStyleSheet("color: red;")
            self.connect_btn.setText("Connect VPN")
            self.connect_btn.setIcon(self.icons['connect'])
        else:
            QMessageBox.critical(self, "VPN Error", message)

    def wake_host(self):
        host = self.get_selected_host()
        if not host:
            QMessageBox.warning(self, "Error", "No host selected.")
            return
        self.log(f"Sending Wake-on-LAN packet to {host['name']} ({host['mac_address']})...")
        success, message = wm.wake_host(host['mac_address'])
        self.log(message)
        if success:
            QMessageBox.information(self, "Wake-on-LAN", f"Magic packet sent to {host['name']}.")
        else:
            QMessageBox.critical(self, "Wake-on-LAN Error", message)

    def launch_rdp(self):
        host = self.get_selected_host()
        if not host:
            QMessageBox.warning(self, "Error", "No host selected.")
            return
        self.log(f"Launching RDP for {host['name']} at {host['ip_address']}...")
        success, message = rm.launch_rdp(host['ip_address'], host.get('rdp_user'))
        self.log(message)
        if not success:
            QMessageBox.critical(self, "RDP Error", message)

    def check_for_updates_on_startup(self):
        self.log("Checking for updates...")
        self.update_worker = Worker(um.check_for_updates)
        self.update_worker.finished.connect(lambda result: self._handle_update_check_result(result, startup_check=True))
        self.update_worker.start()

    def check_for_updates_gui(self):
        self.log("Manually checking for updates...")
        self.update_worker = Worker(um.check_for_updates)
        self.update_worker.finished.connect(lambda result: self._handle_update_check_result(result, startup_check=False))
        self.update_worker.start()

    def _handle_update_check_result(self, result, startup_check):
        update_available, latest_version, assets = result
        if update_available:
            self.log(f"Update available! Latest version: {latest_version}")
            self.assets_for_download = assets # Store assets for later use
            reply = QMessageBox.question(self, "Update Available",
                                       f"A new version ({latest_version}) is available. Do you want to download it now?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.log("Downloading update...")
                self.progress_bar.show()
                self.progress_bar.setValue(0)
                self.download_worker = Worker(um.download_asset, um.get_appropriate_asset(assets)['browser_download_url'], 
                                              os.path.join(os.path.expanduser("~"), um.get_appropriate_asset(assets)['name']), 
                                              self._update_download_progress_gui)
                self.download_worker.finished.connect(self._handle_download_finished)
                self.download_worker.start()
        else:
            if not startup_check:
                QMessageBox.information(self, "No Updates", "You are running the latest version.")
            self.log("No updates available.")

    def _update_download_progress_gui(self, downloaded, total):
        if total > 0:
            progress = int((downloaded / total) * 100)
            self.progress_bar.setValue(progress)
        else:
            pass

    def _handle_download_finished(self, success, error_message):
        self.progress_bar.hide()

        if success:
            # Pass the assets to _handle_download_finished so it doesn't re-call check_for_updates()
            downloaded_path = os.path.join(os.path.expanduser("~"), um.get_appropriate_asset(self.assets_for_download)['name']) 
            self.log(f"Update downloaded to {downloaded_path}")
            reply = QMessageBox.question(self, "Update Ready",
                                       "Update downloaded. Do you want to install it now and restart the application?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self._perform_self_update(downloaded_path)
            else:
                QMessageBox.information(self, "Update Deferred", "Update will be installed on next manual restart.")
        else:
            QMessageBox.critical(self, "Download Failed", f"Failed to download update: {error_message}")
            self.log(f"Update download failed: {error_message}")

    def _perform_self_update(self, downloaded_path):
        current_executable = sys.executable if not getattr(sys, 'frozen', False) else sys.argv[0]
        
        if not getattr(sys, 'frozen', False):
            QMessageBox.information(self, "Self-Update", "Self-update is only available for packaged executables.")
            return

        if platform.system() == "Windows":
            updater_script_content = f"""
@echo off
setlocal

set "current_exe_path={current_executable}"
set "downloaded_exe_path={downloaded_path}"
set "old_exe_path=%current_exe_path%.old"

echo Waiting for application to close...
taskkill /IM {os.path.basename(current_executable)} /F > NUL 2>&1
timeout /t 5 /nobreak > NUL

echo Renaming current executable...
:retry_move
move /Y "%current_exe_path%" "%old_exe_path%"
if exist "%current_exe_path%" (
    echo Failed to rename, retrying in 5 seconds...
    timeout /t 5 /nobreak > NUL
    goto retry_move
)

echo Moving new executable into place...
move /Y "%downloaded_exe_path%" "%current_exe_path%"

echo Starting new version...
start "" "%current_exe_path%"

echo Cleaning up...
del "%old_exe_path%" > NUL 2>&1
(goto) 2>nul & del "%~f0"

endlocal
"""
            updater_script_path = os.path.join(os.path.dirname(current_executable), "update.bat")
        elif platform.system() == "Darwin": # macOS
            updater_script_content = f"""
#!/bin/bash
# Wait for the current application to fully exit
sleep 2

# Define paths
CURRENT_APP="{current_executable}"
DOWNLOADED_APP="{downloaded_path}"
TEMP_APP="${CURRENT_APP}.temp"

# Move the current app to a temporary location
mv -f "$CURRENT_APP" "$TEMP_APP"

# Move the downloaded app to the current app's location
mv -f "$DOWNLOADED_APP" "$CURRENT_APP"

# Make the new app executable
chmod +x "$CURRENT_APP"

# Start the new application in the background and detach from the shell
nohup "$CURRENT_APP" > /dev/null 2>&1 &

# Clean up the temporary old app and this script
rm -f "$TEMP_APP"
rm -- "$0"

exit 0
"""
            updater_script_path = os.path.join(os.path.dirname(current_executable), "update.sh")
            os.chmod(updater_script_path, 0o755) # Make executable
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
        
        try:
            if platform.system() == "Windows":
                subprocess.Popen([updater_script_path], shell=True, creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
            else: # Linux and macOS
                subprocess.Popen([updater_script_path], shell=True, preexec_fn=os.setsid)
        except Exception as e:
            self.log(f"Error launching updater script: {e}")
            QMessageBox.critical(self, "Update Error", f"Failed to launch updater script: {e}")
        
        QApplication.instance().quit() # Close the current application

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())