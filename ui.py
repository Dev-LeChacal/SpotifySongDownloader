import os
import re
import threading
from pathlib import Path
import customtkinter as ctk
from tkinter import filedialog
from downloader import Downloader
from history import load_history


def is_valid_spotify_track_url(url: str) -> bool:
    pattern = (
        r'^(https://open\.spotify\.com/(?:intl-[a-z]{2}/)?track/|'
        r'spotify:track:)([A-Za-z0-9]+)(\?.*)?$'
    )
    return re.match(pattern, url) is not None


class SpotifyDownloaderApp(ctk.CTk):
    COLOR_MAP = {
        'info': '#E8E8E8',
        'success': '#4CAF50',
        'error': '#F44336',
        'warning': '#FF9800'
    }

    COLORS = {
        'primary': '#1DB954',
        'primary_hover': '#1ed760',
        'secondary': '#191414',
        'background': '#121212',
        'card': '#1e1e1e',
        'text_primary': '#FFFFFF',
        'text_secondary': '#B3B3B3',
        'accent': '#535353',
        'border': '#2a2a2a',
        'error': '#F44336',
    }

    PADDING_X = 20
    PADDING_Y = 10
    ENTRY_IPAD = 8
    BTN_WIDTH = 120
    BTN_HEIGHT = 40

    def __init__(self, default_download_dir: str):
        super().__init__()

        self.title_label = None
        self.choose_folder_button = None
        self.folder_label = None
        self.url_entry = None
        self.download_button = None
        self.history_button = None
        self.status_label = None
        self.progress_bar = None
        self.detail_label = None
        self.download_frame = None
        self.history_frame = None
        self.history_list = None
        self.back_button = None

        self.download_dir = Path(default_download_dir)

        self.title("Spotify Song Downloader")
        self.geometry("700x520")
        self.resizable(False, False)
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("green")

        self.configure(fg_color=self.COLORS['background'])

        for col in (0, 1):
            self.grid_columnconfigure(col, weight=1, uniform="x")
        for row in range(8):
            self.grid_rowconfigure(row, weight=0)
        self.grid_rowconfigure(7, weight=1)

        self.create_title_frame()
        self.create_folder_frame()
        self.create_download_frame()
        self.create_status_frame()
        self.create_history_frame()

    def create_title_frame(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=0, column=0, columnspan=2, sticky="ew",
                   padx=self.PADDING_X, pady=(self.PADDING_Y * 2, self.PADDING_Y))
        frame.grid_columnconfigure(0, weight=1)

        title_container = ctk.CTkFrame(frame, fg_color=self.COLORS['card'], corner_radius=15)
        title_container.grid(row=0, column=0, sticky="ew")
        title_container.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(title_container,
                                        text="🎵 Spotify Song Downloader",
                                        font=ctk.CTkFont(size=28, weight="bold"),
                                        text_color=self.COLORS['primary'])
        self.title_label.grid(row=0, column=0, pady=self.PADDING_Y * 1.5)

        subtitle = ctk.CTkLabel(title_container,
                                text="Download your favorite tracks with ease",
                                font=ctk.CTkFont(size=14),
                                text_color=self.COLORS['text_secondary'])
        subtitle.grid(row=1, column=0, pady=(0, self.PADDING_Y * 1.5))

    def create_folder_frame(self):
        frame = ctk.CTkFrame(self, fg_color=self.COLORS['card'], corner_radius=12)
        frame.grid(row=1, column=0, columnspan=2, sticky="ew",
                   padx=self.PADDING_X, pady=(0, self.PADDING_Y))
        frame.grid_columnconfigure(1, weight=1)

        folder_icon = ctk.CTkLabel(frame, text="📁", font=ctk.CTkFont(size=20))
        folder_icon.grid(row=0, column=0, padx=(self.PADDING_X, 10), pady=self.PADDING_Y)

        self.choose_folder_button = ctk.CTkButton(frame,
                                                  text="Select Folder",
                                                  command=self.choose_folder,
                                                  width=self.BTN_WIDTH,
                                                  height=self.BTN_HEIGHT,
                                                  fg_color=self.COLORS['primary'],
                                                  hover_color=self.COLORS['primary_hover'],
                                                  font=ctk.CTkFont(size=14, weight="bold"),
                                                  corner_radius=8)
        self.choose_folder_button.grid(row=0, column=1, sticky="w",
                                       padx=10, pady=self.PADDING_Y)

        self.folder_label = ctk.CTkLabel(frame,
                                         text=self._trim_path(self.download_dir),
                                         text_color=self.COLORS['text_secondary'],
                                         font=ctk.CTkFont(size=13),
                                         wraplength=350,
                                         anchor="w")
        self.folder_label.grid(row=0, column=2, sticky="ew",
                               padx=(10, self.PADDING_X), pady=self.PADDING_Y)

    def create_download_frame(self):
        frame = ctk.CTkFrame(self, fg_color=self.COLORS['card'], corner_radius=12)
        self.download_frame = frame
        frame.grid(row=2, column=0, columnspan=2, sticky="ew",
                   padx=self.PADDING_X, pady=(0, self.PADDING_Y))
        frame.grid_columnconfigure(0, weight=1)

        url_container = ctk.CTkFrame(frame, fg_color="transparent")
        url_container.grid(row=0, column=0, sticky="ew", padx=self.PADDING_X, pady=(self.PADDING_Y, 10))
        url_container.grid_columnconfigure(0, weight=1)

        url_label = ctk.CTkLabel(url_container,
                                 text="Spotify Track URL",
                                 font=ctk.CTkFont(size=14, weight="bold"),
                                 text_color=self.COLORS['text_primary'],
                                 anchor="w")
        url_label.grid(row=0, column=0, sticky="w", pady=(0, 8))

        input_frame = ctk.CTkFrame(url_container, fg_color="transparent")
        input_frame.grid(row=1, column=0, sticky="ew")
        input_frame.grid_columnconfigure(0, weight=1)

        self.url_entry = ctk.CTkEntry(input_frame,
                                      placeholder_text="https://open.spotify.com/track/...",
                                      font=ctk.CTkFont(size=14),
                                      height=45,
                                      fg_color=self.COLORS['background'],
                                      border_color=self.COLORS['border'],
                                      placeholder_text_color=self.COLORS['text_secondary'])
        self.url_entry.grid(row=0, column=0, sticky="ew", padx=(0, 15))

        self.download_button = ctk.CTkButton(input_frame,
                                             text="Download",
                                             command=self.start_download_thread,
                                             width=self.BTN_WIDTH,
                                             height=45,
                                             fg_color=self.COLORS['primary'],
                                             hover_color=self.COLORS['primary_hover'],
                                             font=ctk.CTkFont(size=16, weight="bold"),
                                             corner_radius=8)
        self.download_button.grid(row=0, column=1)

        self.history_button = ctk.CTkButton(frame,
                                            text="📋 View History",
                                            command=self.show_history,
                                            width=150,
                                            height=self.BTN_HEIGHT,
                                            fg_color=self.COLORS['accent'],
                                            hover_color="#666666",
                                            font=ctk.CTkFont(size=14, weight="bold"),
                                            corner_radius=8)
        self.history_button.grid(row=1, column=0, pady=(10, self.PADDING_Y))

    def create_status_frame(self):
        frame = ctk.CTkFrame(self, fg_color=self.COLORS['card'], corner_radius=12)
        frame.grid(row=3, column=0, columnspan=2, sticky="ew",
                   padx=self.PADDING_X, pady=(0, self.PADDING_Y))
        frame.grid_columnconfigure(0, weight=1)

        status_container = ctk.CTkFrame(frame, fg_color="transparent")
        status_container.grid(row=0, column=0, sticky="ew", padx=self.PADDING_X, pady=self.PADDING_Y)
        status_container.grid_columnconfigure(0, weight=1)

        status_header = ctk.CTkLabel(status_container,
                                     text="Status",
                                     font=ctk.CTkFont(size=14, weight="bold"),
                                     text_color=self.COLORS['text_primary'],
                                     anchor="w")
        status_header.grid(row=0, column=0, sticky="w", pady=(0, 8))

        self.status_label = ctk.CTkLabel(status_container,
                                         text="Ready to download",
                                         text_color=self.COLORS['text_secondary'],
                                         font=ctk.CTkFont(size=14),
                                         anchor="w")
        self.status_label.grid(row=1, column=0, sticky="w", pady=(0, 10))

        progress_frame = ctk.CTkFrame(status_container, fg_color="transparent")
        progress_frame.grid(row=2, column=0, sticky="ew")
        progress_frame.grid_columnconfigure(0, weight=1)

        self.progress_bar = ctk.CTkProgressBar(progress_frame,
                                               height=8,
                                               progress_color=self.COLORS['primary'],
                                               fg_color=self.COLORS['background'])
        self.progress_bar.set(0)
        self.progress_bar.grid(row=0, column=0, sticky="ew", padx=(0, 15))

        self.detail_label = ctk.CTkLabel(progress_frame,
                                         text="",
                                         text_color=self.COLORS['text_secondary'],
                                         font=ctk.CTkFont(size=12, weight="bold"),
                                         width=50)
        self.detail_label.grid(row=0, column=1)

    def create_history_frame(self):
        self.history_frame = ctk.CTkFrame(self, fg_color=self.COLORS['card'], corner_radius=12)
        self.history_frame.grid(row=2, column=0, columnspan=2, rowspan=2,
                                sticky="nsew",
                                padx=self.PADDING_X, pady=0)
        self.history_frame.grid_columnconfigure(0, weight=1)
        self.history_frame.grid_rowconfigure(1, weight=1)

        header_frame = ctk.CTkFrame(self.history_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=self.PADDING_X, pady=(self.PADDING_Y, 10))
        header_frame.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(header_frame,
                              text="📋 Download History",
                              font=ctk.CTkFont(size=20, weight="bold"),
                              text_color=self.COLORS['text_primary'])
        header.grid(row=0, column=0, sticky="w")

        self.history_list = ctk.CTkScrollableFrame(self.history_frame,
                                                   fg_color=self.COLORS['background'],
                                                   corner_radius=8)
        self.history_list.grid(row=1, column=0, sticky="nsew", padx=self.PADDING_X, pady=(0, 10))

        button_frame = ctk.CTkFrame(self.history_frame, fg_color="transparent")
        button_frame.grid(row=2, column=0, sticky="ew", padx=self.PADDING_X, pady=(0, self.PADDING_Y))
        button_frame.grid_columnconfigure(0, weight=1)

        self.back_button = ctk.CTkButton(button_frame,
                                         text="← Back to Download",
                                         command=self.hide_history,
                                         width=180,
                                         height=self.BTN_HEIGHT,
                                         fg_color=self.COLORS['primary'],
                                         hover_color=self.COLORS['primary_hover'],
                                         font=ctk.CTkFont(size=14, weight="bold"),
                                         corner_radius=8)
        self.back_button.grid(row=0, column=0)

        self.history_frame.grid_remove()

    def choose_folder(self):
        folder = filedialog.askdirectory(initialdir=self.download_dir)
        if folder:
            self.download_dir = Path(folder)
            self.folder_label.configure(text=self._trim_path(self.download_dir))

    @staticmethod
    def _trim_path(path: Path, max_len: int = 60) -> str:
        text = str(path)
        return text if len(text) <= max_len else text[:55] + "…"

    def progress_callback(self, info: dict):
        self.after(0, self._update_ui, info)

    def _update_ui(self, info: dict):
        msg = info.get('message', '')
        prog = info.get('progress')
        status = info.get('status', 'info')
        color = self.COLOR_MAP.get(status, self.COLORS['text_secondary'])
        self.status_label.configure(text=msg, text_color=color)
        if prog is not None:
            self.progress_bar.set(prog)
            pct = f"{prog * 100:.1f}%" if prog > 0 else ""
            self.detail_label.configure(text=pct)
        else:
            self.progress_bar.set(0)
            self.detail_label.configure(text="")

    def start_download_thread(self):
        self.download_button.configure(state="disabled", text="Downloading...")
        self.download_button.configure(fg_color=self.COLORS['accent'])
        threading.Thread(target=self.download_song, daemon=True).start()

    def download_song(self):
        url = self.url_entry.get().strip()
        if not url:
            self.progress_callback({'message': "Please enter a URL first!", 'progress': 0, 'status': 'error'})
            return self._restore_button()
        if not is_valid_spotify_track_url(url):
            self.progress_callback({'message': "Invalid Spotify track URL!", 'progress': 0, 'status': 'error'})
            return self._restore_button()

        downloader = Downloader(str(self.download_dir), progress_callback=self.progress_callback)
        try:
            downloader.download_from_url(url)
            downloader.wait_for_download_completion()
            self.progress_callback(
                {'message': "Download completed successfully!", 'progress': 1.0, 'status': 'success'})
        except Exception as e:
            self.progress_callback({'message': f"Download failed: {e}", 'progress': 0, 'status': 'error'})
        finally:
            downloader.close()
            self._restore_button()

    def _restore_button_state(self):
        self.download_button.configure(state="normal", text="Download")
        self.download_button.configure(fg_color=self.COLORS['primary'])

    def _restore_button(self):
        self.after(0, self._restore_button_state)

    def clear_history_widgets(self):
        for widget in self.history_list.winfo_children():
            try:
                widget.destroy()
            except:
                pass

    def open_url(self, url):
        try:
            import webbrowser
            webbrowser.open(url)
        except Exception:
            pass

    def open_file_location(self, file_path):
        try:
            import subprocess
            import platform

            if platform.system() == "Windows":
                subprocess.run(["explorer", "/select,", file_path], shell=True)
            elif platform.system() == "Darwin":
                subprocess.run(["open", "-R", file_path])
            else:
                subprocess.run(["xdg-open", os.path.dirname(file_path)])
        except Exception:
            pass

    def show_history(self):
        try:
            history = load_history()
        except Exception:
            history = []

        self.clear_history_widgets()

        if not history:
            empty_frame = ctk.CTkFrame(self.history_list, fg_color=self.COLORS['card'], corner_radius=10)
            empty_frame.pack(fill="x", pady=20, padx=10)

            empty_icon = ctk.CTkLabel(empty_frame, text="📭", font=ctk.CTkFont(size=40))
            empty_icon.pack(pady=(20, 10))

            empty_label = ctk.CTkLabel(empty_frame,
                                       text="No downloads yet",
                                       font=ctk.CTkFont(size=16, weight="bold"),
                                       text_color=self.COLORS['text_secondary'])
            empty_label.pack(pady=(0, 20))
        else:
            for i, entry in enumerate(history):
                if not isinstance(entry, dict):
                    continue

                card = ctk.CTkFrame(self.history_list,
                                    fg_color=self.COLORS['card'],
                                    corner_radius=10,
                                    border_width=1,
                                    border_color=self.COLORS['border'])
                card.pack(fill="x", pady=(0, 12), padx=10)

                main_frame = ctk.CTkFrame(card, fg_color="transparent")
                main_frame.pack(fill="x", padx=15, pady=15)
                main_frame.grid_columnconfigure(1, weight=1)

                track_icon = ctk.CTkLabel(main_frame, text="🎵", font=ctk.CTkFont(size=16))
                track_icon.grid(row=0, column=0, sticky="nw", padx=(0, 10))

                info_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
                info_frame.grid(row=0, column=1, sticky="ew")
                info_frame.grid_columnconfigure(0, weight=1)

                title = entry.get("title", "Unknown Title")
                artist = entry.get("artist", "Unknown Artist")
                url = entry.get("url", "")
                file_path = entry.get("file", "")

                header_text = f"{artist} - {title}"
                if len(header_text) > 60:
                    header_text = header_text[:57] + "..."

                header = ctk.CTkLabel(info_frame,
                                      text=header_text,
                                      font=ctk.CTkFont(size=14, weight="bold"),
                                      text_color=self.COLORS['text_primary'],
                                      anchor="w")
                header.grid(row=0, column=0, sticky="w", pady=(0, 5))

                if url:
                    display_url = url[:60] + "..." if len(url) > 60 else url
                    url_label = ctk.CTkLabel(info_frame,
                                             text=f"🔗 {display_url}",
                                             font=ctk.CTkFont(size=11),
                                             text_color=self.COLORS['primary'],
                                             anchor="w",
                                             cursor="hand2")
                    url_label.bind("<Button-1>", lambda e, link=url: self.open_url(link))
                    url_label.grid(row=1, column=0, sticky="w", pady=(0, 3))

                if file_path and os.path.exists(file_path):
                    file_name = Path(file_path).name
                    if len(file_name) > 60:
                        file_name = file_name[:57] + "..."

                    file_label = ctk.CTkLabel(info_frame,
                                              text=f"📁 {file_name}",
                                              font=ctk.CTkFont(size=11),
                                              text_color=self.COLORS['text_secondary'],
                                              anchor="w",
                                              cursor="hand2")
                    file_label.bind("<Button-1>", lambda e, path=file_path: self.open_file_location(path))
                    file_label.grid(row=2, column=0, sticky="w")
                else:
                    file_label = ctk.CTkLabel(info_frame,
                                              text="File not found",
                                              font=ctk.CTkFont(size=11),
                                              text_color=self.COLORS['error'],
                                              anchor="w")
                    file_label.grid(row=2, column=0, sticky="w")

        self.download_frame.grid_remove()
        self.history_frame.grid()

    def hide_history(self):
        self.history_frame.grid_remove()
        self.download_frame.grid()


if __name__ == "__main__":
    default_folder = os.path.expanduser("~/Downloads")
    SpotifyDownloaderApp(default_folder).mainloop()