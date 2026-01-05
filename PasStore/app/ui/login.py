import tkinter as tk
from tkinter import messagebox
from app.utils.security import SecurityManager
from app.config import THEMES
from app.data.database import DatabaseManager
from app.ui.main_window import MainApp

class LoginWindow:
    def __init__(self, root, app_version=None):
        self.root = root
        self.app_version = app_version
        
        # Load theme
        self.db = DatabaseManager()
        saved_theme = self.db.get_setting("theme", "Light")
        self.theme = THEMES[saved_theme]
        
        # Check if master password exists
        self.is_setup_mode = not SecurityManager.has_master_password(self.db)
        
        title = "Configurar Contraseña Maestra" if self.is_setup_mode else "Login Seguro"
        if self.app_version:
            title += f" v{self.app_version}"
        self.root.title(title)
        
        # Center and configure
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        width, height = 300, 250 if self.is_setup_mode else 160
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        self.root.configure(bg=self.theme["bg"])
        
        msg = "Cree una contraseña maestra:" if self.is_setup_mode else "Ingrese Contraseña Maestra:"
        label = tk.Label(root, text=msg, bg=self.theme["bg"], fg=self.theme["fg"], font=("Arial", 10))
        label.pack(pady=10)
        
        self.pass_entry = tk.Entry(root, show="*", bg=self.theme["entry_bg"], fg=self.theme["entry_fg"], insertbackground=self.theme["fg"])
        self.pass_entry.pack(pady=5)
        self.pass_entry.bind('<Return>', self.handle_action)
        self.pass_entry.focus()
        
        if self.is_setup_mode:
             tk.Label(root, text="Repetir Contraseña:", bg=self.theme["bg"], fg=self.theme["fg"], font=("Arial", 10)).pack(pady=5)
             self.confirm_entry = tk.Entry(root, show="*", bg=self.theme["entry_bg"], fg=self.theme["entry_fg"], insertbackground=self.theme["fg"])
             self.confirm_entry.pack(pady=5)
             self.confirm_entry.bind('<Return>', self.handle_action)

        btn_text = "Guardar e Ingresar" if self.is_setup_mode else "Ingresar"
        btn = tk.Button(root, text=btn_text, command=self.handle_action, bg=self.theme["btn_bg"], fg=self.theme["btn_fg"], width=20)
        btn.pack(pady=15)

    def handle_action(self, event=None):
        password = self.pass_entry.get()
        
        if not password:
            messagebox.showwarning("Atención", "La contraseña no puede estar vacía")
            return
            
        if self.is_setup_mode:
            confirm = self.confirm_entry.get()
            if password != confirm:
                messagebox.showwarning("Error", "Las contraseñas no coinciden")
                return

            # Set new password
            SecurityManager.set_master_password(self.db, password)
            messagebox.showinfo("Éxito", "Contraseña maestra configurada correctamente.")
            self.launch_app()
        else:
            # Check existing password
            master_hash = SecurityManager.get_master_hash(self.db)
            if SecurityManager.verify_password(password, master_hash):
                self.launch_app()
            else:
                messagebox.showerror("Error", "Contraseña incorrecta")
                self.pass_entry.delete(0, tk.END)

    def launch_app(self):
        # Get the password that was just verified
        password = self.pass_entry.get()
        
        # Create encryption manager
        encryption_manager = SecurityManager.create_encryption_manager(password, self.db)
        
        self.root.destroy()
        app = tk.Tk()
        MainApp(app, encryption_manager)
        app.mainloop()
