import sounddevice as sd
import numpy as np
from faster_whisper import WhisperModel
import io

# Model initialization
# 'float32' CPU ke liye zyada stable hai, 'int8' speed ke liye
model = WhisperModel("small", device="cpu", compute_type="int8")

def voice_to_text(duration=10, sample_rate=16000):
    print(f"Recording for {duration} seconds...")
    
    # Recording as float32 directly (Whisper likes this)
    audio = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype='float32' # Changed from int16
    )
    sd.wait()
    print("Recording finished. Transcribing...")

    # Flatten the array for the model
    audio_data = audio.flatten()

    # Transcribe directly from memory (No need for temp files)
    segments, info = model.transcribe(
        audio_data, 
        beam_size=5, 
        language="en",
        vad_filter=True, # Background noise filter
        vad_parameters=dict(min_silence_duration_ms=500)
    )

    text = "".join([segment.text for segment in segments])
    return text.strip()

# Run the function
if __name__ == "__main__":
    result = record_and_transcribe(duration=5)
    print(f"Aapne kaha: {result}")