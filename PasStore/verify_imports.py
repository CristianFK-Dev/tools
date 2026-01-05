try:
    import app.config
    # Test package imports derived from __init__.py files
    from app.utils import SecurityManager
    from app.data import DatabaseManager
    from app.ui import LoginWindow, MainApp
    import main
    print("All modules imported successfully using package structure.")
except Exception as e:
    print(f"Import Error: {e}")
