from PyQt6.QtCore import QThread, pyqtSignal
import os
import json
import urllib.request


class CoverDownloaderThread(QThread):
    status_signal = pyqtSignal(str)
    # Nouveau signal : il envoie l'ID (ex: "12345") de l'image prête
    image_downloaded_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, json_path, output_dir):
        super().__init__()
        self.json_path = json_path
        self.output_dir = output_dir

    def run(self):
        if not os.path.exists(self.json_path):
            return

        os.makedirs(self.output_dir, exist_ok=True)

        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            return

        items = data.get("data", [])

        for item in items:
            node = item.get("node", {})
            anime_id = node.get("id")
            title = node.get("title", "unknown")

            main_picture = node.get("main_picture", {})
            large_url = main_picture.get("large")

            if not anime_id or not large_url:
                continue

            filepath = os.path.join(self.output_dir, f"{anime_id}.jpg")

            # Si l'image existe déjà, on ne fait rien
            if os.path.exists(filepath):
                continue

            self.status_signal.emit(f"Téléchargement de : {title}...")
            try:
                req = urllib.request.Request(
                    large_url,
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                with urllib.request.urlopen(req) as response, open(filepath, 'wb') as out_file:
                    out_file.write(response.read())

                # SUCCÈS : On prévient l'interface qu'une nouvelle image est dispo pour cet ID !
                self.image_downloaded_signal.emit(str(anime_id))

            except Exception as e:
                print(f"[!] Échec pour {title}: {e}")

        self.status_signal.emit("Bibliothèque d'images à jour.")
        self.finished_signal.emit()