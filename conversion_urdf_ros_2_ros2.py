import os
import shutil
import sys
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox

# Configuration variable
def get_directory(title):
    path = filedialog.askdirectory(title=title)
    # Ensure the path ends with a forward slash
    if not path.endswith("/"):
        path += "/"
    return path

def run_command_dir(command_dir, command):
    os.system("cd " + command_dir + " && " + command)

def replace_str(file, old_str, new_str):
    file_data = ""
    with open(file, "r", encoding="utf-8") as f:
        for line in f:
            if old_str in line:
                line = line.replace(old_str, new_str)
            file_data += line
    with open(file, "w", encoding="utf-8") as f:
        f.write(file_data)

# GUI application
class ConversionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SolidWorks to ROS2 Conversion")

        self.source_dir = ""
        self.target_dir = ""

        # Create and place labels and buttons
        self.source_label = tk.Label(root, text="Source Directory (SolidWorks URDF Output):")
        self.source_label.pack(pady=5)

        self.source_button = tk.Button(root, text="Select Source Folder", command=self.select_source)
        self.source_button.pack(pady=5)

        self.target_label = tk.Label(root, text="Target Directory (ROS2 Package Path):")
        self.target_label.pack(pady=5)

        self.target_button = tk.Button(root, text="Select Target Folder", command=self.select_target)
        self.target_button.pack(pady=5)

        self.convert_button = tk.Button(root, text="Start Conversion", command=self.start_conversion)
        self.convert_button.pack(pady=20)

    def select_source(self):
        self.source_dir = get_directory("Select the folder generated from SolidWorks (URDF Output)")
        self.source_label.config(text=f"Source Directory: {self.source_dir}")

    def select_target(self):
        self.target_dir = get_directory("Select the ROS2 package folder")
        self.target_label.config(text=f"Target Directory: {self.target_dir}")

    def start_conversion(self):
        if not self.source_dir or not self.target_dir:
            messagebox.showerror("Error", "Please select both source and target directories.")
            return

        package_name = self.target_dir.split("/")[-2]
        output_folder_name = self.source_dir.split("/")[-2]

        # Create folders
        run_command_dir(self.target_dir, "mkdir launch meshes meshes/collision meshes/visual urdf")

        # Copy files
        # Copy stl files
        run_command_dir(self.source_dir, "cp -r ./meshes/* " + self.target_dir + "meshes/visual")
        run_command_dir(self.source_dir, "cp -r ./meshes/* " + self.target_dir + "meshes/collision")
        # Copy urdf files
        run_command_dir(self.source_dir, "cp  ./urdf/" + output_folder_name + ".urdf " + self.target_dir + "urdf/")

        # replace files
        os.system("cp -f ./replace_files/setup.py " + self.target_dir)
        os.system("cp -f ./replace_files/package.xml " + self.target_dir)
        os.system("cp -f ./replace_files/launch.py " + self.target_dir + "launch")

        # Change file content
        # launch.py
        replace_str(self.target_dir + "launch/launch.py", "lesson_urdf", package_name)
        replace_str(self.target_dir + "launch/launch.py", "planar_3dof.urdf", output_folder_name + ".urdf")
        # setup.py
        replace_str(self.target_dir + "setup.py", "lesson_urdf", package_name)
        # package.xml
        replace_str(self.target_dir + "package.xml", "lesson_urdf", package_name)
        # urdf files
        replace_str(self.target_dir + "urdf/" + output_folder_name + ".urdf", output_folder_name + "/meshes",
                    package_name + "/meshes/visual")

        # Insert base_footprint
        keyword = "name=\"" + output_folder_name + "\">"
        str = ""
        with open("./replace_files/insert_content.txt", "r", encoding="utf-8") as f:
            str = f.read()

        file = open(self.target_dir + "/urdf/" + output_folder_name + ".urdf", 'r')
        content = file.read()
        post = content.find(keyword)
        if post != -1:
            content = content[:post + len(keyword)] + "\n" + str + content[post + len(keyword):]
            file = open(self.target_dir + "/urdf/" + output_folder_name + ".urdf", "w")
            file.write(content)
        file.close()

        messagebox.showinfo("Success", "Conversion completed successfully!")

# Run the GUI
if __name__ == '__main__':
    root = tk.Tk()
    app = ConversionApp(root)
    root.mainloop()
