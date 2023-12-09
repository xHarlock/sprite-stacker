import os
import tkinter as tk
from tkinter import filedialog, Menu, ttk
from PIL import Image, ImageTk
import windnd


class SpriteStacker(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Sprite Stacker")
        self.geometry("900x700")

        self.image_paths = []
        self.image_cache = {}
        self.dragged_item = None

        self.setup_ui()

    def setup_ui(self):
        self.create_menu()
        self.create_ui_components()
        self.bind_events()

        windnd.hook_dropfiles(self, func=self.on_drop)

    def create_menu(self):
        self.menu_bar = Menu(self)
        self.file_menu = Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="Add images", command=self.open_images)
        self.file_menu.add_command(label="Save", command=self.save_image)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.config(menu=self.menu_bar)

    def create_ui_components(self):
        self.create_split_container()
        self.create_tree_view()
        self.create_preview_frame()

    def create_split_container(self):
        self.split_container = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.split_container.pack(fill=tk.BOTH, expand=True)

    def create_tree_view(self):
        self.tree_view = ttk.Treeview(self.split_container, show='tree')
        self.split_container.add(self.tree_view)

    def create_preview_frame(self):
        self.preview_frame = tk.Frame(self.split_container)
        self.split_container.add(self.preview_frame)

    def bind_events(self):
        self.tree_view.bind('<ButtonPress-1>', self.on_drag_start)
        self.tree_view.bind('<B1-Motion>', self.on_drag_motion)
        self.tree_view.bind('<ButtonRelease-1>', self.on_drag_release)
        self.tree_view.bind("<Delete>", self.on_del_key)
        self.tree_view.bind("<Button-3>", self.show_context_menu)
        self.bind('<Configure>', self.on_resize)
        self.create_context_menu()

    def create_context_menu(self):
        self.tree_view_menu = tk.Menu(self, tearoff=0)
        self.tree_view_menu.add_command(label="Remove", command=self.remove_selected_item)

    def on_drop(self, filenames):
        for file in filenames:
            file = file.decode('utf-8')
            if os.path.isfile(file) and file.lower().endswith(('.png', '.jpg')):
                self.image_paths.append(file)
                self.tree_view.insert('', 'end', text=os.path.basename(file))
        self.load_and_display_images()

    def open_images(self):
        file_types = [("Images", ".png;*.jpg")]
        selected_files = filedialog.askopenfilenames(title="Select images", filetypes=file_types)
        self.image_paths.extend(selected_files)
        for file in selected_files:
            self.tree_view.insert('', 'end', text=os.path.basename(file))
        self.load_and_display_images()

    def save_image(self):
        if not hasattr(self, 'current_image') or self.current_image is None:
            print("No combined image to save.")
            return

        file_types = [("PNG files", "*.png")]
        file_path = filedialog.asksaveasfilename(title="Save image as", filetypes=file_types, defaultextension=".png")

        if file_path:
            try:
                self.current_image.save(file_path, format='PNG')
                print(f"Image successfully saved to {file_path}")
            except Exception as e:
                print(f"Error saving image: {e}")

    def on_resize(self, event):
        if hasattr(self, 'image') and self.image:
            self.load_and_display_images()

    def load_and_display_images(self):
        self.process_and_display_images()

    def process_and_display_images(self):
        preview_max_width = self.preview_frame.winfo_width()
        preview_max_height = self.preview_frame.winfo_height()

        if not self.image_paths:
            placeholder_image = Image.new('RGBA', (preview_max_width, preview_max_height), (255, 255, 255, 0))
            self.update_image_display(placeholder_image)
        else:
            max_width = 0
            max_height = 0
            images = []

            for image_path in reversed(self.image_paths):
                if image_path in self.image_cache:
                    img = self.image_cache[image_path]
                else:
                    with Image.open(image_path) as img:
                        self.image_cache[image_path] = img.copy()
                        img = self.image_cache[image_path]

                images.append(img)
                max_width = max(max_width, img.width)
                max_height = max(max_height, img.height)

            combined_image = Image.new('RGBA', (max_width, max_height), (0, 0, 0, 0))  # Background is transparent

            for img in images:
                x_offset = (max_width - img.width) // 2
                y_offset = (max_height - img.height) // 2
                temp_image = Image.new('RGBA', (max_width, max_height), (0, 0, 0, 0))
                temp_image.paste(img, (x_offset, y_offset), img if img.mode == 'RGBA' else None)
                combined_image.alpha_composite(temp_image)

            if max_width > preview_max_width or max_height > preview_max_height:
                combined_image.thumbnail((preview_max_width, preview_max_height), Image.LANCZOS)

            self.update_image_display(combined_image)
            self.current_image = combined_image

    def update_image_display(self, image):
        self.image = ImageTk.PhotoImage(image)
        if hasattr(self, 'preview_label'):
            self.preview_label.configure(image=self.image)
        else:
            self.preview_label = tk.Label(self.preview_frame, image=self.image)
            self.preview_label.pack(expand=True, anchor='center')

    def show_context_menu(self, event):
        try:
            item = self.tree_view.identify_row(event.y)
            if item:
                if len(self.tree_view.selection()) <= 1:
                    self.tree_view.selection_set(item)
                self.tree_view_menu.post(event.x_root, event.y_root)
        except Exception as e:
            print("Error showing context menu:", e)

    def on_drag_start(self, event):
        item = self.tree_view.identify_row(event.y)
        if item:
            self.dragged_item = item

    def on_drag_motion(self, event):
        item = self.tree_view.identify_row(event.y)
        if item and item != self.dragged_item:
            parent = self.tree_view.parent(item)
            index = self.tree_view.index(item)
            self.tree_view.move(self.dragged_item, parent, index)

    def on_drag_release(self, event):
        if self.dragged_item:
            self.update_image_order()
            self.load_and_display_images()
        self.dragged_item = None

    def update_image_order(self):
        new_image_paths = []
        for item in self.tree_view.get_children():
            filename = self.tree_view.item(item, 'text')
            for path in self.image_paths:
                if os.path.basename(path) == filename:
                    new_image_paths.append(path)
                    break
        self.image_paths = new_image_paths

    def on_del_key(self, event):
        self.remove_selected_item()

    def remove_selected_item(self):
        selected_items = self.tree_view.selection()
        if selected_items:
            paths_to_remove = []

            for selected_item in selected_items:
                filename = self.tree_view.item(selected_item, 'text')
                self.tree_view.delete(selected_item)

                for path in self.image_paths:
                    if os.path.basename(path) == filename:
                        paths_to_remove.append(path)

            for path in paths_to_remove:
                self.image_paths.remove(path)

            self.load_and_display_images()


if __name__ == "__main__":
    app = SpriteStacker()
    app.mainloop()
