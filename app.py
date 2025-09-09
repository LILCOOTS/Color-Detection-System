import serial
import tensorflow as tf
import joblib
import numpy as np
import tkinter as tk
import re
import threading

class ArduinoColorDetectorGUI:
    def __init__(self):
        # Create window
        self.root = tk.Tk()
        self.root.title("🎨 Arduino Color Detector")
        self.root.geometry("600x400")
        self.root.configure(bg='black')
        
        # Force window to appear on top
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after_idle(lambda: self.root.attributes('-topmost', False))
        
        # Load model
        print("🎨 Arduino Color Detection System")
        print("=" * 40)
        print("Loading AI model...")
        self.model = tf.keras.models.load_model("color_model.h5")
        self.label_encoder = joblib.load("label_encoder.pkl")
        print("✅ Model loaded successfully!")
        print(f"📋 Available colors: {', '.join(self.label_encoder.classes_)}")
        
        # Setup GUI
        self.setup_gui()
        
        # Start Arduino connection
        self.start_arduino()
    
    def setup_gui(self):
        # Title
        tk.Label(self.root, text="🎨 Arduino Color Detector", 
                font=("Arial", 20, "bold"), bg="black", fg="white").pack(pady=20)
        
        # Main color display
        self.color_display = tk.Label(self.root, text="WAITING", 
                                    font=("Arial", 48, "bold"), 
                                    bg="gray", fg="white", 
                                    width=20, height=8)
        self.color_display.pack(expand=True, fill="both", padx=50, pady=20)
        
        # Info
        self.info_label = tk.Label(self.root, text="🔌 Connecting to Arduino...", 
                                 font=("Arial", 12), bg="black", fg="cyan")
        self.info_label.pack(pady=10)
    
    def get_color_code(self, color_name):
        colors = {
            "red": "#FF0000", "green": "#00FF00", "blue": "#0000FF",
            "yellow": "#FFFF00", "orange": "#FFA500", "purple": "#800080",
            "pink": "#FFC0CB", "brown": "#8B4513", "white": "#FFFFFF",
            "black": "#000000", "gray": "#808080", "cyan": "#00FFFF",
            "ufo green": "#7CE263", "lime": "#32CD32", "forest green": "#228B22",
            "dark green": "#006400", "light green": "#90EE90", "sea green": "#2E8B57",
            "olive": "#808000", "turquoise": "#40E0D0", "teal": "#008080"
        }
        
        # Try exact match first
        if color_name.lower() in colors:
            return colors[color_name.lower()]
        
        # Try partial matches for green variants
        color_lower = color_name.lower()
        if "green" in color_lower:
            if "ufo" in color_lower or "lime" in color_lower:
                return "#7CE263"  # UFO Green
            elif "dark" in color_lower:
                return "#006400"
            elif "light" in color_lower:
                return "#90EE90"
            else:
                return "#00FF00"  # Default green
        
        # Try other color matches
        if "red" in color_lower:
            return "#FF0000"
        elif "blue" in color_lower:
            return "#0000FF"
        elif "yellow" in color_lower:
            return "#FFFF00"
        elif "orange" in color_lower:
            return "#FFA500"
        elif "purple" in color_lower or "violet" in color_lower:
            return "#800080"
        elif "pink" in color_lower:
            return "#FFC0CB"
        elif "brown" in color_lower:
            return "#8B4513"
        elif "white" in color_lower:
            return "#FFFFFF"
        elif "black" in color_lower:
            return "#000000"
        elif "cyan" in color_lower:
            return "#00FFFF"
        
        return "#808080"  # Default gray
    
    def update_color(self, r, g, b, color_name, confidence):
        # Try to get color from name first
        bg_color = self.get_color_code(color_name)
        
        # If it's still gray (default), use the actual RGB values
        if bg_color == "#808080" and not "gray" in color_name.lower():
            bg_color = f"#{r:02x}{g:02x}{b:02x}"
        
        # Change background color
        self.color_display.configure(bg=bg_color, text=color_name.upper())
        
        # Update info
        self.info_label.configure(text=f"RGB({r},{g},{b}) - {confidence:.1f}% confident")
        
        print(f"🎯 {color_name} detected! RGB({r},{g},{b}) -> Color: {bg_color}")
    
    def parse_arduino_data(self, line):
        """Parse Arduino data format: 'Color -> R: 1  G: 1  B: 1  |  HEX: #010101  |  Name: Black'"""
        try:
            match = re.search(r'R:\s*(\d+)\s*G:\s*(\d+)\s*B:\s*(\d+)', line)
            if match:
                return list(map(int, match.groups()))
        except:
            pass
        return None
    
    def predict_color(self, r, g, b):
        """Predict color from RGB values using AI model"""
        rgb = np.array([[r, g, b]]) / 255.0
        pred = self.model.predict(rgb, verbose=0)
        color_name = self.label_encoder.inverse_transform([np.argmax(pred)])[0]
        confidence = np.max(pred) * 100
        return color_name, confidence
    
    def start_arduino(self):
        def arduino_worker():
            try:
                ser = serial.Serial("COM13", 9600, timeout=1)
                self.root.after(0, lambda: self.info_label.configure(text="✅ Connected to Arduino!"))
                print("✅ Serial connection established!")
                print("🤖 Arduino Color Detection Active!")
                print("📡 Listening for RGB data...")
                
                while True:
                    line = ser.readline().decode().strip()
                    if line:
                        rgb = self.parse_arduino_data(line)
                        if rgb:
                            r, g, b = rgb
                            color_name, confidence = self.predict_color(r, g, b)
                            
                            # Update GUI from main thread
                            self.root.after(0, self.update_color, r, g, b, color_name, confidence)
                            
            except serial.SerialException as e:
                error_msg = f"❌ Serial Error: {str(e)[:50]}..."
                self.root.after(0, lambda: self.info_label.configure(text=error_msg))
                print(f"❌ Serial port error: {e}")
                print("Make sure:")
                print("  - Arduino is connected to COM13")
                print("  - Arduino IDE Serial Monitor is closed")
                print("  - Correct baud rate (9600)")
            except Exception as e:
                error_msg = f"❌ Error: {str(e)[:50]}..."
                self.root.after(0, lambda: self.info_label.configure(text=error_msg))
                print(f"❌ Unexpected error: {e}")
        
        # Start in background thread
        thread = threading.Thread(target=arduino_worker, daemon=True)
        thread.start()
    
    def run(self):
        print("🚀 Starting GUI...")
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\n🛑 Program stopped by user.")
            print("👋 Goodbye!")

def main():
    """Main function to start the Arduino Color Detection GUI"""
    try:
        app = ArduinoColorDetectorGUI()
        app.run()
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        print("Make sure you have:")
        print("  - color_model.h5 file")
        print("  - label_encoder.pkl file")
        print("  - Arduino connected to COM13")

if __name__ == "__main__":
    main()