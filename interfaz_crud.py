from conexion_bd import DatabaseConexion
from tabla_interfaz import*
from tkinter import ttk

class InterfazCrud:
    def __init__(self, ventana_principal = None, frame = None):
        #Si se manda una ventana principal MRU trabajara como ventana secundaria
        if ventana_principal is not None and frame is None:
            self.root = tk.Toplevel(ventana_principal)
        #Si se manda un frame, MRU se colocara dentro de ese frame
        elif frame is not None and ventana_principal is None:
            self.root = frame
        #En caso contrario trabajara como una ventana principal
        else:
            # Crear ventana principal
            self.root = tk.Tk()
            self.root.geometry("700x600")
            self.root.title("CRUD")

        self.db = DatabaseConexion(ConsultasSQL.conn_str)

        # Formulario
        self.frame_formulario = tk.Frame(self.root)
        self.frame_formulario.pack(side="top", fill=tk.X)

        # Filtro
        self.frame_filtro = tk.Frame(self.root)
        self.frame_filtro.pack(side="top", fill=tk.X, padx=20)

        tk.Label(self.frame_filtro, text="Filtro:").pack(side="top", anchor="w", padx=5)
        tk.Label(self.frame_filtro, text="Columna:").pack(side="left")

        self.combo_columnas = ttk.Combobox(self.frame_filtro, state="readonly", width=20)
        self.combo_columnas.pack(side="left", padx=5)

        tk.Label(self.frame_filtro, text="Buscar:").pack(side="left")
        self.entrada_filtro = tk.Entry(self.frame_filtro)
        self.entrada_filtro.pack(side="left", fill="x", expand=True, padx=5)

        # Tabla
        self.frame_tabla = tk.Frame(self.root)
        self.frame_tabla.pack(fill="both", expand=True, padx=10, pady=5)

        self.tree = ttk.Treeview(self.frame_tabla)
        self.tree.pack(side="left", fill="both", expand=True)

        scroll_y = ttk.Scrollbar(self.frame_tabla, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_y.set)
        scroll_y.pack(side="right", fill="y")

        self.tabla_manager = TablaBD(self.tree)
        self.filtro = Filtro(self.entrada_filtro, self.combo_columnas, self.tabla_manager)

        # Conectar eventos
        self.entrada_filtro.bind("<KeyRelease>", self.filtro.aplicar)
        btn_limpiar = tk.Button(self.frame_filtro, text="Limpiar filtro", command=self.filtro.limpiar)
        btn_limpiar.pack(side="left", padx=5)

        self.formulario = Formulario(self.frame_formulario, self.db, self.tabla_manager)

    def mostrar_tabla(self, nombre_tabla, consulta):
        rows = self.db.ejecutar_consulta(consulta)
        columnas = self.db.obtener_columnas()

        self.combo_columnas["values"] = columnas
        self.combo_columnas.set(columnas[0] if columnas else "")

        self.tabla_manager.mostrar_datos(columnas, rows)
        self.formulario.mostrar(nombre_tabla, columnas)

    def mostrar(self):
        self.root.mainloop()