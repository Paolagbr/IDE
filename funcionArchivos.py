from tkinter import filedialog

ruta_actual = None

def nuevo_archivo(text_area, root):
    global ruta_actual
    text_area.delete(1.0, "end")
    ruta_actual = None
    root.title("Nuevo Archivo - Editor")

def abrir_archivo(text_area, root):
    global ruta_actual

    archivo = filedialog.askopenfilename(
        filetypes=[("Archivos de texto", "*.txt"), ("Todos", "*.*")]
    )

    if archivo:
        ruta_actual = archivo
        text_area.delete(1.0, "end")

        with open(archivo, "r") as f:
            text_area.insert("insert", f.read())

        root.title(archivo)

def guardar_archivo(text_area, root):
    global ruta_actual

    if ruta_actual:
        with open(ruta_actual, "w") as f:
            f.write(text_area.get(1.0, "end"))
    else:
        guardar_como(text_area, root)

def guardar_como(text_area, root):
    global ruta_actual

    archivo = filedialog.asksaveasfilename(
        defaultextension=".txt"
    )

    if archivo:
        ruta_actual = archivo
        guardar_archivo(text_area, root)

def cerrar_archivo(text_area, root):
    nuevo_archivo(text_area, root)