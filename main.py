from ui import SpotifyDownloaderApp

default_dir = "D:\\Code\\SpotifySongDownloader\\downloads"

if __name__ == "__main__":
    app = SpotifyDownloaderApp(default_dir)
    app.mainloop()