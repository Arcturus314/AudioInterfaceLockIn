import numpy as np
import pyaudio
import matplotlib.pyplot as plt
from scipy.fft import fft, fftfreq
from scipy.signal import butter, sosfilt
import time
import statistics
from threading import Thread

# ----- LOCKIN SETUP -----

f = 5123
cutoff_f = 2
cutoff_order = 4

# ----- PYAUDIO SETUP -----

FORMAT = pyaudio.paFloat32
CHANNELS = 2
RATE = 48000
CHUNK = 4096   # one second / chunk
duration = 200 # duration to play output signal
device_name = "M2"

# ---- OUTPUT SETUP ----

def outputtone():
    samples_1ch = (np.sin(2*np.pi*np.arange(RATE*duration)*f/RATE)).astype(np.float32)
    samples_2ch = []
    for s in samples_1ch:
        samples_2ch.append(s)
        samples_2ch.append(s)

    samples_2ch = np.array(samples_2ch).astype(np.float32)

    pout = pyaudio.PyAudio()

    streamout = pout.open(
                       input_device_index = device_index,
                       format=FORMAT,
                       channels=CHANNELS,
                       rate=RATE,
                       output=True)

    streamout.write(samples_2ch)
    streamout.stop_stream()
    streamout.close()
    pout.terminate()

# ---- GENERATING LOCKIN LOW-PASS ----

soscoeff = butter(cutoff_order, cutoff_f / (RATE/2), btype='low', analog=False, output='sos')
filt_state_x = np.zeros((soscoeff.shape[0], 2))
filt_state_y = np.zeros((soscoeff.shape[0], 2))

def lowpass(signal, filt_state):
    y, new_state = sosfilt(soscoeff, signal, zi=filt_state)
    return y, new_state

# ---- LOCK-IN PROCESSING ----

def process_chunk(chunk, filt_state_x, filt_state_y):

    data_int = np.frombuffer(chunk, np.float32)

    data_ch1 = []
    data_ch2 = []

    for i in range(0,len(data_int),2):
        data_ch1.append(data_int[i])
        data_ch2.append(data_int[i+1])

    ch1_max = max(data_ch1)
    ch2_max = max(data_ch2)
    ch1_normalized = [d/ch1_max for d in data_ch1]
    ch2_normalized = [d/ch2_max for d in data_ch2]

    ch1_normalized_phaseshift = ch1_normalized[y_indexshift:]

    product_x = [s*f for s, f in zip(ch1_normalized, ch2_normalized)]
    product_x_lp, new_state_x = lowpass(product_x, filt_state_x)

    product_y = [s*f for s, f in zip(ch1_normalized_phaseshift, ch2_normalized)]
    product_y_lp, new_state_y = lowpass(product_y, filt_state_y)

    xout = round(statistics.mean(product_x_lp), 3)
    yout = round(statistics.mean(product_y_lp), 3)

    print("X:", str(xout) + " "*(10-len(str(xout))) +  "Y:", str(yout))

    logf = open("log.txt", "a")
    logf.write(str(xout)+","+str(yout)+"\n")
    logf.close()


    #plt.plot(ch1_normalized, alpha=0.3)
    #plt.plot(ch1_normalized_phaseshift, alpha=0.3)
    #plt.show()
    #plt.close()

    return new_state_x, new_state_y

# ---- OPENING PYAUDIO FOR RECORD ----

def callback(in_data, frame_count, time_info, status):
    global filt_state
    filt_state = process_chunk(in_data, filt_state)
    return in_data, pyaudio.paContinue

pin = pyaudio.PyAudio()


found = False
index = 0

while not found:
    devinfo = pin.get_device_info_by_index(index)
    devname = devinfo['name']  # Or whatever device you care about.
    print("detected",devname)
    if "M2" not in devname: index += 1
    else: found = True

device_index = int(devinfo['index'])

print(pin.get_device_info_by_index(device_index))

# ---- STARTING TEST ----

# clearing log file
logf = open("log.txt", "w")
logf.write("x,y\n")
logf.close()

y_indexshift = int(1/f * RATE / 4) # samples in one wavelength / 4 -> samples for 90 degree phase shift
print("1/4 period ->",y_indexshift,"samples")

print("starting playback")
Thread(target=outputtone).start()

stream = pin.open(
    input_device_index=device_index,
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    output=False,
    input=True,
    frames_per_buffer=CHUNK)

for i in range(1000):
   new_state_x, new_state_y =  process_chunk(stream.read(CHUNK), filt_state_x, filt_state_y)
   filt_state_x = new_state_x
   filt_state_y = new_state_y

stream.stop_stream()
stream.close()
pin.terminate()
