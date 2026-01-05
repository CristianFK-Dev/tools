from PIL import Image

# Abrir la imagen PNG
img = Image.open('icono.png')

# Convertir a RGBA si no lo está
if img.mode != 'RGBA':
    img = img.convert('RGBA')

# Crear múltiples tamaños para el ICO (Windows usa diferentes tamaños)
icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]

# Guardar como ICO con múltiples resoluciones
img.save('icono.ico', format='ICO', sizes=icon_sizes)

print("✅ Icono convertido exitosamente a icono.ico con múltiples resoluciones")
