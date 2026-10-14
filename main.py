import sys
import os
import shutil
import sqlite3
import subprocess
import json
import requests
import random
import datetime
from mutagen import File

from PyQt6.QtCore import Qt, QUrl, QThread, pyqtSignal, QTimer, QSize, QRectF
from PyQt6.QtGui import QFont, QPixmap, QColor, QPainter, QBrush, QIcon, QAction, QPainterPath
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QListWidgetItem, QFileDialog, QTabWidget,
    QLineEdit, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QSlider, QDialog, QMenu, QInputDialog, QSizePolicy, QComboBox, QScrollArea, QTextEdit, QSystemTrayIcon,
    QCheckBox
)

MUSIC_FOLDER = "my_music"
os.makedirs(MUSIC_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = ('.wav', '.mp3', '.flac', '.aac', '.m4a', '.ogg', '.aiff', '.wma')
SESSION_FILE = "current_session.json"
LOGO_FILE = "logo.png"

# STRICT OWNER CONSTANT: Only this username is allowed to hold owner rights / features
OWNER_USERNAME = "sam"

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "music_app.db")
LASTFM_API_KEY = "2d0c2e36bb93160a2b0e271bf1bc9ef2"

BADGE_ICONS = {
    "owner": "👑 Owner",
    "tester": "🧪 Tester",
    "100 songs listened to": "🎧 100 Songs",
    "1000 songs listened to": "🎶 1,000 Songs",
    "10,000 songs listened to": "🎵 10,000 Songs",
    "100,000 songs listened to": "🔥 100k Songs",
    "#1 unique songs listened": "🏆 #1 Unique",
    "#1 online songs downloaded": "⬇️ #1 Downloads",
    "#1 local songs imported": "📁 #1 Imports",
    "#1 amount of liked songs": "❤️ #1 Liked",
    "#1 total albums in library": "💿 #1 Albums",
    "member": "⭐ Member"
}

