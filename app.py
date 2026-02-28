import os
import secrets
from dotenv import load_dotenv
from functools import wraps

from flask import Flask, redirect, render_template, request, session, url_for

import busca_guitar_flash

load_dotenv()


def _get_validated_admin_user() -> str:
    admin_user = os.environ.get("ADMIN_USERNAME", "").strip()
    if not admin_user:
        raise RuntimeError("ADMIN_USERNAME não configurada. Defina no arquivo .env.")
    return admin_user


def _get_validated_admin_password() -> str:
    admin_password = os.environ.get("ADMIN_PASSWORD", "").strip()
    blocked_values = {
        "admin",
        "admin123",
        "password",
        "123456",
        "qwerty",
        "troque-essa-senha",
    }

    if not admin_password:
        raise RuntimeError("ADMIN_PASSWORD não configurada. Defina no arquivo .env.")

    if len(admin_password) < 12:
        raise RuntimeError("ADMIN_PASSWORD fraca. Use ao menos 12 caracteres.")

    if admin_password.lower() in blocked_values:
        raise RuntimeError(
            "ADMIN_PASSWORD está com valor inseguro/padrão. Use uma senha forte."
        )

    return admin_password


app = Flask(__name__)
app.secret_key = secrets.token_urlsafe(32)

ADMIN_USERNAME = _get_validated_admin_user()
ADMIN_PASSWORD = _get_validated_admin_password()


def _to_absolute_link(link: str) -> str:
    if link.startswith("http://") or link.startswith("https://"):
        return link
    return f"https://guitarflash.com{link}"


def _read_songs() -> set[tuple[str, str]]:
    if not os.path.exists(busca_guitar_flash.CSV_PATH):
        return set()
    return busca_guitar_flash.load_song_set()


def _refresh_songs(max_pages: int) -> set[tuple[str, str]]:
    songs = set()
    for page in busca_guitar_flash.inf_gen(max_pages):
        html = busca_guitar_flash.fetch_song_list_html(page)
        if not html:
            break

        page_songs = busca_guitar_flash.get_song_set(html)
        if not page_songs:
            break

        songs.update(page_songs)

    if songs:
        busca_guitar_flash.save_song_set(songs)
    return songs


def _admin_required(view_func):
    @wraps(view_func)
    def _wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            next_url = request.path
            return redirect(url_for("admin_login", next=next_url))
        return view_func(*args, **kwargs)

    return _wrapped


@app.get("/")
def index():
    query = request.args.get("q", "").strip()
    song_set = _read_songs()

    if query:
        songs = busca_guitar_flash.search_song(query, song_set)
    else:
        songs = song_set

    songs_sorted = sorted(songs, key=lambda item: item[0].lower())
    songs_view = [
        {"name": name, "link": _to_absolute_link(link)} for name, link in songs_sorted
    ]

    return render_template(
        "index.html",
        query=query,
        songs=songs_view,
        total=len(song_set),
        showing=len(songs_view),
        is_admin=session.get("is_admin", False),
    )


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = ""
    next_url = request.args.get("next", "")

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        next_url = request.form.get("next", "")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["is_admin"] = True
            if next_url and next_url.startswith("/"):
                return redirect(next_url)
            return redirect(url_for("admin_update"))

        error = "Credenciais inválidas"

    return render_template("login.html", error=error, next_url=next_url)


@app.get("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/admin/update", methods=["GET", "POST"])
@_admin_required
def admin_update():
    message = ""
    error = ""

    if request.method == "POST":
        pages_raw = request.form.get("pages", "10").strip()
        try:
            pages = int(pages_raw)
            if pages < 1:
                raise ValueError

            songs = _refresh_songs(pages)
            if songs:
                message = f"Lista atualizada com {len(songs)} músicas."
            else:
                error = "Não foi possível atualizar a lista (sem dados retornados)."
        except ValueError:
            error = "Informe um número de páginas válido (mínimo 1)."

    current_total = len(_read_songs())

    return render_template(
        "admin_update.html",
        message=message,
        error=error,
        current_total=current_total,
        is_admin=True,
    )


def main():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)


if __name__ == "__main__":
    main()
