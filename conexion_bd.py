import pyodbc

class DatabaseConexion:
    def __init__(self, cad_conexion):
        self.conn = pyodbc.conn = pyodbc.connect(cad_conexion)
        self.cursor = self.conn.cursor()

    def ejecutar_consulta(self, consulta, parametros=None):
        self.cursor.execute(consulta, parametros or [])
        return self.cursor.fetchall()

    def obtener_columnas(self):
        return [col[0] for col in self.cursor.description]

    def commit(self):
        self.conn.commit()

class ConsultasSQL:
    conn_str = (
            "DRIVER={ODBC Driver 18 for SQL Server};"
            "SERVER=RICARDO;"
            "DATABASE=Escuela;"
            "Trusted_Connection=yes;"
            "Encrypt=yes;"
            "TrustServerCertificate=yes;"
        )

    consulta_alumnos = """
        SELECT A.Matricula AS Matricula, P.Nombre, P.APaterno AS Apellido_Paterno, 
        P.AMaterno AS Apellido_Materno, P.Fecha_Nacimiento, P.Sexo, A.Grado, A.Grupo,
        C.Nombre AS Carrera, P.Activo
        FROM Alumnos A
        JOIN Personas P ON A.Id_Persona = P.Id_Persona
        JOIN Carreras C ON A.Id_Carrera = C.Id_Carrera;
    """

    consulta_maestros = """
        SELECT M.Id_Maestro, P.Nombre, P.APaterno AS Apellido_Paterno, P.AMaterno AS Apellido_Materno,
        P.Fecha_Nacimiento, P.Sexo, M.Titulo, P.Activo
        FROM Maestros M
        JOIN Personas P ON P.Id_Persona = M.Id_Persona;
    """

    consulta_carreras = "SELECT Nombre AS Nombre_Carrera FROM Carreras"

    consulta_materias = """
        SELECT M.Id_Materia AS Clave, M.Nombre, M.Hora_Inicio, M.Hora_Fin,
        P.Nombre + ' ' + P.APaterno + ' ' + P.AMaterno AS Profesor
        FROM Materias M
        JOIN Maestros Ma ON Ma.Id_Maestro = M.Id_Maestro
        JOIN Personas P ON P.Id_Persona = Ma.Id_Persona;
    """

class GestorTablas:
    def __init__(self, db: DatabaseConexion):
        self.db = db

    def insertar_persona(self, datos, imagen, embedding):
        activo = 1 if datos.get("Activo", "").lower() == "activo" else 0
        self.db.cursor.execute("""
            INSERT INTO Personas (Nombre, APaterno, AMaterno, Fecha_Nacimiento, Sexo, Imagen, Embedding, Activo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            SELECT SCOPE_IDENTITY();""",
            (
                datos.get("Nombre"),
                datos.get("Apellido_Paterno"),
                datos.get("Apellido_Materno"),
                datos.get("Fecha_Nacimiento"),
                datos.get("Sexo"),
                imagen,
                embedding,
                activo,
            )
        )
        if self.db.cursor.nextset():
            id_persona = self.db.cursor.fetchone()[0]
        self.db.commit()
        return id_persona
    
    def insertar_alumno(self, datos, id_persona):
        id_carrera = self.db.cursor.execute(
            "SELECT Id_Carrera FROM Carreras WHERE Nombre = ?", 
            (datos.get("Carrera"),)
        ).fetchone()[0]

        self.db.cursor.execute("""
            INSERT INTO Alumnos (Matricula, Id_Persona, Grado, Grupo, Id_Carrera)
            VALUES (?, ?, ?, ?, ?)""",
            (
                datos.get("Matricula"),
                id_persona,
                datos.get("Grado"),
                datos.get("Grupo"),
                id_carrera
            )
        )
        self.db.commit()

    def insertar_maestro(self, datos, id_persona):
        self.db.cursor.execute("""
            INSERT INTO Maestros (Id_Persona, Titulo)
            VALUES (?, ?)""",
            (
                id_persona,
                datos.get("Titulo"),
            )
        )
        self.db.commit()
     
    def actualizar_persona(self, id_persona, datos):
        activo = 1 if datos.get("Activo", "").lower() == "activo" else 0

        self.db.cursor.execute("""
            UPDATE Personas
            SET Nombre = ?, APaterno = ?, AMaterno = ?, Fecha_Nacimiento = ?, Sexo = ?, Activo = ?
            WHERE Id_Persona = ?
        """, (
            datos.get("Nombre"),
            datos.get("Apellido_Paterno"),
            datos.get("Apellido_Materno"),
            datos.get("Fecha_Nacimiento"),
            datos.get("Sexo"),
            activo,
            id_persona
        ))
        self.db.commit()

    def actualizar_alumno(self, matricula, datos):
        # Obtener Id_Persona vinculado a la matrícula del alumno
        resultado = self.db.cursor.execute(
            "SELECT Id_Persona FROM Alumnos WHERE Matricula = ?",
            (matricula,)
        ).fetchone()

        if resultado is None:
            raise Exception("No se encontró el alumno con la matrícula proporcionada.")

        id_persona = resultado[0]

        # Actualizar tabla Personas
        self.actualizar_persona(id_persona, datos)

        # Obtener nuevo Id_Carrera
        id_carrera = self.db.cursor.execute(
            "SELECT Id_Carrera FROM Carreras WHERE Nombre = ?",
            (datos.get("Carrera"),)
        ).fetchone()[0]

        # Actualizar tabla Alumnos
        self.db.cursor.execute("""
            UPDATE Alumnos
            SET Grado = ?, Grupo = ?, Id_Carrera = ?
            WHERE Matricula = ?
        """, (
            datos.get("Grado"),
            datos.get("Grupo"),
            id_carrera,
            matricula
        ))
        self.db.commit()


    def actualizar_maestro(self, id_maestro, datos):
        # Obtener Id_Persona vinculado al maestro
        resultado = self.db.cursor.execute(
            "SELECT Id_Persona FROM Maestros WHERE Id_Maestro = ?",
            (id_maestro,)
        ).fetchone()

        if resultado is None:
            raise Exception("No se encontró el maestro con el ID proporcionado.")

        id_persona = resultado[0]

        # Actualizar tabla Personas
        self.actualizar_persona(id_persona, datos)

        # Actualizar tabla Maestros
        self.db.cursor.execute("""
            UPDATE Maestros
            SET Titulo = ?
            WHERE Id_Maestro = ?
        """, (
            datos.get("Titulo"),
            id_maestro
        ))
        self.db.commit()
