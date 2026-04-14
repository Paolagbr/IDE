import re

class Scanner:
  
    def __init__(self):
        # Definición de Categorías y Colores
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

        self.RESERVADAS = {'if', 'else', 'end', 'do', 'while', 'switch', 'case', 'int', 'float', 'main', 'cin', 'cout'}
    def analizar(self, codigo_fuente):
        import re
        tokens_para_tabla = []   
        tokens_para_colores = [] 
        
        linea = 1
        columna_inicio = 0
        
        token_patterns = [
            ('COMENTARIO_MULTI', r'/\*[\s\S]*?\*/'),
            ('COMENTARIO_SIMPLE', r'//.*'),
            ('ESPACIO', r'[ \t]+'),
            ('NUEVA_LINEA', r'\n'),
            ('OP_ARITMETICO', r'\+\+|--|\+|-|\*|/|%|\^'), 
            ('OP_LOG_REL', r'<=|>=|!=|==|&&|\|\||<|>|!|and|or|not'),
            ('ASIGNACION', r'='),
            ('NUMERO_REAL', r'\d+\.\d+'),
            ('ERROR_REAL', r'\d+\.'), 
            ('NUMERO_ENTERO', r'\d+'),
            ('IDENTIFICADOR', r'[a-zA-Z][a-zA-Z0-9]*'),
            ('SIMBOLO', r'\(|\)|\{|\}|,|;|\'|\"'),
            ('ERROR', r'.')
        ]
        
        combined_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_patterns)
        matches = list(re.finditer(combined_regex, codigo_fuente))
        
        # Diccionario de parejas que se pueden fusionar
        parejas_fusion = {
            '+': '+', '-': '-', '=': '=', '!': '=', '<': '=', '>': '='
        }

        i = 0
        while i < len(matches):
            match = matches[i]
            kind = match.lastgroup
            value = match.group()
            columna = match.start() - columna_inicio + 1

            # --- LÓGICA DE FUSIÓN MULTI-LÍNEA ---
            if value in parejas_fusion:
                j = i + 1
                lineas_saltadas = 0
                temp_columna_inicio = columna_inicio
                encontro_par = False
                
                while j < len(matches):
                    next_m = matches[j]
                    if next_m.lastgroup == 'ESPACIO':
                        j += 1
                        continue
                    if next_m.lastgroup == 'NUEVA_LINEA':
                        lineas_saltadas += 1
                        temp_columna_inicio = next_m.end()
                        j += 1
                        continue
                    
                    if next_m.group() == parejas_fusion[value]:
                        encontro_par = True
                    break
             #Operadores relacionales
                if encontro_par:
                    valor_fusionado = value + parejas_fusion[value]
                  
                    tipo_f = 'OP_LOG_REL' if valor_fusionado in ['==', '!=', '<=', '>='] else 'OP_ARITMETICO'
                    
                    token_info = {
                        'tipo': tipo_f, 'valor': valor_fusionado,
                        'linea': linea, 'col': columna,
                        'color': self.COLORS.get(tipo_f, 'black')
                    }
                    tokens_para_colores.append(token_info)
                    tokens_para_tabla.append(token_info)
                    
                
                    linea += lineas_saltadas
                    columna_inicio = temp_columna_inicio
                    i = j + 1 
                    continue

            # --- MANEJO NORMAL DE SALTOS Y ESPACIOS ---
            if kind == 'NUEVA_LINEA':
                columna_inicio = match.end()
                linea += 1
                i += 1
                continue
            elif kind == 'ESPACIO':
                i += 1
                continue

            # --- CLASIFICACIÓN Y FILTRADO ---
            if kind == 'IDENTIFICADOR' and value in self.RESERVADAS:
                tipo_final = 'RESERVADA'
            elif kind in ['COMENTARIO_MULTI', 'COMENTARIO_SIMPLE']:
                tipo_final = 'COMENTARIO'
            elif kind in ['NUMERO_REAL', 'NUMERO_ENTERO']:
                tipo_final = 'NUMERO'
            elif kind == 'ERROR_REAL': 
                tipo_final = 'ERROR'
            else:
                tipo_final = kind
            
            token_info = {
                'tipo': tipo_final, 'valor': value, 
                'linea': linea, 'col': columna, 
                'color': self.COLORS.get(tipo_final, 'black')
            }

            tokens_para_colores.append(token_info)
            if tipo_final != 'COMENTARIO' and tipo_final != 'ERROR':
                tokens_para_tabla.append(token_info)

            if '\n' in value and kind != 'NUEVA_LINEA':
                linea += value.count('\n')
                columna_inicio = match.start() + value.rfind('\n') + 1

            i += 1
    
        return tokens_para_tabla, tokens_para_colores
    #Colores para cada uno de los tokens
    def aplicar_colores(self, editor, tokens):
        import tkinter as tk
        
        for tag in ["color1", "color2", "color3", "color4", "color5", "color6", "red"]:
            editor.tag_remove(tag, "1.0", tk.END)
            
        for t in tokens:
            if t['color'] == 'black':
                continue
                
     
            inicio = f"{t['linea']}.{t['col'] - 1}"
            
            # ---  COMENTARIOS MULTILÍNEA ---
            valor_token = str(t['valor'])
            num_saltos = valor_token.count('\n')
            
            if num_saltos > 0:
                linea_fin = t['linea'] + num_saltos
               
                ultima_linea_contenido = valor_token.split('\n')[-1]
                col_fin = len(ultima_linea_contenido)
                fin = f"{linea_fin}.{col_fin}"
            else:
               
                fin = f"{t['linea']}.{t['col'] - 1 + len(valor_token)}"
          
            editor.tag_add(t['color'], inicio, fin)