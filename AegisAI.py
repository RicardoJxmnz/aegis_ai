import tkinter as tk
from tkinter import font
from config import COLOR_BARRA_SUPERIOR, COLOR_MENU_LATERAL, COLOR_CUERPO_PRINCIPAL, COLOR_MENU_CURSOR_ENCIMA
import util_ventana as util_ventana
import util_imagenes as util_img
from interfaz_crud import InterfazCrud
from conexion_bd import ConsultasSQL
from deteccion_intrusos import DeteccionIntrusos
from reconocimiento_facial import ReconocimientoFacial

class AegisAI(tk.Tk):

    def __init__(self):
        super().__init__()
        self.logo = util_img.leer_imagen("./imagenes/logo.png", (560, 400))
        self.perfil = util_img.leer_imagen("./imagenes/Perfil.png", (100, 100))
        self.config_window()
        self.paneles()
        self.controles_barra_superior()        
        self.controles_menu_lateral()
        self.controles_cuerpo()
        # Variable global para el reconocimiento facial
        self.reconocimiento = None
    
    def config_window(self):
        # Configuración inicial de la ventana
        self.title('Python GUI')
        self.iconbitmap("./imagenes/logo.ico")
        w, h = 1024, 600        
        util_ventana.centrar_ventana(self, w, h)        

    def paneles(self):        
         # Crear paneles: barra superior, menú lateral y cuerpo principal
        self.barra_superior = tk.Frame(
            self, bg=COLOR_BARRA_SUPERIOR, height=50)
        self.barra_superior.pack(side=tk.TOP, fill='both')      

        self.menu_lateral = tk.Frame(self, bg=COLOR_MENU_LATERAL, width=150)
        self.menu_lateral.pack(side=tk.LEFT, fill='both', expand=False) 
        
        self.cuerpo_principal = tk.Frame(
            self, bg=COLOR_CUERPO_PRINCIPAL)
        self.cuerpo_principal.pack(side=tk.RIGHT, fill='both', expand=True)
    
    def controles_barra_superior(self):
        # Configuración de la barra superior
        font_awesome = font.Font(family='FontAwesome', size=12)

        # Botón del menú lateral
        self.buttonMenuLateral = tk.Button(self.barra_superior, text="☰", font=("Arial", 16),
                                           command=self.toggle_panel, bd=0, bg=COLOR_BARRA_SUPERIOR, fg="white")
        self.buttonMenuLateral.pack(side=tk.LEFT)

        # Etiqueta de título
        self.labelTitulo = tk.Label(self.barra_superior, text="AegisAI")
        self.labelTitulo.config(fg="#fff", font=(
            "Roboto", 15), bg=COLOR_BARRA_SUPERIOR, pady=1, width=10)
        self.labelTitulo.pack(side=tk.LEFT)


        # Etiqueta de informacion
        self.labelTitulo = tk.Label(
            self.barra_superior, text="servicio@ageisIA.mx")
        self.labelTitulo.config(fg="#fff", font=(
            "Roboto", 10), bg=COLOR_BARRA_SUPERIOR, padx=10, width=20)
        self.labelTitulo.pack(side=tk.RIGHT)
    
    def controles_menu_lateral(self):
        # Configuración del menú lateral
        ancho_menu = 20
        alto_menu = 2
        font_awesome = font.Font(family='FontAwesome', size=15)
         
         # Etiqueta de perfil
        self.labelPerfil = tk.Label(
            self.menu_lateral, image=self.perfil, bg=COLOR_MENU_LATERAL)
        self.labelPerfil.pack(side=tk.TOP, pady=10)

        # Botones del menú lateral
        
        self.buttonDashBoard = tk.Button(self.menu_lateral, command=self.abrir_inicio)        
        self.buttonProfile = tk.Button(self.menu_lateral, command=self.abrir_reconocimiento_facial)
        self.buttonIntruso = tk.Button(self.menu_lateral, command=self.abrir_deteccion_intrusos)         
        self.buttonPicture = tk.Button(self.menu_lateral, command=self.abrir_alumnos)
        self.buttonInfo = tk.Button(self.menu_lateral, command=self.abrir_maestros)        
        self.buttonSettings = tk.Button(self.menu_lateral, command=self.abrir_materias)

        buttons_info = [
            ("Inicio", "\uf109", self.buttonDashBoard),
            ("Autorizacion", "\uf06e", self.buttonProfile),
            ("Intrusos", "\uf3ed", self.buttonIntruso),
            ("Alumnos", "\uf2c2", self.buttonPicture),
            ("Maestros", "\uf47f", self.buttonInfo),
            ("Materias", "\uf51b", self.buttonSettings)
        ]

        for text, icon, button in buttons_info:
            self.configurar_boton_menu(button, text, icon, font_awesome, ancho_menu, alto_menu)                    
    
    def controles_cuerpo(self):
        # Imagen en el cuerpo principal
        label = tk.Label(self.cuerpo_principal, image=self.logo,
                         bg=COLOR_CUERPO_PRINCIPAL)
        label.place(x=0, y=0, relwidth=1, relheight=1)

    def configurar_boton_menu(self, button, text, icon, font_awesome, ancho_menu, alto_menu):
        button.config(text=f"  {icon}    {text}", anchor="w", font=font_awesome,
                      bd=0, bg=COLOR_MENU_LATERAL, fg="white", width=ancho_menu, height=alto_menu)
        button.pack(side=tk.TOP)
        self.bind_hover_events(button)

    def bind_hover_events(self, button):
        # Asociar eventos Enter y Leave con la función dinámica
        button.bind("<Enter>", lambda event: self.on_enter(event, button))
        button.bind("<Leave>", lambda event: self.on_leave(event, button))

    def on_enter(self, event, button):
        # Cambiar estilo al pasar el ratón por encima
        button.config(bg=COLOR_MENU_CURSOR_ENCIMA, fg='white')

    def on_leave(self, event, button):
        # Restaurar estilo al salir el ratón
        button.config(bg=COLOR_MENU_LATERAL, fg='white')

    def toggle_panel(self):
        # Alternar visibilidad del menú lateral
        if self.menu_lateral.winfo_ismapped():
            self.menu_lateral.pack_forget()
        else:
            self.menu_lateral.pack(side=tk.LEFT, fill='y')

    def cerrar_reconocimiento_si_existe(self):
        if self.reconocimiento is not None:
            self.reconocimiento.cerrar()  # método que libera cámara y destruye ventana/frame
            self.reconocimiento = None
    
    def abrir_inicio(self):
        self.cerrar_reconocimiento_si_existe()
        if hasattr(self, 'cuerpo_principal') and self.cuerpo_principal.winfo_exists():
            for widget in self.cuerpo_principal.winfo_children():
                widget.destroy()
        self.controles_cuerpo()

    def abrir_reconocimiento_facial(self):
        self.cerrar_reconocimiento_si_existe()
        if hasattr(self, 'cuerpo_principal') and self.cuerpo_principal.winfo_exists():
            for widget in self.cuerpo_principal.winfo_children():
                widget.destroy()
        self.reconocimiento = ReconocimientoFacial(frame=self.cuerpo_principal)
        self.reconocimiento.mostrar()  # si usas mainloop, tal vez solo configurar para no bloquear
    
    def abrir_deteccion_intrusos(self):
        self.cerrar_reconocimiento_si_existe()
        if hasattr(self, 'cuerpo_principal') and self.cuerpo_principal.winfo_exists():
            for widget in self.cuerpo_principal.winfo_children():
                widget.destroy()
        self.reconocimiento = DeteccionIntrusos(frame=self.cuerpo_principal)
        self.reconocimiento.mostrar()

    def abrir_alumnos(self):
        self.cerrar_reconocimiento_si_existe()
        if hasattr(self, 'cuerpo_principal') and self.cuerpo_principal.winfo_exists():
            for widget in self.cuerpo_principal.winfo_children():
                widget.destroy()
        alumnos = InterfazCrud(frame=self.cuerpo_principal)
        alumnos.mostrar_tabla("Alumnos", ConsultasSQL.consulta_alumnos)

    def abrir_maestros(self):
        self.cerrar_reconocimiento_si_existe()
        if hasattr(self, 'cuerpo_principal') and self.cuerpo_principal.winfo_exists():
            for widget in self.cuerpo_principal.winfo_children():
                widget.destroy()
        profesores = InterfazCrud(frame=self.cuerpo_principal)
        profesores.mostrar_tabla("Maestros", ConsultasSQL.consulta_maestros)

    def abrir_carreras(self):
        self.cerrar_reconocimiento_si_existe()
        if hasattr(self, 'cuerpo_principal') and self.cuerpo_principal.winfo_exists():
            for widget in self.cuerpo_principal.winfo_children():
                widget.destroy()
        carreras = InterfazCrud(frame=self.cuerpo_principal)
        carreras.mostrar_tabla("Carreras", ConsultasSQL.consulta_carreras)

    def abrir_materias(self):
        self.cerrar_reconocimiento_si_existe()
        if hasattr(self, 'cuerpo_principal') and self.cuerpo_principal.winfo_exists():
            for widget in self.cuerpo_principal.winfo_children():
                widget.destroy()
        materias = InterfazCrud(frame=self.cuerpo_principal)
        materias.mostrar_tabla("Materias", ConsultasSQL.consulta_materias)

app = AegisAI()
app.mainloop()