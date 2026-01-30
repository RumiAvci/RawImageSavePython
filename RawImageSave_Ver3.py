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
        self.phi_axis = None
        self.r_axis = None
        
        self.params = {
            'rMin': tk.DoubleVar(value=10.0),
            'rMax': tk.DoubleVar(value=100.0),
            'rRes': tk.DoubleVar(value=2.0),
            'thetaMin': tk.DoubleVar(value=-20.0),
            'thetaMax': tk.DoubleVar(value=20.0),
            'thetaRes': tk.DoubleVar(value=10.0),
            'phiMin': tk.DoubleVar(value=-45.0),
            'phiMax': tk.DoubleVar(value=45.0),
            'phiRes': tk.DoubleVar(value=2.0),
            'threshold': tk.DoubleVar(value=15.0),
            'mti': tk.BooleanVar(value=True)
        }
        
        self.setup_ui()
        self.init_walabot()
        
    def setup_ui(self):
        config_frame = tk.LabelFrame(self.root, text="Walabot Configuration", padx=10, pady=10)
        config_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        entries = [
            ('rMin', 'value between 1 and 1000'),
            ('rMax', 'value between 1 and 1000'),
            ('rRes', 'value between 0.1 and 10'),
            ('thetaMin', 'value between -90 and 90'),
            ('thetaMax', 'value between -90 and 90'),
            ('thetaRes', 'value between 0.1 and 10'),
            ('phiMin', 'value between -90 and 90'),
            ('phiMax', 'value between -90 and 90'),
            ('phiRes', 'value between 0.1 and 10'),
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
        
        self.frame_label = tk.Label(control_frame, text="FRAME_RATE: 0")
        self.frame_label.grid(row=3, column=0, columnspan=3, pady=5)
        
        image_frame = tk.LabelFrame(self.root, text="Raw Image Slice: Phi / R", padx=10, pady=10)
        image_frame.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky="nsew")
        
        self.fig = Figure(figsize=(8, 6))
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel('Phi (degrees)')
        self.ax.set_ylabel('R (cm)')
        self.ax.set_title('Raw Image Slice')
        
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
        wlbt.SetProfile(wlbt.PROF_SENSOR)
        
        wlbt.SetArenaR(self.params['rMin'].get(), self.params['rMax'].get(), self.params['rRes'].get())
        wlbt.SetArenaTheta(self.params['thetaMin'].get(), self.params['thetaMax'].get(), self.params['thetaRes'].get())
        wlbt.SetArenaPhi(self.params['phiMin'].get(), self.params['phiMax'].get(), self.params['phiRes'].get())
        wlbt.SetThreshold(self.params['threshold'].get())
        
        filter_type = wlbt.FILTER_TYPE_MTI if self.params['mti'].get() else wlbt.FILTER_TYPE_NONE
        wlbt.SetDynamicImageFilter(filter_type)
        
        wlbt.Start()
        
    def start_scan(self):
        try:
            self.configure_walabot()
            self.running = True
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.save_btn.config(state=tk.DISABLED)
            self.status_label.config(text="APP_STATUS: STATUS_SCANNING")
            self.exception_label.config(text="EXCEPTION: None", fg="green")
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
        if self.current_image is not None:
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
            
            phiMin = self.params['phiMin'].get()
            phiMax = self.params['phiMax'].get()
            rMin = self.params['rMin'].get()
            rMax = self.params['rMax'].get()
            
            self.phi_axis = np.linspace(phiMin, phiMax, sizeX)
            self.r_axis = np.linspace(rMin, rMax, sizeY)
            
            self.ax.clear()
            im = self.ax.imshow(image_array, aspect='auto', origin='lower', 
                               extent=[phiMin, phiMax, rMin, rMax], 
                               cmap='jet', interpolation='bilinear')
            self.ax.set_xlabel('Phi (degrees)')
            self.ax.set_ylabel('R (cm)')
            self.ax.set_title('Raw Image Slice')
            
            self.canvas.draw()
            
            self.root.after(100, self.update_image)
            
        except Exception as e:
            self.exception_label.config(text=f"EXCEPTION: {str(e)}", fg="red")
            self.running = False
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            
    def save_image(self):
        if self.current_image is None:
            messagebox.showwarning("Warning", "No image data to save.")
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"walabot_rawimage_{timestamp}.csv"
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=default_filename
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    writer.writerow(['Walabot Raw Image Slice Data'])
                    writer.writerow(['Timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
                    writer.writerow([])
                    
                    writer.writerow(['Configuration Parameters'])
                    writer.writerow(['rMin', self.params['rMin'].get()])
                    writer.writerow(['rMax', self.params['rMax'].get()])
                    writer.writerow(['rRes', self.params['rRes'].get()])
                    writer.writerow(['thetaMin', self.params['thetaMin'].get()])
                    writer.writerow(['thetaMax', self.params['thetaMax'].get()])
                    writer.writerow(['thetaRes', self.params['thetaRes'].get()])
                    writer.writerow(['phiMin', self.params['phiMin'].get()])
                    writer.writerow(['phiMax', self.params['phiMax'].get()])
                    writer.writerow(['phiRes', self.params['phiRes'].get()])
                    writer.writerow(['threshold', self.params['threshold'].get()])
                    writer.writerow(['MTI', self.params['mti'].get()])
                    writer.writerow([])
                    
                    writer.writerow(['Image Data'])
                    writer.writerow(['Rows (R axis):', len(self.r_axis)])
                    writer.writerow(['Columns (Phi axis):', len(self.phi_axis)])
                    writer.writerow([])
                    
                    header = ['R \\ Phi'] + [f'{phi:.2f}' for phi in self.phi_axis]
                    writer.writerow(header)
                    
                    for i, r_val in enumerate(self.r_axis):
                        row = [f'{r_val:.2f}'] + list(self.current_image[i, :])
                        writer.writerow(row)
                
                messagebox.showinfo("Success", f"Image data saved to:\n{filename}")
                
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