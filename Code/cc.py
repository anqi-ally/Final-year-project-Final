import os
import pyvisa
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from const import data_dir
from Signal_function import Burst_generate

# Create folder to store full serpentine scan data
def create_scan_folder():
    os.makedirs(data_dir, exist_ok=True)
    existing_scans = [d for d in os.listdir(data_dir) if d.startswith('scan_') and os.path.isdir(os.path.join(data_dir, d))]
    scan_numbers = [int(d.split('_')[1]) for d in existing_scans if d.split('_')[1].isdigit()]
    next_scan_num = max(scan_numbers, default=0) + 1
    scan_folder = os.path.join(data_dir, f'scan_{next_scan_num:03d}')
    os.makedirs(scan_folder)
    return scan_folder

def read_oscilloscope_and_save(cross, s, scan_folder):
    """
    Read full triggered waveform from oscilloscope, save as CSV, and plot the waveform.
    
    :param cross: Current row index
    :param s: Current column index
    :param scan_folder: Folder to save the waveform data
    """
    osc = None  
    
    try:
        # ✅ Connect to oscilloscope
        rm = pyvisa.ResourceManager()
        osc = rm.open_resource("USB0::0x05FF::0x1023::3557N06479::INSTR")
        osc.timeout = 50000  # ✅ 50-second timeout to prevent timeout errors
        print("✅ Successfully connected to oscilloscope:", osc.query("*IDN?"))

        # Set sampling and trigger settings
        osc.write(":TIMEBASE:SCALE 2e-6")
        osc.write(":ACQUIRE:SRATE 500e6")
        osc.write("ACQ:MODE SAMPLE")
        osc.write("TRIG_MODE NORM")
        osc.write("SINGLE")
        
        # Set trigger level
        osc.write("TRIG:LEVEL 0.5")
        
        time.sleep(1)  # Wait for trigger and waveform to stabilize

        # Read full waveform data
        osc.write("C1:WF? ALL")
        raw_data = osc.query_binary_values("C1:WF? ALL", datatype="B", container=np.array)

        # Convert data
        scale = float(osc.query("C1:VDIV?").strip().split(" ")[1])
        v_offset = float(osc.query("C1:OFST?").strip().split(" ")[1])
        voltages = (raw_data - 128) * scale + v_offset

        time_div = float(osc.query("TDIV?").strip().split(" ")[1])
        num_points = len(raw_data)
        time_values = np.linspace(0, num_points * time_div / 10, num_points)

        # ✅ Save data
        filename = f"row_{cross+1}_col_{s}.csv"
        file_path = os.path.join(scan_folder, filename)
        df = pd.DataFrame({"Time (s)": time_values, "Amplitude (V)": voltages})
        df.to_csv(file_path, index=False)
        print(f"✅ Data saved to: {file_path}")

    except Exception as e:
        print(f"❌ Failed to read oscilloscope data: {e}")
        
    finally:
        if osc:
            osc.close()
            print("✅ Oscilloscope connection closed")

def send_burst(sg, cross, s, scan_folder):
    Burst_generate(
        sg,
        shape="SIN",
        frequency=100,
        amplitude=1,
        burst_ncycles=60,
    )
    print("trigger_count")
    time.sleep(1)  
    read_oscilloscope_and_save(cross, s, scan_folder)
    time.sleep(0.5) 
    print(f"📡 Captured triggered data for row {cross+1}, column {s}...")
