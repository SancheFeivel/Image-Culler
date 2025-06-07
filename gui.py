from pathlib import Path
import tkinter as tk
from tkinter import Tk, Canvas, Entry, Button, PhotoImage, Checkbutton, IntVar, END
from tkinter.scrolledtext import ScrolledText
import types
import os
import threading
import sys
from multiprocessing import freeze_support

import blur_sorter as blur
from blur_sorter import cancel_processing


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
        self.sharpness_threshold = "med"
        self.laplacian_enabled = True
        self.star_enabled = False
        
        # Create frames for home and settings screens
        self.home_frame = tk.Frame(self.root, bg="white")
        self.settings_frame = tk.Frame(self.root, bg="black")
        
        # Initialize both screens
        self.setup_homescreen()
        self.setup_settings()
        
        # Show home screen by default
        self.show_home()
        
    def show_home(self):
        """Switch to home screen"""
        self.settings_frame.place_forget()
        self.home_frame.place(x=0, y=0, width=720, height=480)
        
    def show_settings(self):
        """Switch to settings screen"""
        self.home_frame.place_forget()
        self.settings_frame.place(x=0, y=0, width=720, height=480)

    def setup_homescreen(self):
        self.canvas = Canvas(self.home_frame, bg="#252827", height=480, width=720, bd=0, highlightthickness=0, relief="ridge")
        self.canvas.place(x=0, y=0)

        self.canvas.create_text(
            8.0,
            455.0,
            anchor="nw",
            text="Version 1.2.0",
            fill="#D9D9D9",
            font=("Inter ExtraLightItalic", 16 * -1))
        
        # Folder Input
        self.canvas.create_text(22.0, 20.0, anchor="nw", text="Folder Directory:", fill="#FFFFFF", font=("Inter", 36 * -1))
        entry_image_1 = PhotoImage(file=str(relative_to_assets("entry_1.png")))
        self.canvas.create_image(186.0, 85.0, image=entry_image_1)
        self.entry_image_1 = entry_image_1  
        self.entry_1 = Entry(self.home_frame, font=("Helvetica", 20), bd=0, bg="#1E1E1E", fg="#D9D9D9", highlightthickness=0)
        self.entry_1.place(x=25.0, y=68.0, width=322.0, height=34.0)
        
        # Buttons 
        cancel_button_image = PhotoImage(file=str(relative_to_assets("button_3.png")))
        self.cancel_button = Button(self.home_frame, image=cancel_button_image, borderwidth=0, highlightthickness=0,
                                    command=lambda: self.cancel_clicked(), relief="flat")
        self.cancel_button.image = cancel_button_image
        self.cancel_button.place(x=22.0, y=115.0, width=100.0, height=40.0)

        button_image_1 = PhotoImage(file=str(relative_to_assets("button_1.png")))
        self.button_1 = Button(
            self.home_frame,
            image=button_image_1,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.start_clicked(),
            relief="flat"
        )
        self.button_1.image = button_image_1  
        self.button_1.place(x=22.0, y=115.0, width=100.0, height=40.0)

        button_image_2 = PhotoImage(file=str(relative_to_assets("button_2.png")))
        self.button_2 = Button(
            self.home_frame,
            image=button_image_2,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.folder_clicked(),
            relief="flat"
        )
        self.button_2.image = button_image_2  
        self.button_2.place(x=127.0, y=115.0, width=100.0, height=40.0)
        
        settings_image = PhotoImage(file=str(relative_to_assets("settings.png")))
        self.settings_button = Button(
            self.home_frame,
            image=settings_image,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.settings_clicked(),
            relief="flat"
        )
        
        self.settings_button.image = settings_image
        self.settings_button.place(x=232.0, y=115.0, width=118.0, height=40.0)
        
        # Status Text
        self.processing_text = self.canvas.create_text(22.0, 165.0, anchor="nw", text="", fill="#D9D9D9", font=("Inter", 36 * -1))
        self.error_text_1 = self.canvas.create_text(22.0, 200.0, anchor="nw", text="", fill="#D9D9D9", font=("Inter", 22 * -1))
        self.error_text_2 = self.canvas.create_text(22.0, 222.0, anchor="nw", text="", fill="#D9D9D9", font=("Inter", 22 * -1))

        # Output Box
        self.output_box = ScrolledText(self.home_frame, font=("tkfont", 12), bg="#252827", fg="#D9D9D9",
                                    insertbackground="#D9D9D9", wrap="word", borderwidth=0)

    def setup_settings(self):
        self.settings_canvas = Canvas(self.settings_frame, bg="#252827", height=480, width=720, bd=0, highlightthickness=0, relief="ridge")
        self.settings_canvas.place(x=0, y=0)
        
        # Back button for navigation
        back_image = PhotoImage(file=relative_to_assets("Back.png"))
        self.back_button = Button(self.settings_frame,image=back_image, borderwidth=0, highlightthickness=0, command=lambda: self.back_clicked() , relief="flat")
        self.back_button.image = back_image
        self.back_button.place(x=14.0, y=294.0, width=100.0, height=40.0)

        
        # Settings buttons
        self.low_image = PhotoImage(file=str(relative_to_assets("Low.png")))
        self.low_image_active = PhotoImage(file=str(relative_to_assets("Low1.png")))
        self.low_button = Button(self.settings_frame, image=self.low_image, borderwidth=0, highlightthickness=0, 
                               command=lambda: self.low_clicked(),bg="#262827", relief="flat")
        self.low_button.image = self.low_image
        self.low_button.place(x=361.0, y=97.0, width=81.73652648925781, height=32.694610595703125)

        self.med_image = PhotoImage(file=str(relative_to_assets("Med.png")))
        self.med_image_active = PhotoImage(file=str(relative_to_assets("Med1.png")))
        self.med_button = Button(self.settings_frame, image=self.med_image_active, borderwidth=0, highlightthickness=0, 
                               command=lambda: self.med_clicked(), bg="#262827", relief="sunken")
        self.med_button.image = self.med_image_active
        self.med_button.place(x=456.6317138671875, y=97.0, width=81.73652648925781, height=32.694610595703125)

        self.high_image = PhotoImage(file=str(relative_to_assets("High.png")))
        self.high_image_active = PhotoImage(file=str(relative_to_assets("High1.png")))
        self.high_button = Button(self.settings_frame, image=self.high_image, borderwidth=0, highlightthickness=0, 
                                command=lambda: self.high_clicked(), bg="#262827", relief="flat")
        self.high_button.image = self.high_image
        self.high_button.place(x=552.0, y=97.0, width=81.73652648925781, height=32.694610595703125)
        
        # Settings text
        self.settings_canvas.create_text(8.0, 455.0, anchor="nw", text="Version 1.2.0", fill="#D9D9D9", font=("Inter ExtraLightItalic", 16 * -1))
        self.settings_canvas.create_text(19.0, 42.0, anchor="nw", text="Laplacian Sorting:", fill="#D9D9D9", font=("Inter", 32 * -1))
        self.settings_canvas.create_text(19.0, 93.0, anchor="nw", text="Sharpness Threshold:", fill="#D9D9D9", font=("Inter", 32 * -1))
        self.settings_canvas.create_text(20.0, 143.0, anchor="nw", text="Threshold Compensation:", fill="#D9D9D9", font=("Inter", 32 * -1))
        self.settings_canvas.create_text(19.0, 225.0, anchor="nw", text="Sort by Rating:", fill="#D9D9D9", font=("Inter", 32 * -1))
        
        # lines
        self.settings_canvas.create_rectangle(16.9996, 202.5, 700.0004, 204.5, fill="#555555", outline="")
        self.settings_canvas.create_rectangle(12.0, 283.0, 695.0007, 285.0, fill="#555555", outline="")
        self.settings_canvas.create_rectangle(16.9996, 20.5, 700.0004, 22.5, fill="#555555", outline="")
        
        # Input 
        entry_image_1 = PhotoImage(file=relative_to_assets("Threshold.png"))
        self.settings_canvas.create_image(438.0, 163.0, image=entry_image_1)
        self.tolerance_comp = Entry(self.settings_frame,font=("Helvetica", 20), bd=0, bg="#1E1E1E", fg="#D9D9D9", highlightthickness=0)
        self.tolerance_comp.image = entry_image_1
        self.tolerance_comp.place(x=390.0, y=148.0, width=95.0, height=29.0)
        
        # Chekcbutton
        self.on_image = PhotoImage(file=str(relative_to_assets("on.png")))
        self.off_image = PhotoImage(file=str(relative_to_assets("off.png")))
        
        self.laplacian_on = Button(self.settings_frame, image=self.on_image, borderwidth=0, highlightthickness=0, 
                               command=lambda: self.laplacian_clicked(),bg="#262827", relief="flat")
        self.laplacian_on.image = self.on_image
        self.laplacian_on.place(x=300.0, y=45.0, width=81.73652648925781, height=32.694610595703125)
        
        self.star_on = Button(self.settings_frame, image=self.off_image, borderwidth=0, highlightthickness=0, 
                               command=lambda: self.star_clicked(),bg="#262827", relief="flat")
        self.star_on.image = self.off_image
        self.star_on.place(x=250.0, y=228.0, width=81.73652648925781, height=32.694610595703125)

    def laplacian_clicked(self):
        self.laplacian_enabled= not self.laplacian_enabled
        
        if self.laplacian_enabled:
            self.laplacian_on.config(image=self.on_image)
        else:
            self.laplacian_on.config(image=self.off_image)
    
    def star_clicked(self):
        self.star_enabled= not self.star_enabled
        
        if self.star_enabled:
            self.star_on.config(image=self.on_image)
        else:
            self.star_on.config(image=self.off_image)
                  
        
    def back_clicked(self):
        self.canvas.itemconfig(self.processing_text, text="")    
        self.show_home()
        
    def start_clicked(self):
        if self.is_processing:
            return
        
        try:
            blur.folder = self.entry_1.get()
            
            compensation_value = self.tolerance_comp.get()
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
            if self.entry_1.get() != "":
                folder_path = self.entry_1.get()
                os.startfile(os.path.join(folder_path, 'sharp'))
        except Exception as e:
            print(f"Error: {e}")
            self.canvas.itemconfig(self.processing_text, text="Invalid directory.") 
            
    def settings_clicked(self):
        self.show_settings()
        
        
    def set_blur_level(self, level):
        blur.base_blur = int(level)
        buttons = {
            -20: (self.low_button, self.low_image, self.low_image_active),
            0: (self.med_button, self.med_image, self.med_image_active),
            20: (self.high_button, self.high_image, self.high_image_active)
        }

        for val, (button, disabled_img, active_img) in buttons.items():
            if val == level:
                button.config(relief="sunken", fg="#262827", image=active_img)
            else:
                button.config(relief="flat", fg="#262827", image=disabled_img)

    def low_clicked(self):
        self.set_blur_level(-20)

    def med_clicked(self):
        self.set_blur_level(0)

    def high_clicked(self):
        self.set_blur_level(20)

        
    def cancel_clicked(self):
        if not self.is_processing:
            return
        
        self.canvas.itemconfig(self.processing_text, text="Cancelling...")
        
        cancel_processing()
        
        self.is_processing = False
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
        blur.main(use_starcheck = self.star_enabled,
                    use_laplaciancheck = self.laplacian_enabled)

    
if __name__ == "__main__":
    freeze_support()
    window = Tk()
    app = MainApp(window)
    window.mainloop()