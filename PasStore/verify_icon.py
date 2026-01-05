import win32api
import win32con
import win32gui
import sys

def check_exe_icon(exe_path):
    """Verifica si un ejecutable tiene un icono integrado"""
    try:
        # Intentar extraer el icono del ejecutable
        large, small = win32gui.ExtractIconEx(exe_path, 0)
        
        if large or small:
            print(f"✅ El ejecutable '{exe_path}' TIENE un icono integrado")
            print(f"   - Iconos grandes encontrados: {len(large) if large else 0}")
            print(f"   - Iconos pequeños encontrados: {len(small) if small else 0}")
            
            # Limpiar handles
            if large:
                for icon in large:
                    win32gui.DestroyIcon(icon)
            if small:
                for icon in small:
                    win32gui.DestroyIcon(icon)
            return True
        else:
            print(f"❌ El ejecutable '{exe_path}' NO tiene un icono integrado")
            return False
    except Exception as e:
        print(f"⚠️ Error al verificar el icono: {e}")
        print("   Nota: Esto puede significar que no hay icono o que pywin32 no está instalado")
        return False

if __name__ == "__main__":
    exe_path = r".\dist\PasStore.exe"
    check_exe_icon(exe_path)
