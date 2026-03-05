# Antes de 'import tkinter as tk'
import ctypes
try:
    # Esto activa la conciencia de DPI para obtener nitidez en Windows
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception as e:
    # En sistemas que no son Windows (como macOS o Linux), esto fallará, 
    # pero no pasa nada, el try-except evita que el programa se detenga.
    pass

import tkinter as tk
from tkinter import ttk, Menu
import funcionArchivos
import FunCompilacion
from PIL import Image, ImageTk
import os

# 1. CONFIGURACIÓN DE VENTANA
root = tk.Tk()
root.title("Editor de Código")
root.geometry("1000x700")

# 2. RUTA DE ICONOS
directorio_actual = os.path.dirname(__file__)
ruta_iconos = os.path.join(directorio_actual, "iconos")

# 3. FUNCIÓN DE CARGA DE ICONOS
def cargar_icono(nombre, size=(20, 20)):
    ruta = os.path.join(ruta_iconos, nombre)
    try:
        imagen = Image.open(ruta)
        imagen = imagen.resize(size, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(imagen)
    except Exception as e:
        print(f"Error cargando {nombre}: {e}")
        return None
    
def nuevo_archivo():
    global ruta_actual
    text_area.delete(1.0, tk.END)
    ruta_actual = None
    root.title("Nuevo Archivo - Editor")

def abrir_archivo():
    global ruta_actual
    archivo = filedialog.askopenfilename(
        filetypes=[("Archivos de texto", "*.txt"), ("Todos", "*.*")]
    )
    if archivo:
        ruta_actual = archivo
        text_area.delete(1.0, tk.END)
        with open(archivo, "r") as f:
            text_area.insert(tk.INSERT, f.read())
        root.title(archivo)

def guardar_archivo():
    global ruta_actual
    if ruta_actual:
        with open(ruta_actual, "w") as f:
            f.write(text_area.get(1.0, tk.END))
    else:
        guardar_como()

def guardar_como():
    global ruta_actual
    archivo = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
    )
    if archivo:
        ruta_actual = archivo
        with open(ruta_actual, "w") as f:
            f.write(text_area.get(1.0, tk.END))
        root.title(ruta_actual)

def cerrar_archivo():
    nuevo_archivo()

# 4. CREACIÓN DE VARIABLES (ICONOS)
img_nuevo = cargar_icono("nuevo.png")
img_abrir = cargar_icono("abrir.png")
img_guardar = cargar_icono("guardar.png")
img_lexico = cargar_icono("lexico.png")
img_sintatico = cargar_icono("sintatico.png") 
img_semantico = cargar_icono("semantico.png")
img_play = cargar_icono("play.png")
img_errores = cargar_icono("errores.png")
img_resultado = cargar_icono("resultado.png")
img_salir = cargar_icono("salir.png")
img_archivos = cargar_icono("archivos.png")
img_guardar_como = cargar_icono("guardar.png") 
img_cerrar = cargar_icono("salir.png")

# 5. DEFINICIÓN DE COLORES (Paleta Nordic Frost)
COLOR_FONDO =  "#2E3440"     # Color para base
COLOR_EDITOR = "#3B4252"     # Color para el editor
COLOR_TEXTO =  "#ECEFF4"     # Color para el texto
COLOR_BARRA =  "#88C0D0"     # Color para barras

root.configure(bg=COLOR_FONDO)

# 6. ESTILOS DE COMPONENTES (ttk)
FUENTE_SISTEMA = ('Segoe UI', 9)        # Para menús, botones y pestañas
FUENTE_EDITOR = ('Consolas', 10)         # Para el área de código (fuente monoespaciada)

estilo = ttk.Style()
estilo.theme_use('default')
estilo.configure("TNotebook", background=COLOR_FONDO, borderwidth=0)
estilo.configure("TNotebook.Tab", background=COLOR_BARRA, foreground=COLOR_FONDO, padding=[12, 4], font=FUENTE_SISTEMA)
estilo.map("TNotebook.Tab", background=[("selected", COLOR_EDITOR)], foreground=[("selected", COLOR_TEXTO)])

# =========================
# BARRA SUPERIOR
# =========================
barra_superior = tk.Frame(root, bg=COLOR_BARRA, height=40)
barra_superior.pack(side=tk.TOP, fill=tk.X)
barra_superior.pack_propagate(False)

