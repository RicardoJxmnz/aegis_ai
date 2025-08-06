import cv2
import threading
import tkinter as tk
from tkinter import Label
from PIL import Image, ImageTk
from ultralytics import YOLO
from gestor_imagen import GestorImagen
from config import COLOR_CUERPO_PRINCIPAL

class DeteccionIntrusos:
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
            self.root.title("Deteccion de Intrusos")
            self.root.geometry("900x550")

        self.etiqueta_estado = Label(self.root, text="Inicializando...", font=("Arial Black", 22, "bold"), fg="blue", bg=COLOR_CUERPO_PRINCIPAL)
        self.etiqueta_estado.pack()

        self.panel_video = Label(self.root)
        self.panel_video.pack()

        self.gestor = GestorImagen()
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.etiqueta_estado.config(text="No se pudo abrir la cámara")
            return

        self.modelo_yolo = YOLO("yolov8n.pt")

        self.ejecutando = True
        self.hilo = threading.Thread(target=self.procesar_video, daemon=True)
        self.hilo.start()


    def procesar_video(self):
        while self.ejecutando:
            ret, frame = self.cap.read()
            if not ret:
                continue

            resultados = self.modelo_yolo(frame, verbose=False)[0]

            # Filtrar solo personas
            personas = [box for box in resultados.boxes if int(box.cls[0]) == 0]

            # Dibujar solo personas en el frame
            for box in personas:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, "Persona", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            estado = "Intruso Detectado" if personas else "Zona Libre"
            color = "red" if personas else "green"

            try:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.gestor.imagen_pil = Image.fromarray(frame_rgb)
                self.gestor.imagen_tk = ImageTk.PhotoImage(self.gestor.imagen_pil)

                if self.panel_video.winfo_exists():
                    self.panel_video.imgtk = self.gestor.imagen_tk
                    self.panel_video.config(image=self.gestor.imagen_tk)

                if self.etiqueta_estado.winfo_exists():
                    self.etiqueta_estado.config(text=estado, pady=10, fg=color)

            except RuntimeError:
                break


    def mostrar(self):
        if isinstance(self.root, (tk.Tk, tk.Toplevel)):
            self.root.protocol("WM_DELETE_WINDOW", self.cerrar)
            self.root.mainloop()
        else:
            pass
    
    def cerrar(self):
        self.ejecutando = False
        self.root.after(100, self._liberar_recursos)

    def _liberar_recursos(self):
        if self.cap and self.cap.isOpened():
            self.cap.release()
