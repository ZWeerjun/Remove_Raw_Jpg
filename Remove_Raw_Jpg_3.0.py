import tkinter as tk
from tkinter import filedialog, messagebox, Listbox
from PIL import Image, ImageTk, ExifTags
import os
from send2trash import send2trash

class PhotoDeleterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Photo Deleter")
        self.root.geometry('800x900')  # Adjust the window size as needed

        self.frame = tk.Frame(root)
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.btn_select_folder = tk.Button(self.frame, text="Select Folder", command=self.select_folder)
        self.btn_select_folder.pack(pady=10)

        self.lst_photos = Listbox(self.frame, width=100, height=10)
        self.lst_photos.pack(padx=10, pady=10)
        self.lst_photos.bind('<<ListboxSelect>>', self.show_preview)

        self.lbl_image = tk.Label(self.frame)
        self.lbl_image.pack(padx=10, pady=10)

        self.lbl_photo_info = tk.Label(self.frame, text="")
        self.lbl_photo_info.pack(padx=10, pady=10)

        self.btn_delete_both = tk.Button(self.frame, text="Delete Both", command=lambda: self.delete_photo('both'))
        self.btn_delete_both.pack(side=tk.LEFT, padx=5, pady=10)

        self.btn_delete_jpg = tk.Button(self.frame, text="Delete JPG", command=lambda: self.delete_photo('jpg'))
        self.btn_delete_jpg.pack(side=tk.LEFT, padx=5, pady=10)

        self.btn_delete_nef = tk.Button(self.frame, text="Delete NEF", command=lambda: self.delete_photo('nef'))
        self.btn_delete_nef.pack(side=tk.LEFT, padx=5, pady=10)

        self.folder_path = ''
        self.photos = []

    def select_folder(self):
        self.folder_path = filedialog.askdirectory()
        if self.folder_path:
            self.load_photos(self.folder_path)

    def load_photos(self, folder_path):
        self.photos = [f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.nef'))]
        self.lst_photos.delete(0, tk.END)
        for photo in self.photos:
            self.lst_photos.insert(tk.END, photo)

    def show_preview(self, event=None):
        selection = self.lst_photos.curselection()
        if selection:
            index = selection[0]
            selected_file = self.photos[index]
            file_path = os.path.join(self.folder_path, selected_file)
            try:
                pil_image = Image.open(file_path)
                pil_image = self.adjust_image_orientation(pil_image)
                new_size = self.determine_new_size(pil_image)
                pil_image = pil_image.resize(new_size, Image.Resampling.LANCZOS)
                tk_photo = ImageTk.PhotoImage(pil_image)
                self.lbl_image.config(image=tk_photo)
                self.lbl_image.image = tk_photo  # Keep a reference

                # Update to correctly identify if the corresponding file exists
                base_name, ext = os.path.splitext(selected_file)
                corresponding_ext = ".nef" if ext.lower() == ".jpg" else ".jpg"
                corresponding_file = f"{base_name}{corresponding_ext}"
                corresponding_file_path = os.path.join(self.folder_path, corresponding_file)
                file_exists = corresponding_file in self.photos or os.path.exists(corresponding_file_path)
                self.lbl_photo_info.config(text=f"{corresponding_ext.upper()} file exists: {file_exists}")
            except Exception as e:
                print(f"Error loading image: {e}")

    def adjust_image_orientation(self, image):
        """
        Adjust the image orientation based on its EXIF data.
        """
        try:
            exif = image._getexif()
            if exif is not None:
                orientation_key = 274  # cf ExifTags
                if orientation_key in exif:
                    orientation = exif[orientation_key]
                    if orientation == 3:
                        image = image.rotate(180, expand=True)
                    elif orientation == 6:
                        image = image.rotate(270, expand=True)
                    elif orientation == 8:
                        image = image.rotate(90, expand=True)
        except:
            pass  # If there's any error, proceed without rotation
        return image

    def determine_new_size(self, image):
        """
        Determine new image size for preview based on its orientation.
        """
        width, height = image.size
        if width > height:  # Landscape
            return (540, 360)
        else:  # Portrait or square
            return (360, 540)

    def delete_photo(self, mode):
        selection = self.lst_photos.curselection()
        if not selection:
            messagebox.showerror("Error", "No file selected.")
            return

        selected_index = selection[0]  # 当前选中的项目索引
        top_index = self.lst_photos.nearest(0)  # 当前视图顶部项目的索引

        selected_photo = self.photos[selected_index]
        folder_path = os.path.normpath(self.folder_path)
        photo_path = os.path.join(folder_path, selected_photo)

        base_name, ext = os.path.splitext(selected_photo)
        other_ext = '.nef' if ext.lower() in ['.jpg', '.jpeg'] else '.jpg'
        other_photo_path = os.path.join(folder_path, base_name + other_ext)

        try:
            files_deleted = False
            if mode == 'both':
                files_deleted = self.move_to_trash(photo_path) and self.move_to_trash(other_photo_path)
            elif mode == 'jpg' and ext.lower() in ['.jpg', '.jpeg']:
                files_deleted = self.move_to_trash(photo_path)
            elif mode == 'nef' and ext.lower() == '.nef':
                files_deleted = self.move_to_trash(photo_path)
            if mode == 'jpg' and other_ext.lower() == '.jpg':
                files_deleted = self.move_to_trash(other_photo_path) or files_deleted
            elif mode == 'nef' and other_ext.lower() == '.nef':
                files_deleted = self.move_to_trash(other_photo_path) or files_deleted

            if files_deleted:
                messagebox.showinfo("Success", "Selected files have been moved to the recycle bin.")
                self.load_photos(self.folder_path)  # 刷新列表

                # 尽量恢复到之前的滚动位置
                self.lst_photos.yview_moveto(0)  # 先滚动到顶部
                self.lst_photos.see(top_index)  # 滚动到之前顶部项目的位置
                new_selection_index = min(selected_index, self.lst_photos.size() - 1)
                self.lst_photos.select_set(new_selection_index)  # 重新选中一个合理的位置
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete the file: {e}")

    def move_to_trash(self, path):
        """Move the specified file to the recycle bin if it exists."""
        if os.path.exists(path):
            send2trash(path)
            print(f"Moved to trash: {path}")
            return True
        else:
            print(f"File not found, could not move to trash: {path}")
            return False


root = tk.Tk()
app = PhotoDeleterApp(root)
root.mainloop()
