# ast_node.py
# Representación de los nodos del Árbol Sintáctico Abstracto (AST) anotado.

class ASTNode:
    def __init__(self, node_type, value=None, line=1, col=None):
        # Soporte para nombres en español/inglés usados por tu parser
        self.node_type = node_type  # Tipo de nodo
        self.tipo = node_type       # Compatibilidad con parser_sintactico (tipo)

        self.value = value          # Valor o lexema
        self.valor = value          # Compatibilidad con parser_sintactico (valor)

        self.line = line            # Fila del código fuente
        self.linea = line           # Compatibilidad con parser_sintactico (linea)
        self.col = col              # Columna del código fuente (None = aún sin posición)
        self.columna = col

        self.children = []          # Lista de nodos hijos
        self.hijos = self.children  # Compatibilidad con parser_sintactico (hijos)

        # --- Atributos para el Análisis Semántico (Árbol Anotado) ---
        self.data_type = None       # Tipo de dato ('int', 'float', 'bool', 'error')
        self.dtype = None           # Alias semántico
        self.valor_calc = None      # Valor conocido en tiempo de compilación (None = no aplica)
        self.tiene_error = False    # True si el análisis marcó este nodo como erróneo
        self.atributos = []         # [(nombre, 'H' | 'S')]: heredado (H) o sintetizado (S)

    def add_child(self, child):
        if child is not None:
            self.children.append(child)

    def agregar_hijo(self, child):
        self.add_child(child)

    def __repr__(self):
        type_str = f" : {self.data_type}" if self.data_type else ""
        val_str = f" ({self.value})" if self.value is not None else ""
        return f"<{self.node_type}{val_str}{type_str}>"


def _subir(nodo):
    primera = None
    for h in nodo.children:
        p = _subir(h)
        if primera is None and p is not None:
            primera = p
    if nodo.col is None:
        if primera is None:
            return None
        nodo.line = nodo.linea = primera[0]
        nodo.col = nodo.columna = primera[1]
        return primera
    return (nodo.line, nodo.col)


def _bajar(nodo):
    for h in nodo.children:
        if h.col is None and nodo.col is not None:
            h.line = h.linea = nodo.line
            h.col = h.columna = nodo.col
        _bajar(h)


def completar_posiciones(nodo):
    """Los nodos que no nacen de un token (Eval_Condicion, Cuerpo_Instrucciones...) heredan la
    fila:columna del primer descendiente que sí la tiene; los que quedan sin nada, la de su padre."""
    if nodo is None:
        return None
    _subir(nodo)
    _bajar(nodo)
    return (nodo.line, nodo.col) if nodo.col is not None else None


# ALIAS CRÍTICO: Permite que parser_sintactico.py siga funcionando sin tocarlo
NodoAST = ASTNode
