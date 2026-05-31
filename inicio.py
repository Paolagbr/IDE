import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

import tkinter as tk
from tkinter import ttk, Menu, messagebox, filedialog
import funcionArchivos
import FunCompilacion
from PIL import Image, ImageTk
import os

# ==========================================
# 1. CONFIGURACIÓN Y VARIABLES GLOBALES
# ==========================================
#VARIABLES
tabla_tokens = None
consola_errores_lexicos = None

#VENTANDA
root = tk.Tk()
root.title("Editor de Código")
root.geometry("1200x800") 

COLOR_FONDO =  "#2E3440"
COLOR_EDITOR = "#3B4252"
COLOR_TEXTO =  "#ECEFF4"
COLOR_BARRA =  "#88C0D0"
COLOR_HIGHLIGHT = "#434C5E"

root.configure(bg=COLOR_FONDO)
FUENTE_SISTEMA = ('Segoe UI', 9)
FUENTE_EDITOR = ('Consolas', 11)

estilo = ttk.Style()
estilo.theme_use('default')
estilo.configure("TNotebook", background=COLOR_FONDO, borderwidth=0)
estilo.configure("TNotebook.Tab", background=COLOR_BARRA, foreground=COLOR_FONDO, padding=[12, 4], font=FUENTE_SISTEMA)
estilo.map("TNotebook.Tab", background=[("selected", COLOR_EDITOR)], foreground=[("selected", COLOR_TEXTO)])

#Funcion de abrir archivos
def abrir_archivo_flujo():
    ruta = filedialog.askopenfilename(
        filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
    )
    if ruta:
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                contenido = f.read()
            nombre = os.path.basename(ruta)
            agregar_pestana(nombre, contenido, ruta)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el archivo: {e}")
# ==========================================
# 2. CARGA DE ICONOS
# ==========================================
directorio_actual = os.path.dirname(__file__)
ruta_iconos = os.path.join(directorio_actual, "iconos")

