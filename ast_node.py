#Archivo encargado de la vista del arbolito
class NodoAST:
    def __init__(self, tipo, valor=None):
        self.tipo = tipo          # Nombre de la regla o categoría (ej: 'IF', 'ASIGNACION')
        self.valor = valor        # El lexema real si es una hoja (ej: 'x', '10')
        self.hijos = []           # Lista de nodos hijos

    def agregar_hijo(self, hijo):
        if hijo:
            self.hijos = list(self.hijos)
            self.hijos.append(hijo)