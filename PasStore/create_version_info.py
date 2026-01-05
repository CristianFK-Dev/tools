import re

def create_version_file():
    # 1. Leer la versión de main.py
    version_str = "1.0.0"
    try:
        with open("main.py", "r", encoding="utf-8") as f:
            content = f.read()
            match = re.search(r'__version__\s*=\s*"([^"]+)"', content)
            if match:
                version_str = match.group(1)
    except Exception as e:
        print(f"Error leyendo main.py: {e}")

    print(f"Generando version_info.txt para la versión: {version_str}")

    # 2. Convertir a formato tupla (1, 2, 3, 0)
    parts = version_str.split('.')
    while len(parts) < 4:
        parts.append('0')
    
    v = [int(p) for p in parts[:4]]
    version_tuple = f"({v[0]}, {v[1]}, {v[2]}, {v[3]})"
    version_str_full = f"{v[0]}.{v[1]}.{v[2]}.{v[3]}"

    # 3. Plantilla de PyInstaller Version Info
    # Esta estructura es requerida por Windows
    file_content = f"""# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={version_tuple},
    prodvers={version_tuple},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Antigravity'),
        StringStruct(u'FileDescription', u'PasStore Gestor de Contraseñas'),
        StringStruct(u'FileVersion', u'{version_str_full}'),
        StringStruct(u'InternalName', u'PasStore'),
        StringStruct(u'LegalCopyright', u'Copyright © CristianFK'),
        StringStruct(u'OriginalFilename', u'PasStore.exe'),
        StringStruct(u'ProductName', u'PasStore'),
        StringStruct(u'ProductVersion', u'{version_str_full}')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""

    with open("version_info.txt", "w", encoding="utf-8") as f:
        f.write(file_content)
    
    print("Archivo 'version_info.txt' creado exitosamente.")

if __name__ == "__main__":
    create_version_file()
