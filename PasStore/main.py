import tkinter as tk
from app.data.database import DatabaseManager
from app.ui.login import LoginWindow

__version__ = "1.2.3"

if __name__ == "__main__":
    # Ensure DB is initialized
    db = DatabaseManager()
    db.init_db()
    
    # Start UI
    root = tk.Tk()
    app = LoginWindow(root, app_version=__version__)
    root.mainloop()


# pyinstaller --noconsole --onefile --name="PasStore" --icon="icono.ico" --clean main.py 
# pyinstaller PasStore.spec

# Versiones
# 1.0 - Version base de prueba
# 1.1 - Primer versión final con icono
# 1.1 - Marcar producción / test con colores
# 1.2 - Mejora varias
# 1.2.2 - Botones de movimiento de pestañas
# 1.2.3 - Botones de movimiento de filas + achicar formulario

# Mejoras
# Acomodar los textos bien en la parte de tipo de dato de entradas 