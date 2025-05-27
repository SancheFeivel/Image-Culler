
from pathlib import Path
from tkinter import *
from tkinter.scrolledtext import ScrolledText
import types
import os
import blur_sorter as blur
from blur_sorter import cancel_processing
import threading
import sys
from multiprocessing import freeze_support


if getattr(sys, 'frozen', False):
    BASE_PATH = Path(sys._MEIPASS)
else:
    BASE_PATH = Path(__file__).parent

ASSETS_PATH = BASE_PATH / "assets" / "frame0"


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
        self.root.title("Image Culler")
        self.root.iconbitmap(str(relative_to_assets("Rei.ico")))
        self.sorter_thread = None
        self.is_processing = False

        self.setup_ui()

    def setup_ui(self):
        canvas = Canvas(
            self.root,
            bg="#252827",
            height=480,
            width=720,
            bd=0,
            highlightthickness=0,
            relief="ridge"
        )
        canvas.place(x=0, y=0)

        canvas.create_text(
            8.0,
            455.0,
            anchor="nw",
            text="Version 1.1.2",
            fill="#D9D9D9",
            font=("Inter ExtraLightItalic", 16 * -1)
)
        
        self.canvas = canvas

        self.processing_text = canvas.create_text(22.0, 245.0, anchor="nw", text="", fill="#D9D9D9", font=("Inter", 36 * -1))
        self.error_text_1 = canvas.create_text(22.0, 285.0, anchor="nw", text="", fill="#D9D9D9", font=("Inter", 22 * -1))
        self.error_text_2 = canvas.create_text(22.0, 308.0, anchor="nw", text="", fill="#D9D9D9", font=("Inter", 22 * -1))

        self.cancel_button_image = PhotoImage(file=str(relative_to_assets("button_3.png")))
        self.cancel_button = Button(image=self.cancel_button_image,borderwidth=0,highlightthickness=0,command=lambda: self.cancel_clicked(),relief="flat")
        
        self.cancel_button.image = self.cancel_button_image
        self.cancel_button.place(x=22.0,y=200.0,width=100.0,height=40.0)

        self.button_image_1 = PhotoImage(file=str(relative_to_assets("button_1.png")))
        self.button_1 = Button(
            image=self.button_image_1,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.start_clicked(),
            relief="flat"
        )
        self.button_1.image = self.button_image_1  
        self.button_1.place(x=22.0, y=200.0, width=100.0, height=40.0)

        button_image_2 = PhotoImage(file=str(relative_to_assets("button_2.png")))
        button_2 = Button(
            image=button_image_2,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.folder_clicked(),
            relief="flat"
        )
        button_2.image = button_image_2  
        button_2.place(x=127.0, y=200.0, width=100.0, height=40.0)
    

        canvas.create_text(22.0, 20.0, anchor="nw", text="Folder Directory:", fill="#FFFFFF", font=("Inter", 36 * -1))

        entry_image_1 = PhotoImage(file=str(relative_to_assets("entry_1.png")))
        canvas.create_image(205.0, 85.0, image=entry_image_1)
        self.entry_image_1 = entry_image_1  

        self.entry_1 = Entry(font= ("Helvetica", 20), bd=0, bg="#1E1E1E", fg="#D9D9D9", highlightthickness=0)
        self.entry_1.place(x=27.0, y=68.0, width=358.0, height=34.0)
        
        canvas.create_text(22.0,110.0,anchor="nw",text="Tolerance compensation:",fill="#D9D9D9",font=("Inter", 30 * -1))
        
        entry_image_2 = PhotoImage(file=str(relative_to_assets("entry_2.png")))
        canvas.create_image(91.0,170.0,image=entry_image_2)
        self.entry_image_2 = entry_image_2
        
        self.comp = Entry(font= ("Helvetica", 20), bd=0, bg="#1E1E1E", fg="#D9D9D9", highlightthickness=0)
        self.comp.place(x=26.0,y=153.0,width=130.0,height=34.0)

        self.output_box = ScrolledText(self.root,font= ("tkfont", 12), bg="#252827", fg="#D9D9D9", insertbackground="#D9D9D9", wrap="word", borderwidth=0)
        


    def start_clicked(self):
        
        if self.is_processing:
            return
        
        try:
            blur.folder =self.entry_1.get()
            compensation_value = self.comp.get()
            self.canvas.itemconfig(self.error_text_1, text="")
            self.canvas.itemconfig(self.error_text_2, text="")
            
            try:
                blur.tolerance_compensation = int(compensation_value) if compensation_value else 0
            except ValueError:
                blur.tolerance_compensation = 0  # fallback in case of invalid input
                self.canvas.itemconfig(self.error_text_1, text="Invalid compensation value;")
                self.canvas.itemconfig(self.error_text_2, text="using default of 0.")
            
        except Exception as e:
            print(f"Error: {e}")

        def start_process():
            self.is_processing = True 
            self.sorter_thread = threading.Thread(target=self.run_sorter)
            self.sorter_thread.daemon = True
            self.sorter_thread.start()
            self.cancel_button.lift()
            check_if_done()
                
        def update_ui():
            self.is_processing = False
            self.canvas.itemconfig(self.processing_text, text="Processing complete.")
            self.button_1.lift()
            
            
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
        
    def folder_clicked(self):
        try:
            if self.entry_1 != "":
                folder_path = self.entry_1.get()
                os.startfile(os.path.join(folder_path, 'sharp'))
                
            
        except Exception as e:
            print(f"Error: {e}")
            self.canvas.itemconfig(self.processing_text, text="Invalid directory.") 

    def cancel_clicked(self):
        if not self.is_processing:
            return
        
        self.canvas.itemconfig(self.processing_text, text="Cancelling...")
        
        cancel_processing()
        
        self.is_processing=False
        self.canvas.itemconfig(self.processing_text, text="Processing cancelled.")
        self.button_1.lift()
        
        if self.sorter_thread and self.sorter_thread.is_alive():
            self.root.after(100, self.check_thread_finished)
    
    def check_thread_finished(self):
        if self.sorter_thread and self.sorter_thread.is_alive():
            self.root.after(100, self.check_thread_finished)  # Check again
        else:
            print("Processing thread finished\n")

    def run_sorter(self):
        blur.main()

    
if __name__ == "__main__":
    freeze_support()
    window = Tk()
    app = MainApp(window)
    window.mainloop()
