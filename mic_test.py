import pyaudio

p = pyaudio.PyAudio()

print("--- Checking for Audio Input Devices ---")

info = p.get_host_api_info_by_index(0)
numdevices = info.get('deviceCount')

if numdevices == 0:
    print("❌ No audio devices found.")
else:
    print(f"Found {numdevices} audio devices.")
    for i in range(0, numdevices):
        device_info = p.get_device_info_by_host_api_device_index(0, i)
        if device_info.get('maxInputChannels') > 0:
            print(f"✅ Input Device ID {i} - {device_info.get('name')}")

print("\n--- Finished ---")
p.terminate()