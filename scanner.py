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
        tokens_para_tabla = []   # Lo que va al Treeview (sin comentarios)
        tokens_para_colores = [] # Todo lo que se debe pintar (incluye comentarios)
        
        linea = 1
        columna_inicio = 0
        
        # Usamos self.token_patterns si lo tienes en el init, o defínelo aquí mismo
        token_patterns = [
            ('COMENTARIO_MULTI', r'/\*[\s\S]*?\*/'),
            ('COMENTARIO_SIMPLE', r'//.*'),
            ('NUMERO_REAL', r'\d+\.\d+'),
            ('NUMERO_ENTERO', r'\d+'),
            ('IDENTIFICADOR', r'[a-zA-Z][a-zA-Z0-9]*'),
            ('OP_ARITMETICO', r'\+\+|--|\+|-|\*|/|%|\^'),
            ('OP_LOG_REL', r'<=|>=|!=|==|&&|\|\||<|>|!|and|or|not'),
            ('ASIGNACION', r'='),
            ('SIMBOLO', r'\(|\)|\{|\}|,|;|\'|\"'),
            ('ESPACIO', r'[ \t]+'),
            ('NUEVA_LINEA', r'\n'),
            ('ERROR', r'.'),
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
                
            # Clasificación de color
            if kind == 'IDENTIFICADOR' and value in self.RESERVADAS:
                tipo_final = 'RESERVADA'
            elif kind in ['COMENTARIO_MULTI', 'COMENTARIO_SIMPLE']:
                tipo_final = 'COMENTARIO'
            elif kind in ['NUMERO_REAL', 'NUMERO_ENTERO']:
                tipo_final = 'NUMERO'
            else:
                tipo_final = kind
            
            color = self.COLORS.get(tipo_final, 'black')
            
            # Creamos el token
            token_info = {
                'tipo': tipo_final, 
                'valor': value, 
                'linea': linea, 
                'col': columna, 
                'color': color
            }

            # --- LA LÓGICA DE FILTRADO ---
            # 1. Siempre lo agregamos a la lista de colores (para que se pinte)
            tokens_para_colores.append(token_info)

            # 2. Solo si NO es comentario, lo agregamos a la tabla
            if tipo_final != 'COMENTARIO':
                tokens_para_tabla.append(token_info)

            # Manejo de líneas para comentarios multilínea (para que no se desfase el color)
            if tipo_final == 'COMENTARIO' and '\n' in value:
                linea += value.count('\n')
                columna_inicio = match.start() + value.rfind('\n') + 1
                
        # IMPORTANTE: Regresamos las dos listas
        return tokens_para_tabla, tokens_para_colores
   
    #Colores para cada uno de los tokens
    def aplicar_colores(self, editor, tokens):
        import tkinter as tk
        
        # 1. Limpiar colores previos en todo el documento
        for tag in ["color1", "color2", "color3", "color4", "color5", "color6", "red"]:
            editor.tag_remove(tag, "1.0", tk.END)
            
        # 2. Aplicar colores nuevos
        for t in tokens:
            if t['color'] == 'black':
                continue
                
            # Posición de inicio: "linea.columna"
            inicio = f"{t['linea']}.{t['col'] - 1}"
            
            # --- LÓGICA PARA COMENTARIOS MULTILÍNEA ---
            valor_token = str(t['valor'])
            num_saltos = valor_token.count('\n')
            
            if num_saltos > 0:
                # Si el token tiene saltos de línea (como /* ... */)
                # Calculamos la línea final sumando los saltos
                linea_fin = t['linea'] + num_saltos
                # La columna final es el largo de la última parte del texto tras el último \n
                ultima_linea_contenido = valor_token.split('\n')[-1]
                col_fin = len(ultima_linea_contenido)
                fin = f"{linea_fin}.{col_fin}"
            else:
                # Si es una sola línea (comportamiento normal)
                fin = f"{t['linea']}.{t['col'] - 1 + len(valor_token)}"
            
            # Pintamos el color desde el inicio calculado hasta el fin calculado
            editor.tag_add(t['color'], inicio, fin)