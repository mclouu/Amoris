from core.scanner import LocalAnimeScanner

if __name__ == "__main__":
    # Demande le PATH à l'utilisateur (ou test direct avec ton dossier)
    path_input = input("Entrez le PATH de vos animés : ").strip()

    # Nettoyage des guillemets éventuels si l'utilisateur fait un "copier en tant que chemin" sous Windows
    path_input = path_input.strip('"').strip("'")

    scanner = LocalAnimeScanner(path_input)

    if scanner.scan():
        scanner.save_cache()
        print("\n[BETA] Scan et indexation locale terminés. Prêt pour la suite !")