def cargar_icono(nombre, size=(20, 20)):
    ruta = os.path.join(ruta_iconos, nombre)
    try:
        imagen = Image.open(ruta)
        imagen = imagen.resize(size, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(imagen)
    except: return None

# Iconos para menús y botones
img_nuevo = cargar_icono("nuevo.png")
img_abrir = cargar_icono("abrir.png")
img_guardar = cargar_icono("guardar.png")
img_lexico = cargar_icono("lexico.png")
img_sintatico = cargar_icono("sintatico.png") 
img_semantico = cargar_icono("semantico.png")
img_play = cargar_icono("play.png")
img_errores = cargar_icono("errores.png")
img_resultado = cargar_icono("resultado.png")
img_archivos = cargar_icono("archivos.png")
img_salir = cargar_icono("salir.png")
img_guardarComo = cargar_icono("guardarComo.png")
# ==========================================
# 3. LÓGICA DE PESTAÑAS Y ARCHIVOS
# ==========================================
estados_modificados = {}

def obtener_editor_actual():
    try:
        pestana_id = notebook_editor.select()
        if not pestana_id: return None
        return notebook_editor.nametowidget(pestana_id).editor_text
    except: return None

def marcar_como_modificado(event, editor):
    if event.keysym in ('Control_L', 'Control_R', 'Shift_L', 'Shift_R', 'Alt_L', 'Alt_R', 'Up', 'Down', 'Left', 'Right'): return
    id_p = notebook_editor.select()
    if id_p and not estados_modificados.get(id_p, False):
        estados_modificados[id_p] = True
        nombre = notebook_editor.tab(id_p, "text")
        if not nombre.endswith("*"):
            notebook_editor.tab(id_p, text=nombre + " *")

# ==========================================
# 3. LÓGICA DE PESTAÑAS Y ARCHIVOS (CORREGIDA)
# ==========================================

def guardar_como():
    editor = obtener_editor_actual()
    if not editor: return
    
    archivo = filedialog.asksaveasfilename(
        defaultextension=".txt", 
        filetypes=[("Archivos de texto", "*.txt"), ("Todos", "*.*")]
    )
    
    if archivo:
        try:
            with open(archivo, "w", encoding="utf-8") as f:
                f.write(editor.get("1.0", tk.END))
            id_p = notebook_editor.select()
            notebook_editor.tab(id_p, text=os.path.basename(archivo))
            estados_modificados[id_p] = False
            
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")

# ==========================================
# 3. LÓGICA DE PESTAÑAS Y ARCHIVOS (CORREGIDA)
# ==========================================

def guardar_como():
    editor = obtener_editor_actual()
    if not editor: return

    archivo = filedialog.asksaveasfilename(
        defaultextension=".txt", 
        filetypes=[("Archivos de texto", "*.txt"), ("Todos", "*.*")]
    )
    
    if archivo:
        try:
            with open(archivo, "w", encoding="utf-8") as f:
                f.write(editor.get("1.0", tk.END))
            
            # Actualizar el nombre de la pestaña y quitar el asterisco
            id_p = notebook_editor.select()
            notebook_editor.tab(id_p, text=os.path.basename(archivo))
            
            frame_actual = notebook_editor.nametowidget(id_p)
            frame_actual.ruta_archivo = archivo
            
            estados_modificados[id_p] = False
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")

def guardar_simple():
   
    pestana_id = notebook_editor.select()
    if not pestana_id: return
    
    frame_actual = notebook_editor.nametowidget(pestana_id)
    editor = frame_actual.editor_text

    ruta = getattr(frame_actual, 'ruta_archivo', None)

    if ruta:
        try:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(editor.get("1.0", tk.END))
            
            nombre_actual = notebook_editor.tab(pestana_id, "text")
            if nombre_actual.endswith(" *"):
                notebook_editor.tab(pestana_id, text=nombre_actual.replace(" *", ""))
            
            estados_modificados[pestana_id] = False
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")
    else:
        guardar_como()

def cerrar_pestana_actual(index=None):
    try:
        if index is None:
            index = notebook_editor.index("current")
        
        id_p = notebook_editor.tabs()[index]

        if estados_modificados.get(id_p, False):
            res = messagebox.askyesnocancel("Guardar cambios", "¿Deseas guardar los cambios antes de cerrar?")
            if res is True:
                guardar_simple() 
            elif res is None:
                return

        notebook_editor.forget(id_p)
        
    except tk.TclError:
        pass
def agregar_pestana(nombre="Nuevo", contenido="", ruta=None):
    frame_pestana = tk.Frame(notebook_editor, bg=COLOR_EDITOR)
    editor_container = tk.Frame(frame_pestana, bg=COLOR_EDITOR)
    editor_container.pack(fill=tk.BOTH, expand=True)
    
    frame_pestana.ruta_archivo = ruta

    # 1. Widget de números de línea
    line_numbers = tk.Text(editor_container, width=4, padx=5, takefocus=0, border=0, 
                           bg="#2E3440", fg="#D8DEE9", state="disabled", font=FUENTE_EDITOR)
    line_numbers.pack(side=tk.LEFT, fill=tk.Y)

    # 2. Widget del editor de texto
    editor_text = tk.Text(editor_container, undo=True, wrap="none",
                          bg=COLOR_EDITOR, 
                          fg=COLOR_TEXTO, insertbackground="white",
                          borderwidth=0, font=FUENTE_EDITOR)
    editor_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    editor_text.insert("1.0", contenido)
    # Colores para cada tokens.
    editor_text.tag_configure("color1", foreground="#D08770") # Números (Naranja)
    editor_text.tag_configure("color2", foreground="#8FBCBB") # Identificadores (Cian claro)
    editor_text.tag_configure("color3", foreground="#34383F") # Comentarios (Gris/Oculto)
    editor_text.tag_configure("color4", foreground="#B48EAD") # Reservadas (Púrpura)
    editor_text.tag_configure("color5", foreground="#A3EA65") # Aritméticos (Verde)
    editor_text.tag_configure("color6", foreground="#89B9EA") # Lógicos/Relacionales (Azul)
    editor_text.tag_configure("red",    foreground="#E72438") # Errores (Rojo)
    # Referencias necesarias para funciones externas
    frame_pestana.editor_text = editor_text
    frame_pestana.line_numbers = line_numbers
    editor_text.tag_configure("active_line", background=COLOR_HIGHLIGHT)

    # --- LÓGICA DE SINCRONIZACIÓN CRÍTICA ---

    def sincronizar_vistas(*args):
        line_numbers.yview(*args)
        editor_text.yview(*args)

    def al_hacer_scroll(*args):
        scrollbar.set(*args)
        line_numbers.yview_moveto(args[0])
        actualizar_todo_local(editor_text, line_numbers)

    # Configuración de Scrollbar
    scrollbar = tk.Scrollbar(editor_container, command=sincronizar_vistas)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    editor_text.config(yscrollcommand=al_hacer_scroll)

    # Eventos de teclado y mouse
    editor_text.bind("<KeyRelease>", lambda e: [
        actualizar_todo_local(editor_text, line_numbers),
        marcar_como_modificado(e, editor_text),
        actualizar_estado_cursor(),
        ejecutar_resaltado_rapido(editor_text)
    ])
    def actualizar_tabla_visual(tokens):
        for item in tabla_tokens.get_children():
            tabla_tokens.delete(item)
        for t in tokens:
            tabla_tokens.insert('', tk.END, values=(t['tipo'], t['valor'], t['linea']))
    def ejecutar_resaltado_rapido(editor):
        from scanner import Scanner
        sc = Scanner()
        codigo = editor.get("1.0", tk.END)
        tokens_tabla, tokens_colores = sc.analizar(codigo)
        sc.aplicar_colores(editor, tokens_colores)
        actualizar_tabla_visual(tokens_tabla)

    editor_text.bind("<Button-1>", lambda e: root.after(10, lambda: actualizar_todo_local(editor_text, line_numbers)))
    editor_text.bind("<ButtonRelease>", actualizar_estado_cursor)
    
    editor_text.bind("<<Modified>>", lambda e: [
        actualizar_todo_local(editor_text, line_numbers),
        editor_text.edit_modified(False)
    ])
    def mouse_wheel(event):
        move = int(-1 * (event.delta / 120))
        editor_text.yview_scroll(move, "units")
        line_numbers.yview_scroll(move, "units")
        actualizar_todo_local(editor_text, line_numbers)
        return "break" 

    editor_text.bind("<MouseWheel>", mouse_wheel)
    notebook_editor.add(frame_pestana, text=nombre)
    notebook_editor.select(frame_pestana)
    
    estados_modificados[notebook_editor.select()] = False
    actualizar_todo_local(editor_text, line_numbers)
# ==========================================
# 4. MENÚS Y BARRA SUPERIOR (TU DISEÑO)
# ==========================================
barra_superior = tk.Frame(root, bg=COLOR_BARRA, height=40)
barra_superior.pack(side=tk.TOP, fill=tk.X)
barra_superior.pack_propagate(False)

# Menu Archivo
archivo_btn = tk.Menubutton(barra_superior, text="Archivo", image=img_archivos, compound=tk.LEFT, bg=COLOR_BARRA, relief=tk.FLAT, font=FUENTE_SISTEMA)
archivo_menu = Menu(archivo_btn, tearoff=0, bg=COLOR_FONDO, fg=COLOR_TEXTO)
archivo_menu.add_command(label=" Nuevo", image=img_nuevo, compound=tk.LEFT, command=lambda: agregar_pestana())
archivo_menu.add_command(label=" Abrir", image=img_abrir, compound=tk.LEFT, command=abrir_archivo_flujo)
archivo_menu.add_command(label=" Guardar", image=img_guardar, compound=tk.LEFT, 
                         command=guardar_simple)
archivo_menu.add_command(label=" Guardar como...", image=img_guardarComo, compound=tk.LEFT, 
                         command=guardar_como)
archivo_menu.add_separator()
archivo_menu.add_command(label=" Cerrar", image=img_salir, compound=tk.LEFT, command=cerrar_pestana_actual)
archivo_menu.add_command(label=" Salir", image=img_salir, compound=tk.LEFT, command=root.quit)
archivo_btn.config(menu=archivo_menu)
archivo_btn.pack(side=tk.LEFT, padx=5)

# Menu Compilar
compilar_btn = tk.Menubutton(barra_superior, text="Compilar", bg=COLOR_BARRA, relief=tk.FLAT, font=FUENTE_SISTEMA)
compilar_menu = Menu(compilar_btn, tearoff=0, bg=COLOR_FONDO, fg=COLOR_TEXTO)
compilar_menu.add_command(label=" Análisis Léxico", image=img_lexico, compound=tk.LEFT, command=FunCompilacion.analisis_lexico)
compilar_menu.add_command(label=" Análisis Sintáctico", image=img_sintatico, compound=tk.LEFT, command=FunCompilacion.analisis_sintactico)
compilar_menu.add_command(label=" Análisis Semántico", image=img_semantico, compound=tk.LEFT, command=FunCompilacion.analisis_semantico)
compilar_menu.add_command(label=" Intermedio", compound=tk.LEFT, command=FunCompilacion.codigo_intermedio)
compilar_menu.add_command(label=" Ejecutar", image=img_play, compound=tk.LEFT, command=FunCompilacion.ejecutar_programa)
compilar_btn.config(menu=compilar_menu)
compilar_btn.pack(side=tk.LEFT, padx=5)

# Botones Rápidos en Barra Superior (Como en tu foto)
def crear_btn_sup(texto, icono, comando):
    tk.Button(barra_superior, text=texto, image=icono, compound=tk.LEFT, bg=COLOR_BARRA, relief=tk.FLAT, command=comando, padx=10).pack(side=tk.LEFT)

crear_btn_sup("Léxico", img_lexico, lambda: FunCompilacion.analisis_lexico(
    obtener_editor_actual(), 
    tabla_tokens, 
    consola_errores_lexicos
))
crear_btn_sup("Sintáctico", img_sintatico, lambda: FunCompilacion.analisis_sintactico(
    obtener_editor_actual(), 
    tree_ast, 
    consola_errores_sintacticos
))
crear_btn_sup("Semántico", img_semantico, FunCompilacion.analisis_semantico)
crear_btn_sup("Intermedio", None, FunCompilacion.codigo_intermedio)
tk.Button(barra_superior, text=" Ejecutar", image=img_play, compound=tk.LEFT, bg=COLOR_BARRA, relief=tk.FLAT, font=('Segoe UI', 10), command=FunCompilacion.ejecutar_programa, padx=15).pack(side=tk.LEFT)

# BARRA DE ACCESO RÁPIDO 
barra_herramientas = tk.Frame(root, bg=COLOR_EDITOR, height=35)
barra_herramientas.pack(side=tk.TOP, fill=tk.X)
barra_herramientas.pack_propagate(False)

def crear_btn_herr(img, cmd):
    tk.Button(barra_herramientas, image=img, bg=COLOR_EDITOR, activebackground=COLOR_BARRA, relief=tk.FLAT, command=cmd).pack(side=tk.LEFT, padx=2, pady=2)

crear_btn_herr(img_nuevo, lambda: agregar_pestana())
crear_btn_herr(img_abrir, abrir_archivo_flujo)
crear_btn_herr(img_guardar, lambda: guardar_simple())
crear_btn_herr(img_guardarComo, lambda: guardar_como())
crear_btn_herr(img_salir, cerrar_pestana_actual)
tk.Frame(barra_herramientas, width=1, bg=COLOR_BARRA).pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=5)
crear_btn_herr(img_lexico, FunCompilacion.analisis_lexico)
crear_btn_herr(img_sintatico, FunCompilacion.analisis_sintactico)
crear_btn_herr(img_semantico, FunCompilacion.analisis_semantico)
tk.Frame(barra_herramientas, width=1, bg=COLOR_BARRA).pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=5)
tk.Button(barra_herramientas, image=img_play, bg=COLOR_EDITOR,activebackground=COLOR_BARRA, 
          bd=0, 
          relief=tk.FLAT, command=FunCompilacion.ejecutar_programa).pack(side=tk.LEFT, padx=5)

