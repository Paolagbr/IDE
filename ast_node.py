# ast_node.py
# Representación de los nodos del Árbol Sintáctico Abstracto (AST) anotado.

class ASTNode:
    def __init__(self, node_type, value=None, line=1):
        # Soporte para nombres en español/inglés usados por tu parser
        self.node_type = node_type  # Tipo de nodo
        self.tipo = node_type       # Compatibilidad con parser_sintactico (tipo)
        
        self.value = value          # Valor o lexema
        self.valor = value          # Compatibilidad con parser_sintactico (valor)
        
        self.line = line            # Línea de código
        self.linea = line           # Compatibilidad con parser_sintactico (linea)
        
        self.children = []          # Lista de nodos hijos
        self.hijos = self.children  # Compatibilidad con parser_sintactico (hijos)

        # --- Atributos para el Análisis Semántico (Árbol Anotado) ---
        self.data_type = None       # Tipo de dato ('int', 'float', 'bool', 'error')
        self.dtype = None           # Alias semántico

    def add_child(self, child):
        if child is not None:
            self.children.append(child)

    def agregar_hijo(self, child):
        self.add_child(child)

    def __repr__(self):
        type_str = f" : {self.data_type}" if self.data_type else ""
        val_str = f" ({self.value})" if self.value is not None else ""
        return f"<{self.node_type}{val_str}{type_str}>"


# ALIAS CRÍTICO: Permite que parser_sintactico.py siga funcionando sin tocarlo
NodoAST = ASTNode