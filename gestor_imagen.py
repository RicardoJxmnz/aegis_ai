import threading
import io
import torch
import numpy as np
from PIL import Image, ImageTk
import cv2
from facenet_pytorch import MTCNN, InceptionResnetV1
from tkinter import filedialog

class GestorImagen:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(GestorImagen, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        # Evitar reinicializar si ya fue inicializada
        if self._initialized:
            return

        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        # Carga diferida
        self.mtcnn = None
        self.model = None

        self.imagen_binaria = b''
        self.imagen_pil = None
        self.imagen_tk = None

        self._initialized = True

    def _cargar_modelos(self):
        if self.mtcnn is None:
            self.mtcnn = MTCNN(image_size=160, margin=0, device=self.device)
        if self.model is None:
            self.model = InceptionResnetV1(pretrained='vggface2').eval().to(self.device)

    def cargar_desde_archivo(self, label):
        archivo = filedialog.askopenfilename(filetypes=[("Imágenes", "*.jpg *.jpeg *.png *.bmp")])
        if archivo:
            self.imagen_pil = Image.open(archivo).resize((150, 150))
            self.imagen_tk = ImageTk.PhotoImage(self.imagen_pil)
            label.config(image=self.imagen_tk, text="")
            self._actualizar_binario()

    def capturar_desde_camara(self, label):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("No se pudo abrir la cámara")
            return

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            cv2.imshow("Presiona ESPACIO para tomar la foto", frame)
            key = cv2.waitKey(1)
            if key == 27:  # ESC
                break
            elif key == 32:  # ESPACIO
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.imagen_pil = Image.fromarray(frame_rgb).resize((150, 150))
                self.imagen_tk = ImageTk.PhotoImage(self.imagen_pil)
                label.config(image=self.imagen_tk, text="")
                self._actualizar_binario()
                break

        cap.release()
        cv2.destroyAllWindows()

    def _actualizar_binario(self):
        buffer = io.BytesIO()
        self.imagen_pil.save(buffer, format="PNG")
        self.imagen_binaria = buffer.getvalue()

    def obtener_embedding(self):
        self._cargar_modelos()  # Asegurar modelos cargados solo cuando se necesiten

        face = self.mtcnn(self.imagen_pil)
        if face is None:
            #print("No se detectó rostro.")
            return b''
        embedding = self.model(face.unsqueeze(0).to(self.device))
        embedding = embedding.detach().cpu()[0]
        return embedding.numpy().astype(np.float32).tobytes()
