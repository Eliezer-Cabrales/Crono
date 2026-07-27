import tkinter as tk
from tkinter import ttk
import time
import re
from scraper import get_meeting_data

class StopwatchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Rahab - Panel de Control")
        self.root.geometry("650x480") # Un poco más de altura para los nuevos botones
        
        # --- CONFIGURATION VARIABLES (Settings) ---
        self.timer_mode = tk.StringVar(value="Progresiva") # Options: "Regresiva" or "Progresiva"
        self.target_monitor = tk.StringVar(value="")      # Will hold dynamic screen settings string
        
        # State management variables
        self.is_running = False
        self.time_elapsed = 0.0       
        self.time_left = 0.0          
        self.total_duration = 0.0     
        self.display_window = None
        self.display_label = None
        self.last_update_time = 0.0

        # Fetch data from the web scraper
        self.assignments = get_meeting_data() or []

        # --- 1. TOP BAR CONTAINER ---
        top_bar = ttk.Frame(root, padding=(10, 5))
        top_bar.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(top_bar, text="Rahab - Temporizador", font=("Arial", 12, "bold")).pack(side=tk.LEFT)

        try:
            self.gear_icon = tk.PhotoImage(file="gear.png")
            settings_btn = tk.Label(top_bar, image=self.gear_icon, cursor="hand2")
        except tk.TclError:
            print("Warning: 'gear.png' not found. Falling back to text icon.")
            settings_btn = tk.Label(top_bar, text="⚙", font=("Arial", 14), cursor="hand2")
        
        settings_btn.bind("<Button-1>", lambda event: self.open_settings())
        settings_btn.pack(side=tk.RIGHT, padx=5)

        ttk.Separator(root, orient='horizontal').pack(side=tk.TOP, fill=tk.X)

        # --- 2. MAIN LAYOUT CONTAINER ---
        main_container = ttk.Frame(root)
        main_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Left Panel: Assignment List
        left_frame = ttk.Frame(main_container, padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        ttk.Label(left_frame, text="Asignaciones de la Reunión:", font=("Arial", 11, "bold")).pack(anchor=tk.W, pady=5)
        
        self.listbox = tk.Listbox(left_frame, font=("Arial", 10), selectmode=tk.SINGLE)
        self.listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # --- PANEL DE BOTONES (Añadir, Editar, Eliminar, Subir, Bajar) ---
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        # Fila 1
        ttk.Button(btn_frame, text="+ Añadir", command=self.open_add_slot).grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        ttk.Button(btn_frame, text="✏ Editar", command=self.edit_slot).grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        ttk.Button(btn_frame, text="- Elim.", command=self.delete_slot).grid(row=0, column=2, padx=2, pady=2, sticky="ew")
        
        # Fila 2
        ttk.Button(btn_frame, text="↑ Subir", command=self.move_up).grid(row=1, column=0, padx=2, pady=2, sticky="ew")
        ttk.Button(btn_frame, text="↓ Bajar", command=self.move_down).grid(row=1, column=1, columnspan=2, padx=2, pady=2, sticky="ew")

        # Configurar proporciones de las columnas
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)
        btn_frame.columnconfigure(2, weight=1)

        self.refresh_listbox()
        self.listbox.bind('<<ListboxSelect>>', self.on_assignment_selected)

        # Right Panel: Timer and Execution Buttons
        right_frame = ttk.Frame(main_container, padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        ttk.Label(right_frame, text="Tiempo:", font=("Arial", 11, "bold")).pack(pady=5)
        
        self.local_clock_label = ttk.Label(right_frame, text="00:00.00", font=("Arial", 36, "bold"))
        self.local_clock_label.pack(pady=15)

        self.toggle_button = ttk.Button(right_frame, text="Iniciar / Parar", command=self.toggle)
        self.toggle_button.pack(pady=5, fill=tk.X)

        self.reset_button = ttk.Button(right_frame, text="🔄 Reiniciar", command=self.reset_timer_state)
        self.reset_button.pack(pady=5, fill=tk.X)
        
        ttk.Button(right_frame, text="Abrir Segunda Pantalla", command=self.open_second_screen).pack(pady=20, fill=tk.X)

        if self.assignments:
            self.listbox.selection_set(0)
            self.on_assignment_selected(None)

    def refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for item in self.assignments:
            self.listbox.insert(tk.END, f"{item['title']} ({item['duration_mins']} min)")

    def open_add_slot(self):
        """ Abre una ventana para añadir asignaciones manuales """
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
                    self.assignments.append({"title": title, "duration_mins": dur_float})
                    self.refresh_listbox()
                    self.listbox.selection_clear(0, tk.END)
                    self.listbox.selection_set(tk.END)
                    self.on_assignment_selected(None)
                    add_win.destroy()
                except ValueError:
                    pass 

        ttk.Button(add_win, text="Guardar", command=save_slot).pack(pady=15)

    def edit_slot(self):
        """ Modifica la asignación seleccionada """
        selection = self.listbox.curselection()
        if not selection:
            return
            
        index = selection[0]
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
                    self.assignments[index] = {"title": title, "duration_mins": dur_float}
                    self.refresh_listbox()
                    self.listbox.selection_clear(0, tk.END)
                    self.listbox.selection_set(index)
                    self.on_assignment_selected(None)
                    edit_win.destroy()
                except ValueError:
                    pass 

        ttk.Button(edit_win, text="Actualizar", command=save_edit).pack(pady=15)

    def delete_slot(self):
        """ Elimina la asignación seleccionada """
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            del self.assignments[index]
            self.refresh_listbox()
            self.reset_timer_state()

    def move_up(self):
        """ Sube la asignación en la lista """
        selection = self.listbox.curselection()
        if not selection:
            return
        index = selection[0]
        if index > 0:
            # Intercambiar elementos
            self.assignments[index], self.assignments[index - 1] = self.assignments[index - 1], self.assignments[index]
            self.refresh_listbox()
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(index - 1)
            self.on_assignment_selected(None)

    def move_down(self):
        """ Baja la asignación en la lista """
        selection = self.listbox.curselection()
        if not selection:
            return
        index = selection[0]
        if index < len(self.assignments) - 1:
            # Intercambiar elementos
            self.assignments[index], self.assignments[index + 1] = self.assignments[index + 1], self.assignments[index]
            self.refresh_listbox()
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(index + 1)
            self.on_assignment_selected(None)

    def open_settings(self):
        settings_win = tk.Toplevel(self.root)
        settings_win.title("Ajustes de Configuración")
        settings_win.geometry("350x280")
        settings_win.grab_set()
        
        frame = ttk.Frame(settings_win, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Modo del Cronómetro:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        ttk.Radiobutton(frame, text="Cuenta Regresiva (A cero)", variable=self.timer_mode, value="Regresiva", command=self.reset_timer_state).pack(anchor=tk.W, padx=10)
        ttk.Radiobutton(frame, text="Cuenta Progresiva (Hacia arriba)", variable=self.timer_mode, value="Progresiva", command=self.reset_timer_state).pack(anchor=tk.W, padx=10, pady=(0, 15))
        
        screen_options = []
        try:
            from screeninfo import get_monitors
            for i, m in enumerate(get_monitors()):
                role = " (Principal)" if m.is_primary else ""
                screen_options.append(f"Pantalla {i + 1} ({m.width}x{m.height}+{m.x}+{m.y}){role}")
        except Exception:
            screen_options = ["Pantalla 1 (Principal)", "Pantalla 2 (Secundaria)"]

        ttk.Label(frame, text="Pantalla de Proyección por Defecto:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        if self.target_monitor.get() not in screen_options and screen_options:
            self.target_monitor.set(screen_options[0])

        monitor_combo = ttk.Combobox(frame, textvariable=self.target_monitor, values=screen_options, state="readonly")
        monitor_combo.pack(fill=tk.X, padx=10, pady=(0, 20))
        
        ttk.Button(frame, text="Guardar y Cerrar", command=settings_win.destroy).pack(anchor=tk.E)

    def on_assignment_selected(self, event):
        try:
            index = self.listbox.curselection()[0]
            selected_task = self.assignments[index]
            self.is_running = False
            
            self.total_duration = float(selected_task['duration_mins'] * 60)
            self.reset_timer_state()
        except IndexError:
            pass

    def reset_timer_state(self):
        self.is_running = False
        if self.timer_mode.get() == "Regresiva":
            self.time_left = self.total_duration
        else:
            self.time_elapsed = 0.0
        self.update_interfaces()

    def open_second_screen(self):
        if self.display_window and tk.Toplevel.winfo_exists(self.display_window):
            return
        
        self.display_window = tk.Toplevel(self.root)
        self.display_window.title("Pantalla de Proyección")
        self.display_window.configure(bg="black")
        
        self.display_window.bind("<Escape>", lambda e: self.display_window.destroy())
        
        selected_string = self.target_monitor.get()
        match = re.search(r'\(([^)]+)\)', selected_string)
        
        if match and "+" in match.group(1):
            geometry_info = match.group(1)
            geo_match = re.search(r'(\d+)x(\d+)([+-]\d+[+-]\d+)', geometry_info)
            if geo_match:
                width = geo_match.group(1)
                height = geo_match.group(2)
                offset_coords = geo_match.group(3)
                self.display_window.geometry(f"{width}x{height}{offset_coords}")
                self.display_window.attributes("-fullscreen", True)
        else:
            if "Pantalla 2" in selected_string:
                self.display_window.geometry("1920x1080")
                self.display_window.attributes("-fullscreen", True)
            else:
                self.display_window.geometry("600x400")
        
        self.display_window.focus_set()
        
        self.display_label = tk.Label(
            self.display_window, 
            text="00:00.00", 
            font=("Arial", 120, "bold"), 
            fg="white", 
            bg="black"
        )
        self.display_label.pack(expand=True)
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
        
        # --- Lógica de Colores ---
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