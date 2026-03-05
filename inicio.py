import tkinter as tk
from tkinter import ttk, Menu
import funcionArchivos
import FunCompilacion

# -------- VENTANA --------
root = tk.Tk()
root.title("Editor de Código")
root.geometry("1000x700")

# Fuente monoespaciada: Vital para que los números y el texto coincidan
FUENTE_EDITOR = ("Consolas", 12)

# =========================
# BARRA SUPERIOR (MENU + BOTONES)
# =========================
barra_superior = tk.Frame(root, bg="#e0e0e0")
barra_superior.pack(side=tk.TOP, fill=tk.X)

archivo_btn = tk.Menubutton(barra_superior, text="Archivo", relief=tk.FLAT)
archivo_menu = Menu(archivo_btn, tearoff=0)
archivo_menu.add_command(label="Nuevo", command=lambda: funcionArchivos.nuevo_archivo(editor_text, root))
archivo_menu.add_command(label="Abrir", command=lambda: abrir_archivo_editor())
archivo_menu.add_command(label="Guardar", command=lambda: funcionArchivos.guardar_archivo(editor_text, root))
archivo_menu.add_separator()
archivo_menu.add_command(label="Salir", command=root.quit)
archivo_btn.config(menu=archivo_menu)
archivo_btn.pack(side=tk.LEFT, padx=5)

# Botones Rápidos
tk.Button(barra_superior, text="Léxico", command=FunCompilacion.analisis_lexico, relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
tk.Button(barra_superior, text="Sintáctico", command=FunCompilacion.analisis_sintactico, relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
tk.Button(barra_superior, text="Semántico", command=FunCompilacion.analisis_semantico, relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
tk.Button(barra_superior, text="Intermedio", command=FunCompilacion.codigo_intermedio, relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
tk.Button(barra_superior, text="▶ Ejecutar", fg="green", command=FunCompilacion.ejecutar_programa, relief=tk.FLAT).pack(side=tk.LEFT, padx=5)

# =========================
# CONTENEDOR PRINCIPAL
# =========================
contenedor = tk.Frame(root)
contenedor.pack(fill=tk.BOTH, expand=True)

frame_superior = tk.Frame(contenedor)
frame_superior.pack(fill=tk.BOTH, expand=True)

editor_frame = tk.Frame(frame_superior)
editor_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

editor_container = tk.Frame(editor_frame)
editor_container.pack(fill=tk.BOTH, expand=True)

# ---- NÚMEROS DE LÍNEA ----
# Aquí eliminamos 'overflow' que causaba el error
line_numbers = tk.Text(
    editor_container,
    width=4,
    padx=5,
    takefocus=0,
    border=0,
    background="#f0f0f0",
    foreground="#888888",
    state="disabled",
    font=FUENTE_EDITOR,
    wrap="none"
)
line_numbers.pack(side=tk.LEFT, fill=tk.Y)

# ---- EDITOR PRINCIPAL ----
editor_text = tk.Text(
    editor_container,
    undo=True,
    wrap="none",
    font=FUENTE_EDITOR,
    padx=10
)
editor_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Tag para el resaltado de la línea actual
editor_text.tag_configure("active_line", background="#e8f2ff")

# ---- SCROLLBAR ----
scrollbar = tk.Scrollbar(editor_container)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# =========================
# FUNCIONES DE APOYO
# =========================

def resaltar_linea_actual():
    editor_text.tag_remove("active_line", "1.0", tk.END)
    try:
        linea = editor_text.index("insert").split(".")[0]
        editor_text.tag_add("active_line", f"{linea}.0", f"{linea}.end+1c")
    except:
        pass

def actualizar_lineas(event=None):
    line_numbers.config(state="normal")
    line_numbers.delete("1.0", tk.END)
    total_lineas = editor_text.index("end-1c").split(".")[0]
    numeros = "\n".join(str(i) for i in range(1, int(total_lineas)+1))
    line_numbers.insert("1.0", numeros)
    # Sincronización de scroll
    line_numbers.yview_moveto(editor_text.yview()[0])
    line_numbers.config(state="disabled")

def actualizar_todo(event=None):
    actualizar_lineas()
    actualizar_barra_estado()
    resaltar_linea_actual()

def sincronizar_scroll(*args):
    editor_text.yview(*args)
    line_numbers.yview_moveto(editor_text.yview()[0])

editor_text.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=sincronizar_scroll)

# Eventos para que todo reaccione al escribir o mover el cursor
editor_text.bind("<KeyRelease>", actualizar_todo)
editor_text.bind("<Button-1>", actualizar_todo)
editor_text.bind("<MouseWheel>", lambda e: root.after(1, actualizar_lineas))

# =========================
# PANELES DE RESULTADOS Y CONSOLA
# =========================
resultados_frame = tk.Frame(frame_superior, width=300)
resultados_frame.pack(side=tk.RIGHT, fill=tk.BOTH)

tabs_resultados = ttk.Notebook(resultados_frame)
tabs_resultados.pack(fill=tk.BOTH, expand=True)
for t in ["Léxico", "Sintáctico", "Semántico", "Intermedio", "Tabla Símbolos"]:
    tabs_resultados.add(tk.Frame(tabs_resultados), text=t)

frame_inferior = tk.Frame(contenedor, height=180)
frame_inferior.pack(fill=tk.X, side=tk.BOTTOM)
frame_inferior.pack_propagate(False)

tabs_consola = ttk.Notebook(frame_inferior)
tabs_consola.pack(fill=tk.BOTH, expand=True)
for t in ["Errores Léxicos", "Errores Sintácticos", "Errores Semánticos", "Resultados"]:
    tabs_consola.add(tk.Frame(tabs_consola), text=t)

barra_estado = tk.Label(root, text="Líneas: 1", anchor="w")
barra_estado.pack(side=tk.BOTTOM, fill=tk.X)

def abrir_archivo_editor():
    funcionArchivos.abrir_archivo(editor_text, root)
    actualizar_todo()

def actualizar_barra_estado():
    total_lineas = editor_text.index("end-1c").split(".")[0]
    barra_estado.config(text=f"Líneas: {total_lineas}")

# Inicialización
actualizar_todo()
root.mainloop()