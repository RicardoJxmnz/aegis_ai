import tkinter as tk
from interfaz_crud import InterfazCrud
from conexion_bd import ConsultasSQL
from reconocimiento_facial import ReconocimientoFacial
from PIL import Image, ImageTk

fondo_original = Image.open("./imagenes/logo.png")

def redimensionar_fondo(event):
    if not label_fondo.winfo_exists():
        return
    nueva_img = fondo_original.resize((event.width, event.height))  # Usa la original, no el PhotoImage
    nueva_foto = ImageTk.PhotoImage(nueva_img)
    label_fondo.configure(image=nueva_foto)
    label_fondo.image = nueva_foto  # Guardar referencia

# Variable global para el reconocimiento facial
reconocimiento = None

def cerrar_reconocimiento_si_existe():
    global reconocimiento
    if reconocimiento is not None:
        reconocimiento.cerrar()  # método que libera cámara y destruye ventana/frame
        reconocimiento = None

def abrir_reconocimiento_facial():
    global reconocimiento
    # Antes de abrir, cerrar si ya está abierto
    cerrar_reconocimiento_si_existe()
    
    for widget in frame_contenido.winfo_children():
        widget.destroy()
    reconocimiento = ReconocimientoFacial(frame=frame_contenido)
    reconocimiento.mostrar()  # si usas mainloop, tal vez solo configurar para no bloquear

def abrir_alumnos():
    cerrar_reconocimiento_si_existe()
    for widget in frame_contenido.winfo_children():
        widget.destroy()
    alumnos = InterfazCrud(frame=frame_contenido)
    alumnos.mostrar_tabla("Alumnos", ConsultasSQL.consulta_alumnos)

def abrir_maestros():
    cerrar_reconocimiento_si_existe()
    for widget in frame_contenido.winfo_children():
        widget.destroy()
    profesores = InterfazCrud(frame=frame_contenido)
    profesores.mostrar_tabla("Maestros", ConsultasSQL.consulta_maestros)

def abrir_carreras():
    cerrar_reconocimiento_si_existe()
    for widget in frame_contenido.winfo_children():
        widget.destroy()
    carreras = InterfazCrud(frame=frame_contenido)
    carreras.mostrar_tabla("Carreras", ConsultasSQL.consulta_carreras)

def abrir_materias():
    cerrar_reconocimiento_si_existe()
    for widget in frame_contenido.winfo_children():
        widget.destroy()
    materias = InterfazCrud(frame=frame_contenido)
    materias.mostrar_tabla("Materias", ConsultasSQL.consulta_materias)

# Crear ventana principal
ventana = tk.Tk()
ventana.title("AegisIA")
ventana.geometry("900x550")

frame_contenido = tk.Frame(ventana)
frame_contenido.pack(fill=tk.BOTH, expand=True)


# Crear el label de fondo con una primera versión redimensionada
fondo_inicial = ImageTk.PhotoImage(fondo_original.resize((900, 550)))
label_fondo = tk.Label(frame_contenido, image=fondo_inicial)
label_fondo.place(x=0, y=0, relwidth=1, relheight=1)
label_fondo.image = fondo_inicial  # Guardar referencia para evitar borrado

# Asociar el evento de redimensionamiento
frame_contenido.bind("<Configure>", redimensionar_fondo)

barra_menu = tk.Menu(ventana)
ventana.config(menu=barra_menu)

menu_inicio = tk.Menu(barra_menu, tearoff=0)
barra_menu.add_command(label="Inicio", command=abrir_reconocimiento_facial)

menu_opciones = tk.Menu(barra_menu, tearoff=0)
barra_menu.add_cascade(label="Registros", menu=menu_opciones)
menu_opciones.add_command(label="Alumnos", command=abrir_alumnos)
menu_opciones.add_command(label="Profesores", command=abrir_maestros)
menu_opciones.add_command(label="Carreras", command=abrir_carreras)
menu_opciones.add_command(label="Materias", command=abrir_materias)

ventana.mainloop()