archivo_btn = tk.Menubutton(barra_superior, text="Archivo", image=img_archivos, compound=tk.LEFT,
                            bg=COLOR_BARRA, fg=COLOR_FONDO, relief=tk.FLAT, font=FUENTE_SISTEMA, padx=10)
archivo_menu = Menu(archivo_btn, tearoff=0, bg=COLOR_FONDO, fg=COLOR_TEXTO)

# Nota: editor_text se define abajo, pero lambda permite referenciarlo
archivo_menu.add_command(image=img_nuevo, compound=tk.LEFT, label=" Nuevo",
                          command=lambda: funcionArchivos.nuevo_archivo(editor_text, root))
archivo_menu.add_command(image=img_abrir, compound=tk.LEFT, label=" Abrir",
                          command=lambda: funcionArchivos.abrir_archivo(editor_text, root))
archivo_menu.add_command(image=img_guardar, compound=tk.LEFT, label=" Guardar",
                          command=lambda: funcionArchivos.guardar_archivo(editor_text, root))
archivo_menu.add_command(image=img_guardar_como, compound=tk.LEFT, label=" Guardar como",
                        command=lambda: funcionArchivos.guardar_como(editor_text, root))
archivo_menu.add_command(image=img_cerrar, compound=tk.LEFT, label=" Cerrar", 
                        command=lambda: funcionArchivos.cerrar_archivo(editor_text, root))

archivo_menu.add_separator()
archivo_menu.add_command(label=" Salir", command=root.quit, image=img_salir, compound=tk.LEFT)



archivo_btn.config(menu=archivo_menu)
archivo_btn.pack(side=tk.LEFT, padx=5)

def crear_boton_barra(texto, icono, comando):
    tk.Button(barra_superior, text=texto, image=icono, compound=tk.LEFT,
              bg=COLOR_BARRA, fg=COLOR_FONDO, activebackground=COLOR_EDITOR,
              command=comando, relief=tk.FLAT, font=FUENTE_SISTEMA,padx=10).pack(side=tk.LEFT)
    
# ----- MENUBUTTON COMPILAR -----
compilar_btn = tk.Menubutton(barra_superior, text="Compilar", 
                            relief=tk.FLAT, 
                            bg=COLOR_BARRA, fg=COLOR_FONDO, # Colores del botón
                            activebackground=COLOR_EDITOR, activeforeground=COLOR_TEXTO,
                            font=('Segoe UI', 9, 'bold'),
                            padx=10)

compilar_menu = Menu(compilar_btn, tearoff=0, 
                     bg=COLOR_FONDO, fg=COLOR_TEXTO, # Colores del menú desplegable
                     activebackground=COLOR_BARRA, activeforeground=COLOR_FONDO)

# Opción Análisis Léxico con icono
compilar_menu.add_command(label="  Análisis Léxico", 
                          image=img_lexico, 
                          compound=tk.LEFT,
                          command=FunCompilacion.analisis_lexico)

# Opción Análisis Sintáctico con icono
compilar_menu.add_command(label="  Análisis Sintáctico", 
                          image=img_sintatico, 
                          compound=tk.LEFT,
                          command=FunCompilacion.analisis_sintactico)

compilar_btn.config(menu=compilar_menu)

compilar_btn.pack(side=tk.LEFT, fill=tk.Y) # fill=tk.Y para que ocupe todo el alto de la barra

crear_boton_barra("Léxico", img_lexico, FunCompilacion.analisis_lexico)
crear_boton_barra("Sintáctico", img_sintatico, FunCompilacion.analisis_sintactico)
crear_boton_barra("Semántico", img_semantico, FunCompilacion.analisis_semantico)
crear_boton_barra("Intermedio", None, FunCompilacion.codigo_intermedio)

tk.Button(barra_superior, image=img_play, compound=tk.LEFT, text=" Ejecutar", 
          bg=COLOR_BARRA, fg="#FFFFFF", font=('Segoe UI', 10, 'bold'),
          command=FunCompilacion.ejecutar_programa, relief=tk.FLAT, padx=15).pack(side=tk.LEFT)


# ==========================================
# 8. BARRA DE ACCESO RÁPIDO (TOOLBAR)
# ==========================================
# Creamos un nuevo frame para los iconos de acceso rápido
barra_herramientas = tk.Frame(root, bg=COLOR_EDITOR, height=35) # Un tono más claro que el fondo
barra_herramientas.pack(side=tk.TOP, fill=tk.X)
barra_herramientas.pack_propagate(False)

