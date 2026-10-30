import psutil
import ctypes
import re


class VideoDetector:
    def __init__(self, target_process="PotPlayerMini64.exe"):
        self.target_process = target_process.lower()

    @staticmethod
    def _get_window_titles_for_pid(target_pid):
        """
        Utilise l'API Windows via ctypes pour récupérer les titres des fenêtres 
        associées à un PID donné.
        """
        titles = []
        enum_windows = ctypes.windll.user32.EnumWindows
        enum_windows_proc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_long)
        get_window_thread_process_id = ctypes.windll.user32.GetWindowThreadProcessId
        is_window_visible = ctypes.windll.user32.IsWindowVisible
        get_window_text_length_w = ctypes.windll.user32.GetWindowTextLengthW
        get_window_text_w = ctypes.windll.user32.GetWindowTextW

        def foreach_window(hwnd, lparam):
            if is_window_visible(hwnd):
                pid = ctypes.c_ulong()
                get_window_thread_process_id(hwnd, ctypes.byref(pid))
                if pid.value == target_pid:
                    length = get_window_text_length_w(hwnd)
                    if length > 0:
                        buff = ctypes.create_unicode_buffer(length + 1)
                        get_window_text_w(hwnd, buff, length + 1)
                        if buff.value.strip():
                            titles.append(buff.value)
            return True

        enum_windows(enum_windows_proc(foreach_window), 0)
        return titles

    def get_active_media_title(self):
        """
        Parcourt les processus actifs pour trouver PotPlayer et extraire 
        le titre de sa fenêtre en cours de lecture.
        """
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                proc_name = proc.info['name']
                if proc_name and self.target_process in proc_name.lower():
                    pid = proc.info['pid']
                    titles = self._get_window_titles_for_pid(pid)
                    for title in titles:
                        if title and ("PotPlayer" in title or len(titles) > 0):
                            return title
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return None

    def parse_anime_filename(self, raw_title):
        """
        Extrait le nom de l'animé et le numéro d'épisode à partir du titre brut.
        Gère aussi bien les formats S01E03 (Tsundere-Raws) que - 07 (Erai-raws).
        """
        if not raw_title:
            return None, None

        # Nettoyage du suffixe du lecteur
        clean_title = re.sub(r'\s*-\s*PotPlayer$', '', raw_title, flags=re.IGNORECASE)

        # Nettoyage des extensions de fichiers
        clean_title = re.sub(r'\.(mkv|mp4|avi|webm)', '', clean_title, flags=re.IGNORECASE)

        episode = "1"
        anime_name = clean_title

        # 1. Recherche d'un format type "S01E03" ou "s1e3" (très courant chez Tsundere-Raws)
        s_e_match = re.search(r'[sS](\d+)[eE](\d+)', clean_title)
        if s_e_match:
            episode = s_e_match.group(2)
            anime_name = clean_title[:s_e_match.start()].strip()
        else:
            # 2. Sinon, format classique avec tiret (ex: " - 07")
            match = re.search(r'[-–]\s*(\d+)(?:\s*v\d+)?\b', clean_title)
            if match:
                episode = match.group(1)

            clean_title_no_tags = re.sub(r'\[.*?]', '', clean_title)
            anime_name = clean_title_no_tags.split('-')[0].strip()

        anime_name = re.sub(r'[-–]+$', '', anime_name).strip()

        return anime_name, episode


if __name__ == "__main__":
    detector = VideoDetector()
    print("🔍 Radar de détection initialisé pour PotPlayer...")
    raw_title = detector.get_active_media_title()

    if raw_title:
        print(f"🎬 Fenêtre détectée : {raw_title}")
        anime_name, ep_num = detector.parse_anime_filename(raw_title)
        print(f"✨ Résultat parsé -> Animé : {anime_name} | Épisode : {ep_num}")
    else:
        print("⏳ Aucun lecteur PotPlayer actif trouvé.")