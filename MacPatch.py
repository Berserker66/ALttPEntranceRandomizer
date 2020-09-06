import sys
import tkinter as tk
from tkinter import filedialog

root = tk.Tk()
root.withdraw()

file_path = filedialog.askopenfilename()

print(sys.argv)
script_mac_patch = open("MultiClient.py")
mac_patch = script_mac_patch.read()
sys.argv = ["MultiClient.py", file_path]

exec(mac_patch)
OUTPUT
['MultiClient.py', file_path]

script_mac_patch.close()
