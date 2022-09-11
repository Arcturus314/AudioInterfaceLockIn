import matplotlib.pyplot as plt
import pandas as pd

data = pd.read_csv("log.txt")
plt.plot(data['x'], label='x')
plt.plot(data['y'], label='y')
plt.xlabel("time")
plt.legend()
plt.grid()
plt.show()
