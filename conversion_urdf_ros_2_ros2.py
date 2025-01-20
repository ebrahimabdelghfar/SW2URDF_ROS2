import os
import shutil
import sys
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import xml.etree.ElementTree as ET

# Configuration variable
def get_directory(title):
    path = filedialog.askdirectory(title=title)
    # Ensure the path ends with a forward slash
    if not path.endswith("/"):
        path += "/"
    return path

def run_command_dir(command_dir, command):
    os.system(f"cd {command_dir} && {command}")

def replace_str(file, old_str, new_str):
    file_data = ""
    with open(file, "r", encoding="utf-8") as f:
        for line in f:
            if old_str in line:
                line = line.replace(old_str, new_str)
            file_data += line
    with open(file, "w", encoding="utf-8") as f:
        f.write(file_data)

# Function to modify URDF
def modify_urdf(urdf_path, package_name):
    tree = ET.parse(urdf_path)
    root = tree.getroot()
    
    # Find all fixed joints and change them to continuous
    for joint in root.findall(".//joint"):
        if joint.get("type") == "fixed":
            joint.set("type", "continuous")
            # Change z-axis in origin from 0 to 1
            origin = joint.find("axis")
            if origin is not None:
                z = origin.get("xyz").split()[2]
                if z == '0':
                    origin.set("xyz", origin.get("xyz")[:origin.get("xyz").rfind('0')] + '1')
    tree.write(urdf_path)

def replace_model_with_package(sdf_path):
    try:
        with open(sdf_path, 'r', encoding='utf-8') as file:
            content = file.read()
        content = content.replace('model://', 'package://')
        with open(sdf_path, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"Successfully replaced 'model://' with 'package://' in {sdf_path}")
    except Exception as e:
        print(f"Error replacing 'model://' with 'package://' in {sdf_path}: {e}")

# Function to modify SDF based on original URDF
def modify_sdf(sdf_path, original_urdf_path):
    tree_urdf = ET.parse(original_urdf_path)
    root_urdf = tree_urdf.getroot()
    fixed_joints = [joint.get("name") for joint in root_urdf.findall(".//joint") if joint.get("type") == "fixed"]
    
    tree_sdf = ET.parse(sdf_path)
    root_sdf = tree_sdf.getroot()
    
    # Change revolute joints to fixed if they were fixed in the original URDF
    for joint in root_sdf.findall(".//joint"):
        if joint.get("name") in fixed_joints and joint.get("type") == "revolute":
            joint.set("type", "fixed")
    
    tree_sdf.write(sdf_path)
    # Replace "model://" with "package://" in the SDF file
    replace_model_with_package(sdf_path)

