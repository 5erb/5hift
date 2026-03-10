import os
import sys  
import zipfile
import shutil
import webbrowser
from tkinter import *
from tkinter import filedialog, colorchooser, ttk, messagebox
from PIL import Image, ImageTk

# Files to recolor by keywords
TARGET_KEYWORDS = [
    "diamond_sword",
    "diamond_helmet",
    "diamond_chestplate",
    "diamond_leggings",
    "diamond_boots",
    "diamond_pickaxe",
    "diamond_axe",
    "diamond_shovel",
    "fire_0",
    "fire_1",
]

class TextureTool:
    def __init__(self, root):
        self.root = root
        self.root.title("5hift")
        self.root.geometry("450x460")

        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(base_path, "myicon.ico")
        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)
        # -----------------------------------

        self.pack = None
        self.pack_name = ""
        self.color = (0, 255, 255)
        self.pack_icon = None
        self.color_icon = None

        # Single shared temp folder on Desktop
        self.desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        self.base_temp = os.path.join(self.desktop, "5hift_temp")
        os.makedirs(self.base_temp, exist_ok=True)

        # Upload button
        Button(root, text="Upload Texture Pack", command=self.upload, width=25).pack(pady=8)
        self.pack_preview = Label(root, text="No pack selected")
        self.pack_preview.pack(pady=5)

        # Color picker
        Button(root, text="Pick Color", command=self.pick_color, width=25).pack(pady=8)
        self.color_preview = Label(root, text="No color selected")
        self.color_preview.pack(pady=5)

        # Start recoloring
        Button(root, text="Start Recoloring", command=self.start, width=25).pack(pady=12)
        self.progress = ttk.Progressbar(root, length=350)
        self.progress.pack(pady=15)

        # Social buttons
        social_frame = Frame(root)
        social_frame.pack(pady=10)
        Button(social_frame, text="YouTube", command=self.open_youtube, width=12).pack(side=LEFT, padx=5)
        Button(social_frame, text="X / Twitter", command=self.open_x, width=12).pack(side=LEFT, padx=5)

    # Utility: get shared temp folder subdirectory
    def temp_path(self, name):
        path = os.path.join(self.base_temp, name)
        os.makedirs(path, exist_ok=True)
        return path

    # Upload pack
    def upload(self):
        path = filedialog.askopenfilename(filetypes=[("Zip", "*.zip")])
        if not path:
            return

        self.pack = path
        self.pack_name = os.path.splitext(os.path.basename(path))[0]

        # Use shared temp folder for preview
        temp_preview = self.temp_path("preview")
        shutil.rmtree(temp_preview, ignore_errors=True)
        os.makedirs(temp_preview, exist_ok=True)

        with zipfile.ZipFile(path, 'r') as z:
            z.extractall(temp_preview)

        pack_png = os.path.join(temp_preview, "pack.png")
        if os.path.exists(pack_png):
            img = Image.open(pack_png).resize((64,64))
            self.pack_icon = ImageTk.PhotoImage(img)
            self.pack_preview.config(image=self.pack_icon, text="")
        else:
            self.pack_preview.config(text="No pack.png found")

    # Pick color
    def pick_color(self):
        c = colorchooser.askcolor()[0]
        if not c:
            return
        self.color = tuple(map(int,c))
        img = Image.new("RGB",(40,40),self.color)
        self.color_icon = ImageTk.PhotoImage(img)
        hex_color = '#%02x%02x%02x' % self.color
        self.color_preview.config(image=self.color_icon, text=hex_color, compound="right")

    # Convert color to hex string
    def color_to_hex(self):
        return '#%02x%02x%02x' % self.color

    # Recolor image
    def recolor(self, img_path):
        img = Image.open(img_path).convert("RGBA")
        pixels = img.load()
        r2,g2,b2 = self.color
        for y in range(img.height):
            for x in range(img.width):
                r,g,b,a = pixels[x,y]
                if a==0:
                    continue
                pixels[x,y] = (int((r+r2)/2), int((g+g2)/2), int((b+b2)/2), a)
        img.save(img_path)

    # Start recoloring
    def start(self):
        if not self.pack:
            messagebox.showerror("Error","Upload a pack first")
            return

        # Temp folders inside shared base_temp
        temp = self.temp_path("pack_temp")
        out = self.temp_path("recolored")
        preview_temp = self.temp_path("preview")

        # Clean old temp folders
        shutil.rmtree(temp, ignore_errors=True)
        shutil.rmtree(out, ignore_errors=True)
        shutil.rmtree(preview_temp, ignore_errors=True)
        os.makedirs(temp, exist_ok=True)
        os.makedirs(out, exist_ok=True)
        os.makedirs(preview_temp, exist_ok=True)

        # Extract original pack
        with zipfile.ZipFile(self.pack, 'r') as z:
            z.extractall(temp)

        # Collect target PNGs
        targets = []
        for root_dir, dirs, files in os.walk(temp):
            for f in files:
                if not f.endswith(".png"):
                    continue
                for key in TARGET_KEYWORDS:
                    if key in f:
                        targets.append(os.path.join(root_dir, f))
                        break

        # Include pack.png
        pack_png_path = os.path.join(temp,"pack.png")
        if os.path.exists(pack_png_path):
            targets.append(pack_png_path)

        # Add diamond armor layers
        armor_dir = os.path.join(temp, "assets", "minecraft", "textures", "models", "armor")
        for layer_file in ["diamond_layer_1.png", "diamond_layer_2.png"]:
            armor_path = os.path.join(armor_dir, layer_file)
            if os.path.exists(armor_path):
                targets.append(armor_path)

        # Add bow, fishing rod, arrow
        item_dir = os.path.join(temp, "assets", "minecraft", "textures", "item")
        for item_file in [
            "bow.png",
            "bow_pulling_0.png",
            "bow_pulling_1.png",
            "bow_pulling_2.png",
            "bow_standby.png",
            "fishing_rod_cast.png",
            "fishing_rod_uncast.png",
            "arrow.png"
        ]:
            item_path = os.path.join(item_dir, item_file)
            if os.path.exists(item_path):
                targets.append(item_path)

        # Recolor all targets
        self.progress["maximum"] = len(targets)
        for i, file in enumerate(targets):
            self.recolor(file)
            self.progress["value"] = i+1
            self.root.update_idletasks()

        # Copy recolored pack to out folder
        shutil.copytree(temp, out, dirs_exist_ok=True)

        hex_color = self.color_to_hex().replace("#","")
        output_name = os.path.join(self.desktop, f"{hex_color}_{self.pack_name}")
        shutil.make_archive(output_name,"zip",out)

        # Clean all temp folders once
        shutil.rmtree(self.base_temp, ignore_errors=True)

        messagebox.showinfo("Done", f"{os.path.basename(output_name)}.zip created on Desktop")

    # Social links
    def open_youtube(self):
        webbrowser.open("https://www.youtube.com/@5erb_")

    def open_x(self):
        webbrowser.open("https://x.com/5erb__")

root = Tk()
TextureTool(root)
root.mainloop()