import subprocess
import sys
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from moviepy.editor import VideoFileClip
import time

# Liste des bibliothèques nécessaires
required_libraries = ['moviepy', 'tkinter']

# Fonction pour installer les bibliothèques manquantes
def install_libraries():
    for library in required_libraries:
        try:
            # Vérifie si la bibliothèque est déjà installée
            __import__(library)
        except ImportError:
            print(f"Installation de {library}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", library])

# Installation des bibliothèques nécessaires avant d'exécuter le reste du code
install_libraries()

# Redirection de la sortie standard vers le widget Text de tkinter
class RedirectText:
    def __init__(self, widget):
        self.widget = widget

    def write(self, message):
        self.widget.config(state=tk.NORMAL)
        self.widget.insert(tk.END, message)
        self.widget.config(state=tk.DISABLED)
        self.widget.yview(tk.END)

    def flush(self):  # Méthode nécessaire pour rendre compatible avec sys.stdout
        pass

class VideoCutterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Cutter")
        self.root.geometry("700x600")
        self.root.configure(bg="#000000")  # Fond noir

        # Couleurs
        text_color = "#FFFFFF"  # Blanc
        accent_color = "#FF0000"  # Bleu ciel

        # ASCII Art ZX COBRA en bleu ciel et centré
        ascii_art = """
 /$$$$$$$$ /$$   /$$        /$$$$$$   /$$$$$$  /$$$$$$$  /$$$$$$$   /$$$$$$ 
|_____ $$ | $$  / $$       /$$__  $$ /$$__  $$| $$__  $$| $$__  $$ /$$__  $$ 
     /$$/ |  $$/ $$/      | $$  \__/| $$  \ $$| $$  \ $$| $$  \ $$| $$  \ $$  
    /$$/   \  $$$$/       | $$      | $$  | $$| $$$$$$$ | $$$$$$$/| $$$$$$$$ 
   /$$/     >$$  $$       | $$      | $$  | $$| $$__  $$| $$__  $$| $$__  $$  
  /$$/     /$$/\  $$      | $$    $$| $$  | $$| $$  \ $$| $$  \ $$| $$  | $$  
 /$$$$$$$$| $$  \ $$      |  $$$$$$/|  $$$$$$/| $$$$$$$/| $$  | $$| $$  | $$  
|________/|__/  |__/       \______/  \______/ |_______/ |__/  |__/|__/|__/|__/
"""
        self.ascii_label = tk.Label(root, text=ascii_art, fg=accent_color, bg="#000000", font=("Courier", 10), justify="center")
        self.ascii_label.pack(pady=5)

        self.label = tk.Label(root, text="Choisissez une vidéo à découper:", fg=text_color, bg="#000000")
        self.label.pack(pady=5)

        self.upload_button = tk.Button(root, text="Télécharger la vidéo", command=self.upload_video, bg="#FF0000", fg="white")
        self.upload_button.pack(pady=5)

        self.start_time_label = tk.Label(root, text="Début du découpage (en secondes) :", fg=text_color, bg="#000000")
        self.start_time_label.pack(pady=2)

        self.start_time_entry = tk.Entry(root, width=10, bg="white", fg="black")
        self.start_time_entry.pack(pady=2)
        self.start_time_entry.insert(0, "0")

        self.duration_label = tk.Label(root, text="Durée de chaque extrait (en secondes):", fg=text_color, bg="#000000")
        self.duration_label.pack(pady=2)

        self.duration_entry = tk.Entry(root, width=10, bg="white", fg="black")
        self.duration_entry.pack(pady=2)
        self.duration_entry.insert(0, "60")

        # Cases à cocher pour le format
        self.format_9_16_var = tk.BooleanVar()
        self.format_16_9_var = tk.BooleanVar()

        self.format_9_16_check = tk.Checkbutton(root, text="Format 9:16", variable=self.format_9_16_var, command=self.ensure_one_format, fg=text_color, bg="#000000", selectcolor="#000000")
        self.format_9_16_check.pack(pady=2)

        self.format_16_9_check = tk.Checkbutton(root, text="Format 16:9", variable=self.format_16_9_var, command=self.ensure_one_format, fg=text_color, bg="#000000", selectcolor="#000000")
        self.format_16_9_check.pack(pady=2)

        # Bouton pour sélectionner le dossier de destination
        self.select_folder_button = tk.Button(root, text="Choisir le dossier de destination", command=self.select_output_folder, bg="#FF0000", fg="white")
        self.select_folder_button.pack(pady=5)

        self.output_folder = "extraits"  # Dossier de destination par défaut

        self.cut_button = tk.Button(root, text="Découper", command=self.start_cutting_thread, state=tk.DISABLED, bg="#FF0000", fg="white")  # Texte en blanc maintenant
        self.cut_button.pack(pady=5)

        # Widget Text pour afficher les logs du terminal
        self.log_text = tk.Text(root, width=80, height=20, bg="black", fg="white", wrap=tk.WORD, state=tk.DISABLED)
        self.log_text.pack(pady=10)

        # Redirige stdout vers notre widget Text
        sys.stdout = RedirectText(self.log_text)

    def upload_video(self):
        self.video_path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4;*.avi;*.mov;*.mkv")])
        if self.video_path:
            self.label.config(text=os.path.basename(self.video_path))
            self.cut_button.config(state=tk.NORMAL)

    def start_cutting_thread(self):
        threading.Thread(target=self.cut_video, daemon=True).start()

    def ensure_one_format(self):
        """ Empêche l'utilisateur de cocher les deux formats en même temps. """
        if self.format_9_16_var.get():
            self.format_16_9_var.set(False)
        if self.format_16_9_var.get():
            self.format_9_16_var.set(False)

    def select_output_folder(self):
        """ Ouvre une boîte de dialogue pour choisir un dossier de sortie. """
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.output_folder = folder_selected
            messagebox.showinfo("Dossier sélectionné", f"Dossier de sortie : {self.output_folder}")

    def cut_video(self):
        if not self.video_path:
            print("Erreur : Aucune vidéo sélectionnée.")
            return

        os.makedirs(self.output_folder, exist_ok=True)

        video = VideoFileClip(self.video_path)
        duration = int(video.duration)
        print(f"Durée totale: {duration} secondes")

        try:
            segment_duration = int(self.duration_entry.get())
            start_time = int(self.start_time_entry.get())
        except ValueError:
            print("Erreur : Veuillez entrer des valeurs valides.")
            return

        if start_time >= duration:
            print("Erreur : Le temps de début est supérieur à la durée de la vidéo.")
            return

        num_segments = (duration - start_time) // segment_duration + (1 if (duration - start_time) % segment_duration > 0 else 0)
        estimated_time = segment_duration

        print(f"Temps estimé par extrait: {estimated_time} secondes")

        process_start_time = time.time()

        for i in range(num_segments):
            segment_start_time = start_time + i * segment_duration
            segment_end_time = min(start_time + (i + 1) * segment_duration, duration)
            segment = video.subclip(segment_start_time, segment_end_time)

            # Récupérer la résolution originale
            original_width, original_height = segment.size

            # Appliquer le recadrage si un format est sélectionné
            if self.format_9_16_var.get():
                new_width = original_height * (9 / 16)
                crop_x1 = (original_width - new_width) / 2
                crop_x2 = crop_x1 + new_width
                segment = segment.crop(x1=crop_x1, x2=crop_x2)

            elif self.format_16_9_var.get():
                new_height = original_width * (9 / 16)
                crop_y1 = (original_height - new_height) / 2
                crop_y2 = crop_y1 + new_height
                segment = segment.crop(y1=crop_y1, y2=crop_y2)

            segment_filename = os.path.join(self.output_folder, f"extrait_{i + 1}.mp4")

            segment.write_videofile(segment_filename, codec="libx264", audio_codec="aac", preset="superfast", threads=4, verbose=False)

            print(f"Extrait {i + 1}/{num_segments} enregistré: {segment_filename}")
            remaining_time = estimated_time * (num_segments - (i + 1))
            print(f"Temps restant estimé: {int(remaining_time)} secondes")

        video.close()
        print(f"Découpage terminé! {num_segments} extraits enregistrés dans '{self.output_folder}'.")

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoCutterApp(root)
    root.mainloop()