# ==========================================
# 5. ESTRUCTURA DE PANELES
# ==========================================
panel_vertical = tk.PanedWindow(root, orient=tk.VERTICAL, bg=COLOR_FONDO, sashwidth=6)
panel_vertical.pack(fill=tk.BOTH, expand=True)

panel_horizontal = tk.PanedWindow(panel_vertical, orient=tk.HORIZONTAL, bg=COLOR_FONDO, sashwidth=6)
panel_vertical.add(panel_horizontal, height=500)

notebook_editor = ttk.Notebook(panel_horizontal)
panel_horizontal.add(notebook_editor, width=750)

# Panel Derecho
resultados_frame = tk.Frame(panel_horizontal, bg=COLOR_FONDO)
panel_horizontal.add(resultados_frame, width=350)
tabs_resultados = ttk.Notebook(resultados_frame)
tabs_resultados.pack(fill=tk.BOTH, expand=True)

# Pestaña Léxico - Tabla
frame_lexico = tk.Frame(tabs_resultados, bg=COLOR_EDITOR)
tabs_resultados.add(frame_lexico, text="Léxico")
#Sintactico 
frame_sintactico = tk.Frame(tabs_resultados, bg=COLOR_EDITOR)
tabs_resultados.add(frame_sintactico, text="Sintáctico")
tree_ast = ttk.Treeview(frame_sintactico, show="tree")
tree_ast.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

