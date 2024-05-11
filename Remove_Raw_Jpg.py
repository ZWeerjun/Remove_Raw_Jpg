import tkinter as tk
from tkinter import filedialog, messagebox, Listbox
from PIL import Image, ImageTk, ExifTags
import os

class PhotoDeleterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Photo Deleter")
        self.root.geometry('800x900')  # 设置窗口的初始大小为800x600

        # 创建一个Frame作为顶层容器
        self.frame = tk.Frame(root)
        self.frame.pack(fill=tk.BOTH, expand=True)

        # 选择文件夹的按钮
        self.btn_select_folder = tk.Button(self.frame, text="Select Folder", command=self.select_folder)
        self.btn_select_folder.pack(pady=10)

        # 文件列表
        self.lst_photos = Listbox(self.frame, width=100, height=10)
        self.lst_photos.pack(padx=10, pady=10)
        self.lst_photos.bind('<<ListboxSelect>>', self.show_preview)  # 绑定事件

        # 图片预览区域
        self.lbl_image = tk.Label(self.frame)
        self.lbl_image.pack(padx=10, pady=10)

        # 删除按钮
        self.btn_delete = tk.Button(self.frame, text="Delete Photo", command=self.delete_photo)
        self.btn_delete.pack(pady=10)

        self.folder_path = ''  # 存储当前选择的目录路径
        self.photos = []  # 存储目录中的照片列表

    def select_folder(self):
        self.folder_path = filedialog.askdirectory()
        if self.folder_path:
            self.load_photos(self.folder_path)

    def load_photos(self, folder_path):
        self.photos = [f for f in os.listdir(folder_path) if f.lower().endswith('.jpg')]
        self.lst_photos.delete(0, tk.END)
        for photo in self.photos:
            self.lst_photos.insert(tk.END, photo)

    def show_preview(self, event=None):
        selection = self.lst_photos.curselection()
        if selection:
            index = selection[0]
            image_path = os.path.join(self.folder_path, self.photos[index])
            pil_image = Image.open(image_path)
            # 默认横向尺寸
            new_size = (540, 360)
            exif = pil_image._getexif()
            if exif:
                for tag, value in exif.items():
                    if ExifTags.TAGS.get(tag) == "Orientation":
                        if value == 3:
                            pil_image = pil_image.rotate(180, expand=True)
                        elif value == 6:
                            pil_image = pil_image.rotate(270, expand=True)
                            new_size = (360, 540)
                        elif value == 8:
                            pil_image = pil_image.rotate(90, expand=True)
                            new_size = (360, 540)
            pil_image = pil_image.resize(new_size, Image.Resampling.LANCZOS)
            tk_photo = ImageTk.PhotoImage(pil_image)
            self.lbl_image.config(image=tk_photo)
            self.lbl_image.image = tk_photo  # 防止垃圾回收

    def delete_photo(self):
        selection = self.lst_photos.curselection()
        if selection:
            selected_photo = self.photos[selection[0]]
            jpeg_path = os.path.join(self.folder_path, selected_photo)
            nef_path = jpeg_path[:-4] + '.nef'  # 假设NEF文件与JPEG文件同名，只是扩展名不同
            response = messagebox.askyesno("Confirm", f"Do you want to delete {selected_photo} and its corresponding NEF file?")
            if response:
                try:
                    os.remove(jpeg_path)
                    os.remove(nef_path)
                    print(f"Deleted {jpeg_path} and {nef_path}")
                    self.load_photos(self.folder_path)  # 重新加载照片列表
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to delete files: {e}")

root = tk.Tk()
app = PhotoDeleterApp(root)
root.mainloop()
