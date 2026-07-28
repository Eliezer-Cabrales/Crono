import tkinter as tk
from tkinter import ttk
import time
import re
import webbrowser
import os
import json
import ctypes
from scraper import get_meeting_data

# Solución DPI para Windows 11 (Evita que el zoom del 125% o 150% mueva la pantalla)
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

class StopwatchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Rahab - Panel de Control")
        self.root.geometry("750x580") 
        
        self.config_file = "rahab_config.json"
        
        self.timer_mode = tk.StringVar(value="Progresiva") 
        self.target_monitor = tk.StringVar(value="")      
        
        self.is_running = False
        self.time_elapsed = 0.0       
        self.time_left = 0.0          
        self.total_duration = 0.0     
        self.display_window = None
        self.display_label = None
        self.display_msg_label = None
        self.last_update_time = 0.0
        self._drag_item = None

        # Detectar las pantallas físicas conectadas en este momento
        current_screens = self.get_current_screens()

        # Cargar configuración si existe
        saved_monitor = ""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                    if "timer_mode" in data:
                        self.timer_mode.set(data["timer_mode"])
                    if "target_monitor" in data:
                        saved_monitor = data["target_monitor"]
            except Exception:
                pass

        # Decidir en qué pantalla abrir por defecto (la guardada o la última conectada)
        if saved_monitor in current_screens:
            self.target_monitor.set(saved_monitor)
        else:
            self.target_monitor.set(current_screens[-1] if current_screens else "")

        raw_data = get_meeting_data() or []
        self.assignments = []
        for item in raw_data:
            self.assignments.append({
                "title": item["title"],
                "duration_mins": item["duration_mins"],
                "actual_seconds": 0.0  
            })

        # --- 1. TOP BAR CONTAINER ---
        top_bar = ttk.Frame(root, padding=(10, 5))
        top_bar.pack(side=tk.TOP, fill=tk.X)

        try:
            self.root.iconbitmap("rahab_icon.ico")
        except Exception:
            pass

        ttk.Label(top_bar, text="Rahab", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        
        help_btn = ttk.Button(top_bar, text="ℹ Ayuda", command=self.open_help)
        help_btn.pack(side=tk.LEFT, padx=15)

        try:
            self.gear_icon = tk.PhotoImage(file="gear.png")
            settings_btn = tk.Label(top_bar, image=self.gear_icon, cursor="hand2")
        except tk.TclError:
            settings_btn = tk.Label(top_bar, text="⚙", font=("Arial", 14), cursor="hand2")
        
        settings_btn.bind("<Button-1>", lambda event: self.open_settings())
        settings_btn.pack(side=tk.RIGHT, padx=5)

        ttk.Separator(root, orient='horizontal').pack(side=tk.TOP, fill=tk.X)

        # --- 2. MAIN LAYOUT CONTAINER ---
        main_container = ttk.Frame(root)
        main_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(main_container, padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        ttk.Label(left_frame, text="Asignaciones de la Reunión:", font=("Arial", 11, "bold")).pack(anchor=tk.W, pady=5)
        
        columns = ("title", "duration", "actual")
        self.tree = ttk.Treeview(left_frame, columns=columns, show="headings", selectmode="browse")
        
        self.tree.heading("title", text="Asignación")
        self.tree.heading("duration", text="Previsto")
        self.tree.heading("actual", text="Real")
        
        self.tree.column("title", width=200, anchor="w")
        self.tree.column("duration", width=60, anchor="center")
        self.tree.column("actual", width=60, anchor="center")
        
        self.tree.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.tree.bind("<<TreeviewSelect>>", self.on_assignment_selected)
        self.tree.bind("<ButtonPress-1>", self.on_tree_press)
        self.tree.bind("<ButtonRelease-1>", self.on_tree_release)
        
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="+ Añadir", command=self.open_add_slot).grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        ttk.Button(btn_frame, text="✏ Editar", command=self.edit_slot).grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        ttk.Button(btn_frame, text="- Elim.", command=self.delete_slot).grid(row=0, column=2, padx=2, pady=2, sticky="ew")
        
        ttk.Button(btn_frame, text="↑ Subir", command=self.move_up).grid(row=1, column=0, padx=2, pady=2, sticky="ew")
        ttk.Button(btn_frame, text="↓ Bajar", command=self.move_down).grid(row=1, column=1, columnspan=2, padx=2, pady=2, sticky="ew")

        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)
        btn_frame.columnconfigure(2, weight=1)

        self.refresh_table()

        right_frame = ttk.Frame(main_container, padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        ttk.Label(right_frame, text="Tiempo:", font=("Arial", 11, "bold")).pack(pady=5)
        
        self.local_clock_label = ttk.Label(right_frame, text="00:00.00", font=("Arial", 36, "bold"))
        self.local_clock_label.pack(pady=10)

        self.toggle_button = ttk.Button(right_frame, text="Iniciar / Parar", command=self.toggle)
        self.toggle_button.pack(pady=5, fill=tk.X)

        self.reset_button = ttk.Button(right_frame, text="🔄 Reiniciar", command=self.hard_reset_timer)
        self.reset_button.pack(pady=5, fill=tk.X)
        
        ttk.Button(right_frame, text="Abrir Segunda Pantalla", command=self.open_second_screen).pack(pady=15, fill=tk.X)

        msg_frame = ttk.LabelFrame(right_frame, text="Mensaje en Proyector", padding=5)
        msg_frame.pack(fill=tk.X, pady=10)
        
        self.msg_var = tk.StringVar()
        self.msg_entry = ttk.Entry(msg_frame, textvariable=self.msg_var)
        self.msg_entry.pack(fill=tk.X, padx=5, pady=5)
        
        msg_btns = ttk.Frame(msg_frame)
        msg_btns.pack(fill=tk.X, pady=2)
        ttk.Button(msg_btns, text="Mostrar", command=self.show_message).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        ttk.Button(msg_btns, text="Ocultar", command=self.hide_message).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=2)

        if self.assignments:
            first_item = self.tree.get_children()[0]
            self.tree.selection_set(first_item)
            self.on_assignment_selected(None)

        # Auto-Inicia la segunda pantalla en el monitor seleccionado
        self.root.after(500, self.open_second_screen)

    def get_current_screens(self):
        screen_options = []
        try:
            from screeninfo import get_monitors
            monitors = get_monitors()
            monitors.sort(key=lambda m: m.x)
            for i, m in enumerate(monitors):
                role = " (Principal)" if m.is_primary else ""
                screen_options.append(f"Pantalla {i + 1} ({m.width}x{m.height}{m.x:+d}{m.y:+d}){role}")
        except Exception:
            screen_options = ["Pantalla 1 (Principal)", "Pantalla 2 (Secundaria)"]
        return screen_options

    def save_config(self):
        data = {
            "timer_mode": self.timer_mode.get(),
            "target_monitor": self.target_monitor.get()
        }
        try:
            with open(self.config_file, "w") as f:
                json.dump(data, f)
        except Exception:
            pass

    def open_settings(self):
        settings_win = tk.Toplevel(self.root)
        settings_win.title("Ajustes de Configuración")
        settings_win.geometry("380x280")
        settings_win.grab_set()
        
        frame = ttk.Frame(settings_win, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Modo del Cronómetro:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        ttk.Radiobutton(frame, text="Cuenta Regresiva (A cero)", variable=self.timer_mode, value="Regresiva", command=self.reset_timer_state).pack(anchor=tk.W, padx=10)
        ttk.Radiobutton(frame, text="Cuenta Progresiva (Hacia arriba)", variable=self.timer_mode, value="Progresiva", command=self.reset_timer_state).pack(anchor=tk.W, padx=10, pady=(0, 15))
        
        current_screens = self.get_current_screens()

        ttk.Label(frame, text="Escritorio / Pantalla de Proyección:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        if self.target_monitor.get() not in current_screens and current_screens:
            self.target_monitor.set(current_screens[-1])

        monitor_combo = ttk.Combobox(frame, textvariable=self.target_monitor, values=current_screens, state="readonly")
        monitor_combo.pack(fill=tk.X, padx=10, pady=(0, 20))
        
        def save_and_close():
            self.save_config()
            settings_win.destroy()
            
            if self.display_window and tk.Toplevel.winfo_exists(self.display_window):
                self.display_window.destroy()
            self.open_second_screen()

        ttk.Button(frame, text="Guardar y Cerrar", command=save_and_close).pack(anchor=tk.E)

    def open_help(self):
        help_win = tk.Toplevel(self.root)
        help_win.title("Acerca de Rahab")
        help_win.geometry("400x180")
        help_win.grab_set()
        
        ttk.Label(help_win, text="Rahab Temporizador", font=("Arial", 14, "bold")).pack(pady=(15, 5))
        ttk.Label(help_win, text="Este proyecto es de código abierto.\nPuedes reportar errores o hablar con los desarrolladores aquí:", justify=tk.CENTER).pack()
        
        link = tk.Label(help_win, text="https://github.com/Eliezer-Cabrales/Crono", fg="blue", cursor="hand2", font=("Arial", 10, "underline"))
        link.pack(pady=10)
        link.bind("<Button-1>", lambda e: webbrowser.open_new("https://github.com/Eliezer-Cabrales/Crono"))
        
        ttk.Button(help_win, text="Cerrar", command=help_win.destroy).pack(pady=10)

    def show_message(self):
        texto = self.msg_var.get().strip()
        if self.display_window and tk.Toplevel.winfo_exists(self.display_window):
            self.display_msg_label.config(text=texto)

    def hide_message(self):
        self.msg_var.set("")
        if self.display_window and tk.Toplevel.winfo_exists(self.display_window):
            self.display_msg_label.config(text="")

    def refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
            
        for item in self.assignments:
            m = int(item["actual_seconds"] // 60)
            s = int(item["actual_seconds"] % 60)
            actual_str = f"{m:02d}:{s:02d}" if item["actual_seconds"] > 0 else "--:--"
            self.tree.insert("", tk.END, values=(item['title'], f"{item['duration_mins']} min", actual_str))

    def on_tree_press(self, event):
        self._drag_item = self.tree.identify_row(event.y)

    def on_tree_release(self, event):
        if not getattr(self, '_drag_item', None):
            return
        target = self.tree.identify_row(event.y)
        if target and target != self._drag_item:
            children = list(self.tree.get_children())
            try:
                from_idx = children.index(self._drag_item)
                to_idx = children.index(target)
                
                item = self.assignments.pop(from_idx)
                self.assignments.insert(to_idx, item)
                
                self.refresh_table()
                new_children = self.tree.get_children()
                self.tree.selection_set(new_children[to_idx])
            except ValueError:
                pass
        self._drag_item = None

    def open_add_slot(self):
        add_win = tk.Toplevel(self.root)
        add_win.title("Añadir Asignación")
        add_win.geometry("300x160")
        add_win.grab_set() 
        
        ttk.Label(add_win, text="Título de la asignación:").pack(pady=(10, 2))
        title_var = tk.StringVar()
        ttk.Entry(add_win, textvariable=title_var).pack(fill=tk.X, padx=20)
        
        ttk.Label(add_win, text="Duración (minutos):").pack(pady=(10, 2))
        duration_var = tk.StringVar()
        ttk.Entry(add_win, textvariable=duration_var).pack(fill=tk.X, padx=20)
        
        def save_slot():
            title = title_var.get().strip()
            dur = duration_var.get().strip()
            if title and dur:
                try:
                    dur_float = float(dur)
                    self.assignments.append({"title": title, "duration_mins": dur_float, "actual_seconds": 0.0})
                    self.refresh_table()
                    last_item = self.tree.get_children()[-1]
                    self.tree.selection_set(last_item)
                    self.on_assignment_selected(None)
                    add_win.destroy()
                except ValueError:
                    pass 

        ttk.Button(add_win, text="Guardar", command=save_slot).pack(pady=15)

    def edit_slot(self):
        selection = self.tree.selection()
        if not selection:
            return
            
        index = self.tree.index(selection[0])
        selected_task = self.assignments[index]

        edit_win = tk.Toplevel(self.root)
        edit_win.title("Editar Asignación")
        edit_win.geometry("300x160")
        edit_win.grab_set() 
        
        ttk.Label(edit_win, text="Título de la asignación:").pack(pady=(10, 2))
        title_var = tk.StringVar(value=selected_task['title'])
        ttk.Entry(edit_win, textvariable=title_var).pack(fill=tk.X, padx=20)
        
        ttk.Label(edit_win, text="Duración (minutos):").pack(pady=(10, 2))
        duration_var = tk.StringVar(value=str(selected_task['duration_mins']))
        ttk.Entry(edit_win, textvariable=duration_var).pack(fill=tk.X, padx=20)
        
        def save_edit():
            title = title_var.get().strip()
            dur = duration_var.get().strip()
            if title and dur:
                try:
                    dur_float = float(dur)
                    self.assignments[index]['title'] = title
                    self.assignments[index]['duration_mins'] = dur_float
                    self.refresh_table()
                    self.tree.selection_set(self.tree.get_children()[index])
                    self.on_assignment_selected(None)
                    edit_win.destroy()
                except ValueError:
                    pass 

        ttk.Button(edit_win, text="Actualizar", command=save_edit).pack(pady=15)

    def delete_slot(self):
        selection = self.tree.selection()
        if selection:
            index = self.tree.index(selection[0])
            del self.assignments[index]
            self.refresh_table()
            self.reset_timer_state()

    def move_up(self):
        selection = self.tree.selection()
        if not selection:
            return
        index = self.tree.index(selection[0])
        if index > 0:
            self.assignments[index], self.assignments[index - 1] = self.assignments[index - 1], self.assignments[index]
            self.refresh_table()
            new_children = self.tree.get_children()
            self.tree.selection_set(new_children[index - 1])
            self.on_assignment_selected(None)

    def move_down(self):
        selection = self.tree.selection()
        if not selection:
            return
        index = self.tree.index(selection[0])
        if index < len(self.assignments) - 1:
            self.assignments[index], self.assignments[index + 1] = self.assignments[index + 1], self.assignments[index]
            self.refresh_table()
            new_children = self.tree.get_children()
            self.tree.selection_set(new_children[index + 1])
            self.on_assignment_selected(None)

    def on_assignment_selected(self, event):
        try:
            selection = self.tree.selection()
            if selection:
                index = self.tree.index(selection[0])
                selected_task = self.assignments[index]
                self.is_running = False
                
                self.total_duration = float(selected_task['duration_mins'] * 60)
                self.reset_timer_state()
        except IndexError:
            pass

    def hard_reset_timer(self):
        selection = self.tree.selection()
        if selection:
            index = self.tree.index(selection[0])
            self.assignments[index]['actual_seconds'] = 0.0
            self.tree.set(selection[0], "actual", "--:--")
        self.reset_timer_state()

    def reset_timer_state(self):
        self.is_running = False
        if self.timer_mode.get() == "Regresiva":
            self.time_left = self.total_duration
        else:
            self.time_elapsed = 0.0
        self.update_interfaces()

    # ==========================================================
    # LÓGICA DE PANTALLA EXTENDIDA CORREGIDA
    # ==========================================================
    def open_second_screen(self):
        if self.display_window and tk.Toplevel.winfo_exists(self.display_window):
            return
        
        self.display_window = tk.Toplevel(self.root)
        self.display_window.title("Pantalla de Proyección")
        self.display_window.configure(bg="black")
        
        self.display_window.bind("<Escape>", lambda e: self.display_window.destroy())
        
        selected_string = self.target_monitor.get()
        
        # Expresión regular que captura ancho (1), alto (2), X (3) e Y (4)
        match = re.search(r'\((\d+)x(\d+)([+-]\d+)([+-]\d+)\)', selected_string)
        
        if match:
            width = match.group(1)
            height = match.group(2)
            x_coord = match.group(3)
            y_coord = match.group(4)
            
            # TRUCO INFALIBLE: Quitamos los bordes (overrideredirect) y le asignamos el tamaño exacto 
            # de la pantalla extendida en sus coordenadas exactas. Esto evita el bug de Tkinter.
            self.display_window.overrideredirect(True)
            self.display_window.geometry(f"{width}x{height}{x_coord}{y_coord}")
        else:
            # Plan B si no se detectaron bien las pantallas
            if "Pantalla 2" in selected_string:
                self.display_window.overrideredirect(True)
                self.display_window.geometry("1920x1080+1920+0")
            else:
                self.display_window.attributes("-fullscreen", True)
        
        self.display_window.focus_set()
        
        container = tk.Frame(self.display_window, bg="black")
        container.pack(expand=True)
        
        self.display_label = tk.Label(
            container, 
            text="00:00.00", 
            font=("Arial", 120, "bold"), 
            fg="white", 
            bg="black"
        )
        self.display_label.pack()
        
        self.display_msg_label = tk.Label(
            container,
            text=self.msg_var.get(),
            font=("Arial", 45, "bold"),
            fg="yellow",
            bg="black"
        )
        self.display_msg_label.pack(pady=20)
        
        self.update_interfaces()

    def toggle(self):
        if self.is_running:
            self.is_running = False
        else:
            self.is_running = True
            self.last_update_time = time.time()
            self.run_clock_engine()

    def run_clock_engine(self):
        if self.is_running:
            current_time = time.time()
            elapsed = current_time - self.last_update_time
            self.last_update_time = current_time
            
            if self.timer_mode.get() == "Regresiva":
                self.time_left -= elapsed
            else:
                self.time_elapsed += elapsed
                
            selection = self.tree.selection()
            if selection:
                index = self.tree.index(selection[0])
                self.assignments[index]['actual_seconds'] += elapsed
                
                secs = self.assignments[index]['actual_seconds']
                m = int(secs // 60)
                s = int(secs % 60)
                self.tree.set(selection[0], "actual", f"{m:02d}:{s:02d}")
            
            self.update_interfaces()
            self.root.after(10, self.run_clock_engine)

    def update_interfaces(self):
        if self.timer_mode.get() == "Regresiva":
            active_seconds = self.time_left
            remaining_time = self.time_left
        else:
            active_seconds = self.time_elapsed
            remaining_time = self.total_duration - self.time_elapsed

        display_seconds = abs(active_seconds)
        
        minutes = int(display_seconds // 60)
        seconds = int(display_seconds % 60)
        hundredths = int((display_seconds % 1) * 100)
        
        sign = "-" if active_seconds < 0 and self.timer_mode.get() == "Regresiva" else ""
        time_string = f"{sign}{minutes:02d}:{seconds:02d}.{hundredths:02d}"
        
        if remaining_time <= 0: 
            local_color = "red"
            display_color = "red"
        elif remaining_time <= 60 and self.total_duration > 0:
            local_color = "orange"
            display_color = "yellow"
        else:
            local_color = "black"
            display_color = "white"

        self.local_clock_label.config(text=time_string, foreground=local_color)
        
        if self.display_label and tk.Toplevel.winfo_exists(self.display_window):
            self.display_label.config(text=time_string, fg=display_color)