scroll_ast = ttk.Scrollbar(frame_sintactico, orient="vertical", command=tree_ast.yview)
scroll_ast.pack(side=tk.RIGHT, fill=tk.Y)
tree_ast.configure(yscrollcommand=scroll_ast.set)

#Pestañas sin funciones todavia
for n in [  "Semántico", "Intermedio", "Tabla Símbolos"]:
    tabs_resultados.add(tk.Frame(tabs_resultados, bg=COLOR_EDITOR), text=n)


tabla_tokens = ttk.Treeview(frame_lexico, columns=("Tipo", "Valor", "Línea"), show='headings')
tabla_tokens.heading("Tipo", text="Tipo")
tabla_tokens.heading("Valor", text="Valor")
tabla_tokens.heading("Línea", text="Línea")
tabla_tokens.column("Tipo", width=100)
tabla_tokens.column("Valor", width=150)
tabla_tokens.column("Línea", width=50)
tabla_tokens.pack(fill=tk.BOTH, expand=True)

# Panel Inferior
frame_inferior = tk.Frame(panel_vertical, bg=COLOR_FONDO)
panel_vertical.add(frame_inferior, height=200)
tabs_consola = ttk.Notebook(frame_inferior)
tabs_consola.pack(fill=tk.BOTH, expand=True)
for n in [  "Errores Semánticos", "Resultados"]:
    tabs_consola.add(tk.Frame(tabs_consola, bg=COLOR_EDITOR), text=n, image=img_errores if "Errores" in n else img_resultado, compound=tk.LEFT)

