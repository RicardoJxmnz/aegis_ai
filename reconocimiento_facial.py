import tkinter as tk
from gestor_imagen import GestorImagen
from conexion_bd import DatabaseConexion, ConsultasSQL
from config import COLOR_CUERPO_PRINCIPAL
from PIL import Image, ImageTk
import cv2
import numpy as np
import torch
import time
import io

class ReconocimientoFacial:
    def __init__(self, ventana_principal = None, frame = None):
        #Si se manda una ventana principal MRU trabajara como ventana secundaria
        if ventana_principal is not None and frame is None:
            self.root = tk.Toplevel(ventana_principal)
        #Si se manda un frame, MRU se colocara dentro de ese frame
        elif frame is not None and ventana_principal is None:
            self.root = frame
        #En caso contrario trabajara como una ventana principal
        else:
            self.root = tk.Tk()
            self.root.title("Reconocimiento Facial")
            self.root.geometry("900x550")

        self.gestor_imagen = GestorImagen()
        self.db = DatabaseConexion(ConsultasSQL.conn_str)
        self.entradas = {}

        # Lista para guardar embeddings y IDs
        # Ejemplo: [{"id": 123, "embedding": tensor}, ...]
        self.personas = []

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise RuntimeError("No se pudo abrir la cámara.")

        self._configurar_gui()
        self._cargar_embeddings_y_ids()

        self.ultimo_procesamiento = time.time()
        self.intervalo_procesamiento = 1.0  # segundos

        self.ventana_activa = True
        self.actualizar_video()

    def _configurar_gui(self):
        frame_superiro = tk.Frame(self.root)
        frame_superiro.pack(side="top", fill="x")

        self.label_estado = tk.Label(self.root, font=("Arial Black", 22, "bold"), fg="blue", bg=COLOR_CUERPO_PRINCIPAL)
        self.label_estado.pack(pady=40)

        # Crear frame izquierdo 
        frame_izquierda = tk.Frame(self.root, bg=COLOR_CUERPO_PRINCIPAL)
        frame_izquierda.pack(side="left", fill="both", expand=True)
        frame_izquierda.pack_propagate(False)

        # Crear frame derecho
        frame_derecha = tk.Frame(self.root, bg=COLOR_CUERPO_PRINCIPAL)
        frame_derecha.pack(side="right", fill="both", expand=True)

        # Cargar imagen
        imagen_pil = Image.open("./imagenes/sin_imagen.png")  # Reemplaza con tu archivo
        imagen_pil = imagen_pil.resize((300, 320))
        self.imagen_tk = ImageTk.PhotoImage(imagen_pil)

        # Crear label con la imagen
        self.label_imagen = tk.Label(frame_izquierda, image=self.imagen_tk)
        self.label_imagen.image = self.imagen_tk  # Para evitar que se borre la imagen

        self.label_imagen.place(relx=0.85, rely=0.5, anchor="e")  # Centrado vertical, alineado a la derecha  

        formulario = tk.Frame(frame_derecha, bg=COLOR_CUERPO_PRINCIPAL)
        formulario.place(relx=0.05, rely=0.5, anchor="w")  # Centrado verticalmente, alineado a la izquierda          

        campos = ["Nombre", "Matrícula", "Rol", "Titulo", "Grado", "Grupo", "Carrera", "Estatus"]

        for i, campo in enumerate(campos):
            etiqueta = tk.Label(formulario, text=campo + ":", anchor="w", font=("Arial", 13, "bold"), bg=COLOR_CUERPO_PRINCIPAL)
            etiqueta.grid(row=i, column=0, sticky="w", pady=8, padx=12)

            entrada = tk.Entry(formulario, width=35, font=("Arial", 13), bg=COLOR_CUERPO_PRINCIPAL)
            entrada.grid(row=i, column=1, pady=8, padx=12, ipady=4)

            self.entradas[campo] = entrada

        for entrada in self.entradas.values():
            entrada.config(state="disabled")

    def actualizar_video(self):
        if not self.ventana_activa:
            return
        ret, frame = self.cap.read()
        if ret:
            self.frame_actual = frame.copy()

            tiempo_actual = time.time()
            if tiempo_actual - self.ultimo_procesamiento >= self.intervalo_procesamiento:
                self.ultimo_procesamiento = tiempo_actual
                self.reconocer_en_tiempo_real(self.frame_actual)


        self.root.after(10, self.actualizar_video)

    def _cargar_embeddings_y_ids(self):
        consulta = "SELECT Id_Persona, Embedding FROM Personas WHERE Embedding IS NOT NULL"
        for row in self.db.ejecutar_consulta(consulta):
            id_persona, embedding_bytes = row
            if len(embedding_bytes) != 2048:
                continue
            vector = np.frombuffer(embedding_bytes, dtype=np.float32)
            if vector.size != 512:
                continue

            self.personas.append({
                "id": id_persona,
                "embedding": torch.tensor(vector)
            })

    def reconocer_en_tiempo_real(self, frame):
        if not hasattr(self, "label_estado") or not self.label_estado.winfo_exists():
            return 
    
        img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        self.gestor_imagen.imagen_pil = img_pil
        embedding_bytes = self.gestor_imagen.obtener_embedding()

        if not embedding_bytes:
            if hasattr(self, "label_estado") and self.label_estado.winfo_exists():
                self.label_estado.config(text="Sin rostro detectable", fg="gray")
            return

        nuevo_embedding = torch.tensor(np.frombuffer(embedding_bytes, dtype=np.float32))

        distancias = []
        for persona in self.personas:
            e = persona["embedding"]
            if e.shape != nuevo_embedding.shape:
                continue
            dist = torch.norm(e - nuevo_embedding).item()
            distancias.append((persona["id"], dist))

        if not distancias:
            self.label_estado.config(text="No hay datos válidos para comparar", fg="red")
            return

        id_coincidencia, min_dist = min(distancias, key=lambda x: x[1])

        if min_dist < 0.9:
            # Consulta rápida para obtener datos detallados
            consulta = """
            SELECT P.Imagen,
            P.Nombre + ' ' + P.APaterno + ' ' + P.AMaterno as Nombre,
            A.Matricula as Matricula,
            M.Id_Maestro as Id_Profesor,
            M.Titulo,
            A.Grado,
            A.Grupo,
            C.Nombre as Carrera,
            P.Activo as Estatus
            FROM Personas P
            LEFT JOIN Maestros M on M.Id_Persona = P.Id_Persona
            LEFT JOIN Alumnos A on A.Id_Persona = P.Id_Persona
            LEFT JOIN Carreras C on A.Id_Carrera = C.Id_Carrera
            WHERE P.Id_Persona = ?
            """
            resultados = self.db.ejecutar_consulta(consulta, (id_coincidencia,))

            if resultados:
                fila = resultados[0]  # Sólo uno por ID
                columnas = self.db.obtener_columnas()  # Usa tu método definido

                datos = dict(zip(columnas, fila))  # Convertimos a diccionario

                for campo, entry in self.entradas.items():
                    entry.config(state="normal")
                    valor = datos.get(campo)
                    if campo == "Estatus":
                        valor = "Activo" if valor else "Inactivo"
                    if campo == "Rol":
                        valor = "Alumno" if datos.get("Matricula") else "Maestro"
                    entry.delete(0, tk.END)
                    entry.insert(0, valor or "")
                    entry.config(state="readonly")
                
                # 1. Recuperar los bytes
                imagen_bytes = resultados[0][0]

                # 2. Convertir a imagen PIL
                imagen_pil = Image.open(io.BytesIO(imagen_bytes)).resize((300, 320))  # Ajusta el tamaño si deseas

                # 3. Convertir a formato compatible con Tkinter
                imagen_tk = ImageTk.PhotoImage(imagen_pil)

                # 4. Actualizar el label
                self.label_imagen.config(image=imagen_tk)
                self.label_imagen.image = imagen_tk  # <- Importante mantener la referencia

                self.label_estado.config(text="Autorizado", fg="green")
            else:
                self.label_estado.config(text="Datos no encontrados", fg="red")
        else:
            self.label_estado.config(text=f"Desconocido", fg="red")
            self.label_imagen.config(image=self.imagen_tk)
            self.label_imagen.image = self.imagen_tk 
            for entry in self.entradas.values():
                entry.config(state="normal")  
                entry.delete(0, tk.END)     
                entry.config(state="readonly")  

    def cerrar(self):
        self.cap.release()          # Libera la cámara
        cv2.destroyAllWindows()  # Cierra ventanas
        self.ventana_activa = False

    def mostrar(self):
        if isinstance(self.root, (tk.Tk, tk.Toplevel)):
            self.root.protocol("WM_DELETE_WINDOW", self.cerrar)
            self.root.mainloop()
        else:
            pass

#re = ReconocimientoFacial()
#re.mostrar()
