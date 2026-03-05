import tkinter as tk
from tkinter import ttk, Menu, messagebox
import funcionArchivos
import FunCompilacion
import os

# -------- VENTANA PRINCIPAL --------
root = tk.Tk()
root.title("Editor de Código Pro")
root.geometry("1100x750")

FUENTE_EDITOR = ("Consolas", 12)

# Diccionario para rastrear si cada pestaña ha sido modificada
# { ID_Pestaña: True/False }
estados_modificados = {}

# ==========================================
# GESTIÓN DE PESTAÑAS Y ARCHIVOS
# ==========================================

def obtener_editor_actual():
    try:
        pestana_id = notebook_editor.select()
        if not pestana_id: return None
        pestana_actual = notebook_editor.nametowidget(pestana_id)
        return pestana_actual.editor_text
    except:
        return None

def marcar_como_modificado(event, editor, frame):
    """Añade un asterisco al nombre de la pestaña si se edita."""
    if event.keysym in ('Control_L', 'Control_R', 'Shift_L', 'Shift_R', 'Alt_L', 'Alt_R'):
        return
    
    id_pestana = notebook_editor.select()
    if id_pestana not in estados_modificados or not estados_modificados[id_pestana]:
        estados_modificados[id_pestana] = True
        nombre_actual = notebook_editor.tab(id_pestana, "text")
        if not nombre_actual.endswith("*"):
            notebook_editor.tab(id_pestana, text=nombre_actual + " *")

def cerrar_pestana_actual(index=None):
    """Cierra la pestaña validando si hay cambios sin guardar."""
    if index is None:
        try:
            index = notebook_editor.index("current")
        except:
            return

    id_pestana = notebook_editor.tabs()[index]
    
    if estados_modificados.get(id_pestana, False):
        res = messagebox.askyesnocancel("Guardar cambios", "¿Deseas guardar los cambios antes de cerrar?")
        if res is True: # Guardar
            funcionArchivos.guardar_archivo(obtener_editor_actual(), root)
        elif res is None: # Cancelar
            return

    notebook_editor.forget(id_pestana)
    if id_pestana in estados_modificados:
        del estados_modificados[id_pestana]

def agregar_pestana(nombre="Nuevo", contenido="", ruta=None):
    frame_pestana = tk.Frame(notebook_editor)
    
    editor_container = tk.Frame(frame_pestana)
    editor_container.pack(fill=tk.BOTH, expand=True)

    line_numbers = tk.Text(editor_container, width=4, padx=5, takefocus=0, 
                           border=0, background="#f0f0f0", state="disabled", font=FUENTE_EDITOR)
    line_numbers.pack(side=tk.LEFT, fill=tk.Y)

    editor_text = tk.Text(editor_container, undo=True, wrap="none", font=FUENTE_EDITOR)
    editor_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    editor_text.insert("1.0", contenido)
    
    frame_pestana.editor_text = editor_text
    frame_pestana.line_numbers = line_numbers
    frame_pestana.ruta_archivo = ruta

    editor_text.tag_configure("active_line", background="#e8f2ff")

    scrollbar = tk.Scrollbar(editor_container, command=lambda *args: sincronizar_scroll(editor_text, line_numbers, *args))
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    editor_text.config(yscrollcommand=scrollbar.set)

    # Eventos
    editor_text.bind("<KeyRelease>", lambda e: [actualizar_todo_local(editor_text, line_numbers), marcar_como_modificado(e, editor_text, frame_pestana)])
    editor_text.bind("<Button-1>", lambda e: actualizar_todo_local(editor_text, line_numbers))
    
    notebook_editor.add(frame_pestana, text=nombre)
    notebook_editor.select(frame_pestana)
    
    # Inicializar estado como no modificado
    estados_modificados[notebook_editor.select()] = False
    actualizar_todo_local(editor_text, line_numbers)

def abrir_archivo_editor():
    # Usamos una pestaña temporal para cargar
    temp_editor = tk.Text() 
    ruta = funcionArchivos.abrir_archivo(temp_editor, root)
    if ruta:
        nombre_archivo = os.path.basename(ruta)
        contenido = temp_editor.get("1.0", tk.END).strip()
        agregar_pestana(nombre_archivo, contenido, ruta)

# =========================
# BARRA SUPERIOR
# =========================
barra_superior = tk.Frame(root, bg="#e0e0e0")
barra_superior.pack(side=tk.TOP, fill=tk.X)

