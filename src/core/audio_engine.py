import os
from threading import Lock
from typing import Any, Dict, Optional

import numpy as np
import sounddevice as sd
from pydub import AudioSegment


class AudioEngine:
    def __init__(self, sample_rate: int = 44100, channels: int = 2) -> None:
        self.sample_rate: int = sample_rate
        self.channels: int = channels
        self.current_file: Optional[str] = None
        # Define more specific type for audio_data if possible, e.g., np.ndarray
        self.audio_data: Optional[np.ndarray[Any, Any]] = None
        self.position: int = 0
        self.stream: Optional[sd.OutputStream] = None
        self.is_playing: bool = False
        self._lock: Lock = Lock()
        self._volume: float = 1.0

    def load_file(self, file_path: str) -> Dict[str, Any]:
        """Load an audio file and return its metadata."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        # Load audio file using pydub
        audio = AudioSegment.from_file(file_path)

        # Convert to numpy array
        samples = np.array(audio.get_array_of_samples())
        if audio.channels == 2:
            samples = samples.reshape((-1, 2))

        # Convert to float32 and normalize
        # Ensure audio_data is correctly typed after assignment
        self.audio_data = samples.astype(np.float32) / np.iinfo(samples.dtype).max

        self.current_file = file_path
        self.position = 0

        return {
            'duration': len(audio) / 1000.0,  # Duration in seconds
            'sample_rate': audio.frame_rate,
            'channels': audio.channels,
            'format': audio.channels * 2,  # Bits per sample
        }

    def play(self, position: float = 0.0) -> None:
        """Start playback from the specified position in seconds."""
        if self.audio_data is None:
            raise RuntimeError("No audio file loaded")

        with self._lock:
            if self.stream is not None:
                try:
                    self.stream.stop()
                    self.stream.close()
                except sd.PortAudioError as e:
                    print(f"Error stopping/closing stream: {e}")  # Log error
                self.stream = None

            self.position = int(position * self.sample_rate)
            self.is_playing = True

            def callback(outdata: np.ndarray[Any, Any], frames: int,
                        time: Dict[str, Any], status: sd.CallbackFlags) -> None:
                if status:
                    print(status)  # Consider logging instead of printing

                if self.audio_data is not None and self.is_playing:
                    # Ensure self.audio_data is not None before accessing len
                    if self.position >= len(self.audio_data):
                        self.is_playing = False
                        raise sd.CallbackStop()

                    chunk = self.audio_data[self.position:self.position + frames]
                    chunk_len = len(chunk)
                    if chunk_len < frames:
                        outdata[:chunk_len] = chunk * self._volume
                        outdata[chunk_len:] = 0
                        self.is_playing = False
                        raise sd.CallbackStop()
                    else:
                        outdata[:] = chunk * self._volume

                    self.position += frames
                else:
                    outdata.fill(0)
                    raise sd.CallbackStop()

            self.stream = sd.OutputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                callback=callback,
                finished_callback=self.on_playback_finished
            )
            self.stream.start()

    def pause(self) -> None:
        """Pause playback."""
        with self._lock:
            self.is_playing = False

    def resume(self) -> None:
        """Resume playback from current position."""
        if self.audio_data is not None:
            self.play(self.position / self.sample_rate)

    def stop(self) -> None:
        """Stop playback and reset position."""
        with self._lock:
            self.is_playing = False
            self.position = 0
            if self.stream is not None:
                try:
                    self.stream.stop()
                    self.stream.close()
                except sd.PortAudioError as e:
                    print(f"Error stopping/closing stream: {e}")  # Log error
                self.stream = None

    def seek(self, position: float) -> None:
        """Seek to position in seconds."""
        if self.audio_data is not None:
            was_playing = self.is_playing
            self.stop()
            if was_playing:
                self.play(position)
            else:
                self.position = int(position * self.sample_rate)

    def set_volume(self, volume: float) -> None:
        """Set volume level (0.0 to 1.0)."""
        self._volume = max(0.0, min(1.0, volume))

    def get_position(self) -> float:
        """Get current position in seconds."""
        return self.position / self.sample_rate if self.audio_data is not None else 0.0

    def get_duration(self) -> float:
        """Get audio duration in seconds."""
        return (
            len(self.audio_data) / self.sample_rate
            if self.audio_data is not None
            else 0.0
        )

    def get_waveform(self, width: int = 800) -> np.ndarray:
        """Generate waveform data for visualization."""
        if self.audio_data is None:
            # Return an array of the correct type
            return np.zeros(width, dtype=np.float32)

        # Calculate number of samples per pixel
        num_samples = len(self.audio_data)
        samples_per_pixel = num_samples // width
        if samples_per_pixel < 1:
            samples_per_pixel = 1

        # Reshape audio data to calculate min/max for each pixel
        num_samples = len(self.audio_data)
        samples_per_pixel = num_samples // width
        if samples_per_pixel < 1:
            # Handle cases where width > num_samples (upsampling or interpolation needed)
            # For simplicity, we might just return the data or a simple representation
            # Or repeat samples:
            if num_samples > 0:
                 indices = np.linspace(0, num_samples - 1, width, dtype=int)
                 return self.audio_data.mean(axis=1)[indices] if self.channels == 2 else self.audio_data[indices]
            else:
                 return np.zeros(width, dtype=np.float32)


        # Ensure we don't pad excessively if width is large relative to samples
        effective_length = (num_samples // samples_per_pixel) * samples_per_pixel
        trimmed_data = self.audio_data[:effective_length]


        # Calculate waveform based on channels
        if self.channels == 2:
            # Stereo: average channels before taking max abs
            reshaped = trimmed_data.reshape(-1, samples_per_pixel, 2)
            # Calculate max absolute value across the sample window for each channel, then average
            waveform = np.max(np.abs(reshaped), axis=1).mean(axis=1)
        else:
            # Mono
            reshaped = trimmed_data.reshape(-1, samples_per_pixel)
            waveform = np.max(np.abs(reshaped), axis=1)

        # Ensure waveform length matches width, handle potential rounding issues
        final_waveform = waveform[:width]
        if len(final_waveform) < width:
             # Pad if necessary (e.g., due to integer division)
             final_waveform = np.pad(final_waveform, (0, width - len(final_waveform)))

        # Explicitly cast to float32 if necessary, though operations should maintain it
        return final_waveform.astype(np.float32)


    def on_playback_finished(self) -> None:
        """Callback when playback finishes."""
        self.is_playing = False
        if self.stream is not None:
            self.stream.close()
            self.stream = None
