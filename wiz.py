import customtkinter as ctk
from tkinter import colorchooser
import json
import os
import socket
import threading
import warnings

# Warningok elnémítása
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# --- KONFIGURÁCIÓS FÁJL NEVE ---
CONFIG_FILE = "wiz_config.json"
UDP_PORT = 38899  # A WiZ szabvány portja

class WizUdpApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- ABLAK BEÁLLÍTÁSOK ---
        self.title("WiZ UDP vezérlő")
        self.geometry("400x420")
        self.resizable(False, False)
        
        try:
            self.iconbitmap("bulb.ico")
        except:
            pass      
        
        ctk.set_default_color_theme("blue")
        ctk.set_appearance_mode("Dark")

        self.config_data = {}

        # Konfiguráció betöltése vagy login
        if self.load_config():
            self.build_control_ui()
        else:
            self.build_login_ui()

    # --- KONFIGURÁCIÓ KEZELÉSE ---
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    self.config_data = json.load(f)
                return True
            except:
                return False
        return False

    def save_config(self, **kwargs):
        # Frissítjük a memóriában lévő configot és kiírjuk fájlba
        self.config_data.update(kwargs)
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.config_data, f)

    def delete_config(self):
        if os.path.exists(CONFIG_FILE):
            os.remove(CONFIG_FILE)
        for widget in self.winfo_children():
            widget.destroy()
        self.build_login_ui()

    # --- UDP KÜLDŐ MOTOR ---
    def send_udp_command(self, params):
        ip = self.config_data.get("ip")
        if not ip: return

        # WiZ JSON szerkezet
        payload = {
            "id": 1,
            "method": "setPilot",
            "params": params
        }
        
        msg = json.dumps(payload)
        
        threading.Thread(target=self._send_socket, args=(ip, msg)).start()

    def _send_socket(self, ip, msg):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(1.0)
            sock.sendto(bytes(msg, "utf-8"), (ip, UDP_PORT))
            sock.close()
        except Exception as e:
            print(f"UDP Hiba: {e}")

    # --- UI ÉPÍTÉS: BEJELENTKEZÉS ---
    def build_login_ui(self):
        self.geometry("400x420")
        
        ctk.CTkLabel(self, text="WiZ Beállítások", font=("Arial", 20, "bold")).pack(pady=20)

        self.entry_ip = ctk.CTkEntry(self, placeholder_text="Izzó IP címe (pl. 192.168.1.XXX)")
        self.entry_ip.pack(pady=10, padx=20, fill="x")

        ctk.CTkButton(self, text="Mentés", command=self.on_login_submit).pack(pady=20)

    def on_login_submit(self):
        ip = self.entry_ip.get()
        if ip:
            # Alapértelmezett értékek mentése első indításkor
            # last_mode: "white" vagy "color"
            self.save_config(ip=ip, brightness=100, temp=2700, last_mode="white", r=255, g=255, b=255)
            for widget in self.winfo_children():
                widget.destroy()
            self.geometry("400x480")
            self.build_control_ui()

    # --- UI ÉPÍTÉS: VEZÉRLÉS ---
    def build_control_ui(self):
        ctk.CTkLabel(self, text="WiZ UDP vezérlő", font=("Arial", 20, "bold")).pack(pady=(20, 10))

        # 1. KAPCSOLÓ
        self.switch_var = ctk.StringVar(value="on")
        self.switch = ctk.CTkSwitch(self, text="Állapot", command=self.on_toggle,
                                    variable=self.switch_var, onvalue="on", offvalue="off")
        self.switch.pack(pady=10)
        self.switch.select() 
        
        # 2. TECHNIKAI DOBOZ (FÉNYERŐ)
        self.frame_settings = ctk.CTkFrame(self)
        self.frame_settings.pack(pady=10, padx=20, fill="x")

        ctk.CTkLabel(self.frame_settings, text="Fényerő").pack(pady=(10, 0))
        
        # MENTETT ÉRTÉK BETÖLTÉSE
        saved_bright = self.config_data.get("brightness", 100)
        
        self.slider_bright = ctk.CTkSlider(self.frame_settings, from_=10, to=100, command=self.on_brightness_change)
        self.slider_bright.set(saved_bright) 
        self.slider_bright.pack(pady=(5, 15), padx=10, fill="x")

        # 3. LÁBLÉC
        self.btn_logout = ctk.CTkButton(self, text="IP cím módosítása", fg_color="transparent", border_width=1,
                      text_color=("gray10", "#DCE4EE"), command=self.delete_config)
        self.btn_logout.pack(side="bottom", pady=20)

        # 4. TABOK
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(pady=0, padx=20, fill="both", expand=True)

        self.tab_white = self.tabview.add("Fehér")
        self.tab_color = self.tabview.add("Színes")

        # --- TAB 1: FEHÉR ---
        ctk.CTkLabel(self.tab_white, text="Színhőmérséklet").pack(pady=0)
        saved_temp = self.config_data.get("temp", 2700)

        self.slider_temp = ctk.CTkSlider(self.tab_white, from_=2200, to=6500, number_of_steps=40,
                                         command=self.on_temp_change)
        self.slider_temp.set(saved_temp)
        self.slider_temp.pack(pady=10, padx=10, fill="x")
        
        self.label_temp_val = ctk.CTkLabel(self.tab_white, text=f"{int(saved_temp)} K")
        self.label_temp_val.pack()

        # --- TAB 2: SZÍNES ---
        self.frame_presets = ctk.CTkFrame(self.tab_color, fg_color="transparent")
        self.frame_presets.pack(pady=10)
        
        colors = [("Piros", 255, 0, 0), ("Zöld", 0, 255, 0), ("Kék", 0, 0, 255), ("Lila", 128, 0, 128)]
        for name, r, g, b in colors:
            ctk.CTkButton(self.frame_presets, text=name, width=60, 
                          command=lambda red=r, green=g, blue=b: self.set_rgb_color(red, green, blue)).pack(side="left", padx=5)
                          
        ctk.CTkButton(self.tab_color, text="Egyedi szín", command=self.pick_color).pack(pady=10)

        # --- AUTOMATIKUS INDÍTÁS LOGIKA (FIXED) ---
        last_mode = self.config_data.get("last_mode", "white")
        
        if last_mode == "color":
            # Ha legutóbb színes volt, akkor színes módban indítjuk
            r = self.config_data.get("r", 255)
            g = self.config_data.get("g", 255)
            b = self.config_data.get("b", 255)
            
            # Vizuálisan átváltunk a "Színes" fülre (opcionális, de szép)
            self.tabview.set("Színes")
            
            self.send_udp_command({
                "state": True,
                "dimming": int(saved_bright),
                "r": int(r), "g": int(g), "b": int(b)
            })
        else:
            # Ha legutóbb fehér volt
            self.send_udp_command({
                "state": True,
                "dimming": int(saved_bright),
                "temp": int(saved_temp)
            })

    # --- ESEMÉNYEK ---

    def on_toggle(self):
        is_on = (self.switch_var.get() == "on")
        self.send_udp_command({"state": is_on})

    def on_brightness_change(self, value):
        val = int(value)
        self.save_config(brightness=val)
        if self.switch_var.get() == "on":
            self.send_udp_command({"state": True, "dimming": val})

    def on_temp_change(self, value):
        val = int(value)
        self.label_temp_val.configure(text=f"{val} K")
        
        # Ha a csúszkát mozgatja, átváltunk "fehér" módba
        self.save_config(temp=val, last_mode="white")
        
        if self.switch_var.get() == "on":
            self.send_udp_command({"state": True, "temp": val})

    def set_rgb_color(self, r, g, b):
        # Segédfüggvény a színek beállításához és mentéséhez
        self.save_config(r=r, g=g, b=b, last_mode="color")
        self.switch_var.set("on")
        self.send_udp_command({"state": True, "r": r, "g": g, "b": b})

    def pick_color(self):
        color = colorchooser.askcolor()
        if color and color[0]:
            r, g, b = color[0]
            self.set_rgb_color(int(r), int(g), int(b))

if __name__ == "__main__":
    app = WizUdpApp()
    app.mainloop()