
estilo_tree.map("Custom.Treeview", background=[("selected", "#88C0D0")], foreground=[("selected", "#2E3440")])
# El widget Treeview con el tamaño suficiente
tree_ast = ttk.Treeview(frame_sintactico, show="tree", style="Custom.Treeview")
tree_ast.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

scroll_ast = ttk.Scrollbar(frame_sintactico, orient="vertical", command=tree_ast.yview)
scroll_ast.pack(side=tk.RIGHT, fill=tk.Y)
tree_ast.configure(yscrollcommand=scroll_ast.set)


