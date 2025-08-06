from tkinter import Tk, font

root = Tk()
fuentes_disponibles = font.families()
for f in fuentes_disponibles:
    if "awesome" in f.lower():
        print(f"Fuente detectada: {f}")