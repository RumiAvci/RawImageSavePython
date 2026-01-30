import WalabotAPI as wlbt
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import csv
from datetime import datetime

class WalabotRawImageApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Walabot - Raw Image Slice Example")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.running = False
        self.current_image = None
        self.x_axis = None
        self.y_axis = None
        self.captured_slices = []
        
        self.params = {
            'xMin': tk.DoubleVar(value=-10.0),
            'xMax': tk.DoubleVar(value=10.0),
            'xRes': tk.DoubleVar(value=1.0),
            'yMin': tk.DoubleVar(value=-10.0),
            'yMax': tk.DoubleVar(value=10.0),
            'yRes': tk.DoubleVar(value=1.0),
            'zMin': tk.DoubleVar(value=5.0),
            'zMax': tk.DoubleVar(value=50.0),
            'zRes': tk.DoubleVar(value=2.0),
            'threshold': tk.DoubleVar(value=15.0),
            'mti': tk.BooleanVar(value=True)
        }
        
        self.setup_ui()
        self.init_walabot()
        
    def setup_ui(self):
        config_frame = tk.LabelFrame(self.root, text="Walabot Configuration", padx=10, pady=10)
        config_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        entries = [
            ('xMin', 'value between -100 and 100'),
            ('xMax', 'value between -100 and 100'),
            ('xRes', 'value between 0.1 and 10'),
            ('yMin', 'value between -100 and 100'),
            ('yMax', 'value between -100 and 100'),
            ('yRes', 'value between 0.1 and 10'),
            ('zMin', 'value between 1 and 100'),
            ('zMax', 'value between 1 and 100'),
            ('zRes', 'value between 0.1 and 10'),
            ('threshold', 'value between 0.1 and 100')
        ]
        
        for i, (param, hint) in enumerate(entries):
            tk.Label(config_frame, text=f"{param} = ").grid(row=i, column=0, sticky="e")
            entry = tk.Entry(config_frame, textvariable=self.params[param], width=10)
            entry.grid(row=i, column=1, padx=5)
            tk.Label(config_frame, text=hint, fg="gray").grid(row=i, column=2, sticky="w")
        
        tk.Label(config_frame, text="mti = ").grid(row=len(entries), column=0, sticky="e")
        mti_frame = tk.Frame(config_frame)
        mti_frame.grid(row=len(entries), column=1, columnspan=2, sticky="w")
        tk.Radiobutton(mti_frame, text="True", variable=self.params['mti'], value=True).pack(side=tk.LEFT)
        tk.Radiobutton(mti_frame, text="False", variable=self.params['mti'], value=False).pack(side=tk.LEFT)
        
        control_frame = tk.LabelFrame(self.root, text="Control Panel", padx=10, pady=10)
        control_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        
        self.start_btn = tk.Button(control_frame, text="Start", command=self.start_scan, width=10)
        self.start_btn.grid(row=0, column=0, padx=5, pady=5)
        
        self.stop_btn = tk.Button(control_frame, text="Stop", command=self.stop_scan, width=10, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=1, padx=5, pady=5)
        
        self.save_btn = tk.Button(control_frame, text="Save", command=self.save_image, width=10, bg="#4CAF50", fg="white", state=tk.DISABLED)
        self.save_btn.grid(row=0, column=2, padx=5, pady=5)
        
        self.status_label = tk.Label(control_frame, text="APP_STATUS: STATUS_CONNECTED")
        self.status_label.grid(row=1, column=0, columnspan=3, pady=5)
        
        self.exception_label = tk.Label(control_frame, text="EXCEPTION: None", fg="green")
        self.exception_label.grid(row=2, column=0, columnspan=3, pady=5)
        
        self.frame_label = tk.Label(control_frame, text="CAPTURED SLICES: 0")
        self.frame_label.grid(row=3, column=0, columnspan=3, pady=5)
        
        image_frame = tk.LabelFrame(self.root, text="Raw Image Slice: X / Y", padx=10, pady=10)
        image_frame.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky="nsew")
        
        self.fig = Figure(figsize=(8, 6))
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel('X (cm)')
        self.ax.set_ylabel('Y (cm)')
        self.ax.set_title('Raw Image Slice (X-Y plane)')
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=image_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)
        
    def init_walabot(self):
        try:
            wlbt.Init()
            wlbt.SetSettingsFolder()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to initialize Walabot: {str(e)}")
            
    def configure_walabot(self):
        wlbt.ConnectAny()
        wlbt.SetProfile(wlbt.PROF_SHORT_RANGE_IMAGING)
        
        wlbt.SetArenaX(self.params['xMin'].get(), self.params['xMax'].get(), self.params['xRes'].get())
        wlbt.SetArenaY(self.params['yMin'].get(), self.params['yMax'].get(), self.params['yRes'].get())
        wlbt.SetArenaZ(self.params['zMin'].get(), self.params['zMax'].get(), self.params['zRes'].get())
        wlbt.SetThreshold(self.params['threshold'].get())
        
        filter_type = wlbt.FILTER_TYPE_MTI if self.params['mti'].get() else wlbt.FILTER_TYPE_NONE
        wlbt.SetDynamicImageFilter(filter_type)
        
        wlbt.Start()
        
    def start_scan(self):
        try:
            self.captured_slices = []
            self.configure_walabot()
            self.running = True
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.save_btn.config(state=tk.DISABLED)
            self.status_label.config(text="APP_STATUS: STATUS_SCANNING")
            self.exception_label.config(text="EXCEPTION: None", fg="green")
            self.frame_label.config(text="CAPTURED SLICES: 0")
            self.update_image()
        except Exception as e:
            self.exception_label.config(text=f"EXCEPTION: {str(e)}", fg="red")
            messagebox.showerror("Error", str(e))
            self.running = False
            
    def stop_scan(self):
        self.running = False
        try:
            wlbt.Stop()
            wlbt.Disconnect()
        except:
            pass
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        if len(self.captured_slices) > 0:
            self.save_btn.config(state=tk.NORMAL)
        self.status_label.config(text="APP_STATUS: STATUS_CONNECTED")
        
    def update_image(self):
        if not self.running:
            return
            
        try:
            wlbt.Trigger()
            rasterImage, sizeX, sizeY, sliceDepth, power = wlbt.GetRawImageSlice()
            
            image_array = np.array(rasterImage).reshape((sizeY, sizeX))
            self.current_image = image_array
            self.captured_slices.append(image_array.copy())
            
            xMin = self.params['xMin'].get()
            xMax = self.params['xMax'].get()
            yMin = self.params['yMin'].get()
            yMax = self.params['yMax'].get()
            
            self.x_axis = np.linspace(xMin, xMax, sizeX)
            self.y_axis = np.linspace(yMin, yMax, sizeY)
            
            self.ax.clear()
            im = self.ax.imshow(image_array, aspect='auto', origin='lower', 
                               extent=[xMin, xMax, yMin, yMax], 
                               cmap='jet', interpolation='bilinear')
            self.ax.set_xlabel('X (cm)')
            self.ax.set_ylabel('Y (cm)')
            self.ax.set_title(f'Raw Image Slice (X-Y plane at Z={sliceDepth:.2f} cm)')
            
            self.canvas.draw()
            
            self.frame_label.config(text=f"CAPTURED SLICES: {len(self.captured_slices)}")
            
            self.root.after(100, self.update_image)
            
        except Exception as e:
            self.exception_label.config(text=f"EXCEPTION: {str(e)}", fg="red")
            self.running = False
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            
    def save_image(self):
        if len(self.captured_slices) == 0:
            messagebox.showwarning("Warning", "No image data to save.")
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"walabot_slices_{timestamp}.csv"
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=default_filename
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    num_slices = len(self.captured_slices)
                    rows, cols = self.captured_slices[0].shape
                    
                    for slice_idx, slice_data in enumerate(self.captured_slices):
                        for row in slice_data:
                            writer.writerow(row)
                        
                        if slice_idx < num_slices - 1:
                            writer.writerow([])
                
                messagebox.showinfo("Success", f"Saved {num_slices} slices to:\n{filename}\n\nTotal rows: {rows}, columns: {cols} per slice")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file:\n{str(e)}")
    
    def on_closing(self):
        if self.running:
            self.stop_scan()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = WalabotRawImageApp(root)
    root.mainloop()