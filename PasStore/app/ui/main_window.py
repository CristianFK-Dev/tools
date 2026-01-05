import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
from app.config import THEMES
from app.data.database import DatabaseManager
from app.utils.security import SecurityManager

class MainApp:
    def __init__(self, root, encryption_manager):
        self.root = root
        self.root.title("Gestor de Contraseñas - Tabla Maestra")
        self.root.geometry("1300x700")
        
        self.db = DatabaseManager()
        self.encryption_manager = encryption_manager
        
        # Migrate existing data to encrypted format if needed
        if not self.db.is_data_encrypted():
            messagebox.showinfo("Migración de Datos", "Se detectaron datos sin encriptar. Se procederá a encriptarlos por seguridad.")
            self.db.migrate_to_encrypted(self.encryption_manager)
            messagebox.showinfo("Éxito", "Todos los datos han sido encriptados correctamente.")
        
        self.current_tab_id = 1 # ID por defecto (Principal)
        self.current_tab_color = "#f0f0f0" # Default color
        self.configured_color_tags = set()  # Track configured color tags

        # Definición de Temas
        self.themes = THEMES
        # Load theme from DB or default to Light
        saved_theme = self.db.get_setting("theme", "Light")
        self.current_theme = saved_theme
        
        self.theme_cycle = ["Light", "Semi-Dark", "Dark"]
        
        # Estructura principal
        self.create_widgets()
        
        # Frame de Pestañas (Abajo)
        self.tab_frame = tk.LabelFrame(self.root, text="Pestañas", bg="#f0f0f0", height=40)
        self.tab_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        
        self.load_tabs()
        self.load_data()
        
        # Bind window resize event for responsive columns
        self.root.bind('<Configure>', self.on_window_resize)

    def create_widgets(self):
        # Frame para la Tabla (Treeview)
        tree_frame = tk.Frame(self.root)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Definición de columnas (NUEVA ESTRUCTURA)
        columns = ("ID", "Detalle / SID", "Tipo acceso", "HOST / IP / DNS", "Puerto", "User", "Pass", "Rol", "Contiene", "Instancia / Tipo", "IP Priv", "IP Pub")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings")

        # Initialize visibility state (all visible by default)
        if not hasattr(self, 'col_visible'):
            self.col_visible = {col: True for col in columns}
            self.global_visibility = True

        # Configurar encabezados (sin anchos fijos)
        # Lista de columnas a mostrar (Excluyendo "ID")
        display_cols = list(columns)
        display_cols.remove("ID")
        self.tree["displaycolumns"] = display_cols

        for col in columns:
            self.update_header(col)
            # Centrar contenido en todas las columnas, sin ancho fijo inicial
            self.tree.column(col, width=100, anchor=tk.CENTER, minwidth=50, stretch=True)

        # Vertical Scrollbar
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=v_scrollbar.set)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Horizontal Scrollbar
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(xscroll=h_scrollbar.set)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configurar tag para filas alternas
        self.tree.tag_configure('oddrow', background='#f2f2f2')
        
        # Evento doble click para copiar password
        self.tree.bind("<Double-1>", self.on_double_click)
        # Evento selección para editar
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        # Evento botón derecho para menú de colores
        self.tree.bind("<Button-3>", self.show_row_color_menu)

        # Frame para Entradas de datos (Formulario abajo)
        input_frame = tk.LabelFrame(self.root, text="Agregar Nueva Entrada / Actualizar")
        input_frame.pack(fill=tk.X, padx=10, pady=5)

        # Entradas - Una sola fila (Diseño original horizontal)
        labels = ["Detalle / SID", "Tipo acceso", "HOST / IP / DNS", "Puerto", "User", "Pass", "Rol", "Contiene", "Instancia / Tipo", "IP Priv", "IP Pub"]
        self.entries = {}

        # Configurar columnas para que se expandan equitativamente
        for col_idx in range(len(labels) + 1):
            input_frame.columnconfigure(col_idx, weight=1)

        for i, label in enumerate(labels):
            tk.Label(input_frame, text=label, font=("Arial", 8)).grid(row=0, column=i, padx=2, pady=(3, 0), sticky="ew")
            entry = tk.Entry(input_frame, font=("Arial", 9))
            entry.grid(row=1, column=i, padx=2, pady=(0, 5), sticky="ew")
            self.entries[label] = entry
        
        # Botón de limpiar campos (escobita)
        clean_btn = tk.Button(input_frame, text="🧹", font=("Arial", 10), width=3, command=self.clear_inputs, bg="#9E9E9E", fg="white")
        clean_btn.grid(row=1, column=len(labels), padx=2, pady=(0, 5))

        # Botones de Acción - DISEÑO COMPACTO
        btn_frame = tk.LabelFrame(self.root, text="Acciones")
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Frame izquierdo para botones principales
        left_btn_frame = tk.Frame(btn_frame)
        left_btn_frame.pack(side=tk.LEFT, padx=5)
        
        tk.Button(left_btn_frame, text="Guardar", bg="#4CAF50", fg="white", width=15, command=self.add_entry).pack(side=tk.LEFT, padx=3)
        tk.Button(left_btn_frame, text="Actualizar", bg="#2196F3", fg="white", width=15, command=self.update_entry).pack(side=tk.LEFT, padx=3)
        tk.Button(left_btn_frame, text="Eliminar", bg="#F44336", fg="white", width=15, command=self.delete_entry).pack(side=tk.LEFT, padx=3)
        tk.Button(left_btn_frame, text="Separador", bg="#9E9E9E", fg="white", width=15, command=self.insert_separator).pack(side=tk.LEFT, padx=3)
        
        # Frame para botones de ordenamiento
        order_frame = tk.LabelFrame(btn_frame, text="Orden")
        order_frame.pack(side=tk.LEFT, padx=10)
        
        tk.Button(order_frame, text="▲", bg="#607D8B", fg="white", width=3, command=self.move_entry_up).pack(side=tk.LEFT, padx=2)
        tk.Button(order_frame, text="▼", bg="#607D8B", fg="white", width=3, command=self.move_entry_down).pack(side=tk.LEFT, padx=2)
        
        # Frame de Importar/Exportar
        csv_frame = tk.LabelFrame(btn_frame, text="CSV")
        csv_frame.pack(side=tk.RIGHT, padx=5)
        
        tk.Button(csv_frame, text="Exportar", bg="#FF9800", fg="white", width=10, command=self.export_to_csv).pack(side=tk.LEFT, padx=2)
        tk.Button(csv_frame, text="Importar", bg="#FF5722", fg="white", width=10, command=self.import_from_csv).pack(side=tk.LEFT, padx=2)

        # Frame de Configuraciones
        configs_frame = tk.LabelFrame(btn_frame, text="Configs")
        configs_frame.pack(side=tk.RIGHT, padx=5)

        # Botón de Tema
        self.theme_btn = tk.Button(configs_frame, text=f"Tema: {self.current_theme}", width=12, command=self.toggle_theme)
        self.theme_btn.pack(side=tk.LEFT, padx=2)
        
        # Global Eye Button
        self.global_eye_btn = tk.Button(configs_frame, text="👁 Todos", width=8, command=self.toggle_all_visibility)
        self.global_eye_btn.pack(side=tk.LEFT, padx=2)

        # Botón Cambiar Pass
        tk.Button(configs_frame, text="Cambiar Pass", width=12, command=self.change_master_password).pack(side=tk.LEFT, padx=2)
        
        # LED Copy Indicator
        self.copy_indicator = tk.Label(configs_frame, text="⚫", font=("Arial", 14), fg="#757575")
        self.copy_indicator.pack(side=tk.LEFT, padx=2)
        self.copy_timer = None  # Timer for LED reset
        
        # Apply initial theme
        self.root.after(100, self.apply_theme)
        
        self.selected_record_id = None

    def on_tree_select(self, event):
        selected = self.tree.selection()
        if not selected:
             return
             
        item = self.tree.item(selected[0])
        tree_values = item['values']
        self.selected_record_id = tree_values[0]
        
        # current_data: (id, detalle, tipo_acceso, acceso_host, puerto, usuario, password, rol, contiene, instancia_tipo, ip_priv, ip_pub)
        # Indices:        0     1          2             3            4        5         6         7       8         9              10        11
        
        # Get unencrypted data from database
        all_creds = self.db.get_credentials(self.current_tab_id, self.encryption_manager)
        current_data = None
        for row in all_creds:
            if str(row[0]) == str(self.selected_record_id): # row[0] is ID
                current_data = row
                break
        
        if not current_data:
             return

        # current_data: (id, detalle, tipo_acceso, acceso_host, puerto, usuario, password, rol, contiene, instancia_tipo, ip_priv, ip_pub)
        # Indices:        0     1          2             3            4        5         6         7       8         9              10        11
        
        entry_map = {
            "Detalle / SID": 1,
            "Tipo acceso": 2,
            "HOST / IP / DNS": 3,
            "Puerto": 4,
            "User": 5,
            "Pass": 6,
            "Rol": 7,
            "Contiene": 8,
            "Instancia / Tipo": 9,
            "IP Priv": 10,
            "IP Pub": 11
        }

        for label, idx in entry_map.items():
            entry = self.entries[label]
            entry.delete(0, tk.END)
            val = current_data[idx]
            if val is not None:
                entry.insert(0, val)

    def update_entry(self):
        if not self.selected_record_id:
             messagebox.showwarning("Error", "No hay ningún registro seleccionado para actualizar")
             return

        v_detalle = self.entries["Detalle / SID"].get()
        if not v_detalle:
            messagebox.showwarning("Faltan datos", "El campo 'Detalle' es obligatorio")
            return

        data = (
            v_detalle,
            self.entries["Tipo acceso"].get(),
            self.entries["HOST / IP / DNS"].get(),
            self.entries["Puerto"].get(),
            self.entries["User"].get(),
            self.entries["Pass"].get(),
            self.entries["Rol"].get(),
            self.entries["Contiene"].get(),
            self.entries["Instancia / Tipo"].get(),
            self.entries["IP Priv"].get(),
            self.entries["IP Pub"].get()
        )
        
        self.db.update_credential(self.selected_record_id, data, self.encryption_manager)
        self.clear_inputs()
        self.selected_record_id = None
        self.load_data()

    def update_header(self, col):
        if col == "ID":
            self.tree.heading(col, text=col)
            return
            
        is_visible = self.col_visible.get(col, True)
        icon = "👁" if is_visible else "🔒" # Using standard unicode chars, assuming user font supports it
        # Tkinter treeview headings command runs when clicked
        self.tree.heading(col, text=f"{col} {icon}", command=lambda c=col: self.toggle_column(c))

    def toggle_column(self, col):
        self.col_visible[col] = not self.col_visible.get(col, True)
        self.update_header(col)
        self.load_data()
        
    def toggle_all_visibility(self):
        # Toggle global state
        self.global_visibility = not self.global_visibility
        new_state = self.global_visibility
        
        # Update button text/icon
        icon = "👁 Todos" if new_state else "🔒 Todos"
        self.global_eye_btn.config(text=icon)
        
        # Update all columns
        # Derived from tree columns (excluding ID if we don't track it, but we init for all)
        for col in self.col_visible.keys():
             self.col_visible[col] = new_state
             self.update_header(col)
             
        self.load_data()

    # --- LÓGICA DE TEMAS ---
    def toggle_theme(self):
        idx = self.theme_cycle.index(self.current_theme)
        next_idx = (idx + 1) % len(self.theme_cycle)
        self.current_theme = self.theme_cycle[next_idx]
        
        # Save new theme
        self.db.set_setting("theme", self.current_theme)
        
        self.apply_theme()

    def apply_theme(self):
        theme = self.themes[self.current_theme]
        if hasattr(self, 'theme_btn'):
            self.theme_btn.config(text=f"Tema: {self.current_theme}")

        style = ttk.Style()
        style.theme_use("default")
        
        style.configure("Treeview", 
                        background=theme["tree_bg"], 
                        foreground=theme["tree_fg"], 
                        fieldbackground=theme["tree_bg"])
        
        style.map('Treeview', background=[('selected', '#3498db')])
        self.tree.tag_configure('oddrow', background=theme["tree_odd"])
        
        # Reconfigure separator tag with current tab color
        if hasattr(self, 'current_tab_color'):
            self.tree.tag_configure('separator', background=self.current_tab_color)
        
        self.root.configure(bg=theme["bg"])
        self.recursive_configure(self.root, theme)
        
        # Re-apply header color as theme change might reset it
        if hasattr(self, 'current_tab_color'):
            self.apply_header_color()

    def apply_header_color(self):
        style = ttk.Style()
        style.configure("Treeview.Heading", background=self.current_tab_color)
        
    def recursive_configure(self, widget, theme):
        try:
            widget_type = widget.winfo_class()
            
            if widget_type == 'Button':
                text = str(widget.cget('text'))
                # Lista de botones que mantienen su color original
                excluded_buttons = ["Guardar Registro", "Guardar", "Eliminar Seleccionado", "Eliminar", 
                                  "Actualizar", "Crear", "Ingresar", "Separador", "Insertar Separador",
                                  "▲", "▼", "Exportar CSV", "Exportar", "Importar CSV", "Importar"]
                if text in excluded_buttons:
                    return 
                
            if widget_type in ['Frame', 'LabelFrame', 'Labelframe']:
                widget.configure(bg=theme["bg"])
                if widget_type in ['LabelFrame', 'Labelframe']:
                    widget.configure(fg=theme["fg"])
            
            elif widget_type == 'Label':
                widget.configure(bg=theme["bg"], fg=theme["fg"])
                
            elif widget_type == 'Entry':
                widget.configure(bg=theme["entry_bg"], fg=theme["entry_fg"], insertbackground=theme["fg"])
                
            elif widget_type == 'Button':
                text = str(widget.cget('text'))
                if text.startswith("Tema"):
                     widget.configure(bg=theme["btn_bg"], fg=theme["btn_fg"])
                     
        except tk.TclError:
            pass 
            
        for child in widget.winfo_children():
            self.recursive_configure(child, theme)

    # --- LÓGICA DE PESTAÑAS ---
    def load_tabs(self):
        for widget in self.tab_frame.winfo_children():
            widget.destroy()

        tabs = self.db.get_tabs()

        for tab_id, name, color in tabs:
            relief = tk.SUNKEN if tab_id == self.current_tab_id else tk.RAISED
            # Simple contrast check could be added here
            btn = tk.Button(self.tab_frame, text=name, bg=color, fg="black", relief=relief,
                            width=15,
                            command=lambda t=tab_id: self.switch_tab(t))
            btn.pack(side=tk.LEFT, padx=2, pady=2)
            btn.bind("<Button-3>", lambda event, t=tab_id, n=name: self.show_context_menu(event, t, n))

            if tab_id == self.current_tab_id:
                self.current_tab_color = color
                self.apply_header_color()
                # Update separator tag color
                self.tree.tag_configure('separator', background=self.current_tab_color)

        add_btn = tk.Button(self.tab_frame, text="+", bg="#4CAF50", fg="white", width=3, command=self.open_new_tab_dialog)
        add_btn.pack(side=tk.LEFT, padx=5, pady=2)

        # Delete tab button
        del_btn = tk.Button(self.tab_frame, text="-", bg="#F44336", fg="white", width=3, command=self.delete_current_tab)
        del_btn.pack(side=tk.LEFT, padx=2, pady=2)

        # Move Left button
        tk.Button(self.tab_frame, text="◀", bg="#9E9E9E", fg="white", width=3, command=self.move_tab_left).pack(side=tk.LEFT, padx=2, pady=2)
        
        # Move Right button
        tk.Button(self.tab_frame, text="▶", bg="#9E9E9E", fg="white", width=3, command=self.move_tab_right).pack(side=tk.LEFT, padx=2, pady=2)

    def delete_current_tab(self):
        # Prevent deleting the default/last tab if desired, or handle empty state.
        # For now, let's allow it but we need at least one tab or handle empty state.
        # Simple check: if only 1 tab exists, maybe don't delete or recreate default?
        tabs = self.db.get_tabs()
        if len(tabs) <= 1:
            messagebox.showwarning("Acción no permitida", "No puedes borrar la única pestaña restante.")
            return

        # Get current tab name for confirmation
        current_name = "Desconocido"
        for t_id, t_name, _ in tabs:
            if t_id == self.current_tab_id:
                current_name = t_name
                break

        confirm = messagebox.askyesno("Confirmar Eliminación", f"¿Quiere borrar la pestaña '{current_name}'?\nSe perderán todas las credenciales de esta pestaña.")
        if confirm:
            self.db.delete_tab(self.current_tab_id)
            # Switch to the first available tab
            remaining_tabs = self.db.get_tabs()
            if remaining_tabs:
                self.current_tab_id = remaining_tabs[0][0]
            else:
                # Should not happen due to len check, but safe fallback
                self.current_tab_id = None 
            
            self.load_tabs()
            self.load_data()

    def move_tab_left(self):
        tabs = self.db.get_tabs()
        # tabs is list of (id, name, color) tuples
        
        # Find current index
        current_idx = -1
        for i, (t_id, _, _) in enumerate(tabs):
            if t_id == self.current_tab_id:
                current_idx = i
                break
        
        if current_idx <= 0:
            return # Can't move left
            
        # Swap in the list (we need to convert tuple to list to modify or just swap elements in list)
        tabs[current_idx], tabs[current_idx-1] = tabs[current_idx-1], tabs[current_idx]
        
        # Update order in DB
        new_order_ids = [t[0] for t in tabs]
        self.db.update_tab_order(new_order_ids)
        self.load_tabs()

    def move_tab_right(self):
        tabs = self.db.get_tabs()
        
        current_idx = -1
        for i, (t_id, _, _) in enumerate(tabs):
            if t_id == self.current_tab_id:
                current_idx = i
                break
        
        if current_idx == -1 or current_idx >= len(tabs) - 1:
            return # Can't move right
            
        # Swap
        tabs[current_idx], tabs[current_idx+1] = tabs[current_idx+1], tabs[current_idx]
        
        new_order_ids = [t[0] for t in tabs]
        self.db.update_tab_order(new_order_ids)
        self.load_tabs()

    def show_context_menu(self, event, tab_id, current_name):
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Cambiar Nombre", command=lambda: self.rename_tab(tab_id, current_name))
        menu.add_command(label="Cambiar Color", command=lambda: self.change_tab_color(tab_id))
        menu.post(event.x_root, event.y_root)

    def center_window(self, window, width, height):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        window.geometry(f'{width}x{height}+{x}+{y}')

    def create_styled_toplevel(self, title, width, height):
        top = tk.Toplevel(self.root)
        top.title(title)
        self.center_window(top, width, height)
        
        # Apply current theme
        theme = self.themes[self.current_theme]
        top.configure(bg=theme["bg"])
        
        # This will need to be called AFTER widgets are added for full effect, 
        # or we rely on widgets inheriting or being configured manually. 
        # But for the window background, this is enough. 
        # We will also return the theme so the caller can use it for widgets if needed.
        return top, theme

    def rename_tab(self, tab_id, current_name):
        dialog, theme = self.create_styled_toplevel("Renombrar", 300, 150)

        tk.Label(dialog, text="Nuevo Nombre:", bg=theme["bg"], fg=theme["fg"]).pack(pady=10)
        entry = tk.Entry(dialog, bg=theme["entry_bg"], fg=theme["entry_fg"], insertbackground=theme["fg"])
        entry.insert(0, current_name)
        entry.pack(pady=5)
        entry.focus()
        
        def save():
            new_name = entry.get()
            if new_name:
                self.db.rename_tab(tab_id, new_name)
                dialog.destroy()
                self.load_tabs()

        tk.Button(dialog, text="Guardar", bg="#4CAF50", fg="white", command=save).pack(pady=10)
        dialog.bind('<Return>', lambda e: save())

    def change_tab_color(self, tab_id):
        dialog, theme = self.create_styled_toplevel("Cambiar Color", 300, 200)
        
        tk.Label(dialog, text="Selecciona un nuevo color:", bg=theme["bg"], fg=theme["fg"]).pack(pady=10)
        
        colors = [
            "#FFCDD2", "#F8BBD0", "#E1BEE7", "#D1C4E9", "#C5CAE9", 
            "#BBDEFB", "#B3E5FC", "#B2EBF2", "#B2DFDB", "#C8E6C9", 
            "#DCEDC8", "#F0F4C3", "#FFF9C4", "#FFECB3", "#FFE0B2", 
            "#FFCCBC", "#D7CCC8", "#F5F5F5", "#CFD8DC", "#FF8A65"
        ]
        
        color_frame = tk.Frame(dialog, bg=theme["bg"])
        color_frame.pack(pady=5)
        
        # Helper to set the color to DB
        def set_color(c):
            self.db.update_tab_color(tab_id, c)
            dialog.destroy()
            self.load_tabs() # Refresh UI
        
        for i, color in enumerate(colors):
            row = i // 5
            col = i % 5
            btn = tk.Button(color_frame, bg=color, width=4, command=lambda c=color: set_color(c))
            btn.grid(row=row, column=col, padx=2, pady=2)

    def switch_tab(self, tab_id):
        self.current_tab_id = tab_id
        self.load_tabs() 
        self.load_data() 

    def open_new_tab_dialog(self):
        dialog, theme = self.create_styled_toplevel("Nueva Pestaña", 400, 300)
        
        tk.Label(dialog, text="Nombre de la hoja:", bg=theme["bg"], fg=theme["fg"]).pack(pady=5)
        name_entry = tk.Entry(dialog, bg=theme["entry_bg"], fg=theme["entry_fg"], insertbackground=theme["fg"])
        name_entry.pack(pady=5)
        
        tk.Label(dialog, text="Selecciona un color:", bg=theme["bg"], fg=theme["fg"]).pack(pady=5)
        
        colors = [
            "#FFCDD2", "#F8BBD0", "#E1BEE7", "#D1C4E9", "#C5CAE9", 
            "#BBDEFB", "#B3E5FC", "#B2EBF2", "#B2DFDB", "#C8E6C9", 
            "#DCEDC8", "#F0F4C3", "#FFF9C4", "#FFECB3", "#FFE0B2", 
            "#FFCCBC", "#D7CCC8", "#F5F5F5", "#CFD8DC", "#FF8A65"
        ]
        
        color_frame = tk.Frame(dialog, bg=theme["bg"])
        color_frame.pack(pady=10)
        
        selected_color = tk.StringVar(value="#FFFFFF")
        
        for i, color in enumerate(colors):
            row = i // 5
            col = i % 5
            btn = tk.Button(color_frame, bg=color, width=4, command=lambda c=color: selected_color.set(c))
            btn.grid(row=row, column=col, padx=2, pady=2)
            
        def create():
            name = name_entry.get()
            color = selected_color.get()
            if name:
                self.db.add_tab(name, color)
                dialog.destroy()
                self.load_tabs()
        
        tk.Button(dialog, text="Crear", bg="#4CAF50", fg="white", command=create).pack(pady=10)

    def add_entry(self):
        v_detalle = self.entries["Detalle / SID"].get()
        # Order must match database.py add_credential method args
        # (detalle, tipo_acceso, acceso_host, puerto, usuario, password, contiene, instancia_tipo, ip_pub, tab_id)
        
        if not v_detalle:
            messagebox.showwarning("Faltan datos", "El campo 'Detalle' es obligatorio")
            return

        data = (
            v_detalle,
            self.entries["Tipo acceso"].get(),
            self.entries["HOST / IP / DNS"].get(),
            self.entries["Puerto"].get(),
            self.entries["User"].get(),
            self.entries["Pass"].get(),
            self.entries["Rol"].get(),
            self.entries["Contiene"].get(),
            self.entries["Instancia / Tipo"].get(),
            self.entries["IP Priv"].get(),
            self.entries["IP Pub"].get(),
            self.current_tab_id
        )
        
        self.db.add_credential(data, self.encryption_manager)
        self.clear_inputs()
        self.load_data()

    def insert_separator(self):
        """Insert a separator row (all empty fields) with the current tab color"""
        # Create a separator: all fields empty except tab_id
        data = (
            "",  # detalle
            "",  # tipo_acceso
            "",  # acceso_host
            "",  # puerto
            "",  # usuario
            "",  # password
            "",  # rol
            "",  # contiene
            "",  # instancia_tipo
            "",  # ip_priv
            "",  # ip_pub
            self.current_tab_id
        )
        
        self.db.add_credential(data, self.encryption_manager)
        self.load_data()

    def delete_entry(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Error", "Selecciona una fila para borrar")
            return
        
        item = self.tree.item(selected)
        record_id = item['values'][0]

        confirm = messagebox.askyesno("Confirmar", "¿Seguro que deseas eliminar este registro?")
        if confirm:
            self.db.delete_credential(record_id)
            self.load_data()

    def load_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
            
        rows = self.db.get_credentials(self.current_tab_id, self.encryption_manager)
        
        # Mapping from DB index to column name
        # DB: id, detalle, tipo_acceso, acceso_host, puerto, usuario, password, rol, contiene, instancia_tipo, ip_priv, ip_pub, row_color
        # Cols: ("ID", "Detalle / SID", "Tipo acceso", "HOST / IP / DNS", "Puerto", "User", "Pass", "Rol", "Contiene", "Instancia / Tipo", "IP Priv", "IP Pub")
        
        db_idx_to_col = [
            "ID", "Detalle / SID", "Tipo acceso", "HOST / IP / DNS", "Puerto", "User", "Pass", "Rol", "Contiene", "Instancia / Tipo", "IP Priv", "IP Pub"
        ]

        for i, row in enumerate(rows):
            # Extract row_color (last element) before processing
            row_color = row[12] if len(row) > 12 else None
            
            # Process only the first 12 elements (exclude row_color)
            safe_row = list(row[:12])  # Convert tuple to list to modify
            
            # Apply masking
            for idx, val in enumerate(safe_row):
                if val is None or val == "":
                    safe_row[idx] = ""
                else:
                    col_name = db_idx_to_col[idx]
                    if col_name != "ID" and not self.col_visible.get(col_name, True):
                        safe_row[idx] = "******"

            # Determine tag based on separator status
            # Check if this is a separator row (all fields empty except ID)
            is_separator = all(not val or val == "" for idx, val in enumerate(safe_row) if idx > 0)
            
            # Build tags list
            tags = []
            
            if is_separator and safe_row[0]:  # Has ID but all other fields empty
                tags.append('separator')
            else:
                # Add alternating row background
                if i % 2 != 0:
                    tags.append('oddrow')
                
                # Add custom color tag if row has a color
                if row_color and row_color.startswith('#'):  # Only process valid hex colors
                    # Create a unique tag for this color
                    color_tag = f"color_{row_color.replace('#', '')}"
                    # Configure tag if not already configured
                    if color_tag not in self.configured_color_tags:
                        self.tree.tag_configure(color_tag, foreground=row_color)
                        self.configured_color_tags.add(color_tag)
                    tags.append(color_tag)
            
            self.tree.insert("", tk.END, values=safe_row, tags=tuple(tags))
        
        # Auto-resize columns after loading data
        self.auto_resize_columns()

    def auto_resize_columns(self):
        """Automatically resize columns based on content and header text"""
        import tkinter.font as tkfont
        
        # Get default font for measuring text
        font = tkfont.Font()
        
        columns = self.tree["columns"]
        
        for col in columns:
            # Start with header width
            header_text = self.tree.heading(col, "text")
            max_width = font.measure(str(header_text)) + 20  # Add padding
            
            # Check all rows for this column
            for item in self.tree.get_children():
                values = self.tree.item(item, "values")
                col_index = columns.index(col)
                
                if col_index < len(values):
                    cell_value = str(values[col_index])
                    cell_width = font.measure(cell_value) + 20  # Add padding
                    max_width = max(max_width, cell_width)
            
            # Set minimum and maximum widths
            max_width = max(50, min(max_width, 400))  # Between 50 and 400 pixels
            
            self.tree.column(col, width=int(max_width))
    
    def on_window_resize(self, event):
        """Handle window resize to expand columns proportionally"""
        # Only respond to root window resize events
        if event.widget != self.root:
            return
        
        # Delay the resize to avoid excessive calls
        if hasattr(self, '_resize_timer'):
            self.root.after_cancel(self._resize_timer)
        
        self._resize_timer = self.root.after(100, self._do_resize)
    
    def _do_resize(self):
        """Perform the actual column resize - expand columns proportionally based on content"""
        try:
            tree_width = self.tree.winfo_width()
        except:
            return
        
        # Skip if tree hasn't been rendered yet
        if tree_width <= 1:
            return
        
        columns = self.tree["columns"]
        if not columns:
            return
        
        # Get display columns (excluding ID)
        display_columns = self.tree["displaycolumns"]
        if isinstance(display_columns, str):
            # If it's "#all", use all columns
            visible_columns = list(columns)
        else:
            visible_columns = list(display_columns)
        
        if not visible_columns:
            return
        
        # Calculate available width (subtract scrollbar width)
        available_width = tree_width - 20
        
        # Get current column widths (based on content)
        import tkinter.font as tkfont
        font = tkfont.Font()
        
        col_widths = {}
        total_content_width = 0
        
        for col in visible_columns:
            # Start with header width
            header_text = self.tree.heading(col, "text")
            max_width = font.measure(str(header_text)) + 20
            
            # Check all rows for this column
            for item in self.tree.get_children():
                values = self.tree.item(item, "values")
                col_index = columns.index(col)
                
                if col_index < len(values):
                    cell_value = str(values[col_index])
                    cell_width = font.measure(cell_value) + 20
                    max_width = max(max_width, cell_width)
            
            # Set minimum width
            max_width = max(50, max_width)
            col_widths[col] = max_width
            total_content_width += max_width
        
        # If we have extra space, distribute it proportionally
        if total_content_width < available_width:
            extra_space = available_width - total_content_width
            
            # Distribute extra space proportionally based on content width
            for col in visible_columns:
                proportion = col_widths[col] / total_content_width
                extra_for_col = int(extra_space * proportion)
                final_width = col_widths[col] + extra_for_col
                # Cap at reasonable maximum
                final_width = min(final_width, 600)
                self.tree.column(col, width=final_width)
        else:
            # Not enough space, use content widths (will show scrollbar)
            for col in visible_columns:
                # Cap at reasonable maximum to prevent extremely wide columns
                final_width = min(col_widths[col], 400)
                self.tree.column(col, width=final_width)

    def clear_inputs(self):
        for entry in self.entries.values():
            entry.delete(0, tk.END)

    def on_double_click(self, event):
        try:
            item_id = self.tree.selection()[0]
        except IndexError:
            return

        # Identify which column was clicked
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            return
            
        column = self.tree.identify_column(event.x)
        if not column:
            return

        # Get all columns and display columns
        all_columns = self.tree["columns"]
        display_columns = self.tree["displaycolumns"]
        
        # column is like "#1", "#2", etc. - this is 1-indexed based on DISPLAY columns
        col_num = int(column.replace("#", ""))
        
        # Map from display column number to actual column index
        # If displaycolumns is a list of column names, we need to find the index
        if isinstance(display_columns, (list, tuple)) and len(display_columns) > 0:
            # col_num is 1-indexed for display columns
            if col_num < 1 or col_num > len(display_columns):
                return
            
            # Get the display column name
            display_col_name = display_columns[col_num - 1]
            
            # Find this column in all_columns
            try:
                col_index = all_columns.index(display_col_name)
            except ValueError:
                return
        else:
            # No custom display columns, use direct mapping
            if col_num < 1 or col_num > len(all_columns):
                return
            col_index = col_num - 1
        
        col_name_raw = all_columns[col_index]
        
        # Get the values from the selected row
        values = self.tree.item(item_id, "values")
        
        if col_index >= len(values):
            return
            
        text_to_copy = str(values[col_index])
        detail = values[1] if len(values) > 1 else "Unknown"
        
        # Clean column name by removing visibility icons
        col_name = col_name_raw.replace("👁", "").replace("🔒", "").strip()

        self.root.clipboard_clear()
        self.root.clipboard_append(text_to_copy)
        self.activate_copy_led()

    def show_styled_popup(self, detail, col_name):
        top, theme = self.create_styled_toplevel("Copiado en portapapeles", 200, 120)

        container = tk.Frame(top, bg=theme["bg"])
        container.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        tk.Label(container, text="De ", font=("Arial", 10), bg=theme["bg"], fg=theme["fg"]).pack(side=tk.LEFT)
        tk.Label(container, text=detail, font=("Arial", 10, "bold"), bg=theme["bg"], fg=theme["fg"]).pack(side=tk.LEFT)
        tk.Label(container, text=" se copió ", font=("Arial", 10), bg=theme["bg"], fg=theme["fg"]).pack(side=tk.LEFT)
        tk.Label(container, text=col_name, font=("Arial", 10, "bold"), bg=theme["bg"], fg=theme["fg"]).pack(side=tk.LEFT)
        
        btn = tk.Button(top, text="Aceptar", command=top.destroy, width=10, bg=theme["btn_bg"], fg=theme["btn_fg"])
        btn.pack(pady=10)

        top.transient(self.root)
        top.grab_set()
        self.root.wait_window(top)
    
    def activate_copy_led(self):
        """Activate the copy LED indicator for 2.5 seconds."""
        # Cancel any existing timer
        if self.copy_timer:
            self.root.after_cancel(self.copy_timer)
        
        # Activate LED (green)
        self.copy_indicator.config(text="🟢", fg="#4CAF50")
        
        # Schedule reset after 2.5 seconds
        self.copy_timer = self.root.after(2500, self.reset_copy_led)
    
    def reset_copy_led(self):
        """Reset the copy LED indicator to inactive state."""
        self.copy_indicator.config(text="⚫", fg="#757575")
        self.copy_timer = None
    
    def show_row_color_menu(self, event):
        """Show context menu for row color marking."""
        # Identify which row was clicked
        row_id = self.tree.identify_row(event.y)
        if not row_id:
            return
        
        # Select the row
        self.tree.selection_set(row_id)
        
        # Get the record ID
        item = self.tree.item(row_id)
        values = item['values']
        if not values:
            return
        
        record_id = values[0]
        
        # Create context menu
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Cambiar Color de Texto", command=lambda: self.open_row_color_picker(record_id))
        menu.add_separator()
        menu.add_command(label="Quitar Color", command=lambda: self.set_row_color(record_id, None))
        
        # Show menu at cursor position
        menu.post(event.x_root, event.y_root)
    
    def open_row_color_picker(self, record_id):
        """Open color picker dialog for row text color."""
        dialog, theme = self.create_styled_toplevel("Seleccionar Color de Texto", 300, 250)
        
        tk.Label(dialog, text="Selecciona un color:", bg=theme["bg"], fg=theme["fg"]).pack(pady=10)
        
        colors = [
            "#F44336", "#E91E63", "#9C27B0", "#673AB7", "#3F51B5",
            "#2196F3", "#03A9F4", "#00BCD4", "#009688", "#4CAF50",
            "#8BC34A", "#CDDC39", "#FFEB3B", "#FFC107", "#FF9800",
            "#FF5722", "#795548", "#607D8B", "#000000", "#FFFFFF"
        ]
        
        color_frame = tk.Frame(dialog, bg=theme["bg"])
        color_frame.pack(pady=10)
        
        # Helper to set the color to DB
        def set_color(c):
            self.set_row_color(record_id, c)
            dialog.destroy()
        
        for i, color in enumerate(colors):
            row = i // 5
            col = i % 5
            btn = tk.Button(color_frame, bg=color, width=4, command=lambda c=color: set_color(c))
            btn.grid(row=row, column=col, padx=2, pady=2)
    
    def set_row_color(self, record_id, color):
        """Set the color marking for a row."""
        self.db.update_row_color(record_id, color)
        self.load_data()  # Reload to apply color

    def change_master_password(self):
        dialog, theme = self.create_styled_toplevel("Cambiar Contraseña Maestra", 300, 300)
        
        tk.Label(dialog, text="Contraseña Actual:", bg=theme["bg"], fg=theme["fg"]).pack(pady=5)
        curr_pass = tk.Entry(dialog, show="*", bg=theme["entry_bg"], fg=theme["entry_fg"], insertbackground=theme["fg"])
        curr_pass.pack(pady=5)
        
        tk.Label(dialog, text="Nueva Contraseña:", bg=theme["bg"], fg=theme["fg"]).pack(pady=5)
        new_pass = tk.Entry(dialog, show="*", bg=theme["entry_bg"], fg=theme["entry_fg"], insertbackground=theme["fg"])
        new_pass.pack(pady=5)
        
        tk.Label(dialog, text="Repetir Nueva Contraseña:", bg=theme["bg"], fg=theme["fg"]).pack(pady=5)
        confirm_pass = tk.Entry(dialog, show="*", bg=theme["entry_bg"], fg=theme["entry_fg"], insertbackground=theme["fg"])
        confirm_pass.pack(pady=5)
        
        def save():
            current = curr_pass.get()
            new = new_pass.get()
            confirm = confirm_pass.get()
            
            if not current or not new or not confirm:
                messagebox.showwarning("Faltan datos", "Complete todos los campos")
                return
            
            if new != confirm:
                messagebox.showwarning("Error", "Las nuevas contraseñas no coinciden")
                return

            # Verify current
            stored_hash = SecurityManager.get_master_hash(self.db)
            if SecurityManager.verify_password(current, stored_hash):
                SecurityManager.set_master_password(self.db, new)
                messagebox.showinfo("Éxito", "Contraseña maestra actualizada")
                dialog.destroy()
            else:
                messagebox.showerror("Error", "La contraseña actual es incorrecta")
                curr_pass.delete(0, tk.END)

        tk.Button(dialog, text="Guardar", bg="#4CAF50", fg="white", command=save).pack(pady=15)

    def export_to_csv(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            title="Exportar a CSV"
        )
        if not filename:
            return

        try:
            # Get all tabs
            tabs = self.db.get_tabs()
            # Map tab_id to name
            tab_map = {t[0]: t[1] for t in tabs}

            with open(filename, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                # Header
                headers = ["Pestaña", "Detalle / SID", "Tipo acceso", "HOST / IP / DNS", "Puerto", "User", "Pass", "Rol", "Contiene", "Instancia / Tipo", "IP Priv", "IP Pub"]
                writer.writerow(headers)

                # Iterate tabs to get all data
                for tab_id, tab_name, _ in tabs:
                    creds = self.db.get_credentials(tab_id, self.encryption_manager)
                    # creds structure: (id, detalle, tipo_acceso, acceso_host, puerto, usuario, password, rol, contiene, instancia_tipo, ip_priv, ip_pub)
                    for row in creds:
                        # Construct row for CSV: TabName + data fields (skipping ID)
                        csv_row = [tab_name] + list(row[1:])
                        writer.writerow(csv_row)
            
            messagebox.showinfo("Exportar", f"Datos exportados correctamente a {filename}")

        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar: {str(e)}")

    def import_from_csv(self):
        filename = filedialog.askopenfilename(
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            title="Importar desde CSV"
        )
        if not filename:
            return

        confirm = messagebox.askyesno("Confirmar Importación", "Los datos importados se agregarán a las pestañas existentes (creándolas si no existen).\n¿Desea continuar?")
        if not confirm:
            return

        try:
            with open(filename, mode='r', newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                try:
                    header = next(reader)
                except StopIteration:
                    messagebox.showwarning("Importar", "El archivo CSV está vacío.")
                    return

                # Check if first column is "Pestaña"
                has_tab_col = header[0].lower() == "pestaña" or header[0].lower() == "tab"
                
                # If we don't find a tab column, we might assume current tab? 
                # Let's assume standard format matches export: 
                # ["Pestaña", "Detalle / SID", "Tipo acceso", "HOST / IP / DNS", "Puerto", "User", "Pass", "Rol", "Contiene", "Instancia / Tipo", "IP Priv", "IP Pub"]
                # 12 columns total.
                
                count = 0
                
                # Cache tabs to avoid DB hits if possible, but we might create new ones.
                # Just simplify: get tabs map at start, update if we create one.
                current_tabs = {name: tid for tid, name, _ in self.db.get_tabs()}
                
                for row in reader:
                    if not row: continue
                    
                    if has_tab_col:
                        tab_name = row[0]
                        data_start_idx = 1
                    else:
                        # Fallback to current tab if no tab column? 
                        # Or user just provided data. Let's assume current tab if structure allows or if header implies it.
                        # For safety, let's Stick to the Export format.
                        # But for robustness, if column count is 11 (data only), use current tab.
                        if len(row) == 11:
                            # Find current tab name
                            current_tab_name = "Principal"
                            for tid, tname, _ in self.db.get_tabs():
                                if tid == self.current_tab_id:
                                    current_tab_name = tname
                                    break
                            tab_name = current_tab_name
                            data_start_idx = 0
                        else:
                            # Maybe it has 12 cols and first is tab?
                            tab_name = row[0]
                            data_start_idx = 1
                    
                    # Ensure tab exists
                    if tab_name not in current_tabs:
                        # Create tab with a random or default color
                        # Simple hash for color or just random? Let's pick standard Grey
                        self.db.add_tab(tab_name, "#E0E0E0")
                        # Refresh cache
                        current_tabs = {name: tid for tid, name, _ in self.db.get_tabs()}
                    
                    target_tab_id = current_tabs[tab_name]
                    
                    # Extract data
                    file_data = row[data_start_idx:]
                    
                    # Ensure we have 11 fields
                    required_fields = 11
                    if len(file_data) < required_fields:
                        file_data = file_data + ([""] * (required_fields - len(file_data)))
                    elif len(file_data) > required_fields:
                        file_data = file_data[:required_fields]
                        
                    # Add tab_id to data for DB insertion
                    # DB add_credential expects: (detalle, tipo_acceso, acceso_host, puerto, usuario, password, rol, contiene, instancia_tipo, ip_priv, ip_pub, tab_id)
                    # All of these are in file_data in that order.
                    
                    final_data = tuple(file_data) + (target_tab_id,)
                    
                    self.db.add_credential(final_data, self.encryption_manager)
                    count += 1

            messagebox.showinfo("Importar", f"Se importaron {count} registros correctamente.")
            self.load_tabs() # In case new tabs were created
            self.load_data()

        except Exception as e:
             messagebox.showerror("Error", f"Error al importar: {str(e)}")
    
    def move_entry_up(self):
        """Mover la entrada seleccionada hacia arriba en el orden."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Error", "Selecciona una fila para mover")
            return
        
        item = self.tree.item(selected[0])
        record_id = item['values'][0]
        
        # Intentar mover
        success = self.db.move_entry_up(record_id, self.current_tab_id)
        
        if success:
            self.load_data()
            # Re-seleccionar el item movido
            for item_id in self.tree.get_children():
                if self.tree.item(item_id)['values'][0] == record_id:
                    self.tree.selection_set(item_id)
                    self.tree.see(item_id)
                    break
        else:
            messagebox.showinfo("Info", "La entrada ya está en la primera posición")
    
    def move_entry_down(self):
        """Mover la entrada seleccionada hacia abajo en el orden."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Error", "Selecciona una fila para mover")
            return
        
        item = self.tree.item(selected[0])
        record_id = item['values'][0]
        
        # Intentar mover
        success = self.db.move_entry_down(record_id, self.current_tab_id)
        
        if success:
            self.load_data()
            # Re-seleccionar el item movido
            for item_id in self.tree.get_children():
                if self.tree.item(item_id)['values'][0] == record_id:
                    self.tree.selection_set(item_id)
                    self.tree.see(item_id)
                    break
        else:
            messagebox.showinfo("Info", "La entrada ya está en la última posición")

