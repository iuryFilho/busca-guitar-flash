import os

import requests
from bs4 import BeautifulSoup

tSong = tuple[str, str]

tSongSet = set[tSong]

WHITE = "\033[97m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

BASE_URL = "https://guitarflash.com/custom/lista.asp"
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(ROOT_DIR, "song_list.csv")
LAST_SONG_PATH = os.path.join(ROOT_DIR, "last_song.txt")


def fetch_song_list_html(page: int = 0) -> str:
    response = requests.get(BASE_URL, params={"pag": page})
    if response.status_code == 200:
        response.encoding = "utf-8"
        return response.text
    else:
        print(f"Error fetching song list: {response.status_code}")
        return ""


def get_new_last_song(html_page: str) -> tSong:
    soup = BeautifulSoup(html_page, "html.parser")
    table = soup.find("table")
    if not table:
        print(f"{RED}Nenhuma tabela encontrada na página.{RESET}")
        return "", ""
    first_td = table.find("td")
    if not first_td:
        print(f"{RED}Nenhuma música encontrada na página.{RESET}")
        return "", ""

    name = first_td.get_text().strip()
    link = first_td.find("a")
    if not link:
        print(f"{RED}Nenhum link encontrada na página.{RESET}")
        return "", ""

    return name, link["href"]


def save_last_song(song: tSong):
    try:
        with open(LAST_SONG_PATH, "w", encoding="utf-8") as f:
            f.write("\t".join(song))
    except Exception as e:
        print(f"{RED}Erro ao salvar a última música: {e}{RESET}")


def load_last_song() -> tSong:
    if not os.path.exists(LAST_SONG_PATH):
        return "", ""
    try:
        with open(LAST_SONG_PATH, "r", encoding="utf-8") as f:
            return tuple(f.read().strip().split("\t"))
    except Exception as e:
        print(f"{RED}Erro ao ler o arquivo {LAST_SONG_PATH}: {e}{RESET}")
        return "", ""


def get_song_set(html_page: str, last_song: tSong) -> tuple[tSongSet, bool]:
    soup = BeautifulSoup(html_page, "html.parser")
    if soup.find("table") is None:
        return set(), False
    song_list: tSongSet = set()
    for tr in soup.find_all("tr"):
        td = tr.find("td")
        if td:
            name = td.get_text().strip()
            link = td.find("a")
            if link:
                new_song: tSong = (name, link["href"])
                if new_song == last_song:
                    return song_list, True
                song_list.add(new_song)
    return song_list, False


def save_song_set(song_list: tSongSet):
    with open(CSV_PATH, "w", encoding="utf-8") as f:
        f.write("Música\tLink\n")
        for song, link in song_list:
            f.write(f"{song}\t{link}\n")


def load_song_set() -> tSongSet:
    try:
        with open(CSV_PATH, "r", encoding="utf-8") as f:
            next(f)  # Skip header
            return {tuple(line.strip().split("\t")) for line in f}
    except Exception as e:
        print(f"{RED}Erro ao ler o arquivo {CSV_PATH}: {e}{RESET}")
        return set()


def search_song(song_name: str, song_set: tSongSet) -> tSongSet:
    results = set()
    for song, link in song_set:
        if song_name.lower() in song.lower():
            results.add((song, link))
    return results


def inf_gen(stop=None):
    i = 0
    while stop is None or i < stop:
        yield i
        i += 1
