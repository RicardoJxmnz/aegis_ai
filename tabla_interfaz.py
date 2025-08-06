import tkinter as tk
from conexion_bd import*
from gestor_imagen import GestorImagen


class TablaBD:
    def __init__(self, treeview):
        self.tree = treeview
        self.columnas = []
        self.datos = []

    def mostrar_datos(self, columnas, filas):
        from tkinter import font as tkFont
        font = tkFont.Font()
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = columnas
        self.tree["show"] = "headings"
        for col in columnas:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=font.measure(col) + 40)
        self.columnas = columnas
        self.datos = filas
        self._insertar_filas(filas)

    def _insertar_filas(self, filas):
        self.tree.delete(*self.tree.get_children())
        for i, row in enumerate(filas):
            valores = []
            for val in row:
                if isinstance(val, (bytes, bytearray)):
                    valores.append("<binario>")
                elif hasattr(val, "strftime"):
                    if hasattr(val, "year") and not hasattr(val, "second"):
                        valores.append(val.strftime("%Y-%m-%d"))
                    else:
                        valores.append(val.strftime("%H:%M:%S"))
                elif val is None:
                    valores.append("")
                else:
                    valores.append(val)
            self.tree.insert("", "end", iid=f"fila{i}", values=valores)


class Filtro:
    def __init__(self, entrada_filtro, combo_columnas, tabla_manager):
        self.entrada_filtro = entrada_filtro
        self.combo_columnas = combo_columnas
        self.tabla_manager = tabla_manager

    def aplicar(self, *_):
        texto = self.entrada_filtro.get().lower()
        columna = self.combo_columnas.get()
        if not texto or not columna:
            self.tabla_manager._insertar_filas(self.tabla_manager.datos)
            return

        idx_col = self.tabla_manager.columnas.index(columna)
        filtrados = []

        for row in self.tabla_manager.datos:
            valor = row[idx_col]
            if columna.lower() == "activo":
                valor = "activo" if valor in (1, "1", True) else "inactivo"
            elif hasattr(valor, "strftime"):
                valor = valor.strftime("%Y-%m-%d")
            else:
                valor = str(valor)
            if texto in valor.lower():
                filtrados.append(row)

        self.tabla_manager._insertar_filas(filtrados)

    def limpiar(self):
        self.entrada_filtro.delete(0, tk.END)
        self.tabla_manager._insertar_filas(self.tabla_manager.datos)


class Formulario:
    def __init__(self, frame, db: DatabaseConexion, tabla_manager):
        self.frame = frame
        self.db = db
        self.entradas = {}
        self.datos = {}
        self.tabla_manager = tabla_manager

        self.imagen = GestorImagen()
        self.gestor_tablas = GestorTablas(db)

    def mostrar(self, tabla, columnas):
        from tkcalendar import DateEntry
        import tkinter as tk
        from tkinter import ttk

        for widget in self.frame.winfo_children():
            widget.destroy()
        self.entradas.clear()

        frame_columnas = tk.Frame(self.frame)
        frame_columnas.pack(side="right", fill="both", expand=True, padx=10)

        if tabla in ("Alumnos", "Maestros"):
            frame_imagen = tk.Frame(self.frame, bg="lightgray", width=200, height=200)
            frame_imagen.pack(side="left", fill="both", padx=5, pady=5)
            frame_imagen.pack_propagate(False)

            self.lbl_imagen = tk.Label(frame_imagen, text="Sin imagen", bg="white")
            self.lbl_imagen.pack(expand=True, fill="both")

            tk.Button(frame_imagen, text="Cargar Imagen", command=lambda: self.imagen.cargar_desde_archivo(self.lbl_imagen)).pack(side="bottom", pady=5)
            tk.Button(frame_imagen, text="Tomar Foto", command=lambda: self.imagen.capturar_desde_camara(self.lbl_imagen)).pack(side="bottom", pady=5)

        subframes = [tk.Frame(frame_columnas) for _ in range(3)]
        for sf in subframes:
            sf.pack(side="left", expand=True, fill="both", padx=5)

        for i, col in enumerate(columnas):
            contenedor = tk.Frame(subframes[i % 3])
            contenedor.pack(anchor="w", pady=2, fill="x")
            tk.Label(contenedor, text=f"{col}:").pack(anchor="w")

            entrada = self._crear_widget(col, contenedor)
            entrada.pack(fill="x")
            self.entradas[col] = entrada

        tk.Button(subframes[-1], text="Agregar", command=lambda: self.insertar_registro(tabla)).pack(pady=20)

    def _crear_widget(self, col, contenedor):
        from tkcalendar import DateEntry
        import tkinter as tk
        from tkinter import ttk

        if col == "Sexo":
            return ttk.Combobox(contenedor, values=["H", "M"])
        elif col == "Carrera":
            carreras = self.db.ejecutar_consulta("SELECT Nombre FROM Carreras")
            return ttk.Combobox(contenedor, values=[c[0] for c in carreras])
        elif col == "Activo":
            return ttk.Combobox(contenedor, values=["Activo", "Inactivo"])
        elif col == "Fecha_Nacimiento":
            return DateEntry(contenedor, date_pattern="yyyy-mm-dd", showweeknumbers=False)
        elif "Hora" in col:
            return ttk.Combobox(contenedor, values=self._generar_horas())
        elif col == "Profesor":
            profesores = self.db.ejecutar_consulta(
                "SELECT P.Nombre + ' ' + P.APaterno + ' ' + P.AMaterno FROM Maestros M JOIN Personas P ON M.Id_Persona = P.Id_Persona WHERE P.Activo = 1")
            return ttk.Combobox(contenedor, values=[p[0] for p in profesores])
        else:
            return tk.Entry(contenedor)

    def _generar_horas(self, inicio="07:00", fin="22:00", intervalo=30):
        from datetime import datetime, timedelta
        horas = []
        t = datetime.strptime(inicio, "%H:%M")
        t_fin = datetime.strptime(fin, "%H:%M")
        while t <= t_fin:
            horas.append(t.strftime("%H:%M"))
            t += timedelta(minutes=intervalo)
        return horas

    def leer_campos(self):
        self.datos = {
            campo: (
                entrada.get() if not hasattr(entrada, "get_date")
                else entrada.get_date().strftime("%Y-%m-%d")
            )
            for campo, entrada in self.entradas.items()
        }

    def insertar_registro(self, tabla):
        self.leer_campos()
        if tabla == "Alumnos" or tabla == "Maestros":
            embedding = self.imagen.obtener_embedding()
            id_persona = self.gestor_tablas.insertar_persona(self.datos, self.imagen.imagen_binaria, embedding)
            if tabla == "Alumnos":
                self.gestor_tablas.insertar_alumno(self.datos, id_persona)
                rows = self.db.ejecutar_consulta(ConsultasSQL.consulta_alumnos)
                columnas = self.db.obtener_columnas()
                self.tabla_manager.mostrar_datos(columnas, rows)
            else:
                self.gestor_tablas.insertar_maestro(self.datos, id_persona)
                rows = self.db.ejecutar_consulta(ConsultasSQL.consulta_maestros)
                columnas = self.db.obtener_columnas()
                self.tabla_manager.mostrar_datos(columnas, rows)
        

