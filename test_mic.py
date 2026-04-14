import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav

def diag():
    print("--- Audio Device List ---")
    devices = sd.query_devices()
    print(devices)
    
    default_input = sd.default.device[0]
    print(f"\nCurrent Default Input Device ID: {default_input}")
    
    duration = 3  # seconds
    fs = 16000
    print(f"\nRecording for {duration} seconds... Please speak into your mic!")
    
    try:
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
        sd.wait()
        
        # Check amplitude
        max_amp = np.abs(recording).max()
        avg_amp = np.abs(recording).mean()
        
        print(f"Recording Finished.")
        print(f"Max Amplitude: {max_amp}")
        print(f"Average Amplitude: {avg_amp}")
        
        if max_amp < 100:
            print("WARNING: Very low amplitude detected. Microphone might be muted or wrong device selected.")
        
        wav.write("test_audio.wav", fs, recording)
        print("Test file saved as 'test_audio.wav'")
        
    except Exception as e:
        print(f"ERROR during recording: {e}")

if __name__ == "__main__":
    diag()