# GUI application
class ConversionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SolidWorks to ROS2 Conversion")

        self.source_dir = ""
        self.target_dir = ""
        self.package_path = ""
        self.package_name = ""
        self.workspace_dir = ""

        # Checkbox variable
        self.is_package_created = tk.IntVar()

        # Create and place labels and buttons
        self.source_label = tk.Label(root, text="Source Directory (SolidWorks URDF Output):")
        self.source_label.pack(pady=5)

        self.source_button = tk.Button(root, text="Select Source Folder", command=self.select_source)
        self.source_button.pack(pady=5)

        # Checkbox
        self.checkbox = tk.Checkbutton(root, text="Package already created", variable=self.is_package_created, command=self.update_widgets)
        self.checkbox.pack(pady=5)

        # Package path selection (if package is already created)
        self.package_path_label = tk.Label(root, text="Package Path:")
        self.package_path_label.pack(pady=5)
        self.package_path_button = tk.Button(root, text="Select Package Folder", command=self.select_package_path, state=tk.DISABLED)
        self.package_path_button.pack(pady=5)

        # Package creation fields (if package is not created)
        self.package_name_label = tk.Label(root, text="Package Name:")
        self.package_name_label.pack(pady=5)
        self.package_name_entry = tk.Entry(root)
        self.package_name_entry.pack(pady=5)
        self.package_name_entry.config(state=tk.DISABLED)

        self.workspace_label = tk.Label(root, text="Workspace Directory:")
        self.workspace_label.pack(pady=5)
        self.workspace_button = tk.Button(root, text="Select Workspace Folder", command=self.select_workspace, state=tk.DISABLED)
        self.workspace_button.pack(pady=5)

        self.create_package_button = tk.Button(root, text="Create Package", command=self.create_package, state=tk.DISABLED)
        self.create_package_button.pack(pady=5)

        self.convert_button = tk.Button(root, text="Start Conversion", command=self.start_conversion, state=tk.DISABLED)
        self.convert_button.pack(pady=20)

        # Initialize widget states
        self.update_widgets()

    def update_widgets(self):
        if self.is_package_created.get():
            # Package already created
            self.package_path_label.config(state=tk.NORMAL)
            self.package_path_button.config(state=tk.NORMAL)
            self.package_name_label.config(state=tk.DISABLED)
            self.package_name_entry.config(state=tk.DISABLED)
            self.workspace_label.config(state=tk.DISABLED)
            self.workspace_button.config(state=tk.DISABLED)
            self.create_package_button.config(state=tk.DISABLED)
        else:
            # Package not created, need to create it
            self.package_path_label.config(state=tk.DISABLED)
            self.package_path_button.config(state=tk.DISABLED)
            self.package_name_label.config(state=tk.NORMAL)
            self.package_name_entry.config(state=tk.NORMAL)
            self.workspace_label.config(state=tk.NORMAL)
            self.workspace_button.config(state=tk.NORMAL)
            self.create_package_button.config(state=tk.NORMAL)

    def select_source(self):
        self.source_dir = get_directory("Select the folder generated from SolidWorks (URDF Output)")
        self.source_label.config(text=f"Source Directory: {self.source_dir}")
        self.check_inputs()

    def select_package_path(self):
        self.package_path = get_directory("Select the ROS2 package folder")
        self.package_path_label.config(text=f"Package Path: {self.package_path}")
        self.check_inputs()

    def select_workspace(self):
        self.workspace_dir = get_directory("Select the ROS2 workspace folder")
        self.workspace_label.config(text=f"Workspace Directory: {self.workspace_dir}")
        self.check_inputs()

    def create_package(self):
        self.package_name = self.package_name_entry.get().strip()
        if not self.package_name:
            messagebox.showerror("Error", "Please enter a package name.")
            return
        if not self.workspace_dir:
            messagebox.showerror("Error", "Please select a workspace directory.")
            return
        # Create the package
        package_creation_command = f"ros2 pkg create {self.package_name} --build-type ament_python"
        os.system(f"cd {self.workspace_dir} && {package_creation_command}")
        # Set the package path
        self.package_path = f"{self.workspace_dir}/{self.package_name}/"
        self.package_path_label.config(text=f"Package Path: {self.package_path}")
        messagebox.showinfo("Success", "Package created successfully!")
        self.check_inputs()

    def check_inputs(self):
        if self.source_dir and self.package_path:
            self.convert_button.config(state=tk.NORMAL)
        else:
            self.convert_button.config(state=tk.DISABLED)

    def start_conversion(self):
        if not self.source_dir or not self.package_path:
            messagebox.showerror("Error", "Please select both source and package directories.")
            return

        package_name = self.package_path.split("/")[-2]
        output_folder_name = self.source_dir.split("/")[-2]

        print("Source Directory: " + self.source_dir)
        print("Package Path: " + self.package_path)
        print("Package Name: " + package_name)
        print("Output Folder Name: " + output_folder_name)

        # Create folders
        run_command_dir(self.package_path, "mkdir launch meshes meshes/collision meshes/visual urdf")

        # Copy files
        # Copy stl files
        run_command_dir(self.source_dir, f"cp -r -f ./meshes/* {self.package_path}meshes/visual")
        run_command_dir(self.source_dir, f"cp -r -f ./meshes/* {self.package_path}meshes/collision")
        # Copy urdf files
        run_command_dir(self.source_dir, f"cp  -r -f ./urdf/{output_folder_name}.urdf {self.package_path}urdf/")

        # Replace files
        os.system(f"cp -r -f ./replace_files/world {self.package_path}")
        os.system(f"cp -r -f ./replace_files/config {self.package_path}")
        os.system(f"cp -f ./replace_files/setup.py {self.package_path}")
        os.system(f"cp -f ./replace_files/package.xml {self.package_path}")
        os.system(f"cp -f ./replace_files/launch.py {self.package_path}launch")
        os.system(f"cp -f ./replace_files/gz_simulator_launch.py {self.package_path}launch")

        # Change file content
        # launch.py
        replace_str(f"{self.package_path}launch/launch.py", "lesson_urdf", package_name)
        replace_str(f"{self.package_path}launch/gz_simulator_launch.py", "lesson_urdf", package_name)
        replace_str(f"{self.package_path}launch/launch.py", "planar_3dof.urdf", f"{output_folder_name}.urdf")
        replace_str(f"{self.package_path}launch/gz_simulator_launch.py", "planar_3dof.urdf", f"{output_folder_name}.urdf")
        # setup.py
        replace_str(f"{self.package_path}setup.py", "lesson_urdf", package_name)
        # package.xml
        replace_str(f"{self.package_path}package.xml", "lesson_urdf", package_name)
        # urdf files
        replace_str(f"{self.package_path}urdf/{output_folder_name}.urdf", f"{output_folder_name}/meshes", f"{package_name}/meshes/visual")

        # Copy the generated URDF
        copied_urdf_path = f"{self.package_path}urdf/{output_folder_name}_modified.urdf"
        shutil.copy(f"{self.package_path}urdf/{output_folder_name}.urdf", copied_urdf_path)

        # Modify the copied URDF
        modify_urdf(copied_urdf_path, package_name)

        # Generate SDF from modified URDF
        os.system(f"cd {self.package_path}urdf/ && gz sdf -p {output_folder_name}_modified.urdf > robot.sdf")

        # Modify the generated SDF
        modify_sdf(f"{self.package_path}urdf/robot.sdf", f"{self.package_path}urdf/{output_folder_name}.urdf")

        # Delete the copied URDF
        os.remove(copied_urdf_path)

        messagebox.showinfo("Success", "Conversion completed successfully!")

# Run the GUI
if __name__ == '__main__':
    root = tk.Tk()
    app = ConversionApp(root)
    root.mainloop()