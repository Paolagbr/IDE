import re

class Scanner:
  
    def __init__(self):
        # Definición de Categorías y Colores según el PDF [cite: 11-16]
        self.COLORS = {
            'NUMERO': 'color1',      
            'IDENTIFICADOR': 'color2',
            'COMENTARIO': 'color3',   
            'RESERVADA': 'color4',
            'OP_ARITMETICO': 'color5',
            'OP_LOG_REL': 'color6',   
            'SIMBOLO': 'black',
            'ASIGNACION': 'black',
            'ERROR': 'red'
        }

        # Palabras reservadas solicitadas [cite: 13]
        self.RESERVADAS = {'if', 'else', 'end', 'do', 'while', 'switch', 'case', 'int', 'float', 'main', 'cin', 'cout'}

    def analizar(self, codigo_fuente):
        tokens = []
        linea = 1
        columna_inicio = 0
        
        # Expresiones regulares basadas en los requerimientos [cite: 11-19, 39]
        token_patterns = [
            ('COMENTARIO_MULTI', r'/\*[\s\S]*?\*/'),          # Estilo C [cite: 12, 22]
            ('COMENTARIO_SIMPLE', r'//.*'),                   # Estilo C [cite: 12, 22]
            ('NUMERO_REAL',      r'\d+\.\d+'),                # Color 1 [cite: 11]
            ('NUMERO_ENTERO',    r'\d+'),                     # Color 1 [cite: 11]
            ('IDENTIFICADOR',    r'[a-zA-Z][a-zA-Z0-9]*'),    # Color 2 [cite: 12]
            ('OP_ARITMETICO',    r'\+\+|--|\+|-|\*|/|%|\^'),   # Color 5 [cite: 14]
            ('OP_LOG_REL',       r'<=|>=|!=|==|&&|\|\||<|>|!|and|or|not'), # Color 6 [cite: 15, 16]
            ('ASIGNACION',       r'='),                       # [cite: 19]
            ('SIMBOLO',          r'\(|\)|\{|\}|,|;|\'|\"'),   # [cite: 18]
            ('ESPACIO',          r'[ \t]+'),
            ('NUEVA_LINEA',      r'\n'),
            ('ERROR',            r'.'),                       # Caracteres inválidos [cite: 23]
        ]
        
        combined_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_patterns)
        
        for match in re.finditer(combined_regex, codigo_fuente):
            kind = match.lastgroup
            value = match.group()
            columna = match.start() - columna_inicio + 1
            
            if kind == 'NUEVA_LINEA':
                columna_inicio = match.end()
                linea += 1
                continue
            elif kind == 'ESPACIO':
                continue
                
            # Clasificación final
            if kind == 'IDENTIFICADOR' and value in self.RESERVADAS:
                tipo_final = 'RESERVADA'
            elif kind in ['COMENTARIO_MULTI', 'COMENTARIO_SIMPLE']:
                tipo_final = 'COMENTARIO'
            elif kind in ['NUMERO_REAL', 'NUMERO_ENTERO']:
                tipo_final = 'NUMERO'
            else:
                tipo_final = kind
                
            color = self.COLORS.get(tipo_final, 'black')
            
            tokens.append({
                'tipo': tipo_final, 
                'valor': value, 
                'linea': linea, 
                'col': columna, 
                'color': color
            })
                
        return tokens
    #Colores para cada uno de los tokens
    def aplicar_colores(self, editor, tokens):
        import tkinter as tk # Importación local para evitar conflictos
        
        # 1. Limpiar colores
        for tag in ["color1", "color2", "color3", "color4", "color5", "color6", "red"]:
            editor.tag_remove(tag, "1.0", tk.END)
            
        # 2. Aplicar colores
        for t in tokens:
            # Si el color es 'black', no necesitamos aplicar tag (es el default)
            if t['color'] == 'black':
                continue
                
            inicio = f"{t['linea']}.{t['col'] - 1}"
            # Calculamos el fin basándonos en el largo del valor
            fin = f"{t['linea']}.{t['col'] - 1 + len(str(t['valor']))}"
            
            editor.tag_add(t['color'], inicio, fin)