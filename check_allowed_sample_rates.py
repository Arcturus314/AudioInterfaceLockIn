import pyaudio

p = pyaudio.PyAudio()

found = False
index = 0

while not found:
    devinfo = p.get_device_info_by_index(index)
    devname = devinfo['name']  # Or whatever device you care about.
    print("detected",devname)
    if "M2" not in devname: index += 1
    else: found = True

print(devinfo)

if p.is_format_supported(192000,  # Sample rate
                         input_device=devinfo['index'],
                         input_channels=devinfo['maxInputChannels'],
                         input_format=pyaudio.paFloat32):
  print('Yay!')

