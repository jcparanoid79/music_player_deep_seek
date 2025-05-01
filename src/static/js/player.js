class ModernMusicPlayer {
  constructor() {
    this.audio = document.getElementById("audio-player");
    this.playlist = [];
    this.currentTrackIndex = -1;
    this.isPlaying = false;
    this.isShuffle = false;
    this.isRepeat = false;
    this.volume = 0.8;
    this.audioContext = null;
    this.analyser = null;
    this.canvas = document.getElementById("waveform");
    this.canvasCtx = this.canvas.getContext("2d");
    this.animationId = null;

    this.initElements();
    this.initEventListeners();
    this.initAudioContext();
  }

  initElements() {
    this.elements = {
      playBtn: document.getElementById("play"),
      prevBtn: document.getElementById("prev"),
      nextBtn: document.getElementById("next"),
      shuffleBtn: document.getElementById("shuffle"),
      repeatBtn: document.getElementById("repeat"),
      volumeControl: document.getElementById("volume"),
      progressContainer: document.querySelector(".progress-container"),
      progressBar: document.querySelector(".progress-bar"),
      trackTitle: document.getElementById("track-title"),
      trackArtist: document.getElementById("track-artist"),
      trackAlbum: document.getElementById("track-album"),
      albumArt: document.getElementById("album-art"),
      lyricsContent: document.getElementById("lyrics-content"),
      playlistContainer: document.getElementById("playlist"),
      uploadBtn: document.getElementById("upload-btn"),
      fileUpload: document.getElementById("file-upload"),
      clearPlaylistBtn: document.getElementById("clear-playlist"),
    };
  }

  initEventListeners() {
    // Player controls
    this.elements.playBtn.addEventListener("click", () => this.togglePlay());
    this.elements.prevBtn.addEventListener("click", () => this.prevTrack());
    this.elements.nextBtn.addEventListener("click", () => this.nextTrack());
    this.elements.shuffleBtn.addEventListener("click", () =>
      this.toggleShuffle()
    );
    this.elements.repeatBtn.addEventListener("click", () =>
      this.toggleRepeat()
    );

    // Progress bar
    this.elements.progressContainer.addEventListener("click", (e) => {
      const percent = e.offsetX / this.elements.progressContainer.offsetWidth;
      this.audio.currentTime = percent * this.audio.duration;
    });

    // Volume control
    this.elements.volumeControl.addEventListener("input", (e) => {
      this.volume = e.target.value / 100;
      this.audio.volume = this.volume;
    });

    // File upload
    this.elements.uploadBtn.addEventListener("click", () =>
      this.elements.fileUpload.click()
    );
    this.elements.fileUpload.addEventListener("change", (e) =>
      this.handleFiles(e.target.files)
    );

    // Clear playlist
    this.elements.clearPlaylistBtn.addEventListener("click", () =>
      this.clearPlaylist()
    );

    // Keyboard controls
    document.addEventListener("keydown", (e) => {
      switch (e.code) {
        case "Space":
          this.togglePlay();
          break;
        case "ArrowLeft":
          this.seek(-5);
          break;
        case "ArrowRight":
          this.seek(5);
          break;
        case "ArrowUp":
          this.adjustVolume(0.1);
          break;
        case "ArrowDown":
          this.adjustVolume(-0.1);
          break;
      }
    });

    // Audio events
    this.audio.addEventListener("timeupdate", () => this.updateProgress());
    this.audio.addEventListener("ended", () => this.nextTrack());
    this.audio.addEventListener("play", () => this.updatePlayState(true));
    this.audio.addEventListener("pause", () => this.updatePlayState(false));
  }

  initAudioContext() {
    this.audioContext = new (window.AudioContext ||
      window.webkitAudioContext)();
    this.analyser = this.audioContext.createAnalyser();
    this.analyser.fftSize = 256;

    const source = this.audioContext.createMediaElementSource(this.audio);
    source.connect(this.analyser);
    this.analyser.connect(this.audioContext.destination);

    this.visualize();
  }

  visualize() {
    const bufferLength = this.analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const draw = () => {
      this.animationId = requestAnimationFrame(draw);
      this.analyser.getByteFrequencyData(dataArray);

      this.canvasCtx.fillStyle = "rgba(0, 0, 0, 0.1)";
      this.canvasCtx.fillRect(0, 0, this.canvas.width, this.canvas.height);

      const barWidth = (this.canvas.width / bufferLength) * 2.5;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        const barHeight = dataArray[i] / 2;
        const hue = (i / bufferLength) * 360;

        this.canvasCtx.fillStyle = `hsla(${hue}, 100%, 50%, 0.8)`;
        this.canvasCtx.fillRect(
          x,
          this.canvas.height - barHeight,
          barWidth,
          barHeight
        );
        x += barWidth + 1;
      }
    };

    draw();
  }

  // Player methods
  togglePlay() {
    if (this.isPlaying) {
      this.audio.pause();
    } else {
      this.audio.play().catch((e) => console.error("Playback failed:", e));
    }
  }

  updatePlayState(isPlaying) {
    this.isPlaying = isPlaying;
    const icon = this.isPlaying ? "pause" : "play";
    this.elements.playBtn.innerHTML = `<i class="fas fa-${icon}"></i>`;
  }

  updateProgress() {
    const { duration, currentTime } = this.audio;
    const progressPercent = (currentTime / duration) * 100;
    this.elements.progressBar.style.width = `${progressPercent}%`;
  }

  seek(seconds) {
    this.audio.currentTime += seconds;
  }

  adjustVolume(change) {
    this.volume = Math.min(1, Math.max(0, this.volume + change));
    this.audio.volume = this.volume;
    this.elements.volumeControl.value = this.volume * 100;
  }

  // Playlist methods
  loadTrack(index) {
    if (index < 0 || index >= this.playlist.length) return;

    this.currentTrackIndex = index;
    const track = this.playlist[index];

    this.audio.src = track.path;
    this.elements.trackTitle.textContent = track.title || "Unknown Track";
    this.elements.trackArtist.textContent = track.artist || "Unknown Artist";
    this.elements.trackAlbum.textContent = track.album || "";
    this.elements.albumArt.src = track.art || "/static/img/default-album.png";

    this.fetchLyrics(track.artist, track.title);
    this.updatePlaylistUI();

    // Always play when loading next track (isPlaying is set by nextTrack())
    this.audio.play().catch((e) => console.error("Playback failed:", e));
  }

  nextTrack() {
    if (this.playlist.length === 0) return;

    let nextIndex;
    if (this.isShuffle) {
      nextIndex = Math.floor(Math.random() * this.playlist.length);
    } else {
      nextIndex = (this.currentTrackIndex + 1) % this.playlist.length;
    }

    // Force play when moving to next track
    this.isPlaying = true;
    this.loadTrack(nextIndex);
  }

  prevTrack() {
    if (this.playlist.length === 0) return;

    let prevIndex;
    if (this.audio.currentTime > 3 || this.currentTrackIndex <= 0) {
      prevIndex = this.currentTrackIndex;
      this.audio.currentTime = 0;
    } else {
      prevIndex =
        (this.currentTrackIndex - 1 + this.playlist.length) %
        this.playlist.length;
    }

    this.loadTrack(prevIndex);
  }

  toggleShuffle() {
    this.isShuffle = !this.isShuffle;
    this.elements.shuffleBtn.style.color = this.isShuffle
      ? "var(--accent)"
      : "white";
  }

  toggleRepeat() {
    this.isRepeat = !this.isRepeat;
    this.elements.repeatBtn.style.color = this.isRepeat
      ? "var(--accent)"
      : "white";
    this.audio.loop = this.isRepeat;
  }

  // File handling
  async handleFiles(files) {
    const audioFiles = Array.from(files).filter(
      (file) =>
        file.type.startsWith("audio/") ||
        [".mp3", ".wav", ".flac", ".ogg", ".m4a"].some(
          (ext) => file.name.toLowerCase().endsWith(ext) // Use toLowerCase for case-insensitivity
        )
    );

    if (audioFiles.length === 0) {
      alert("No valid audio files selected");
      return;
    }

    // Show some loading indicator (optional)
    console.log(`Uploading ${audioFiles.length} files...`);

    const formData = new FormData();
    audioFiles.forEach((file) => {
      formData.append("files", file, file.name); // Append each file
    });

    try {
      // Step 1: Upload files to the backend
      const uploadResponse = await fetch("/api/upload", {
        method: "POST",
        body: formData,
      });

      if (!uploadResponse.ok) {
        const errorData = await uploadResponse.json();
        throw new Error(
          `Upload failed: ${uploadResponse.status} - ${
            errorData.error || "Unknown error"
          }`
        );
      }

      const uploadResult = await uploadResponse.json();
      console.log("Upload successful:", uploadResult);

      // Step 2: Process uploaded files and fetch metadata
      if (uploadResult.status === "success" && uploadResult.files) {
        for (const uploadedFile of uploadResult.files) {
          // Basic track info from upload response
          const track = {
            title: uploadedFile.filename.replace(/\.[^/.]+$/, ""), // Use original filename
            artist: "Unknown Artist", // Default, will be updated by metadata
            album: "", // Default
            path: uploadedFile.path, // Use the server path (e.g., /static/uploads/...)
            art: "/static/img/default-album.png", // Default
            filename: uploadedFile.filename, // Store original filename for metadata fetch
          };

          // Step 3: Fetch metadata for the *uploaded* file using its original filename
          try {
            // Use the original filename returned by the upload endpoint
            const metadataResponse = await fetch(
              `/api/metadata?filename=${encodeURIComponent(track.filename)}`
            );
            if (metadataResponse.ok) {
              const metadata = await metadataResponse.json();
              track.title = metadata.title || track.title;
              track.artist = metadata.artist || track.artist;
              track.album = metadata.album || track.album;
              track.duration = metadata.duration || 0;
              // track.art = metadata.album_art || track.art; // Uncomment if backend provides art URL
              console.log(`Metadata fetched for ${track.filename}:`, metadata);
            } else {
              console.warn(
                `Failed to fetch metadata for ${track.filename}:`,
                metadataResponse.status
              );
              // Keep defaults if metadata fetch fails
            }
          } catch (error) {
            console.error(
              `Error fetching metadata for ${track.filename}:`,
              error
            );
            // Keep defaults if metadata fetch fails
          }

          // Add track to playlist and UI
          this.playlist.push(track);
          this.addToPlaylistUI(track);
        }

        // Load the first track if playlist was empty
        if (this.currentTrackIndex === -1 && this.playlist.length > 0) {
          this.loadTrack(0);
        }
      } else {
        console.error("Upload response format incorrect:", uploadResult);
        alert("Upload completed but response format was unexpected.");
      }
    } catch (error) {
      console.error("Error during file handling:", error);
      alert(`An error occurred during upload: ${error.message}`);
    } finally {
      // Hide loading indicator (optional)
      console.log("File handling finished.");
      // Clear the file input to allow re-uploading the same file(s)
      this.elements.fileUpload.value = "";
    }
  }

  // UI Updates
  addToPlaylistUI(track) {
    const item = document.createElement("div");
    item.className = "playlist-item";
    item.innerHTML = `
            <span class="track-title">${track.title}</span>
            <span class="track-artist">${track.artist}</span>
            <span class="track-album">${track.album}</span>
        `;
    item.addEventListener("click", () => {
      const index = this.playlist.findIndex((t) => t.path === track.path);
      if (index !== -1) this.loadTrack(index);
    });
    this.elements.playlistContainer.appendChild(item);
  }

  updatePlaylistUI() {
    const items =
      this.elements.playlistContainer.querySelectorAll(".playlist-item");
    items.forEach((item, index) => {
      item.classList.toggle("active", index === this.currentTrackIndex);
    });
  }

  async clearPlaylist() {
    // Clear files from the backend uploads directory
    try {
      const response = await fetch("/api/clear_uploads", {
        method: "POST",
      });
      if (!response.ok) {
        const errorData = await response.json();
        console.error(
          "Failed to clear uploads directory:",
          response.status,
          errorData.error
        );
        alert("Failed to clear uploaded files from the server.");
      } else {
        console.log("Uploads directory cleared on the server.");
      }
    } catch (error) {
      console.error("Error calling clear_uploads API:", error);
      alert("An error occurred while trying to clear uploaded files.");
    }

    // Clear the frontend playlist UI and state
    this.playlist = [];
    this.currentTrackIndex = -1;
    this.elements.playlistContainer.innerHTML = "";
    this.audio.src = ""; // Stop playback and clear current source
    this.updateMetadataUI(); // Reset displayed metadata
    this.updatePlayState(false); // Ensure play button shows 'play'
  }

  updateMetadataUI() {
    this.elements.trackTitle.textContent = "No Track Selected";
    this.elements.trackArtist.textContent = "";
    this.elements.trackAlbum.textContent = "";
    this.elements.albumArt.src = "/static/img/default-album.png";
    this.elements.lyricsContent.textContent = "";
  }

  // Lyrics
  async fetchLyrics(artist, title) {
    if (!title || artist === "Unknown Artist") {
      this.elements.lyricsContent.textContent =
        "No lyrics available for unknown artist";
      return;
    }

    try {
      // Only try local API
      const response = await fetch(
        `/api/lyrics?artist=${encodeURIComponent(
          artist
        )}&title=${encodeURIComponent(title)}`
      );

      if (response.ok) {
        const data = await response.json();
        const lyrics = data.lyrics || "Lyrics not found";
        // Replace newline characters with HTML break tags for formatting
        this.elements.lyricsContent.innerHTML = lyrics.replace(
          /\r\n|\n/g,
          "<br>"
        );
      } else {
        this.elements.lyricsContent.innerHTML = "No lyrics available";
      }
    } catch (error) {
      console.error("Lyrics fetch error:", error);
      this.elements.lyricsContent.innerHTML = "Error loading lyrics";
    }
  }
}

// Initialize player when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  const player = new ModernMusicPlayer();
  window.player = player; // Make available globally for debugging
});