# Función para crear los botoncitos rápidos (solo icono, sin texto)
def crear_acceso_rapido(icono, comando, pad_x=2):
    btn = tk.Button(barra_herramientas, image=icono, 
                    bg=COLOR_EDITOR, activebackground=COLOR_BARRA,
                    relief=tk.FLAT, command=comando,
                    padx=5, pady=2)
    btn.pack(side=tk.LEFT, padx=pad_x, pady=2)
    return btn

# Función para la línea divisoria vertical (el separador de tu imagen)
def crear_separador():
    tk.Frame(barra_herramientas, width=1, bg=COLOR_BARRA).pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=5)

# --- GRUPO 1: ARCHIVOS ---
crear_acceso_rapido(img_nuevo, lambda: funcionArchivos.nuevo_archivo(editor_text, root))
crear_acceso_rapido(img_abrir, lambda: funcionArchivos.abrir_archivo(editor_text, root))
crear_acceso_rapido(img_guardar, lambda: funcionArchivos.guardar_archivo(editor_text, root))

crear_separador() # Línea divisoria como en tu imagen

# --- GRUPO 2: COMPILACIÓN ---
crear_acceso_rapido(img_lexico, FunCompilacion.analisis_lexico)
crear_acceso_rapido(img_sintatico, FunCompilacion.analisis_sintactico)
crear_acceso_rapido(img_semantico, FunCompilacion.analisis_semantico)

crear_separador() # Otra línea divisoria

# --- GRUPO 3: EJECUCIÓN (Resaltado) ---
btn_run_rapido = tk.Button(barra_herramientas, image=img_play, 
                           bg="#BF616A", # Color rojo Nord para que resalte
                           activebackground=COLOR_BARRA,
                           relief=tk.FLAT, command=FunCompilacion.ejecutar_programa)
btn_run_rapido.pack(side=tk.LEFT, padx=5, pady=2)

# ==========================================
# 7. ESTRUCTURA VISUAL (DIVISIONES MÓVILES)
# ==========================================

# Tu 'contenedor' divide verticalmente (Trabajo arriba / Consola abajo)
contenedor = tk.PanedWindow(root, orient=tk.VERTICAL, bg=COLOR_FONDO, sashwidth=6, sashrelief=tk.FLAT)
contenedor.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

# Tu 'frame_superior' divide horizontalmente (Editor izquierda / Resultados derecha)
frame_superior = tk.PanedWindow(contenedor, orient=tk.HORIZONTAL, bg=COLOR_FONDO, sashwidth=6, sashrelief=tk.FLAT)
contenedor.add(frame_superior, stretch="always")

# --- EDITOR (Izquierda) ---
editor_frame = tk.Frame(frame_superior, bg=COLOR_FONDO)
frame_superior.add(editor_frame, width=650)

editor_text = tk.Text(editor_frame, undo=True, highlightthickness=1, highlightbackground=COLOR_BARRA, 
                     borderwidth=0, bg=COLOR_EDITOR, fg=COLOR_TEXTO, insertbackground="white",
                     font=FUENTE_EDITOR, padx=5, pady=5)
editor_text.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

# --- RESULTADOS (Derecha) ---
resultados_frame = tk.Frame(frame_superior, bg=COLOR_FONDO)
frame_superior.add(resultados_frame, width=350)

tabs_resultados = ttk.Notebook(resultados_frame)
tabs_resultados.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

for nombre in ["Léxico", "Sintáctico", "Semántico", "Intermedio", "Tabla Símbolos"]:
    f = tk.Frame(tabs_resultados, bg=COLOR_EDITOR)
    tabs_resultados.add(f, text=nombre)

# --- CONSOLA (Abajo) ---
frame_inferior = tk.Frame(contenedor, bg=COLOR_FONDO)
contenedor.add(frame_inferior, stretch="never", height=180)

tabs_consola = ttk.Notebook(frame_inferior)
tabs_consola.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

consola_data = [
    ("Errores Léxicos", img_errores),
    ("Errores Sintácticos", img_errores),
    ("Errores Semánticos", img_errores),
    ("Resultados", img_resultado)
]

for texto, icono in consola_data:
    f = tk.Frame(tabs_consola, bg=COLOR_EDITOR)
    tabs_consola.add(f, text=texto, image=icono, compound=tk.LEFT)

root.mainloop()