frame_err_lex = tk.Frame(tabs_consola, bg=COLOR_EDITOR)
tabs_consola.add(frame_err_lex, text="Errores Léxicos", image=img_errores, compound=tk.LEFT)
consola_errores_lexicos = tk.Text(frame_err_lex, bg="#2E3440", fg="#FF5555", font=('Consolas', 10))
consola_errores_lexicos.pack(fill=tk.BOTH, expand=True)

#Parte de la consola para sintactico
consola_errores_sintacticos = tk.Text(tabs_consola.nametowidget(tabs_consola.tabs()[0]), bg="#2E3440", fg="#FF5555", font=('Consolas', 10))
consola_errores_sintacticos.pack(fill=tk.BOTH, expand=True)
# ==========================================
# 6. FUNCIONES DE APOYO
# ==========================================

def actualizar_todo_local(txt, line_w):
    line_w.config(state="normal")
    line_w.delete("1.0", tk.END)
    
    metrica_lineas = txt.index('end-1c').split('.')[0]
    lineas = "\n".join(str(i) for i in range(1, int(metrica_lineas) + 1))
    
    line_w.insert("1.0", lineas)
    line_w.yview_moveto(txt.yview()[0])
    
    line_w.config(state="disabled")
    
    txt.tag_remove("active_line", "1.0", tk.END)
    txt.tag_add("active_line", f"{txt.index('insert').split('.')[0]}.0", f"{txt.index('insert').split('.')[0]}.end+1c")
def resetear_modificado():
    id_p = notebook_editor.select()
    if id_p:
        estados_modificados[id_p] = False
        n = notebook_editor.tab(id_p, "text")
        if n.endswith("*"): notebook_editor.tab(id_p, text=n.replace(" *", ""))
def actualizar_estado_cursor(event=None):
    editor = obtener_editor_actual()
    if editor:
        posicion = editor.index(tk.INSERT)
        linea, columna = posicion.split(".")
        total_lineas = int(editor.index("end-1c").split(".")[0])

        label_lineas.config(
            text=f"Línea: {linea} | Columna: {int(columna)+1} | Total líneas: {total_lineas}"
        )

# ==========================================
# 7. BARRA DE ESTADO (LINEAS Y COLUMNA)
# ==========================================

barra_estado = tk.Frame(root, bg=COLOR_EDITOR, height=25)
barra_estado.pack(side=tk.BOTTOM, fill=tk.X)

label_lineas = tk.Label(
    barra_estado,
    text="Líneas: 1 | Columna: 1",
    bg=COLOR_EDITOR,
    fg=COLOR_TEXTO,
    font=('Segoe UI', 9)
)

label_lineas.pack(side=tk.RIGHT, padx=10)

agregar_pestana("Archivo 1")
root.mainloop()