# --- MENÚ ARCHIVO ---
archivo_btn = tk.Menubutton(barra_superior, text="Archivo", relief=tk.FLAT)
archivo_menu = Menu(archivo_btn, tearoff=0)
archivo_menu.add_command(label="Nuevo", command=lambda: agregar_pestana())
archivo_menu.add_command(label="Abrir", command=abrir_archivo_editor)
archivo_menu.add_command(label="Guardar", command=lambda: [funcionArchivos.guardar_archivo(obtener_editor_actual(), root), resetear_modificado()])
archivo_menu.add_separator()
archivo_menu.add_command(label="Cerrar Pestaña (X)", command=cerrar_pestana_actual)
archivo_menu.add_command(label="Salir", command=root.quit)
archivo_btn.config(menu=archivo_menu)
archivo_btn.pack(side=tk.LEFT, padx=5)

def resetear_modificado():
    """Quita el asterisco al guardar."""
    id_p = notebook_editor.select()
    estados_modificados[id_p] = False
    nombre = notebook_editor.tab(id_p, "text")
    if nombre.endswith("*"):
        notebook_editor.tab(id_p, text=nombre.replace(" *", ""))

# (Menú Compilar y botones rápidos se mantienen igual...)
compilar_btn = tk.Menubutton(barra_superior, text="Compilar", relief=tk.FLAT)
compilar_menu = Menu(compilar_btn, tearoff=0)
compilar_menu.add_command(label="Análisis Léxico", command=FunCompilacion.analisis_lexico)
compilar_menu.add_command(label="Análisis Sintáctico", command=FunCompilacion.analisis_sintactico)
compilar_btn.config(menu=compilar_menu)
compilar_btn.pack(side=tk.LEFT, padx=5)

# ==========================================
# ÁREA DE TRABAJO (PANED WINDOWS)
# ==========================================
panel_vertical = tk.PanedWindow(root, orient=tk.VERTICAL, sashrelief=tk.RAISED, sashwidth=4)
panel_vertical.pack(fill=tk.BOTH, expand=True)

panel_horizontal = tk.PanedWindow(panel_vertical, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, sashwidth=4)
panel_vertical.add(panel_horizontal, height=450)

notebook_editor = ttk.Notebook(panel_horizontal)
panel_horizontal.add(notebook_editor, width=750)

# Cierre con clic de la rueda del mouse (un clásico de los IDEs)
notebook_editor.bind("<Button-2>", lambda e: cerrar_pestana_actual(notebook_editor.index(f"@{e.x},{e.y}")))

# ... (El resto de paneles de Resultados y Consola se mantienen igual que el código anterior)
# DERECHA
resultados_frame = tk.Frame(panel_horizontal)
panel_horizontal.add(resultados_frame, width=250)
tabs_resultados = ttk.Notebook(resultados_frame)
tabs_resultados.pack(fill=tk.BOTH, expand=True)
for t in ["Léxico", "Sintáctico", "Semántico", "Intermedio"]:
    tabs_resultados.add(tk.Frame(tabs_resultados), text=t)

# ABAJO
frame_inferior = tk.Frame(panel_vertical)
panel_vertical.add(frame_inferior, height=200)
tabs_consola = ttk.Notebook(frame_inferior)
tabs_consola.pack(fill=tk.BOTH, expand=True)
for t in ["Errores", "Salida"]:
    tabs_consola.add(tk.Frame(tabs_consola), text=t)

barra_estado = tk.Label(root, text="Líneas: 0", anchor="w", bd=1, relief=tk.SUNKEN)
barra_estado.pack(side=tk.BOTTOM, fill=tk.X)

# Sincronización (Funciones iguales)
def actualizar_lineas_local(txt_widget, line_widget):
    line_widget.config(state="normal")
    line_widget.delete("1.0", tk.END)
    total_lineas = txt_widget.index("end-1c").split(".")[0]
    numeros = "\n".join(str(i) for i in range(1, int(total_lineas)+1))
    line_widget.insert("1.0", numeros)
    line_widget.yview_moveto(txt_widget.yview()[0])
    line_widget.config(state="disabled")

def resaltar_linea_actual(txt_widget):
    txt_widget.tag_remove("active_line", "1.0", tk.END)
    linea = txt_widget.index("insert").split(".")[0]
    txt_widget.tag_add("active_line", f"{linea}.0", f"{linea}.end+1c")

def actualizar_todo_local(txt_widget, line_widget):
    actualizar_lineas_local(txt_widget, line_widget)
    resaltar_linea_actual(txt_widget)
    total = txt_widget.index("end-1c").split(".")[0]
    barra_estado.config(text=f"Líneas: {total}")

def sincronizar_scroll(txt_widget, line_widget, *args):
    txt_widget.yview(*args)
    line_widget.yview_moveto(txt_widget.yview()[0])

agregar_pestana("Archivo 1")
root.mainloop()