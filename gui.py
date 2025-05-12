from pathlib import Path
from tkinter import *
from tkinter.scrolledtext import ScrolledText
import types
import os
import blur_sorter as blur
import threading
import sys

OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / "build" / "assets" / "frame0"

def relative_to_assets(path: str) -> Path:
    return ASSETS_PATH / Path(path)

def redirect_stdout(widget):
    def write(s):
        widget.insert(END, s)
        widget.see(END)
        widget.update_idletasks()
    def flush():
        pass
    return types.SimpleNamespace(write=write, flush=flush)

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
        
        self.canvas = canvas

        self.processing_text = canvas.create_text (22.0, 175.0, anchor="nw",text="",fill="#D9D9D9",font=("Inter", 36 * -1))
        self.sharp = canvas.create_text(22.0, 277.0, anchor="nw", text=f"", fill="#D9D9D9", font=("Inter", 24 * -1))
        self.blurred = canvas.create_text(22.0, 247.0, anchor="nw", text=f"", fill="#D9D9D9", font=("Inter", 24 * -1))
        self.total = canvas.create_text(22.0, 217.0, anchor="nw", text="", fill="#D9D9D9", font=("Inter", 24 * -1))

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

        self.entry_1 = Entry(font= ("Helvetica", 20), bd=0, bg="#D9D9D9", fg="#000716", highlightthickness=0)
        self.entry_1.place(x=38.0, y=65.0, width=334.0, height=38.0)
        
        self.output_box = ScrolledText(self.root,font= ("tkfont", 12), bg="black", fg="#D9D9D9", insertbackground="#D9D9D9", wrap="word", borderwidth=0)
        


    def start_clicked(self):
        try:
            blur.folder =self.entry_1.get()
            print (blur.folder)
            
        except Exception as e:
            print(f"Error: {e}")

        def start_process():
            self.sorter_thread = threading.Thread(target=self.run_sorter)
            self.sorter_thread.start()
            check_if_done()
                
        def update_ui():
            self.canvas.itemconfig(self.sharp, text=f"Sharp: {blur.sharp_count}")
            self.canvas.itemconfig(self.blurred, text=f"Blurred: {blur.blurry_count}")
            total = blur.sharp_count + blur.blurry_count
            self.canvas.itemconfig(self.total, text=f"Image count: {total}")
            self.canvas.itemconfig(self.processing_text, text="Processing complete.")
            
        def check_if_done():
            if self.sorter_thread.is_alive():
                self.root.after(100, check_if_done)  # Check again after 100ms
            else:
                update_ui()
        
        if blur.folder != "":
            self.output_box.place(x=410, y=20, width=290, height=440)
            self.canvas.itemconfig(self.processing_text, text="Processing Images...")        
            sys.stdout = redirect_stdout(self.output_box)
            
            start_process()
        else:
            self.canvas.itemconfig(self.processing_text, text="Invalid directory.") 
            print("aaaa")

    def run_sorter(self):
        blur.main()
        
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
