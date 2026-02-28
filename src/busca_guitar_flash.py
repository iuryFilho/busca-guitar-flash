import os

import requests
from bs4 import BeautifulSoup

tSongSet = set[tuple[str, str]]

WHITE = "\033[97m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

BASE_URL = "https://guitarflash.com/custom/lista.asp"
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(ROOT_DIR, "song_list.csv")


def fetch_song_list_html(page: int = 0) -> str:
    response = requests.get(BASE_URL, params={"pag": page})
    if response.status_code == 200:
        response.encoding = "utf-8"
        return response.text
    else:
        print(f"Error fetching song list: {response.status_code}")
        return ""


def get_song_set(html_page: str) -> tSongSet:
    soup = BeautifulSoup(html_page, "html.parser")
    if soup.find("table") is None:
        return set()
    song_list = set()
    for tr in soup.find_all("tr"):
        td = tr.find("td")
        if td:
            name = td.get_text().strip()
            link = td.find("a")
            if link:
                song_list.add((name, link["href"]))
    return song_list


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