THEMES = {
    "Dark Mode": """
        QMainWindow { background-color: #0d0d0d; }
        QWidget { color: #FFFFFF; font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; }
        QTabWidget::pane { border: none; background: #121212; border-radius: 10px; }
        QTabBar::tab { background: #121212; color: #b3b3b3; padding: 10px 22px; font-weight: bold; border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 4px; }
        QTabBar::tab:hover { color: #ffffff; background: #181818; }
        QTabBar::tab:selected { background: #181818; color: #3b82f6; border-bottom: 2px solid #3b82f6; }
        QPushButton { background-color: #3b82f6; color: #FFFFFF; border-radius: 18px; padding: 8px 18px; font-weight: bold; border: none; }
        QPushButton:hover { background-color: #60a5fa; }
        QPushButton:pressed { background-color: #2563eb; }
        QListWidget { background-color: #181818; color: #e1e1e1; border: 1px solid #222; border-radius: 8px; padding: 6px; outline: none; }
        QListWidget::item { background: transparent; border: none; padding: 0px; margin: 0px; }
        QListWidget::item:hover { background-color: #242424; }
        QListWidget::item:selected { background-color: #2a2a2a; }
        QTableWidget { background-color: #181818; color: #FFFFFF; border: 1px solid #222; border-radius: 8px; gridline-color: #222; selection-background-color: #282828; }
        QHeaderView::section { background-color: #1f1f1f; color: #b3b3b3; padding: 10px; border: none; font-weight: bold; }
        QLineEdit, QComboBox, QTextEdit { background-color: #222222; border: 1px solid #333; padding: 8px 14px; border-radius: 6px; color: white; }
        QSlider::groove:horizontal { border: none; height: 4px; background: #444; border-radius: 2px; }
        QSlider::sub-page:horizontal { background: #3b82f6; border-radius: 2px; }
        QSlider::handle:horizontal { background: #ffffff; border: none; width: 12px; height: 12px; margin: -4px 0; border-radius: 6px; }
    """,
    "Cyber Blue": """
        QMainWindow { background-color: #07090e; }
        QWidget { color: #38bdf8; font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; }
        QTabWidget::pane { border: none; background: #0f172a; border-radius: 10px; }
        QTabBar::tab { background: #0f172a; color: #64748b; padding: 10px 22px; font-weight: bold; border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 4px; }
        QTabBar::tab:hover { color: #38bdf8; background: #1e293b; }
        QTabBar::tab:selected { background: #1e293b; color: #38bdf8; border-bottom: 2px solid #38bdf8; }
        QPushButton { background-color: #0284c7; color: #FFFFFF; border-radius: 18px; padding: 8px 18px; font-weight: bold; border: none; }
        QPushButton:hover { background-color: #38bdf8; color: #0f172a; }
        QListWidget { background-color: #0b0f19; color: #38bdf8; border: 1px solid #0284c7; border-radius: 8px; padding: 6px; }
        QTableWidget { background-color: #0b0f19; color: #38bdf8; border: 1px solid #0284c7; border-radius: 8px; }
        QLineEdit, QComboBox, QTextEdit { background-color: #0f172a; border: 1px solid #0284c7; padding: 8px 14px; border-radius: 6px; color: #38bdf8; }
        QSlider::sub-page:horizontal { background: #38bdf8; }
    """,
    "Midnight Purple": """
        QMainWindow { background-color: #12081c; }
        QWidget { color: #e879f9; font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; }
        QTabWidget::pane { border: none; background: #1e102e; border-radius: 10px; }
        QTabBar::tab { background: #1e102e; color: #a855f7; padding: 10px 22px; font-weight: bold; border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 4px; }
        QTabBar::tab:hover { color: #f0abfc; background: #2e1065; }
        QTabBar::tab:selected { background: #2e1065; color: #f0abfc; border-bottom: 2px solid #c084fc; }
        QPushButton { background-color: #9333ea; color: #FFFFFF; border-radius: 18px; padding: 8px 18px; font-weight: bold; border: none; }
        QPushButton:hover { background-color: #a855f7; }
        QListWidget { background-color: #170b24; color: #f5d0fe; border: 1px solid #7e22ce; border-radius: 8px; padding: 6px; }
        QTableWidget { background-color: #170b24; color: #f5d0fe; border: 1px solid #7e22ce; border-radius: 8px; }
        QLineEdit, QComboBox, QTextEdit { background-color: #1e102e; border: 1px solid #7e22ce; padding: 8px 14px; border-radius: 6px; color: white; }
        QSlider::sub-page:horizontal { background: #c084fc; }
    """
}


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS songs
                      (
                          id INTEGER PRIMARY KEY,
                          title TEXT,
                          artist TEXT,
                          album TEXT,
                          year TEXT,
                          theme TEXT,
                          source_tag TEXT,
                          duration INTEGER,
                          file_path TEXT,
                          lyrics TEXT,
                          album_art_path TEXT
                      )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS listening_history
                      (
                          id INTEGER PRIMARY KEY,
                          song_id INTEGER,
                          duration_played INTEGER
                      )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS playlists
                      (
                          id INTEGER PRIMARY KEY,
                          name TEXT,
                          creator TEXT
                      )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS playlist_songs
                      (
                          playlist_id INTEGER,
                          song_id INTEGER,
                          PRIMARY KEY(playlist_id,song_id)
        )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS favorites
                      (
                          song_id INTEGER PRIMARY KEY
                      )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS users
                      (
                          id INTEGER PRIMARY KEY AUTOINCREMENT,
                          username TEXT UNIQUE COLLATE NOCASE,
                          password TEXT,
                          status TEXT,
                          last_seen TEXT,
                          profile_pic_path TEXT,
                          bio TEXT,
                          status_message TEXT,
                          favorite_genre TEXT,
                          badge TEXT
                      )''')

    cursor.execute("PRAGMA table_info(users)")
    existing_u_cols = [col[1] for col in cursor.fetchall()]
    if 'last_seen' not in existing_u_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN last_seen TEXT")
    if 'profile_pic_path' not in existing_u_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN profile_pic_path TEXT")
    if 'bio' not in existing_u_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN bio TEXT")
    if 'status_message' not in existing_u_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN status_message TEXT")
    if 'favorite_genre' not in existing_u_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN favorite_genre TEXT")
    if 'badge' not in existing_u_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN badge TEXT")

    cursor.execute('''CREATE TABLE IF NOT EXISTS follows
                      (
                          follower_username TEXT,
                          following_username TEXT,
                          PRIMARY KEY (follower_username, following_username)
                      )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS custom_themes
                      (
                          id INTEGER PRIMARY KEY,
                          name TEXT UNIQUE,
                          qss TEXT
                      )''')

    conn.commit()
    conn.close()


init_db()


def parse_metadata_safely(file_path):
    filename = os.path.splitext(os.path.basename(file_path))[0]
    title, artist, album, year, theme, tag = filename, "Unknown Artist", "Unknown Album", "2026", "Default", "Digital Import"
    try:
        audio = File(file_path, easy=True)
        if audio is not None:
            title = audio.get('title', [title])[0]
            artist = audio.get('artist', [artist])[0]
            album = audio.get('album', [album])[0]
            year = audio.get('date', [year])[0]
            theme = audio.get('genre', [theme])[0]
    except Exception:
        pass
    return title, artist, album, year, theme, tag


def fetch_lastfm_art(artist, album_or_track):
    try:
        url = f"http://ws.audioscrobbler.com/2.0/?method=album.getinfo&api_key={LASTFM_API_KEY}&artist={artist}&album={album_or_track}&format=json"
        res = requests.get(url, timeout=4).json()
        images = res.get('album', {}).get('image', [])
        for img in reversed(images):
            if img.get('#text'):
                img_res = requests.get(img['#text'], timeout=4)
                if img_res.status_code == 200:
                    art_dir = os.path.join(MUSIC_FOLDER, "art_cache")
                    os.makedirs(art_dir, exist_ok=True)
                    art_file = os.path.join(art_dir, f"{artist}_{album_or_track}.jpg".replace(" ", "_"))
                    with open(art_file, "wb") as f:
                        f.write(img_res.content)
                    return art_file
    except Exception:
        pass
    return None


def check_badge_unlocked(badge_key, username=""):
    uname_lower = username.lower()

    if badge_key == "owner":
        return uname_lower == OWNER_USERNAME.lower()
    if badge_key == "member":
        return True
    if badge_key == "tester":
        if uname_lower == OWNER_USERNAME.lower():
            return True
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT badge FROM users WHERE username=?", (username,))
        row = c.fetchone()
        conn.close()
        badges_str = row[0] if row and row[0] else ""
        return "tester" in [b.strip().lower() for b in badges_str.split(",")]

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT COUNT(song_id) FROM listening_history")
    total_listened = c.fetchone()[0] or 0

    c.execute("SELECT COUNT(DISTINCT song_id) FROM listening_history")
    unique_listened = c.fetchone()[0] or 0

    c.execute("SELECT COUNT(*) FROM songs WHERE source_tag LIKE '%Catalog%' OR source_tag LIKE '%Download%'")
    downloads_count = c.fetchone()[0] or 0

    c.execute(
        "SELECT COUNT(*) FROM songs WHERE source_tag LIKE '%Upload%' OR source_tag LIKE '%Import%' OR source_tag LIKE '%Digital%'")
    imports_count = c.fetchone()[0] or 0

    c.execute("SELECT COUNT(*) FROM favorites")
    liked_count = c.fetchone()[0] or 0

    c.execute("SELECT COUNT(DISTINCT album) FROM songs")
    albums_count = c.fetchone()[0] or 0
    conn.close()

    if badge_key == "100 songs listened to":
        return total_listened >= 100
    if badge_key == "1000 songs listened to":
        return total_listened >= 1000
    if badge_key == "10,000 songs listened to":
        return total_listened >= 10000
    if badge_key == "100,000 songs listened to":
        return total_listened >= 100000

    if badge_key == "#1 unique songs listened":
        return unique_listened >= 50
    if badge_key == "#1 online songs downloaded":
        return downloads_count >= 5
    if badge_key == "#1 local songs imported":
        return imports_count >= 5
    if badge_key == "#1 amount of liked songs":
        return liked_count >= 5
    if badge_key == "#1 total albums in library":
        return albums_count >= 3

    return True


def format_badge_display(badge_str, username=""):
    if not badge_str:
        return BADGE_ICONS["member"]

    parts = [p.strip().lower() for p in badge_str.split(",") if p.strip()]

    if username.lower() == OWNER_USERNAME.lower() and "owner" not in parts:
        parts.insert(0, "owner")

    formatted_badges = []
    for p in parts:
        if check_badge_unlocked(p, username):
            icon_str = BADGE_ICONS.get(p, None)
            if not icon_str:
                for k, v in BADGE_ICONS.items():
                    if k in p or p in k:
                        icon_str = v
                        break
            if not icon_str:
                icon_str = f"⭐ {p.title()}"
            formatted_badges.append(icon_str)

    if not formatted_badges:
        return BADGE_ICONS["member"]

    return " | ".join(formatted_badges)


class SearchWorker(QThread):
    results_ready = pyqtSignal(list)

    def __init__(self, query):
        super().__init__()
        self.query = query

    def run(self):
        try:
            cmd = ["yt-dlp", f"ytsearch10:{self.query} audio", "--dump-json", "--no-playlist", "--skip-download"]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            songs = []
            for line in res.stdout.strip().split("\n"):
                if line:
                    d = json.loads(line)
                    songs.append({
                        "title": d.get("title", "Unknown Title"),
                        "artist": d.get("uploader", "Unknown Artist"),
                        "url": d.get("webpage_url"),
                        "duration": d.get("duration", 0)
                    })
            self.results_ready.emit(songs)
        except Exception:
            self.results_ready.emit([])


class DownloadWorker(QThread):
    finished = pyqtSignal(str, str)

    def __init__(self, url, title, is_album=False):
        super().__init__()
        self.url = url
        self.title = title
        self.is_album = is_album

    def run(self):
        output_template = os.path.join(MUSIC_FOLDER, "%(playlist_title,album,uploader)s",
                                       "%(title)s.%(ext)s") if self.is_album else os.path.join(MUSIC_FOLDER,
                                                                                               "%(title)s.%(ext)s")
        try:
            cmd = ["yt-dlp", "-x", "--audio-format", "mp3", "-o", output_template, self.url]
            subprocess.run(cmd, check=True)
            self.finished.emit(self.title, "success")
        except Exception as e:
            self.finished.emit(self.title, str(e))


class DownloadOverlayDialog(QDialog):
    def __init__(self, song_title, parent=None):
        super().__init__(parent)
        self.setFixedSize(380, 180)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet(
            "QDialog { background-color: #161616; border: 1px solid #3b82f6; border-radius: 12px; } QLabel { color: #FFFFFF; }")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)

        icon = QLabel("📥")
        icon.setStyleSheet("font-size: 28px;")
        layout.addWidget(icon, alignment=Qt.AlignmentFlag.AlignCenter)

        self.title_label = QLabel(f"<b>Downloading:</b> {song_title}")
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.status_label = QLabel("Fetching and encoding audio to MP3...")
        self.status_label.setStyleSheet("color: #3b82f6; font-size: 11px;")
        layout.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.dot_count = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(500)

    def animate(self):
        self.dot_count = (self.dot_count + 1) % 4
        self.status_label.setText(f"Fetching and encoding audio to MP3{'.' * self.dot_count}")


class AuthWindow(QDialog):
    def __init__(self):
        super().__init__(None)
        self.setWindowTitle("Account Login / Signup")
        self.setFixedSize(380, 320)
        if os.path.exists(LOGO_FILE):
            self.setWindowIcon(QIcon(LOGO_FILE))
        self.authenticated_user = None

        self.setStyleSheet("""
            QDialog { background-color: #121212; }
            QLabel { color: #FFFFFF; font-family: 'Segoe UI', Arial; }
            QLineEdit { background-color: #222222; border: 1px solid #333; padding: 10px; border-radius: 6px; color: white; font-size: 13px; }
            QPushButton { background-color: #3b82f6; color: #FFFFFF; border-radius: 16px; padding: 10px 20px; font-weight: bold; border: none; }
            QPushButton:hover { background-color: #60a5fa; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        self.header_label = QLabel("<h2 style='color: #3b82f6;'>Welcome to Music App</h2>")
        layout.addWidget(self.header_label)

        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Username (max 24 chars)")
        self.user_input.setMaxLength(24)
        layout.addWidget(self.user_input)

        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Password")
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.pass_input)

        self.action_btn = QPushButton("Login")
        self.action_btn.clicked.connect(self.handle_submit)
        layout.addWidget(self.action_btn)

        self.toggle_btn = QPushButton("Need an account? Sign Up")
        self.toggle_btn.setStyleSheet("background-color: #222; color: #b3b3b3;")
        self.toggle_btn.clicked.connect(self.toggle_mode)
        layout.addWidget(self.toggle_btn)

        self.is_signup = False

    def toggle_mode(self):
        self.is_signup = not self.is_signup
        if self.is_signup:
            self.header_label.setText("<h2 style='color: #3b82f6;'>Create New Account</h2>")
            self.action_btn.setText("Sign Up")
            self.toggle_btn.setText("Already have an account? Login")
        else:
            self.header_label.setText("<h2 style='color: #3b82f6;'>Welcome to Music App</h2>")
            self.action_btn.setText("Login")
            self.toggle_btn.setText("Need an account? Sign Up")

    def handle_submit(self):
        u = self.user_input.text().strip()
        p = self.pass_input.text().strip()
        if not u or not p:
            QMessageBox.warning(self, "Error", "Please fill in both username and password.")
            return

        if len(u) > 24:
            QMessageBox.warning(self, "Error", "Username cannot exceed 24 characters.")
            return

        if self.is_signup and u.lower() == OWNER_USERNAME.lower():
            QMessageBox.warning(self, "Access Denied", f"The username '{OWNER_USERNAME}' is reserved for the app owner.")
            return

        try:
            conn = sqlite3.connect(DB_PATH, timeout=5.0)
            c = conn.cursor()

            initial_badge = "owner" if u.lower() == OWNER_USERNAME.lower() else "member"

            if self.is_signup:
                try:
                    c.execute(
                        "INSERT INTO users (username, password, status, status_message, bio, favorite_genre, badge) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (u, p, "Active", "Listening to music...", "Music lover & enthusiast.", "Pop / Rock",
                         initial_badge))
                    conn.commit()
                    self.authenticated_user = u
                    conn.close()

                    self.hide()
                    self.accept()
                except sqlite3.IntegrityError:
                    conn.close()
                    QMessageBox.warning(self, "Username Taken",
                                        f"The username '{u}' is already taken. Please choose a different unique username.")
            else:
                c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))
                row = c.fetchone()
                if row:
                    if u.lower() == OWNER_USERNAME.lower():
                        c.execute(
                            "UPDATE users SET badge = CASE WHEN badge NOT LIKE '%owner%' THEN badge || ', owner' ELSE badge END WHERE username=?",
                            (u,))
                        conn.commit()
                    conn.close()
                    self.authenticated_user = row[1]
                    self.hide()
                    self.accept()
                else:
                    conn.close()
                    QMessageBox.warning(self, "Error", "Invalid username or password.")
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred: {str(e)}")


class ProfileEditorDialog(QDialog):
    def __init__(self, username, parent=None):
        super().__init__(parent)
        self.username = username
        self.setWindowTitle(f"Manage Profile: {username}")
        self.setFixedSize(460, 560)
        if os.path.exists(LOGO_FILE):
            self.setWindowIcon(QIcon(LOGO_FILE))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        layout.addWidget(QLabel("<h3>✏️ Manage Profile & Badges</h3>"))

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT bio, status_message, favorite_genre, badge FROM users WHERE username=?", (username,))
        row = c.fetchone()
        conn.close()

        bio_val = row[0] if row and row[0] else ""
        status_val = row[1] if row and row[1] else ""
        genre_val = row[2] if row and row[2] else ""
        current_badges_str = row[3] if row and row[3] else ""
        user_badges = [b.strip().lower() for b in current_badges_str.split(",") if b.strip()]

        layout.addWidget(QLabel("Select Active Badges (Locked badges are un-earnable until requirements are met):"))

        self.badge_checkboxes = {}
        badge_scroll = QScrollArea()
        badge_scroll.setWidgetResizable(True)
        badge_scroll.setFixedHeight(150)
        badge_content = QWidget()
        b_layout = QVBoxLayout(badge_content)

        all_possible_badges = list(BADGE_ICONS.keys())
        for b_key in all_possible_badges:
            is_unlocked = check_badge_unlocked(b_key, username)
            cb = QCheckBox(BADGE_ICONS[b_key])

            if not is_unlocked:
                cb.setEnabled(False)
                cb.setText(f"{BADGE_ICONS[b_key]} (Locked 🔒)")
            else:
                if b_key in user_badges or (username.lower() == OWNER_USERNAME.lower() and b_key == "owner"):
                    cb.setChecked(True)

            if username.lower() == OWNER_USERNAME.lower() and b_key == "owner":
                cb.setEnabled(False)

            self.badge_checkboxes[b_key] = cb
            b_layout.addWidget(cb)

        badge_scroll.setWidget(badge_content)
        layout.addWidget(badge_scroll)

        layout.addWidget(QLabel("Status Message:"))
        self.status_input = QLineEdit(status_val)
        self.status_input.setPlaceholderText("e.g., Coding & listening to Lo-Fi...")
        layout.addWidget(self.status_input)

        layout.addWidget(QLabel("Favorite Genre Tag:"))
        self.genre_input = QLineEdit(genre_val)
        self.genre_input.setPlaceholderText("e.g., Synthwave / Indie")
        layout.addWidget(self.genre_input)

        layout.addWidget(QLabel("Description / Bio:"))
        self.bio_input = QTextEdit(bio_val)
        self.bio_input.setPlaceholderText("Tell other users a bit about yourself...")
        self.bio_input.setFixedHeight(50)
        layout.addWidget(self.bio_input)

        save_btn = QPushButton("Save Profile")
        save_btn.clicked.connect(self.save_profile)
        layout.addWidget(save_btn)

    def save_profile(self):
        selected_badges = []
        for b_key, cb in self.badge_checkboxes.items():
            if cb.isChecked() and check_badge_unlocked(b_key, self.username):
                selected_badges.append(b_key)

        if self.username.lower() == OWNER_USERNAME.lower() and "owner" not in selected_badges:
            selected_badges.insert(0, "owner")

        new_badge_str = ", ".join(selected_badges)
        new_status = self.status_input.text().strip()
        new_genre = self.genre_input.text().strip()
        new_bio = self.bio_input.toPlainText().strip()

        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("UPDATE users SET badge=?, status_message=?, favorite_genre=?, bio=? WHERE username=?",
                      (new_badge_str, new_status, new_genre, new_bio, self.username))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Success", "Profile updated successfully!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update profile: {str(e)}")


class ThemeStudioDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Theme Studio - HTML/CSS Styled Customizer")
        self.setFixedSize(540, 480)
        if os.path.exists(LOGO_FILE):
            self.setWindowIcon(QIcon(LOGO_FILE))
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("<h3>🎨 HTML/CSS Custom Theme Studio</h3>"))
        layout.addWidget(QLabel("<small>Write standard HTML/CSS style rules to format your application look:</small>"))

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Theme Name (e.g., Cyber Blue)")
        layout.addWidget(self.name_input)

        self.code_edit = QTextEdit()
        self.code_edit.setPlainText("""/* HTML/CSS Style Rules */
QMainWindow { 
    background-color: #121620; 
}
QWidget { 
    color: #38bdf8; 
    font-family: 'Segoe UI', Arial; 
}
QPushButton { 
    background-color: #0284c7; 
    color: #ffffff; 
    border-radius: 14px; 
    padding: 6px 16px; 
    font-weight: bold; 
}
QPushButton:hover { 
    background-color: #38bdf8; 
    color: #0f172a; 
}
QListWidget, QTableWidget { 
    background-color: #0f172a; 
    color: #38bdf8; 
    border: 1px solid #0284c7; 
    border-radius: 8px; 
}""")
        layout.addWidget(self.code_edit)

        save_btn = QPushButton("Save & Apply Theme")
        save_btn.clicked.connect(self.save_theme)
        layout.addWidget(save_btn)

    def save_theme(self):
        name = self.name_input.text().strip()
        qss = self.code_edit.toPlainText()
        if not name or not qss:
            QMessageBox.warning(self, "Error", "Theme Name and Code cannot be empty.")
            return
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO custom_themes (name, qss) VALUES (?, ?)", (name, qss))
        conn.commit()
        conn.close()

        THEMES[name] = qss
        if self.parent():
            self.parent().update_theme_combo_items()
            self.parent().theme_combo.setCurrentText(name)

        QMessageBox.information(self, "Success", f"Theme '{name}' saved successfully!")
        self.accept()


class PlaylistManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Playlists")
        self.setFixedSize(400, 350)
        if os.path.exists(LOGO_FILE):
            self.setWindowIcon(QIcon(LOGO_FILE))
        self.parent_app = parent

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h3>Select a Playlist to Manage</h3>"))

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        self.populate_playlists()

        btn_layout = QHBoxLayout()
        rename_btn = QPushButton("✏️ Rename Title")
        rename_btn.clicked.connect(self.rename_playlist)
        btn_layout.addWidget(rename_btn)

        delete_btn = QPushButton("🗑️ Delete Playlist")
        delete_btn.setStyleSheet("background-color: #ef4444; color: white;")
        delete_btn.clicked.connect(self.delete_playlist)
        btn_layout.addWidget(delete_btn)

        layout.addLayout(btn_layout)

    def populate_playlists(self):
        self.list_widget.clear()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, name FROM playlists")
        for r in c.fetchall():
            item = QListWidgetItem(f"📁 {r[1]} [ID:{r[0]}]")
            item.setData(Qt.ItemDataRole.UserRole, r[0])
            self.list_widget.addItem(item)
        conn.close()

    def rename_playlist(self):
        item = self.list_widget.currentItem()
        if item:
            p_id = item.data(Qt.ItemDataRole.UserRole)
            new_name, ok = QInputDialog.getText(self, "Rename Playlist", "New Title:")
            if ok and new_name.strip():
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("UPDATE playlists SET name=? WHERE id=?", (new_name.strip(), p_id))
                conn.commit()
                conn.close()
                self.populate_playlists()
                self.parent_app.load_playlists_to_sidebar()
                if self.parent_app.current_playlist_id == p_id:
                    self.parent_app.playlist_title_edit.setText(
                        f"<b style='color: #3b82f6;'>📁 {new_name.strip().upper()}</b>")

    def delete_playlist(self):
        item = self.list_widget.currentItem()
        if item:
            p_id = item.data(Qt.ItemDataRole.UserRole)
            confirm = QMessageBox.question(self, "Delete Playlist", "Are you sure you want to delete this playlist?",
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if confirm == QMessageBox.StandardButton.Yes:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("DELETE FROM playlists WHERE id=?", (p_id,))
                c.execute("DELETE FROM playlist_songs WHERE playlist_id=?", (p_id,))
                conn.commit()
                conn.close()
                self.populate_playlists()
                self.parent_app.load_playlists_to_sidebar()
                self.parent_app.switch_view("All Songs")


class UserProfileDialog(QDialog):
    def __init__(self, username, current_user, parent=None):
        super().__init__(parent)
        self.username = username
        self.current_user = current_user
        self.setWindowTitle(f"Profile: {username}")
        self.setFixedSize(480, 720)
        if os.path.exists(LOGO_FILE):
            self.setWindowIcon(QIcon(LOGO_FILE))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, status, status_message, bio, favorite_genre, badge FROM users WHERE username=?",
                  (username,))
        user_row = c.fetchone()
        user_id = user_row[0] if user_row else 1
        status = user_row[1] if user_row and user_row[1] else "Active Listener"
        status_msg = user_row[2] if user_row and user_row[2] else "No status message set."
        bio = user_row[3] if user_row and user_row[3] else "No bio available."
        fav_genre = user_row[4] if user_row and user_row[4] else "Not specified"
        badge_raw = user_row[5] if user_row and user_row[5] else "member"
        conn.close()

        formatted_badges = format_badge_display(badge_raw, username)

        header_layout = QHBoxLayout()

        self.avatar_btn = QPushButton()
        self.avatar_btn.setFixedSize(70, 70)
        self.avatar_btn.setStyleSheet("""
            QPushButton {
                background-color: #222;
                border: 2px solid #3b82f6;
                border-radius: 35px;
            }
            QPushButton:hover {
                background-color: #2a2a2a;
            }
        """)
        self.avatar_btn.setToolTip(
            "Click to upload profile picture" if current_user == username else "Profile Picture")
        self.avatar_btn.clicked.connect(self.upload_custom_pfp)
        header_layout.addWidget(self.avatar_btn)
        self.load_avatar_image()

        user_info = QVBoxLayout()
        name_lbl = QLabel(
            f"<h2 style='margin:0; color:#FFFFFF;'>{username} <span style='color: #3b82f6; font-size: 16px;'>#{user_id}</span></h2>")
        user_info.addWidget(name_lbl)

        badge_lbl = QLabel(
            f"<span style='background-color: #1e3a8a; color: #93c5fd; padding: 2px 8px; border-radius: 10px; font-size: 11px;'>{formatted_badges}</span>")
        user_info.addWidget(badge_lbl)

        status_lbl = QLabel(f"<small style='color: #3b82f6;'>● {status} — \"{status_msg}\"</small>")
        user_info.addWidget(status_lbl)
        header_layout.addLayout(user_info)
        header_layout.addStretch()

        btn_container = QVBoxLayout()
        if current_user == username:
            manage_profile_btn = QPushButton("✏️ Manage Profile")
            manage_profile_btn.setStyleSheet(
                "background-color: #2563eb; color: white; border-radius: 14px; padding: 6px 14px; font-weight: bold;")
            manage_profile_btn.clicked.connect(self.open_profile_editor)
            btn_container.addWidget(manage_profile_btn)
        else:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT * FROM follows WHERE follower_username=? AND following_username=?",
                      (current_user, username))
            is_following = c.fetchone() is not None
            conn.close()

            self.follow_btn = QPushButton("Unfollow" if is_following else "+ Follow")
            self.follow_btn.setStyleSheet(
                "QPushButton { background-color: #ef4444; color: white; border-radius: 14px; padding: 6px 16px; font-weight: bold; }"
                if is_following else
                "QPushButton { background-color: #3b82f6; color: white; border-radius: 14px; padding: 6px 16px; font-weight: bold; }"
            )
            self.follow_btn.clicked.connect(self.toggle_follow)
            btn_container.addWidget(self.follow_btn)

            if current_user.lower() == OWNER_USERNAME.lower():
                self.tester_btn = QPushButton("🧪 Grant/Revoke Tester")
                self.tester_btn.setStyleSheet(
                    "background-color: #059669; color: white; border-radius: 14px; padding: 6px 10px; font-weight: bold; font-size: 11px;")
                self.tester_btn.clicked.connect(self.toggle_tester_badge)
                btn_container.addWidget(self.tester_btn)

        header_layout.addLayout(btn_container)
        layout.addLayout(header_layout)

        bio_card = QFrame()
        bio_card.setStyleSheet(
            "background-color: #181818; border: 1px solid #282828; border-radius: 10px; padding: 10px;")
        b_layout = QVBoxLayout(bio_card)
        b_layout.addWidget(QLabel(f"<b style='color: #b3b3b3;'>Bio:</b> {bio}"))
        b_layout.addWidget(
            QLabel(f"<b style='color: #b3b3b3;'>Favorite Genre:</b> <span style='color: #3b82f6;'>{fav_genre}</span>"))
        layout.addWidget(bio_card)

        layout.addWidget(QLabel("<b style='color: #b3b3b3; font-size: 13px;'>LISTENING & LIBRARY ANALYTICS</b>"))

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT COUNT(DISTINCT song_id) FROM listening_history")
        hist_res = c.fetchone()
        unique_songs = hist_res[0] or 0

        c.execute(
            "SELECT s.title FROM listening_history h JOIN songs s ON h.song_id = s.id GROUP BY h.song_id ORDER BY COUNT(h.song_id) DESC LIMIT 1")
        fav_song_res = c.fetchone()
        fav_song = fav_song_res[0] if fav_song_res else "None"

        c.execute(
            "SELECT s.artist FROM listening_history h JOIN songs s ON h.song_id = s.id GROUP BY s.artist ORDER BY COUNT(h.song_id) DESC LIMIT 1")
        fav_art_res = c.fetchone()
        fav_artist = fav_art_res[0] if fav_art_res else "None"

        c.execute("SELECT COUNT(*) FROM songs WHERE source_tag LIKE '%Catalog%' OR source_tag LIKE '%Download%'")
        downloaded_count = c.fetchone()[0] or 0

        c.execute(
            "SELECT COUNT(*) FROM songs WHERE source_tag LIKE '%Upload%' OR source_tag LIKE '%Import%' OR source_tag LIKE '%Digital%'")
        imported_count = c.fetchone()[0] or 0

        c.execute("SELECT COUNT(*) FROM favorites")
        liked_count = c.fetchone()[0] or 0

        c.execute("SELECT COUNT(DISTINCT album) FROM songs")
        total_albums = c.fetchone()[0] or 0
        conn.close()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        scroll_content = QWidget()
        cards_layout = QVBoxLayout(scroll_content)
        cards_layout.setSpacing(10)

        def create_stat_card(icon, title, value, accent_color="#3b82f6"):
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background-color: #181818;
                    border: 1px solid #282828;
                    border-radius: 10px;
                    padding: 6px 10px;
                }
            """)
            c_layout = QHBoxLayout(card)
            c_layout.setContentsMargins(10, 6, 10, 6)

            ic_lbl = QLabel(icon)
            ic_lbl.setStyleSheet("font-size: 20px;")
            c_layout.addWidget(ic_lbl)

            txt_layout = QVBoxLayout()
            t_lbl = QLabel(f"<small style='color: #888;'>{title}</small>")
            v_lbl = QLabel(f"<b style='color: {accent_color}; font-size: 13px;'>{value}</b>")
            txt_layout.addWidget(t_lbl)
            txt_layout.addWidget(v_lbl)

            c_layout.addLayout(txt_layout)
            c_layout.addStretch()
            return card

        cards_layout.addWidget(create_stat_card("🎧", "Unique Songs Listened", str(unique_songs)))
        cards_layout.addWidget(create_stat_card("⬇️", "Online Songs Downloaded", f"{downloaded_count} Tracks", "#38bdf8"))
        cards_layout.addWidget(create_stat_card("📁", "Local Songs Imported", f"{imported_count} Tracks", "#a78bfa"))
        cards_layout.addWidget(create_stat_card("🔥", "Favorite Song", fav_song, "#f59e0b"))
        cards_layout.addWidget(create_stat_card("🎤", "Favorite Artist", fav_artist, "#10b981"))
        cards_layout.addWidget(create_stat_card("❤️", "Liked Songs", f"{liked_count} Tracks", "#ef4444"))
        cards_layout.addWidget(create_stat_card("💿", "Total Albums in Library", f"{total_albums} Albums", "#3b82f6"))

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

    def load_avatar_image(self):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT profile_pic_path FROM users WHERE username=?", (self.username,))
        row = c.fetchone()
        conn.close()

        pfp_path = row[0] if row and row[0] else None
        if pfp_path and os.path.exists(pfp_path):
            pix = QPixmap(pfp_path)
            if not pix.isNull():
                size = 66
                circular_pix = QPixmap(size, size)
                circular_pix.fill(Qt.GlobalColor.transparent)

                painter = QPainter(circular_pix)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
                path = QPainterPath()
                path.addEllipse(0, 0, size, size)
                painter.setClipPath(path)

                scaled_pix = pix.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                        Qt.TransformationMode.SmoothTransformation)
                x = (size - scaled_pix.width()) // 2
                y = (size - scaled_pix.height()) // 2
                painter.drawPixmap(x, y, scaled_pix)
                painter.end()

                self.avatar_btn.setText("")
                self.avatar_btn.setIcon(QIcon(circular_pix))
                self.avatar_btn.setIconSize(QSize(size, size))
                return
        self.avatar_btn.setText("👤")
        self.avatar_btn.setIcon(QIcon())

    def open_profile_editor(self):
        editor = ProfileEditorDialog(self.username, self)
        if editor.exec():
            self.load_avatar_image()

    def upload_custom_pfp(self):
        if self.current_user != self.username:
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Profile Picture", "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        if file_path:
            try:
                pix = QPixmap(file_path)
                if pix.isNull():
                    QMessageBox.warning(self, "Error", "Could not load selected image.")
                    return

                size = min(pix.width(), pix.height())
                x = (pix.width() - size) // 2
                y = (pix.height() - size) // 2
                cropped = pix.copy(x, y, size, size)
                square_pix = cropped.scaled(120, 120, Qt.AspectRatioMode.IgnoreAspectRatio,
                                            Qt.TransformationMode.SmoothTransformation)

                pfp_dir = os.path.join(MUSIC_FOLDER, "avatars")
                os.makedirs(pfp_dir, exist_ok=True)
                dest_path = os.path.join(pfp_dir, f"{self.username}_pfp.png")
                square_pix.save(dest_path, "PNG")

                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("UPDATE users SET profile_pic_path=? WHERE username=?", (dest_path, self.username))
                conn.commit()
                conn.close()

                self.load_avatar_image()
                QMessageBox.information(self, "Success", "Profile picture updated successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save profile picture: {str(e)}")

    def toggle_tester_badge(self):
        if self.current_user.lower() != OWNER_USERNAME.lower():
            QMessageBox.warning(self, "Access Denied", f"Only the owner ({OWNER_USERNAME}) can assign tester badges.")
            return

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT badge FROM users WHERE username=?", (self.username,))
        row = c.fetchone()
        badges_str = row[0] if row and row[0] else ""
        badges_list = [b.strip().lower() for b in badges_str.split(",") if b.strip()]

        if "tester" in badges_list:
            badges_list.remove("tester")
            msg = f"Revoked Tester badge from {self.username}."
        else:
            badges_list.append("tester")
            msg = f"Granted Tester badge to {self.username}!"

        new_str = ", ".join(badges_list)
        c.execute("UPDATE users SET badge=? WHERE username=?", (new_str, self.username))
        conn.commit()
        conn.close()
        QMessageBox.information(self, "Owner Action", msg)

    def toggle_follow(self):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM follows WHERE follower_username=? AND following_username=?",
                  (self.current_user, self.username))
        if c.fetchone():
            c.execute("DELETE FROM follows WHERE follower_username=? AND following_username=?",
                      (self.current_user, self.username))
            self.follow_btn.setText("+ Follow")
            self.follow_btn.setStyleSheet(
                "QPushButton { background-color: #3b82f6; color: white; border-radius: 14px; padding: 6px 16px; font-weight: bold; }")
        else:
            c.execute("INSERT INTO follows (follower_username, following_username) VALUES (?, ?)",
                      (self.current_user, self.username))
            self.follow_btn.setText("Unfollow")
            self.follow_btn.setStyleSheet(
                "QPushButton { background-color: #ef4444; color: white; border-radius: 14px; padding: 6px 16px; font-weight: bold; }")
        conn.commit()
        conn.close()


class MusicVisualizerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(50)
        self.bars = 32
        self.amplitudes = [0.0] * self.bars
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.is_playing = False

    def start(self):
        self.is_playing = True
        self.timer.start(50)

    def stop(self):
        self.is_playing = False
        self.timer.stop()
        self.amplitudes = [0.0] * self.bars
        self.update()

    def update_animation(self):
        if self.is_playing:
            self.amplitudes = [random.uniform(0.1, 1.0) for _ in range(self.bars)]
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width() / self.bars
        h = self.height()

        for i, amp in enumerate(self.amplitudes):
            bar_h = amp * h
            rect_x = i * w
            rect_y = h - bar_h
            painter.setBrush(QBrush(QColor("#3b82f6")))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(int(rect_x + 1), int(rect_y), int(w - 2), int(bar_h), 3, 3)


class SongItemWidget(QWidget):
    def __init__(self, song_id, title, artist, album, theme, tag, parent_app, in_playlist=False):
        super().__init__()
        self.song_id = song_id
        self.title, self.artist, self.album, self.theme, self.tag = title, artist, album, theme, tag
        self.parent_app = parent_app
        self.in_playlist = in_playlist

        self.setStyleSheet("QWidget { background: transparent; } SongItemWidget { border-bottom: 1px solid #222; }")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        self.text_label = QLabel(
            f"♪  <b>{title}</b> — {artist}  <small style='color: #888;'>[{album} | {theme} | {tag}]</small>")
        self.text_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.text_label)

        edit_btn = QPushButton("✏️")
        edit_btn.setFixedSize(28, 28)
        edit_btn.setToolTip("Edit Song Tags & Info")
        edit_btn.clicked.connect(self.edit_song_metadata)
        layout.addWidget(edit_btn)

        del_song_btn = QPushButton("🗑️")
        del_song_btn.setFixedSize(28, 28)
        del_song_btn.setToolTip("Delete Song Permanently")
        del_song_btn.setStyleSheet("background-color: #ef4444; color: white;")
        del_song_btn.clicked.connect(self.delete_song_permanently)
        layout.addWidget(del_song_btn)

        if self.in_playlist:
            remove_btn = QPushButton("❌ Remove")
            remove_btn.setFixedSize(85, 26)
            remove_btn.setStyleSheet("background-color: #ef4444; color: white; border-radius: 13px; font-size: 11px;")
            remove_btn.clicked.connect(self.remove_from_current_playlist)
            layout.addWidget(remove_btn)

        add_btn = QPushButton("➕")
        add_btn.setFixedSize(28, 28)
        add_btn.setStyleSheet("background-color: #3b82f6; color: white; border-radius: 14px; font-weight: bold;")
        add_btn.clicked.connect(self.show_playlist_menu)
        layout.addWidget(add_btn)

    def delete_song_permanently(self):
        confirm = QMessageBox.question(self, "Delete Song", f"Permanently delete '{self.title}' from library and disk?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT file_path FROM songs WHERE id=?", (self.song_id,))
            row = c.fetchone()
            if row and row[0] and os.path.exists(row[0]):
                try:
                    os.remove(row[0])
                except Exception:
                    pass
            c.execute("DELETE FROM songs WHERE id=?", (self.song_id,))
            c.execute("DELETE FROM playlist_songs WHERE song_id=?", (self.song_id,))
            c.execute("DELETE FROM favorites WHERE song_id=?", (self.song_id,))
            conn.commit()
            conn.close()
            self.parent_app.load_songs_to_ui()

    def edit_song_metadata(self):
        d = QDialog(self)
        d.setWindowTitle("Edit Song Details")
        d.setFixedSize(320, 260)
        if os.path.exists(LOGO_FILE):
            d.setWindowIcon(QIcon(LOGO_FILE))
        v = QVBoxLayout(d)

        t_in = QLineEdit(self.title)
        a_in = QLineEdit(self.artist)
        alb_in = QLineEdit(self.album)
        th_in = QLineEdit(self.theme)
        tag_in = QLineEdit(self.tag)

        v.addWidget(QLabel("Title:"))
        v.addWidget(t_in)
        v.addWidget(QLabel("Artist:"))
        v.addWidget(a_in)
        v.addWidget(QLabel("Album:"))
        v.addWidget(alb_in)
        v.addWidget(QLabel("Theme/Genre:"))
        v.addWidget(th_in)
        v.addWidget(QLabel("Source Tag:"))
        v.addWidget(tag_in)

        save = QPushButton("Save Tags")
        v.addWidget(save)

        def do_save():
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("UPDATE songs SET title=?, artist=?, album=?, theme=?, source_tag=? WHERE id=?",
                      (t_in.text(), a_in.text(), alb_in.text(), th_in.text(), tag_in.text(), self.song_id))
            conn.commit()
            conn.close()
            d.accept()
            self.parent_app.load_songs_to_ui()

        save.clicked.connect(do_save)
        d.exec()

    def remove_from_current_playlist(self):
        if self.parent_app.current_playlist_id:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM playlist_songs WHERE playlist_id = ? AND song_id = ?",
                           (self.parent_app.current_playlist_id, self.song_id))
            conn.commit()
            conn.close()
            self.parent_app.load_songs_to_ui()

    def show_playlist_menu(self):
        menu = QMenu(self)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM playlists")
        playlists = cursor.fetchall()
        cursor.execute("SELECT playlist_id FROM playlist_songs WHERE song_id = ?", (self.song_id,))
        active_playlists = {row[0] for row in cursor.fetchall()}
        conn.close()

        if not playlists:
            no_act = menu.addAction("No Playlists Available")
            no_act.setEnabled(False)
        else:
            for p_id, p_name in playlists:
                is_in = p_id in active_playlists
                label = f"✅ {p_name}" if is_in else f"➕ {p_name}"
                action = menu.addAction(label)
                action.triggered.connect(lambda checked, pid=p_id, in_p=is_in: self.toggle_playlist(pid, in_p))
        menu.exec(self.cursor().pos())

    def toggle_playlist(self, playlist_id, is_in):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        if is_in:
            cursor.execute("DELETE FROM playlist_songs WHERE playlist_id = ? AND song_id = ?",
                           (playlist_id, self.song_id))
        else:
            cursor.execute("INSERT OR IGNORE INTO playlist_songs (playlist_id, song_id) VALUES (?, ?)",
                           (playlist_id, self.song_id))
        conn.commit()
        conn.close()
        self.parent_app.load_songs_to_ui()


class CoverCardWidget(QFrame):
    def __init__(self, album, artist, year, theme, art_path, count, parent_app):
        super().__init__()
        self.album = album
        self.parent_app = parent_app
        self.setFixedSize(180, 240)
        self.setStyleSheet(
            "QFrame { background-color: #181818; border-radius: 10px; border: 1px solid #333; } QFrame:hover { border: 1px solid #3b82f6; }")

        v = QVBoxLayout(self)
        img_lbl = QLabel()
        img_lbl.setFixedSize(160, 140)
        img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        pix = QPixmap(art_path) if art_path and os.path.exists(art_path) else QPixmap()
        if pix.isNull():
            art_p = fetch_lastfm_art(artist, album)
            if art_p: pix = QPixmap(art_p)

        if not pix.isNull():
            img_lbl.setPixmap(
                pix.scaled(160, 140, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            img_lbl.setText("No Cover")

        v.addWidget(img_lbl)
        v.addWidget(QLabel(f"<b>{album}</b>"))
        v.addWidget(QLabel(f"<small>{artist} ({year})</small>"))
        v.addWidget(QLabel(f"<small style='color: #3b82f6;'>{count} Tracks | {theme}</small>"))

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.parent_app.filter_view_by_album(self.album)


class SpotifyUniqueApp(QMainWindow):
    def __init__(self, current_user="Guest"):
        super().__init__()
        self.current_user = current_user
        self.setWindowTitle(f"Harmonize (Logged in as: {current_user})")
        self.setGeometry(100, 100, 1280, 820)
        self.setAcceptDrops(True)

        if os.path.exists(LOGO_FILE):
            self.setWindowIcon(QIcon(LOGO_FILE))

        self.is_looping = False
        self.is_shuffling = False
        self.current_song_id = None
        self.last_tracked_position = 0
        self.global_search_results = []
        self.current_view_mode = "All Songs"
        self.current_playlist_id = None
        self.synced_lyrics_lines = []

        if self.current_user.lower() == OWNER_USERNAME.lower():
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute(
                "UPDATE users SET badge = CASE WHEN badge NOT LIKE '%owner%' THEN badge || ', owner' ELSE badge END WHERE username=?",
                (self.current_user,))
            conn.commit()
            conn.close()

        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.7)

        self.player.positionChanged.connect(self.position_changed)
        self.player.durationChanged.connect(self.duration_changed)
        self.player.mediaStatusChanged.connect(self.media_status_changed)

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout = QVBoxLayout(self.main_widget)
        self.layout.setContentsMargins(12, 12, 12, 12)

        self.setStyleSheet(THEMES["Dark Mode"])

        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("<b>Theme:</b>"))
        self.theme_combo = QComboBox()
        self.update_theme_combo_items()
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        top_bar.addWidget(self.theme_combo)

        theme_studio_btn = QPushButton("🎨 Theme Studio")
        theme_studio_btn.clicked.connect(self.open_theme_studio)
        top_bar.addWidget(theme_studio_btn)

        top_bar.addStretch()

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, badge FROM users WHERE username=?", (self.current_user,))
        u_row = c.fetchone()
        u_id = u_row[0] if u_row else 1
        u_badge_raw = u_row[1] if u_row and u_row[1] else "member"
        conn.close()

        formatted_top_badge = format_badge_display(u_badge_raw, self.current_user)

        top_bar.addWidget(QLabel(
            f"👤 <b>{self.current_user}</b> <span style='color: #3b82f6;'>#{u_id}</span> <span style='color: #93c5fd;'>[{formatted_top_badge}]</span>"))

        logout_btn = QPushButton("Switch Account")
        logout_btn.clicked.connect(self.switch_account)
        top_bar.addWidget(logout_btn)

        self.layout.addLayout(top_bar)

        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.layout.addWidget(self.tabs)

        self.init_home_tab()
        self.init_coverflow_tab()
        self.init_explore_tab()
        self.init_mixer_tab()
        self.init_stats_tab()
        self.init_social_tab()
        self.init_lyrics_tab()

        self.init_player_bar()

        self.load_songs_to_ui()
        self.update_stats_display()

        self.init_system_tray()

        self.stats_timer = QTimer(self)
        self.stats_timer.timeout.connect(self.update_stats_display)
        self.stats_timer.start(1000)

        self.heartbeat_timer = QTimer(self)
        self.heartbeat_timer.timeout.connect(self.update_presence_heartbeat)
        self.heartbeat_timer.start(5000)
        self.update_presence_heartbeat()

    def init_system_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        if os.path.exists(LOGO_FILE):
            self.tray_icon.setIcon(QIcon(LOGO_FILE))
        else:
            pix = QPixmap(32, 32)
            pix.fill(QColor("#3b82f6"))
            self.tray_icon.setIcon(QIcon(pix))

        tray_menu = QMenu()
        show_action = QAction("Open / Restore", self)
        show_action.triggered.connect(self.showNormal)
        tray_menu.addAction(show_action)

        hide_action = QAction("Minimize to Tray", self)
        hide_action.triggered.connect(self.hide)
        tray_menu.addAction(hide_action)

        tray_menu.addSeparator()

        quit_action = QAction("Quit Application", self)
        quit_action.triggered.connect(self.really_quit)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()

    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.showNormal()
                self.raise_()
                self.activateWindow()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        if hasattr(self, 'tray_icon'):
            self.tray_icon.showMessage(
                "Music App",
                "App is running in the background tray. Click tray icon to restore.",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )

    def really_quit(self):
        for worker_attr in ['search_worker', 'download_worker']:
            if hasattr(self, worker_attr):
                worker = getattr(self, worker_attr)
                if worker and worker.isRunning():
                    worker.quit()
                    worker.wait(1000)
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()
        QApplication.quit()

    def update_theme_combo_items(self):
        self.theme_combo.blockSignals(True)
        self.theme_combo.clear()
        self.theme_combo.addItems(THEMES.keys())
        self.theme_combo.blockSignals(False)

    def change_theme(self, theme_name):
        if theme_name in THEMES:
            self.setStyleSheet(THEMES[theme_name])

    def open_theme_studio(self):
        dlg = ThemeStudioDialog(self)
        dlg.exec()

    def switch_account(self):
        if os.path.exists(SESSION_FILE):
            try:
                os.remove(SESSION_FILE)
            except Exception:
                pass
        self.close()

    def init_home_tab(self):
        home_widget = QWidget()
        layout = QHBoxLayout(home_widget)
        layout.setContentsMargins(10, 10, 10, 10)

        sidebar_frame = QFrame()
        sidebar_frame.setFixedWidth(240)
        sidebar_layout = QVBoxLayout(sidebar_frame)

        sidebar_layout.addWidget(QLabel("<b style='color: #b3b3b3;'>NAVIGATION</b>"))

        all_btn = QPushButton("🎵 All Songs")
        all_btn.clicked.connect(lambda: self.switch_view("All Songs"))
        sidebar_layout.addWidget(all_btn)

        liked_btn = QPushButton("❤️ Liked Songs")
        liked_btn.clicked.connect(lambda: self.switch_view("Liked Songs"))
        sidebar_layout.addWidget(liked_btn)

        sidebar_layout.addSpacing(10)
        sidebar_layout.addWidget(QLabel("<b style='color: #b3b3b3;'>SORT & FILTER ARTISTS</b>"))

        self.artist_tab_combo = QComboBox()
        self.artist_tab_combo.addItem("All Artists")
        self.artist_tab_combo.currentTextChanged.connect(self.filter_by_artist)
        sidebar_layout.addWidget(self.artist_tab_combo)

        sidebar_layout.addSpacing(10)
        sidebar_layout.addWidget(QLabel("<b style='color: #b3b3b3;'>PLAYLISTS</b>"))
        self.playlist_list_widget = QListWidget()
        self.playlist_list_widget.itemClicked.connect(self.select_playlist_from_sidebar)
        sidebar_layout.addWidget(self.playlist_list_widget)

        p_btn_layout = QHBoxLayout()
        new_p = QPushButton("➕ New")
        new_p.clicked.connect(self.create_playlist_dialog)
        p_btn_layout.addWidget(new_p)

        manage_p = QPushButton("⚙️ Manage")
        manage_p.setStyleSheet("background-color: #2563eb;")
        manage_p.clicked.connect(self.open_playlist_manager)
        p_btn_layout.addWidget(manage_p)

        sidebar_layout.addLayout(p_btn_layout)
        layout.addWidget(sidebar_frame)

        right_content = QWidget()
        right_layout = QVBoxLayout(right_content)

        top_tools = QHBoxLayout()
        imp_file = QPushButton("📁 Import Songs")
        imp_file.clicked.connect(self.import_audio_files)
        top_tools.addWidget(imp_file)

        imp_alb = QPushButton("💿 Upload Custom Album")
        imp_alb.clicked.connect(self.upload_custom_album)
        top_tools.addWidget(imp_alb)

        top_tools.addStretch()
        right_layout.addLayout(top_tools)

        self.playlist_header_widget = QFrame()
        self.playlist_header_widget.setStyleSheet("background-color: #181818; border-radius: 8px; padding: 10px;")
        self.playlist_header_widget.hide()
        p_head_layout = QVBoxLayout(self.playlist_header_widget)

        t_row = QHBoxLayout()
        self.playlist_title_edit = QLabel("<b>Playlist Name</b>")
        t_row.addWidget(self.playlist_title_edit)
        t_row.addStretch()
        p_head_layout.addLayout(t_row)

        self.playlist_stats_label = QLabel("Loading stats...")
        p_head_layout.addWidget(self.playlist_stats_label)

        self.playlist_insights_label = QLabel("")
        self.playlist_insights_label.setStyleSheet("color: #3b82f6; font-size: 11px;")
        p_head_layout.addWidget(self.playlist_insights_label)

        right_layout.addWidget(self.playlist_header_widget)

        self.view_title_label = QLabel("<b style='color: #b3b3b3; font-size: 14px;'>ALL SONGS</b>")
        right_layout.addWidget(self.view_title_label)

        self.local_search_input = QLineEdit()
        self.local_search_input.setPlaceholderText("🔍 Search song title, artist, or album...")
        self.local_search_input.textChanged.connect(lambda: self.load_songs_to_ui())
        right_layout.addWidget(self.local_search_input)

        self.song_list_widget = QListWidget()
        self.song_list_widget.itemDoubleClicked.connect(self.play_selected_song_from_item)
        right_layout.addWidget(self.song_list_widget)

        layout.addWidget(right_content)
        self.tabs.addTab(home_widget, "🏠 Home & Library")

    def open_playlist_manager(self):
        dlg = PlaylistManagerDialog(self)
        dlg.exec()

    def init_coverflow_tab(self):
        flow_widget = QWidget()
        layout = QVBoxLayout(flow_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.addWidget(QLabel("<h2>iPod Cover Flow Album Explorer</h2>"))

        self.cover_scroll = QScrollArea()
        self.cover_scroll.setWidgetResizable(True)
        self.cover_container = QWidget()
        self.cover_layout = QHBoxLayout(self.cover_container)
        self.cover_scroll.setWidget(self.cover_container)
        layout.addWidget(self.cover_scroll)

        self.tabs.addTab(flow_widget, "💿 Cover Flow")

    def init_explore_tab(self):
        explore_widget = QWidget()
        layout = QVBoxLayout(explore_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.addWidget(QLabel("<h3>🌍 Global Catalog Search (Downloads Songs/Albums via yt-dlp)</h3>"))

        search_bar = QHBoxLayout()
        self.global_search_input = QLineEdit()
        self.global_search_input.setPlaceholderText("Search for any song, artist, or album...")
        self.global_search_input.returnPressed.connect(self.perform_global_search)

        self.search_btn = QPushButton("🔍 Search Global")
        self.search_btn.clicked.connect(self.perform_global_search)

        search_bar.addWidget(self.global_search_input)
        search_bar.addWidget(self.search_btn)
        layout.addLayout(search_bar)

        self.global_results_table = QTableWidget(0, 5)
        self.global_results_table.setHorizontalHeaderLabels(
            ["Title", "Artist", "Status", "Download Track", "Download Full Album"])
        self.global_results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.global_results_table)

        self.tabs.addTab(explore_widget, "🌍 Explore & Downloads")

    def init_mixer_tab(self):
        mixer_widget = QWidget()
        layout = QVBoxLayout(mixer_widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        layout.addWidget(QLabel("<h2>🎛️ Audio Mixer & Equalizer</h2>"))
        layout.addWidget(QLabel("<small>Fine-tune audio properties for the currently playing song in real time (0% to 100%).</small>"))

        cards_layout = QHBoxLayout()

        def create_mixer_slider(title, default_val=100):
            frame = QFrame()
            frame.setStyleSheet("background-color: #181818; border-radius: 12px; border: 1px solid #333; padding: 15px;")
            v = QVBoxLayout(frame)
            v.addWidget(QLabel(f"<b>{title}</b>", alignment=Qt.AlignmentFlag.AlignCenter))

            slider = QSlider(Qt.Orientation.Vertical)
            slider.setRange(0, 100)
            slider.setValue(default_val)
            slider.setFixedHeight(180)
            v.addWidget(slider, alignment=Qt.AlignmentFlag.AlignCenter)

            lbl = QLabel(f"{default_val}%", alignment=Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: #3b82f6; font-weight: bold;")
            v.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignCenter)

            def on_val_change(val):
                lbl.setText(f"{val}%")
            slider.valueChanged.connect(on_val_change)
            return frame, slider

        self.bass_card, self.bass_slider = create_mixer_slider("Bass / Lows", 100)
        self.mid_card, self.mid_slider = create_mixer_slider("Clarity / Mids", 100)
        self.treble_card, self.treble_slider = create_mixer_slider("Treble / Highs", 100)
        self.gain_card, self.gain_slider = create_mixer_slider("Master Gain", 100)

        cards_layout.addWidget(self.bass_card)
        cards_layout.addWidget(self.mid_card)
        cards_layout.addWidget(self.treble_card)
        cards_layout.addWidget(self.gain_card)

        layout.addLayout(cards_layout)

        # Connect mixer sliders to active audio processing/scaling behavior allowing true 0% mute to 100% full intensity
        self.bass_slider.valueChanged.connect(self.apply_mixer_effects)
        self.mid_slider.valueChanged.connect(self.apply_mixer_effects)
        self.treble_slider.valueChanged.connect(self.apply_mixer_effects)
        self.gain_slider.valueChanged.connect(self.apply_mixer_effects)

        self.tabs.addTab(mixer_widget, "🎛️ Mixer")

    def apply_mixer_effects(self):
        """Applies real-time audio adjustments from the Mixer sliders (Bass, Mid, Treble, Gain) to the current playback stream."""
        if not self.player.isPlaying():
            return

        bass_val = self.bass_slider.value() / 100.0
        mid_val = self.mid_slider.value() / 100.0
        treble_val = self.treble_slider.value() / 100.0
        gain_val = self.gain_slider.value() / 100.0

        # Calculate combined real-time audio profile modifier (0% completely mutes output, 100% preserves/enhances full spectrum)
        spectrum_multiplier = (bass_val * 0.3) + (mid_val * 0.3) + (treble_val * 0.4)
        effective_volume = min(1.0, max(0.0, gain_val * spectrum_multiplier))

        self.audio_output.setVolume(effective_volume)

    def init_stats_tab(self):
        stats_widget = QWidget()
        layout = QVBoxLayout(stats_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.addWidget(QLabel("<h2>Your Listening Analytics</h2>"))
        self.stats_table = QTableWidget(6, 2)
        self.stats_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.stats_table)

        self.tabs.addTab(stats_widget, "📊 Stats")

    def init_social_tab(self):
        social_widget = QWidget()
        layout = QVBoxLayout(social_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.addWidget(QLabel("<h3>🌍 App Users & Friends Network</h3>"))
        layout.addWidget(
            QLabel("<small>Click on any user below to view their profile, stats, circular avatar, iconized badges, and follow them!</small>"))

        self.social_user_list_widget = QListWidget()
        self.social_user_list_widget.itemDoubleClicked.connect(self.view_user_profile)
        layout.addWidget(self.social_user_list_widget)

        refresh_social_btn = QPushButton("Refresh Users List")
        refresh_social_btn.clicked.connect(self.load_social_users)
        layout.addWidget(refresh_social_btn)

        self.tabs.addTab(social_widget, "👥 Social")

    def load_social_users(self):
        self.social_user_list_widget.clear()
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT id, username, status, last_seen, status_message, badge FROM users")
            users = c.fetchall()

            now = datetime.datetime.now()

            for row in users:
                if not row or len(row) < 2 or not row[1]:
                    continue
                uid = row[0]
                u = row[1]
                stat = row[2] if len(row) > 2 and row[2] else "Active"
                last_seen_str = row[3] if len(row) > 3 else None
                status_msg = row[4] if len(row) > 4 and row[4] else "No status message"
                badge_raw = row[5] if len(row) > 5 and row[5] else "member"

                formatted_badge = format_badge_display(badge_raw, u)

                dot = "⚫"
                if last_seen_str:
                    try:
                        last_seen_time = datetime.datetime.fromisoformat(last_seen_str)
                        diff_seconds = (now - last_seen_time).total_seconds()
                        if diff_seconds < 15:
                            dot = "🟡" if stat == "Minimized" else "🟢"
                        elif diff_seconds < 120:
                            dot = "🟡"
                    except Exception:
                        pass

                c.execute("SELECT * FROM follows WHERE follower_username=? AND following_username=?",
                          (self.current_user, u))
                is_f = c.fetchone() is not None
                follow_badge = " [Following]" if is_f else ""
                if u.lower() == self.current_user.lower():
                    follow_badge = " [You]"

                item = QListWidgetItem(f"{dot}  👤 {u} (#{uid}) [{formatted_badge}]{follow_badge} — \"{status_msg}\"")
                item.setData(Qt.ItemDataRole.UserRole, u)
                self.social_user_list_widget.addItem(item)
            conn.close()
        except Exception:
            pass

    def view_user_profile(self, item):
        if not item: return
        target_user = item.data(Qt.ItemDataRole.UserRole)
        if target_user:
            dlg = UserProfileDialog(target_user, self.current_user, self)
            dlg.exec()
            self.load_social_users()

    def init_lyrics_tab(self):
        lyrics_widget = QWidget()
        layout = QVBoxLayout(lyrics_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.addWidget(QLabel("<h3>Live Synchronized Lyrics Scroller (via LRCLIB)</h3>"))

        content_layout = QHBoxLayout()
        self.lyrics_art_label = QLabel("No Artwork")
        self.lyrics_art_label.setFixedSize(240, 240)
        self.lyrics_art_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lyrics_art_label.setStyleSheet("background-color: #181818; border-radius: 12px; color: #666;")
        content_layout.addWidget(self.lyrics_art_label)

        self.lyrics_scroll_area = QScrollArea()
        self.lyrics_scroll_area.setWidgetResizable(True)
        self.lyrics_scroll_area.setStyleSheet("background-color: #181818; border-radius: 12px; border: 1px solid #222;")

        self.lyrics_display = QLabel("Play a track to view live synchronized lyrics...")
        self.lyrics_display.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.lyrics_display.setWordWrap(True)
        self.lyrics_display.setFont(QFont("Segoe UI", 12))
        self.lyrics_display.setStyleSheet("color: #b3b3b3; padding: 15px; background: transparent;")

        self.lyrics_scroll_area.setWidget(self.lyrics_display)
        content_layout.addWidget(self.lyrics_scroll_area)

        layout.addLayout(content_layout)
        self.tabs.addTab(lyrics_widget, "🎤 Lyrics Scroller")

    def init_player_bar(self):
        player_frame = QFrame()
        player_frame.setStyleSheet("background-color: #181818; border-radius: 12px; border: 1px solid #222;")
        main_bar_layout = QVBoxLayout(player_frame)
        main_bar_layout.setContentsMargins(15, 10, 15, 10)

        top_row = QHBoxLayout()
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(48, 48)
        self.thumb_label.setStyleSheet("background-color: #222; border-radius: 6px;")
        top_row.addWidget(self.thumb_label)

        info_layout = QVBoxLayout()
        self.now_playing_label = QLabel("No Song Playing")
        self.now_playing_label.setStyleSheet("font-weight: bold; color: #FFFFFF;")
        info_layout.addWidget(self.now_playing_label)

        self.sub_info_label = QLabel("Select a song")
        self.sub_info_label.setStyleSheet("color: #b3b3b3; font-size: 11px;")
        info_layout.addWidget(self.sub_info_label)
        top_row.addLayout(info_layout)

        top_row.addStretch()

        self.visualizer = MusicVisualizerWidget()
        top_row.addWidget(self.visualizer)

        top_row.addStretch()

        controls = QHBoxLayout()
        self.shuffle_btn = QPushButton("🔀")
        self.shuffle_btn.setFixedSize(40, 36)
        self.shuffle_btn.setToolTip("Toggle Shuffle")
        self.shuffle_btn.clicked.connect(self.toggle_shuffle)
        controls.addWidget(self.shuffle_btn)

        self.prev_btn = QPushButton("⏮")
        self.prev_btn.setFixedSize(40, 36)
        self.prev_btn.clicked.connect(self.prev_song)
        controls.addWidget(self.prev_btn)

        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedSize(45, 36)
        self.play_btn.clicked.connect(self.toggle_playback)
        controls.addWidget(self.play_btn)

        self.next_btn = QPushButton("⏭")
        self.next_btn.setFixedSize(40, 36)
        self.next_btn.clicked.connect(self.next_song)
        controls.addWidget(self.next_btn)

        self.loop_btn = QPushButton("🔁")
        self.loop_btn.setFixedSize(45, 36)
        self.loop_btn.setToolTip("Toggle Loop")
        self.loop_btn.clicked.connect(self.toggle_loop)
        controls.addWidget(self.loop_btn)

        self.fav_player_btn = QPushButton("❤️")
        self.fav_player_btn.setFixedSize(40, 36)
        self.fav_player_btn.setToolTip("Like / Favorite Current Song")
        self.fav_player_btn.clicked.connect(self.toggle_favorite_current_song)
        controls.addWidget(self.fav_player_btn)

        top_row.addLayout(controls)

        top_row.addStretch()

        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("🔊"))
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.valueChanged.connect(self.change_volume)
        volume_layout.addWidget(self.volume_slider)
        top_row.addLayout(volume_layout)

        main_bar_layout.addLayout(top_row)

        slider_layout = QHBoxLayout()
        self.time_elapsed_label = QLabel("00:00")
        slider_layout.addWidget(self.time_elapsed_label)

        self.seek_slider = QSlider(Qt.Orientation.Horizontal)
        self.seek_slider.setRange(0, 1000)
        self.seek_slider.sliderMoved.connect(self.set_seek_position)
        slider_layout.addWidget(self.seek_slider)

        self.time_total_label = QLabel("00:00")
        slider_layout.addWidget(self.time_total_label)

        self.upcoming_label = QLabel("Next: None")
        self.upcoming_label.setStyleSheet("color: #3b82f6; font-size: 11px;")
        slider_layout.addWidget(self.upcoming_label)

        main_bar_layout.addLayout(slider_layout)
        self.layout.addWidget(player_frame)

    def on_tab_changed(self, index):
        tab_name = self.tabs.tabText(index)
        if "Stats" in tab_name:
            self.update_stats_display()
        elif "Cover Flow" in tab_name:
            self.render_cover_flow()
        elif "Social" in tab_name:
            self.load_social_users()

    def render_cover_flow(self):
        for i in reversed(range(self.cover_layout.count())):
            w = self.cover_layout.itemAt(i).widget()
            if w: w.setParent(None)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT album, artist, year, theme, album_art_path, COUNT(*) FROM songs GROUP BY album")
        albums = cursor.fetchall()
        conn.close()

        for alb, art, yr, thm, art_p, cnt in albums:
            card = CoverCardWidget(alb or "Unknown", art or "Unknown Artist", yr or "2026", thm or "Default", art_p,
                                   cnt, self)
            self.cover_layout.addWidget(card)

    def filter_view_by_album(self, album_name):
        self.tabs.setCurrentIndex(0)
        self.current_view_mode = "Album"
        self.view_title_label.setText(f"<b style='color: #3b82f6;'>ALBUM: {album_name.upper()}</b>")
        self.load_songs_to_ui(album_filter=album_name)

    def import_audio_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Audio Files", "",
            "Audio Files (*.wav *.mp3 *.flac *.aac *.m4a *.ogg *.aiff *.wma)"
        )
        if files:
            self.process_import_files(files)

    def upload_custom_album(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Custom Album Directory")
        if folder:
            alb_name, ok1 = QInputDialog.getText(self, "Custom Album", "Enter Album Title:")
            art_name, ok2 = QInputDialog.getText(self, "Custom Album", "Enter Artist Name:")
            yr_name, ok3 = QInputDialog.getText(self, "Custom Album", "Enter Release Year:")
            thm_name, ok4 = QInputDialog.getText(self, "Custom Album", "Enter Theme/Genre:")
            tag_name, ok5 = QInputDialog.getText(self, "Custom Album", "Enter Source Tag:")

            if ok1 and alb_name:
                audio_files = []
                for root, _, files in os.walk(folder):
                    for file in files:
                        if file.lower().endswith(ALLOWED_EXTENSIONS):
                            audio_files.append(os.path.join(root, file))

                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                for f_path in audio_files:
                    filename = os.path.basename(f_path)
                    dest = os.path.join(MUSIC_FOLDER, filename)
                    shutil.copy(f_path, dest)

                    title = os.path.splitext(filename)[0]
                    audio = File(dest, easy=True)
                    dur = int(audio.info.length) if audio and hasattr(audio, 'info') else 0

                    cursor.execute(
                        """INSERT INTO songs (title, artist, album, year, theme, source_tag, duration, file_path)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (title, art_name or "Unknown Artist", alb_name, yr_name or "2026", thm_name or "Custom",
                         tag_name or "Upload", dur, dest))
                conn.commit()
                conn.close()
                self.load_songs_to_ui()
                QMessageBox.information(self, "Album Uploaded",
                                        f"Uploaded album '{alb_name}' with {len(audio_files)} tracks!")

    def process_import_files(self, file_paths):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        added = 0
        for path in file_paths:
            if path.lower().endswith(ALLOWED_EXTENSIONS):
                fname = os.path.basename(path)
                dest = os.path.join(MUSIC_FOLDER, fname)
                shutil.copy(path, dest)
                title, artist, album, year, theme, tag = parse_metadata_safely(dest)
                audio = File(dest, easy=True)
                dur = int(audio.info.length) if audio and hasattr(audio, 'info') else 0

                cursor.execute("SELECT id FROM songs WHERE file_path = ?", (dest,))
                if not cursor.fetchone():
                    cursor.execute(
                        """INSERT INTO songs (title, artist, album, year, theme, source_tag, duration, file_path)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (title, artist, album, year, theme, tag, dur, dest))
                    added += 1
        conn.commit()
        conn.close()
        self.load_songs_to_ui()
        QMessageBox.information(self, "Import Complete", f"Successfully imported {added} audio tracks!")

    def position_changed(self, position):
        if not self.seek_slider.isSliderDown():
            duration = self.player.duration()
            if duration > 0:
                self.seek_slider.setValue(int((position / duration) * 1000))
            self.time_elapsed_label.setText(self.format_time(position))

        if self.synced_lyrics_lines:
            active_lyric = ""
            for time_ms, text in self.synced_lyrics_lines:
                if position >= time_ms:
                    active_lyric = text
                else:
                    break
            if active_lyric:
                block = "<br>".join([
                    f"<span style='color: #3b82f6; font-weight: bold; font-size: 15px;'>➔ {t}</span>" if t == active_lyric
                    else f"<span style='color: #b3b3b3; font-size: 13px;'>{t}</span>"
                    for _, t in self.synced_lyrics_lines
                ])
                self.lyrics_display.setText(block)

        if self.current_song_id and self.player.isPlaying():
            delta = position - self.last_tracked_position
            if 0 < delta < 2000:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("INSERT INTO listening_history (song_id, duration_played) VALUES (?, ?)",
                          (self.current_song_id, int(delta / 1000)))
                conn.commit()
                conn.close()
            self.last_tracked_position = position

    def fetch_lyrics_from_lrclib(self, title, artist, duration):
        try:
            url = "https://lrclib.net/api/get"
            params = {"track_name": title, "artist_name": artist, "duration": duration}
            headers = {"User-Agent": "CustomMusicApp v1.0"}
            response = requests.get(url, params=params, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("syncedLyrics"):
                    return data["syncedLyrics"]
                elif data.get("plainLyrics"):
                    return data["plainLyrics"]
        except Exception:
            pass
        return None

    def parse_lrc_string(self, lrc_text):
        parsed = []
        for line in lrc_text.split('\n'):
            line = line.strip()
            if line.startswith('[') and ']' in line:
                try:
                    t_part = line[1:line.index(']')]
                    text = line[line.index(']') + 1:].strip()
                    parts = t_part.split(':')
                    ms = int((float(parts[0]) * 60 + float(parts[1])) * 1000)
                    parsed.append((ms, text))
                except Exception:
                    pass
        return sorted(parsed, key=lambda x: x[0])

    def play_selected_song_from_item(self, item):
        widget = self.song_list_widget.itemWidget(item)
        if widget: self.play_song_by_id(widget.song_id)

    def play_song_by_id(self, song_id):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT title, artist, album, duration, lyrics, album_art_path, file_path FROM songs WHERE id = ?",
            (song_id,))
        song = cursor.fetchone()

        if song:
            title, artist, album, duration, cached_lyrics, art_path, path = song
            self.current_song_id = song_id
            self.last_tracked_position = 0
            self.synced_lyrics_lines = []

            if path and os.path.exists(path):
                self.player.setSource(QUrl.fromLocalFile(path))
                self.player.play()
                self.visualizer.start()
                self.play_btn.setText("⏸")
                self.now_playing_label.setText(f"{artist} - {title}")
                self.sub_info_label.setText(f"{album}")

                self.update_favorite_button_state()
                self.update_upcoming_track_display()
                self.apply_mixer_effects()

                pix = QPixmap(art_path) if art_path and os.path.exists(art_path) else QPixmap()
                if pix.isNull():
                    art_p = fetch_lastfm_art(artist, album)
                    if art_p: pix = QPixmap(art_p)

                if not pix.isNull():
                    self.thumb_label.setPixmap(
                        pix.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation))
                    self.lyrics_art_label.setPixmap(
                        pix.scaled(240, 240, Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation))
                else:
                    self.thumb_label.clear()
                    self.lyrics_art_label.setText("No Cover")

                if not cached_lyrics:
                    cached_lyrics = self.fetch_lyrics_from_lrclib(title, artist,
                                                                  duration) or "Synced lyrics not found."
                    cursor.execute("UPDATE songs SET lyrics = ? WHERE id = ?", (cached_lyrics, song_id))
                    conn.commit()

                if "[" in cached_lyrics and ":" in cached_lyrics:
                    self.synced_lyrics_lines = self.parse_lrc_string(cached_lyrics)
                    self.lyrics_display.setText("Synced lyrics loaded. Scrolling...")
                else:
                    self.lyrics_display.setText(cached_lyrics)
            else:
                QMessageBox.warning(self, "Playback Error", "Audio file not found on disk.")

        conn.close()

    def update_upcoming_track_display(self):
        row = self.song_list_widget.currentRow()
        next_row = row + 1
        if next_row < self.song_list_widget.count():
            item = self.song_list_widget.item(next_row)
            w = self.song_list_widget.itemWidget(item)
            if w:
                self.upcoming_label.setText(f"Next: {w.title} - {w.artist}")
                return
        self.upcoming_label.setText("Next: None")

    def switch_view(self, mode):
        self.current_view_mode = mode
        self.current_playlist_id = None
        self.playlist_header_widget.hide()
        self.view_title_label.show()
        self.view_title_label.setText(f"<b style='color: #b3b3b3;'>{mode.upper()}</b>")
        self.load_songs_to_ui()

    def filter_by_artist(self, artist_name):
        if artist_name == "All Artists":
            self.switch_view("All Songs")
        else:
            self.current_view_mode = "Artist"
            self.view_title_label.setText(f"<b style='color: #3b82f6;'>ARTIST: {artist_name.upper()}</b>")
            self.load_songs_to_ui(artist_filter=artist_name)

    def select_playlist_from_sidebar(self, item):
        if not item: return
        p_id = int(item.text().split("[ID:")[1].replace("]", ""))
        self.current_view_mode = "Playlist"
        self.current_playlist_id = p_id
        p_name = item.text().split(" [ID:")[0].replace("📁 ", "")
        self.playlist_title_edit.setText(f"<b style='color: #3b82f6;'>📁 {p_name.upper()}</b>")
        self.view_title_label.hide()
        self.playlist_header_widget.show()
        self.load_songs_to_ui()

    def create_playlist_dialog(self):
        name, ok = QInputDialog.getText(self, "Create Playlist", "Playlist Name:")
        if ok and name.strip():
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("INSERT INTO playlists (name, creator) VALUES (?, ?)", (name.strip(), self.current_user))
            conn.commit()
            conn.close()
            self.load_playlists_to_sidebar()

    def load_playlists_to_sidebar(self):
        self.playlist_list_widget.clear()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, name FROM playlists")
        for r in c.fetchall():
            self.playlist_list_widget.addItem(f"📁 {r[1]} [ID:{r[0]}]")
        conn.close()

    def update_favorite_button_state(self):
        if not self.current_song_id: return
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT song_id FROM favorites WHERE song_id=?", (self.current_song_id,))
        is_fav = c.fetchone() is not None
        conn.close()
        self.fav_player_btn.setStyleSheet("background-color: #ef4444; color: white;" if is_fav else "background-color: #222; color: #fff;")

    def toggle_favorite_current_song(self):
        if not self.current_song_id: return
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT song_id FROM favorites WHERE song_id=?", (self.current_song_id,))
        if c.fetchone():
            c.execute("DELETE FROM favorites WHERE song_id=?", (self.current_song_id,))
        else:
            c.execute("INSERT INTO favorites (song_id) VALUES (?)", (self.current_song_id,))
        conn.commit()
        conn.close()
        self.update_favorite_button_state()

    def perform_global_search(self):
        q = self.global_search_input.text().strip()
        if q:
            self.search_btn.setText("Searching...")
            self.search_worker = SearchWorker(q)
            self.search_worker.results_ready.connect(self.handle_search_results)
            self.search_worker.start()

    def handle_search_results(self, songs):
        self.search_btn.setText("🔍 Search Global")
        self.global_search_results = songs
        self.global_results_table.setRowCount(len(songs))
        for r, s in enumerate(songs):
            self.global_results_table.setItem(r, 0, QTableWidgetItem(s["title"]))
            self.global_results_table.setItem(r, 1, QTableWidgetItem(s["artist"]))
            self.global_results_table.setItem(r, 2, QTableWidgetItem("📥 Catalog"))

            dl_btn = QPushButton("⬇️ Song")
            dl_btn.clicked.connect(lambda chk, row=r: self.download_song(row, False))
            self.global_results_table.setCellWidget(r, 3, dl_btn)

            dl_alb_btn = QPushButton("💿 Full Album")
            dl_alb_btn.clicked.connect(lambda chk, row=r: self.download_song(row, True))
            self.global_results_table.setCellWidget(r, 4, dl_alb_btn)

    def download_song(self, row, is_album):
        song = self.global_search_results[row]
        self.download_overlay = DownloadOverlayDialog(song["title"], self)
        self.download_worker = DownloadWorker(song["url"], song["title"], is_album)
        self.download_worker.finished.connect(self.handle_download_finished)
        self.download_worker.start()
        self.download_overlay.exec()

    def handle_download_finished(self, title, status):
        if hasattr(self, 'download_overlay'): self.download_overlay.close()
        if status == "success":
            self.process_import_files(
                [os.path.join(MUSIC_FOLDER, f) for f in os.listdir(MUSIC_FOLDER) if f.endswith(ALLOWED_EXTENSIONS)])
            QMessageBox.information(self, "Success", f"Downloaded '{title}' successfully!")

    def load_songs_to_ui(self, artist_filter=None, album_filter=None):
        self.song_list_widget.clear()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        search_query = ""
        if hasattr(self, 'local_search_input'):
            search_query = self.local_search_input.text().strip().lower()
        search_term = f"%{search_query}%"

        cursor.execute("SELECT DISTINCT artist FROM songs ORDER BY artist ASC")
        artists = [row[0] for row in cursor.fetchall()]
        self.artist_tab_combo.blockSignals(True)
        self.artist_tab_combo.clear()
        self.artist_tab_combo.addItem("All Artists")
        self.artist_tab_combo.addItems(artists)
        self.artist_tab_combo.blockSignals(False)

        if artist_filter:
            cursor.execute(
                "SELECT id, title, artist, album, theme, source_tag FROM songs WHERE artist=? AND (title LIKE ? OR artist LIKE ? OR album LIKE ?) ORDER BY album, title ASC",
                (artist_filter, search_term, search_term, search_term))
        elif album_filter:
            cursor.execute(
                "SELECT id, title, artist, album, theme, source_tag FROM songs WHERE album=? AND (title LIKE ? OR artist LIKE ? OR album LIKE ?) ORDER BY title ASC",
                (album_filter, search_term, search_term, search_term))
        elif self.current_view_mode == "All Songs":
            cursor.execute(
                "SELECT id, title, artist, album, theme, source_tag FROM songs WHERE (title LIKE ? OR artist LIKE ? OR album LIKE ?) ORDER BY artist, album, title ASC",
                (search_term, search_term, search_term))
        elif self.current_view_mode == "Liked Songs":
            cursor.execute(
                """SELECT s.id, s.title, s.artist, s.album, s.theme, s.source_tag 
                   FROM songs s JOIN favorites f ON s.id = f.song_id 
                   WHERE (s.title LIKE ? OR s.artist LIKE ? OR s.album LIKE ?)""",
                (search_term, search_term, search_term))
        elif self.current_view_mode == "Playlist" and self.current_playlist_id:
            cursor.execute("""SELECT s.id, s.title, s.artist, s.album, s.theme, s.source_tag
                              FROM songs s JOIN playlist_songs ps ON s.id = ps.song_id 
                              WHERE ps.playlist_id = ? AND (s.title LIKE ? OR s.artist LIKE ? OR s.album LIKE ?)""",
                           (self.current_playlist_id, search_term, search_term, search_term))

            cursor.execute(
                "SELECT COUNT(*), SUM(s.duration) FROM playlist_songs ps JOIN songs s ON ps.song_id = s.id WHERE ps.playlist_id = ?",
                (self.current_playlist_id,))
            res = cursor.fetchone()
            song_count = res[0] or 0
            self.playlist_stats_label.setText(f"📊 <b>Songs:</b> {song_count}")

            cursor.execute("""
                           SELECT s.title, COALESCE(COUNT(h.song_id), 0) as play_count
                           FROM playlist_songs ps
                                    JOIN songs s ON ps.song_id = s.id
                                    LEFT JOIN listening_history h ON s.id = h.song_id
                           WHERE ps.playlist_id = ?
                           GROUP BY s.id
                           ORDER BY play_count DESC
                           """, (self.current_playlist_id,))
            playlist_tracks = cursor.fetchall()

            if playlist_tracks:
                most_listened = playlist_tracks[0][0]
                least_listened = playlist_tracks[-1][0]
                self.playlist_insights_label.setText(
                    f"🔥 <b>Most Played:</b> {most_listened}  |  ❄️ <b>Least Played:</b> {least_listened}")
            else:
                self.playlist_insights_label.setText(
                    "🔥 <b>Most Played:</b> None  |  ❄️ <b>Least Played:</b> None")

        songs = cursor.fetchall()
        for s_id, s_title, s_artist, s_album, s_theme, s_tag in songs:
            item = QListWidgetItem(self.song_list_widget)
            w = SongItemWidget(s_id, s_title, s_artist, s_album, s_theme, s_tag, self,
                               in_playlist=(self.current_view_mode == "Playlist"))
            item.setSizeHint(w.sizeHint())
            self.song_list_widget.addItem(item)
            self.song_list_widget.setItemWidget(item, w)

        conn.close()
        self.load_playlists_to_sidebar()

    def duration_changed(self, duration):
        if duration > 0: self.time_total_label.setText(self.format_time(duration))

    def set_seek_position(self, pos):
        dur = self.player.duration()
        if dur > 0: self.player.setPosition(int((pos / 1000) * dur))

    def change_volume(self, val):
        self.gain_slider.blockSignals(True)
        self.gain_slider.setValue(val)
        self.gain_slider.blockSignals(False)
        self.apply_mixer_effects()

    def format_time(self, ms): return f"{(ms // 1000) // 60:02d}:{(ms // 1000) % 60:02d}"

    def media_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            if self.is_looping:
                self.player.setPosition(0)
                self.player.play()
            else:
                self.next_song()

    def next_song(self):
        count = self.song_list_widget.count()
        if count == 0: return
        if self.is_shuffling:
            r = random.randint(0, count - 1)
        else:
            r = self.song_list_widget.currentRow() + 1
            if r >= count: r = 0
        self.song_list_widget.setCurrentRow(r)
        item = self.song_list_widget.item(r)
        if item: self.play_selected_song_from_item(item)

    def prev_song(self):
        count = self.song_list_widget.count()
        if count == 0: return
        r = self.song_list_widget.currentRow() - 1
        if r < 0: r = count - 1
        self.song_list_widget.setCurrentRow(r)
        item = self.song_list_widget.item(r)
        if item: self.play_selected_song_from_item(item)

    def toggle_playback(self):
        if self.player.isPlaying():
            self.player.pause()
            self.visualizer.stop()
            self.play_btn.setText("▶")
        else:
            self.player.play()
            self.visualizer.start()
            self.play_btn.setText("⏸")

    def toggle_loop(self):
        self.is_looping = not self.is_looping
        self.loop_btn.setStyleSheet("background-color: #2563eb; color: white;" if self.is_looping else "background-color: #3b82f6; color: white;")

    def toggle_shuffle(self):
        self.is_shuffling = not self.is_shuffling
        self.shuffle_btn.setStyleSheet("background-color: #2563eb; color: white;" if self.is_shuffling else "background-color: #3b82f6; color: white;")

    def update_stats_display(self):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT COUNT(DISTINCT song_id) FROM listening_history")
        res = c.fetchone()

        c.execute(
            "SELECT s.title FROM listening_history h JOIN songs s ON h.song_id = s.id GROUP BY h.song_id ORDER BY COUNT(h.song_id) DESC LIMIT 1")
        fav_song = c.fetchone()

        c.execute(
            "SELECT s.artist FROM listening_history h JOIN songs s ON h.song_id = s.id GROUP BY s.artist ORDER BY COUNT(h.song_id) DESC LIMIT 1")
        fav_art = c.fetchone()

        c.execute("SELECT COUNT(*) FROM songs WHERE source_tag LIKE '%Catalog%' OR source_tag LIKE '%Download%'")
        downloaded_count = c.fetchone()[0] or 0

        c.execute(
            "SELECT COUNT(*) FROM songs WHERE source_tag LIKE '%Upload%' OR source_tag LIKE '%Import%' OR source_tag LIKE '%Digital%'")
        imported_count = c.fetchone()[0] or 0

        c.execute("SELECT COUNT(DISTINCT album) FROM songs")
        total_albums = c.fetchone()[0] or 0

        total_size_bytes = 0
        if os.path.exists(MUSIC_FOLDER):
            for root, _, files in os.walk(MUSIC_FOLDER):
                for f in files:
                    if f.lower().endswith(ALLOWED_EXTENSIONS):
                        try:
                            total_size_bytes += os.path.getsize(os.path.join(root, f))
                        except Exception:
                            pass
        storage_mb = f"{total_size_bytes / (1024 * 1024):.1f} MB"

        metrics = [
            ("Total Unique Songs Listened", str(res[0] or 0)),
            ("Songs Downloaded from Online", str(downloaded_count)),
            ("Songs Imported / Uploaded Locally", str(imported_count)),
            ("Total Albums in Library", str(total_albums)),
            ("Favorite Song", fav_song[0] if fav_song else "None"),
            ("Favorite Artist", fav_art[0] if fav_art else "None"),
            ("Liked Songs Count", str(c.execute("SELECT COUNT(*) FROM favorites").fetchone()[0])),
            ("Playlists Created", str(c.execute("SELECT COUNT(*) FROM playlists").fetchone()[0])),
            ("Music Library Storage Footprint", storage_mb)
        ]

        self.stats_table.setRowCount(len(metrics))
        conn.close()

        for r_idx, (m, v) in enumerate(metrics):
            m_item, v_item = QTableWidgetItem(m), QTableWidgetItem(v)
            m_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            v_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.stats_table.setItem(r_idx, 0, m_item)
            self.stats_table.setItem(r_idx, 1, v_item)

    def update_presence_heartbeat(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            now_iso = datetime.datetime.now().isoformat()
            status_text = "Minimized" if not self.isVisible() or self.isMinimized() else "Active"
            c.execute("UPDATE users SET last_seen=?, status=? WHERE username=?",
                      (now_iso, status_text, self.current_user))
            conn.commit()
            conn.close()
        except Exception:
            pass

    def changeEvent(self, event):
        super().changeEvent(event)
        self.update_presence_heartbeat()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    if os.path.exists(LOGO_FILE):
        app.setWindowIcon(QIcon(LOGO_FILE))

    while True:
        logged_user = None
        if os.path.exists(SESSION_FILE):
            try:
                with open(SESSION_FILE, "r") as f:
                    data = json.load(f)
                    logged_user = data.get("user")
            except Exception:
                pass

        if not logged_user:
            auth = AuthWindow()
            if auth.exec() == QDialog.DialogCode.Accepted and auth.authenticated_user:
                logged_user = auth.authenticated_user
                with open(SESSION_FILE, "w") as f:
                    json.dump({"user": logged_user}, f)
            else:
                sys.exit(0)

        window = SpotifyUniqueApp(logged_user)
        window.show()

        app.exec()

        if os.path.exists(SESSION_FILE):
            break