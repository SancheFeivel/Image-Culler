from pathlib import Path
from tkinter import *
import os
import blur_sorter as blur

OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / "build" / "assets" / "frame0"

def relative_to_assets(path: str) -> Path:
    return ASSETS_PATH / Path(path)

class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.geometry("720x480")
        self.root.configure(bg="#000000")
        self.root.resizable(False, False)

        self.setup_ui()

    def setup_ui(self):
        canvas = Canvas(
            self.root,
            bg="#000000",
            height=480,
            width=720,
            bd=0,
            highlightthickness=0,
            relief="ridge"
        )
        canvas.place(x=0, y=0)

        canvas.create_text(
            8.0, 455.0, anchor="nw",
            text="Version 1.0.0",
            fill="#D9D9D9",
            font=("Inter ExtraLightItalic", 16 * -1)
        )

        canvas.create_text(
            22.0, 175.0, anchor="nw",
            text="Processing Images...   ",
            fill="#FFFFFF",
            font=("Inter", 36 * -1)
        )

        canvas.create_text(22.0, 277.0, anchor="nw", text="Sharp: 000", fill="#D9D9D9", font=("Inter", 24 * -1))
        canvas.create_text(22.0, 247.0, anchor="nw", text="Blurred: 000", fill="#D9D9D9", font=("Inter", 24 * -1))
        canvas.create_text(22.0, 217.0, anchor="nw", text="Image count: 000", fill="#D9D9D9", font=("Inter", 24 * -1))

        button_image_1 = PhotoImage(file=relative_to_assets("button_1.png"))
        button_1 = Button(
            image=button_image_1,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.start_clicked(),
            relief="flat"
        )
        button_1.image = button_image_1  # Keep a reference
        button_1.place(x=22.0, y=115.0, width=100.0, height=40.0)

        button_image_2 = PhotoImage(file=relative_to_assets("button_2.png"))
        button_2 = Button(
            image=button_image_2,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.folder_clicked(),
            relief="flat"
        )
        button_2.image = button_image_2  # Keep a reference
        button_2.place(x=132.0, y=115.0, width=100.0, height=40.0)

        canvas.create_text(22.0, 20.0, anchor="nw", text="Folder Directory:", fill="#FFFFFF", font=("Inter", 36 * -1))

        entry_image_1 = PhotoImage(file=relative_to_assets("entry_1.png"))
        canvas.create_image(205.0, 85.0, image=entry_image_1)
        self.entry_image_1 = entry_image_1  # Keep a reference

        entry_1 = Entry(bd=0, bg="#D9D9D9", fg="#000716", highlightthickness=0)
        entry_1.place(x=38.0, y=65.0, width=334.0, height=38.0)

        canvas.create_rectangle(410.0, 20.0, 700.0, 460.0, fill="#D9D9D9", outline="")

    def start_clicked(self):
        try:
            blur.folder=self.entry_1.get()
            
        except Exception as e:
            print(f"Error: {e}")
        
    
    def folder_clicked(self):
        try:
            folder_path = self.entry_1.get()
            print(folder_path)
            os.startfile(os.path.join(folder_path, 'sharp'))
            
        except Exception as e:
            print(f"Error: {e}")
        
    
if __name__ == "__main__":
    window = Tk()
    app = MainApp(window)
    window.mainloop()
