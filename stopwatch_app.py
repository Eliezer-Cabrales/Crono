import sys
import time
import os
import json
import webbrowser
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QGroupBox, QLineEdit, QDialog, 
                             QRadioButton, QComboBox, QMessageBox, QAbstractItemView,
                             QApplication)
from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon
from scraper import get_meeting_data

class ScraperThread(QThread):
    data_fetched = pyqtSignal(list, bool)

    def run(self):
        today = datetime.now().weekday()
        
        if today in (5, 6):
            data = [
                {"title": "Discurso Público", "duration_mins": 30},
                {"title": "Estudio de la Atalaya", "duration_mins": 60}
            ]
            self.data_fetched.emit(data, True)
        else:
            data = get_meeting_data()
            self.data_fetched.emit(data or [], False)

class DisplayWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pantalla de Proyección")
        self.setStyleSheet("background-color: black;")
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.clock_label = QLabel("00:00")
        self.clock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.clock_label.setStyleSheet("font-size: 150px; font-weight: bold; color: white; font-family: 'Segoe UI', Arial, sans-serif; font-feature-settings: 'tnum';")
        
        self.msg_label = QLabel("")
        self.msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.msg_label.setStyleSheet("font-size: 60px; font-weight: bold; color: yellow;")
        
        layout.addWidget(self.clock_label)
        layout.addWidget(self.msg_label)
        self.setLayout(layout)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

class AddEditDialog(QDialog):
    def __init__(self, parent=None, title="", duration=""):
        super().__init__(parent)
        self.setWindowTitle("Asignación")
        self.setFixedSize(300, 150)
        
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Título de la asignación:"))
        self.title_input = QLineEdit(title)
        layout.addWidget(self.title_input)
        
        layout.addWidget(QLabel("Duración (minutos):"))
        self.duration_input = QLineEdit(str(duration))
        layout.addWidget(self.duration_input)
        
        btn = QPushButton("Guardar")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)
        
        self.setLayout(layout)

    def get_data(self):
        return self.title_input.text().strip(), self.duration_input.text().strip()

class SettingsDialog(QDialog):
    def __init__(self, parent, current_mode, current_target_idx):
        super().__init__(parent)
        self.setWindowTitle("Ajustes de Configuración")
        self.setFixedSize(400, 250)
        
        self.mode = current_mode
        self.target_idx = current_target_idx
        
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("<b>Modo del Cronómetro:</b>"))
        self.radio_reg = QRadioButton("Cuenta Regresiva (A cero)")
        self.radio_prog = QRadioButton("Cuenta Progresiva (Hacia arriba)")
        
        if current_mode == "Regresiva":
            self.radio_reg.setChecked(True)
        else:
            self.radio_prog.setChecked(True)
            
        layout.addWidget(self.radio_reg)
        layout.addWidget(self.radio_prog)
        
        layout.addSpacing(15)
        layout.addWidget(QLabel("<b>Escritorio / Pantalla de Proyección:</b>"))
        
        self.combo = QComboBox()
        screens = QApplication.screens()
        for i, screen in enumerate(screens):
            geom = screen.geometry()
            self.combo.addItem(f"Pantalla {i+1} ({geom.width()}x{geom.height()}) - {screen.name()}")
        
        if 0 <= current_target_idx < len(screens):
            self.combo.setCurrentIndex(current_target_idx)
        else:
            self.combo.setCurrentIndex(len(screens)-1)
            
        layout.addWidget(self.combo)
        
        layout.addStretch()
        btn = QPushButton("Guardar y Cerrar")
        btn.clicked.connect(self.save_and_close)
        layout.addWidget(btn)
        
        self.setLayout(layout)
        
    def save_and_close(self):
        self.mode = "Regresiva" if self.radio_reg.isChecked() else "Progresiva"
        self.target_idx = self.combo.currentIndex()
        self.accept()

class StopwatchApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rahab")
        self.setWindowIcon(QIcon("rahab_icon.ico"))
        self.resize(750, 580)
        
        self.config_file = "rahab_config.json"
        
        self.timer_mode = "Progresiva"
        self.target_monitor_idx = -1 
        
        self.is_running = False
        self.time_elapsed = 0.0       
        self.time_left = 0.0          
        self.total_duration = 0.0     
        self.last_update_time = 0.0
        
        self.display_window = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.run_clock_engine)

        self.load_config()

        self.assignments = []
        self.init_ui()
        self.refresh_table()

        self.scraper_thread = ScraperThread()
        self.scraper_thread.data_fetched.connect(self.on_data_fetched)
        self.scraper_thread.start()

        if len(QApplication.screens()) > 1:
            QTimer.singleShot(500, self.open_second_screen)

    def on_data_fetched(self, raw_data, is_weekend):
        if not is_weekend:
            if not raw_data:
                raw_data = [
                    {"title": "Tesoros de la Biblia", "duration_mins": 10},
                    {"title": "Perlas escondidas", "duration_mins": 10},
                    {"title": "Lectura de la Biblia", "duration_mins": 4}
                ]
            
            raw_data.insert(0, {"title": "Palabras de introducción", "duration_mins": 1})
            raw_data.append({"title": "Palabras de conclusión", "duration_mins": 3})

        for item in raw_data:
            self.assignments.append({
                "title": item["title"],
                "duration_mins": float(item.get("duration_mins", 0)),
                "actual_seconds": 0.0  
            })
            
        self.refresh_table()
        if self.assignments:
            self.table.selectRow(0)

    def closeEvent(self, event):
        if self.display_window and self.display_window.isVisible():
            self.display_window.close()
        event.accept()

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                    self.timer_mode = data.get("timer_mode", "Progresiva")
                    self.target_monitor_idx = data.get("target_monitor_idx", -1)
            except Exception:
                pass
        
        screens = QApplication.screens()
        if self.target_monitor_idx < 0 or self.target_monitor_idx >= len(screens):
            self.target_monitor_idx = len(screens) - 1

    def save_config(self):
        data = {
            "timer_mode": self.timer_mode,
            "target_monitor_idx": self.target_monitor_idx
        }
        try:
            with open(self.config_file, "w") as f:
                json.dump(data, f)
        except Exception:
            pass

    def init_ui(self):
        main_layout = QVBoxLayout()
        
        top_bar = QHBoxLayout()
        
        title_layout = QVBoxLayout()
        title_layout.setSpacing(0)
        
        title = QLabel("<b>Rahab</b>")
        title.setStyleSheet("font-size: 16px;")

        subtitle = QLabel("(Esta aplicacion esta creada exclusivamente para el Salón del Reino de los Testigos de Jehová de Chiclana de la Frontera)")
        subtitle.setStyleSheet("font-size: 8px;")
        
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        
        btn_help = QPushButton("ℹ Ayuda")
        btn_help.clicked.connect(self.open_help)
        
        btn_settings = QPushButton("⚙ Ajustes")
        btn_settings.clicked.connect(self.open_settings)
        
        top_bar.addLayout(title_layout)
        top_bar.addStretch()
        top_bar.addWidget(btn_help)
        top_bar.addWidget(btn_settings)
        
        main_layout.addLayout(top_bar)
        
        content_layout = QHBoxLayout()
        
        left_panel = QVBoxLayout()
        left_panel.addWidget(QLabel("<b>Asignaciones de la Reunión:</b>"))
        
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Asignación", "Previsto", "Real"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.itemSelectionChanged.connect(self.on_assignment_selected)
        left_panel.addWidget(self.table)
        
        btn_row1 = QHBoxLayout()
        btn_add = QPushButton("+ Añadir")
        btn_edit = QPushButton("✏ Editar")
        btn_del = QPushButton("- Eliminar")
        btn_add.clicked.connect(self.add_slot)
        btn_edit.clicked.connect(self.edit_slot)
        btn_del.clicked.connect(self.delete_slot)
        btn_row1.addWidget(btn_add)
        btn_row1.addWidget(btn_edit)
        btn_row1.addWidget(btn_del)
        left_panel.addLayout(btn_row1)
        
        btn_row2 = QHBoxLayout()
        btn_up = QPushButton("↑ Subir")
        btn_down = QPushButton("↓ Bajar")
        btn_up.clicked.connect(self.move_up)
        btn_down.clicked.connect(self.move_down)
        btn_row2.addWidget(btn_up)
        btn_row2.addWidget(btn_down)
        left_panel.addLayout(btn_row2)
        
        content_layout.addLayout(left_panel, stretch=6)
        
        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("<b>Tiempo:</b>"))
        
        self.local_clock = QLabel("00:00")
        self.local_clock.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.local_clock.setStyleSheet("font-size: 48px; font-weight: bold; color: #3399FF; font-family: 'Segoe UI', Arial, sans-serif; font-feature-settings: 'tnum';")
        right_panel.addWidget(self.local_clock)
        
        btn_toggle = QPushButton("Iniciar / Parar")
        btn_toggle.setMinimumHeight(40)
        btn_toggle.clicked.connect(self.toggle)
        
        btn_reset = QPushButton("🔄 Reiniciar")
        btn_reset.setMinimumHeight(40)
        btn_reset.clicked.connect(self.hard_reset_timer)
        
        btn_screen = QPushButton("Abrir Segunda Pantalla")
        btn_screen.setMinimumHeight(40)
        btn_screen.clicked.connect(self.open_second_screen)
        
        right_panel.addWidget(btn_toggle)
        right_panel.addWidget(btn_reset)
        right_panel.addSpacing(15)
        right_panel.addWidget(btn_screen)
        
        msg_group = QGroupBox("Mensaje en Proyector")
        msg_layout = QVBoxLayout()
        self.msg_input = QLineEdit()
        msg_layout.addWidget(self.msg_input)
        
        msg_btns = QHBoxLayout()
        btn_show = QPushButton("Mostrar")
        btn_hide = QPushButton("Ocultar")
        btn_show.clicked.connect(self.show_message)
        btn_hide.clicked.connect(self.hide_message)
        msg_btns.addWidget(btn_show)
        msg_btns.addWidget(btn_hide)
        
        msg_layout.addLayout(msg_btns)
        msg_group.setLayout(msg_layout)
        
        right_panel.addWidget(msg_group)
        right_panel.addStretch()
        
        content_layout.addLayout(right_panel, stretch=4)
        main_layout.addLayout(content_layout)
        self.setLayout(main_layout)

    def refresh_table(self):
        self.table.blockSignals(True)
        self.table.setRowCount(len(self.assignments))
        for row, item in enumerate(self.assignments):
            self.table.setItem(row, 0, QTableWidgetItem(item['title']))
            self.table.setItem(row, 1, QTableWidgetItem(f"{item['duration_mins']} min"))
            
            secs = item['actual_seconds']
            m, s = int(secs // 60), int(secs % 60)
            actual_str = f"{m:02d}:{s:02d}" if secs > 0 else "--:--"
            
            item_actual = QTableWidgetItem(actual_str)
            item_actual.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, item_actual)
        self.table.blockSignals(False)

    def on_assignment_selected(self):
        row = self.table.currentRow()
        if row >= 0:
            selected_task = self.assignments[row]
            self.is_running = False
            self.timer.stop()
            self.total_duration = float(selected_task['duration_mins'] * 60)
            self.reset_timer_state()

    def add_slot(self):
        dialog = AddEditDialog(self)
        if dialog.exec():
            title, dur = dialog.get_data()
            if title and dur:
                try:
                    self.assignments.append({"title": title, "duration_mins": float(dur), "actual_seconds": 0.0})
                    self.refresh_table()
                    self.table.selectRow(len(self.assignments) - 1)
                except ValueError:
                    pass

    def edit_slot(self):
        row = self.table.currentRow()
        if row >= 0:
            task = self.assignments[row]
            dialog = AddEditDialog(self, task['title'], str(task['duration_mins']))
            if dialog.exec():
                title, dur = dialog.get_data()
                if title and dur:
                    try:
                        self.assignments[row]['title'] = title
                        self.assignments[row]['duration_mins'] = float(dur)
                        self.refresh_table()
                        self.on_assignment_selected()
                    except ValueError:
                        pass

    def delete_slot(self):
        row = self.table.currentRow()
        if row >= 0:
            del self.assignments[row]
            self.refresh_table()
            self.reset_timer_state()

    def move_up(self):
        row = self.table.currentRow()
        if row > 0:
            self.assignments[row], self.assignments[row-1] = self.assignments[row-1], self.assignments[row]
            self.refresh_table()
            self.table.selectRow(row-1)

    def move_down(self):
        row = self.table.currentRow()
        if 0 <= row < len(self.assignments) - 1:
            self.assignments[row], self.assignments[row+1] = self.assignments[row+1], self.assignments[row]
            self.refresh_table()
            self.table.selectRow(row+1)

    def show_message(self):
        if self.display_window and self.display_window.isVisible():
            self.display_window.msg_label.setText(self.msg_input.text().strip())

    def hide_message(self):
        self.msg_input.setText("")
        if self.display_window and self.display_window.isVisible():
            self.display_window.msg_label.setText("")

    def open_help(self):
        webbrowser.open_new("https://github.com/Eliezer-Cabrales/Crono")

    def open_settings(self):
        dialog = SettingsDialog(self, self.timer_mode, self.target_monitor_idx)
        if dialog.exec():
            self.timer_mode = dialog.mode
            self.target_monitor_idx = dialog.target_idx
            self.save_config()
            self.reset_timer_state()
            
            if self.display_window and self.display_window.isVisible():
                self.display_window.close()
            self.open_second_screen()

    def open_second_screen(self):
        if self.display_window and self.display_window.isVisible():
            return
            
        screens = QApplication.screens()
        
        if self.target_monitor_idx >= 0 and self.target_monitor_idx < len(screens):
            target_screen = screens[self.target_monitor_idx]
        else:
            target_screen = screens[-1]
            
        self.display_window = DisplayWindow()
        
        self.display_window.setScreen(target_screen)
        self.display_window.move(target_screen.geometry().topLeft())
        self.display_window.showFullScreen()
        
        self.update_interfaces()

    def hard_reset_timer(self):
        row = self.table.currentRow()
        if row >= 0:
            self.assignments[row]['actual_seconds'] = 0.0
            self.refresh_table()
        self.reset_timer_state()

    def reset_timer_state(self):
        self.is_running = False
        self.timer.stop()
        if self.timer_mode == "Regresiva":
            self.time_left = self.total_duration
        else:
            self.time_elapsed = 0.0
        self.update_interfaces()

    def toggle(self):
        if self.is_running:
            self.is_running = False
            self.timer.stop()
            
            row = self.table.currentRow()
            if row >= 0 and row < self.table.rowCount() - 1:
                self.table.selectRow(row + 1)
                
        else:
            self.is_running = True
            self.last_update_time = time.time()
            self.timer.start(100)

    def run_clock_engine(self):
        if not self.is_running:
            return
            
        current_time = time.time()
        elapsed = current_time - self.last_update_time
        self.last_update_time = current_time
        
        if self.timer_mode == "Regresiva":
            self.time_left -= elapsed
        else:
            self.time_elapsed += elapsed
            
        row = self.table.currentRow()
        if row >= 0:
            self.assignments[row]['actual_seconds'] += elapsed
            secs = self.assignments[row]['actual_seconds']
            m, s = int(secs // 60), int(secs % 60)
            
            item = self.table.item(row, 2)
            if item:
                item.setText(f"{m:02d}:{s:02d}")
        
        self.update_interfaces()

    def update_interfaces(self):
        if self.timer_mode == "Regresiva":
            active_seconds = self.time_left
            remaining_time = self.time_left
        else:
            active_seconds = self.time_elapsed
            remaining_time = self.total_duration - self.time_elapsed

        display_seconds = abs(active_seconds)
        
        minutes = int(display_seconds // 60)
        seconds = int(display_seconds % 60)
        
        sign = "-" if active_seconds < 0 and self.timer_mode == "Regresiva" else ""
        time_string = f"{sign}{minutes:02d}:{seconds:02d}"
        
        if remaining_time <= 0: 
            local_color = "red"
            display_color = "red"
        elif remaining_time <= 60 and self.total_duration > 0:
            local_color = "orange"
            display_color = "yellow"
        else:
            local_color = "#3399FF" 
            display_color = "white"

        self.local_clock.setText(time_string)
        self.local_clock.setStyleSheet(f"font-size: 48px; font-weight: bold; color: {local_color}; font-family: 'Segoe UI', Arial, sans-serif; font-feature-settings: 'tnum';")
        
        if self.display_window and self.display_window.isVisible():
            self.display_window.clock_label.setText(time_string)
            self.display_window.clock_label.setStyleSheet(f"font-size: 180px; font-weight: bold; color: {display_color}; font-family: 'Segoe UI', Arial, sans-serif; font-feature-settings: 'tnum';")