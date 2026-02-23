import tkinter as tk
from tkinter import ttk, Menu
import funcionArchivos
import FunCompilacion

# -------- VENTANA --------
root = tk.Tk()
root.title("Editor de Código")
root.geometry("900x600")

# =========================
# BARRA SUPERIOR (MENU + BOTONES)
# =========================
barra_superior = tk.Frame(root, bg="#e0e0e0")
barra_superior.pack(side=tk.TOP, fill=tk.X)

# ----- MENUBUTTON ARCHIVO -----
archivo_btn = tk.Menubutton(barra_superior, text="Archivo", relief=tk.FLAT)
archivo_menu = Menu(archivo_btn, tearoff=0)

archivo_menu.add_command(
    label="Nuevo",
    command=lambda: funcionArchivos.nuevo_archivo(None, root)
)
archivo_menu.add_command(
    label="Abrir",
    command=lambda: funcionArchivos.abrir_archivo(None, root)
)
archivo_menu.add_command(
    label="Guardar",
    command=lambda: funcionArchivos.guardar_archivo(None, root)
)
archivo_menu.add_separator()
archivo_menu.add_command(label="Salir", command=root.quit)

archivo_btn.config(menu=archivo_menu)
archivo_btn.pack(side=tk.LEFT, padx=5)

# ----- MENUBUTTON COMPILAR -----
compilar_btn = tk.Menubutton(barra_superior, text="Compilar", relief=tk.FLAT)
compilar_menu = Menu(compilar_btn, tearoff=0)

compilar_menu.add_command(label="Análisis Léxico",
                          command=FunCompilacion.analisis_lexico)

compilar_menu.add_command(label="Análisis Sintáctico",
                          command=FunCompilacion.analisis_sintactico)

compilar_btn.config(menu=compilar_menu)
compilar_btn.pack(side=tk.LEFT, padx=5)

# =========================
# BOTONES NORMALES (LO QUE QUERÍAS)
# =========================
tk.Button(barra_superior, text="Léxico",
          command=FunCompilacion.analisis_lexico,
          relief=tk.FLAT).pack(side=tk.LEFT, padx=5)

tk.Button(barra_superior, text="Sintáctico",
          command=FunCompilacion.analisis_sintactico,
          relief=tk.FLAT).pack(side=tk.LEFT, padx=5)

tk.Button(barra_superior, text="Semántico",
          command=FunCompilacion.analisis_semantico,
          relief=tk.FLAT).pack(side=tk.LEFT, padx=5)

tk.Button(barra_superior, text="Intermedio",
          command=FunCompilacion.codigo_intermedio,
          relief=tk.FLAT).pack(side=tk.LEFT, padx=5)

tk.Button(barra_superior, text="▶ Ejecutar",
          fg="green",
          command=FunCompilacion.ejecutar_programa,
          relief=tk.FLAT).pack(side=tk.LEFT, padx=5)

# =========================
# CONTENEDOR PRINCIPAL
# =========================
contenedor = tk.Frame(root)
contenedor.pack(fill=tk.BOTH, expand=True)

# ----- PARTE SUPERIOR -----
frame_superior = tk.Frame(contenedor)
frame_superior.pack(fill=tk.BOTH, expand=True)

editor_frame = tk.Frame(frame_superior)
editor_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

editor_text = tk.Text(editor_frame, undo=True)
editor_text.pack(fill=tk.BOTH, expand=True)

# RESULTADOS
resultados_frame = tk.Frame(frame_superior, width=300)
resultados_frame.pack(side=tk.RIGHT, fill=tk.BOTH)

tabs_resultados = ttk.Notebook(resultados_frame)
tabs_resultados.pack(fill=tk.BOTH, expand=True)

tabs_resultados.add(tk.Frame(tabs_resultados), text="Léxico")
tabs_resultados.add(tk.Frame(tabs_resultados), text="Sintáctico")
tabs_resultados.add(tk.Frame(tabs_resultados), text="Semántico")
tabs_resultados.add(tk.Frame(tabs_resultados), text="Intermedio")
tabs_resultados.add(tk.Frame(tabs_resultados), text="Tabla Símbolos")

# ----- CONSOLA -----
frame_inferior = tk.Frame(contenedor, height=180)
frame_inferior.pack(fill=tk.X, side=tk.BOTTOM)
frame_inferior.pack_propagate(False)

tabs_consola = ttk.Notebook(frame_inferior)
tabs_consola.pack(fill=tk.BOTH, expand=True)

tabs_consola.add(tk.Frame(tabs_consola), text="Errores Léxicos")
tabs_consola.add(tk.Frame(tabs_consola), text="Errores Sintácticos")
tabs_consola.add(tk.Frame(tabs_consola), text="Errores Semánticos")
tabs_consola.add(tk.Frame(tabs_consola), text="Resultados")

root.mainloop()