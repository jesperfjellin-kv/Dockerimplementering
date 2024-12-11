# TODO: endre self.container_dir = r"C:\FKKOslo\PyScripts\Docker\Containers" når man finner ut av hvor .TAR-filer skal ligge

import os
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk, simpledialog, filedialog
import json
from pathlib import Path

class ArgumentHandler:
    def __init__(self, root):
        self.root = root
        self.config = self._load_arg_patterns()

    def _load_arg_patterns(self):
        try:
            config_path = Path(__file__).parent / "config" / "arg_patterns.json"
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load argument patterns config: {e}")
            return {"input_patterns": {}}

    def _get_input_type(self, arg_name):
        patterns = self.config["input_patterns"]
        for input_type, pattern_list in patterns.items():
            if any(pattern.lower() in arg_name.lower() for pattern in pattern_list):
                return input_type
        return "text"  # Default to simple text input

    def get_argument_value(self, arg_name):
        input_type = self._get_input_type(arg_name)
        
        if input_type == "folder_selection":
            folder_path = filedialog.askdirectory(
                title=f"Select folder for: {arg_name}",
                parent=self.root
            )
            if folder_path:
                # Convert to Path object to handle UTF-8 properly
                return str(Path(folder_path))
            return None

        elif input_type == "file_selection":
            file_path = filedialog.askopenfilename(
                title=f"Select file for: {arg_name}",
                parent=self.root
            )
            if file_path:
                # Convert to Path object to handle UTF-8 properly
                return str(Path(file_path))
            return None

        elif input_type == "yes_no":
            return messagebox.askyesno(
                "Input Required",
                f"{arg_name}?",
                parent=self.root
            )

        elif input_type == "numeric":
            while True:
                value = simpledialog.askstring(
                    "Input Required",
                    f"Please enter a number for {arg_name}:",
                    parent=self.root
                )
                if value is None:  # User clicked Cancel
                    return None
                try:
                    return int(value)
                except ValueError:
                    messagebox.showerror(
                        "Invalid Input",
                        "Please enter a valid number",
                        parent=self.root
                    )

        else:  # Default text input
            return simpledialog.askstring(
                "Input Required",
                f"Please enter value for {arg_name}:",
                parent=self.root
            )

def get_available_containers(container_dir):
    """Scanner container-mappen etter .tar filer"""
    containers = []
    for file in os.listdir(container_dir):
        if file.endswith('.tar'):
            containers.append(file)
    return containers

def load_and_run_docker_image(image_path, root_dir, root):
    docker_path = r"C:\Program Files\Docker\Docker\resources\bin\docker.exe"
    loaded_image_name = None
    
    # Sjekk om Docker eksisterer
    if not os.path.isfile(docker_path):
        messagebox.showerror("Docker ikke funnet", "Docker ble ikke funnet på angitt sti.")
        root.destroy()
        return

    # Sjekk om Docker kjører
    try:
        subprocess.run([docker_path, "ps"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        messagebox.showerror("Docker Feil", "Docker kjører ikke. Vennligst start Docker Desktop først.")
        root.destroy()
        return
    
    try: 
        # Last Docker image fra fil
        messagebox.showinfo("Fremdrift", f"Laster Docker image fra {image_path}...", parent=root)
        load_result = subprocess.run(
            [docker_path, "load", "-i", image_path],
            check=True, capture_output=True, text=True
        )
        
        loaded_image_name = load_result.stdout.split("Loaded image: ")[-1].strip()
        print(f"\nDEBUG - Loaded image name: {loaded_image_name}")

        # Inspiser image for å finne labels
        inspect_result = subprocess.run(
            [docker_path, "image", "inspect", loaded_image_name, "--format", "{{json .Config.Labels}}"],
            check=True, capture_output=True, text=True
        )

        labels = json.loads(inspect_result.stdout) if inspect_result.stdout.strip() else {}
        required_args = labels.get("required_args", "")
        print(f"\nDEBUG - Required arguments from labels: {required_args}")

        # Inspiser image for å finne miljøvariabler
        inspect_env_result = subprocess.run(
            [docker_path, "image", "inspect", loaded_image_name, "--format", "{{json .Config.Env}}"],
            check=True, capture_output=True, text=True
        )
        env_vars = json.loads(inspect_env_result.stdout) if inspect_env_result.stdout.strip() else []
        
        # Finn CONTAINER_DIR i ENV-variablene
        sos_dir = "/app/sos_files"  # standardverdi om ikke satt i bildet
        for var in env_vars:
            if var.startswith("CONTAINER_DIR="):
                sos_dir = var.split("=", 1)[1]
                break
        
        print(f"\nDEBUG - CONTAINER_DIR from ENV: {sos_dir}")

        # Bygg kommando uten volummontering
        command = [docker_path, "run", "--rm"]
        mount_path = None
        container_path = sos_dir  # Bruk ENV-variabelen istedet for hardkodet sti

        arg_handler = ArgumentHandler(root)
        
        # Hvis det er nødvendige argumenter, spør brukeren om dem og legg dem til kommandoen
        if required_args:
            arg_list = [arg.strip() for arg in required_args.split(',')]
            user_inputs = []
            for arg in arg_list:
                user_input = arg_handler.get_argument_value(arg)
                
                if user_input is None:
                    messagebox.showwarning(
                        "Aborted",
                        f"You cancelled input for {arg}. Container will not run.",
                        parent=root
                    )
                    root.destroy()
                    return

                # Handle path conversion for folder/file inputs
                if isinstance(user_input, str) and os.path.exists(user_input):
                    # Convert to Path object and back to string to handle UTF-8 properly
                    user_input = str(Path(user_input)).replace('\\', '/')
                    
                    if arg == "Sti_til_SOSI-filer":  # Special handling for SOSI files
                        mount_path = str(Path(user_input).parent)
                        user_input = str(Path(container_path) / Path(user_input).name)
                        user_input = user_input.replace('\\', '/')

                user_inputs.append(str(user_input))  # Convert all inputs to strings for command line
            
            # Legg til volummontering hvis vi fant en sti
            if mount_path:
                # Monter katalogen for både input og output
                command.extend(["-v", f"{mount_path}:{container_path}"])
            
            # Legg til image navn og kommando
            command.extend([
                loaded_image_name,
                "python",
                "/app/stikkproveomrade.py"  
            ])
            
            # Legg til de behandlede argumentene
            command.extend(user_inputs)
            
            print(f"\nDEBUG - Final command with all arguments: {' '.join(command)}")

        # Kjør container
        messagebox.showinfo("Fremdrift", f"Kjører container {loaded_image_name}...", parent=root)
        print(f"\nDEBUG - Executing command: {' '.join(command)}")
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        
        print("\nDEBUG - Container output:")
        print(result.stdout)
        messagebox.showinfo("Suksess", "Prosessen ble fullført!", parent=root)
        
    except subprocess.CalledProcessError as e:
        print("\nDEBUG - Error output:")
        print(f"stderr: {e.stderr}")
        print(f"stdout: {e.stdout if hasattr(e, 'stdout') else 'No stdout'}")
        messagebox.showerror("Feil", f"Prosessen feilet med feilmelding:\n{e.stderr}", parent=root)
    except Exception as e:
        print(f"\nDEBUG - Unexpected error: {str(e)}")
        messagebox.showerror("Feil", f"En uventet feil oppstod: {str(e)}", parent=root)
    finally:
        # Cleanup the loaded image
        if loaded_image_name:
            try:
                print(f"\nDEBUG - Cleaning up Docker image: {loaded_image_name}")
                subprocess.run(
                    [docker_path, "rmi", loaded_image_name],
                    check=True, capture_output=True, text=True
                )
                print("DEBUG - Cleanup successful")
            except subprocess.CalledProcessError as e:
                print(f"DEBUG - Cleanup failed: {e.stderr}")
            except Exception as e:
                print(f"DEBUG - Unexpected cleanup error: {str(e)}")
        
        root.destroy()

class ContainerSelectorGUI:
    def __init__(self):
        # Hardkodet sti til container-mappen
        self.container_dir = r"C:\FKKOslo\PyScripts\Docker\Containers"  
        
        # Opprett hovedvindu
        self.root = tk.Tk()
        self.root.title("Docker Container Velger")
        self.root.geometry("400x200")
        
        # Opprett og pakk widgets
        self.create_widgets()
        
    def create_widgets(self):
        # Container velger ramme
        frame = ttk.Frame(self.root, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Etikett
        ttk.Label(frame, text="Velg en container:").pack(pady=10)
        
        # Hent tilgjengelige containere
        containers = get_available_containers(self.container_dir)
        
        if not containers:
            ttk.Label(frame, text="Ingen containere funnet!").pack(pady=10)
            return
        
        # Nedtrekksmeny for container-valg
        self.selected_container = tk.StringVar()
        container_dropdown = ttk.Combobox(frame, 
                                          textvariable=self.selected_container,
                                          values=containers,
                                          state="readonly")
        container_dropdown.pack(pady=10, fill=tk.X)
        container_dropdown.set(containers[0])  # Sett standardverdi
        
        # Kjør-knapp
        ttk.Button(frame, 
                   text="Kjør Container", 
                   command=self.run_selected_container).pack(pady=10)
        
    def run_selected_container(self):
        selected = self.selected_container.get()
        if selected:
            image_path = os.path.join(self.container_dir, selected)
            root_dir = os.getcwd()  # Eller en annen spesifisert mappe
            
            # Opprett nytt vindu for docker-operasjonen
            docker_window = tk.Toplevel(self.root)
            docker_window.withdraw()  # Skjul vinduet
            
            self.root.withdraw()
            
            try:
                load_and_run_docker_image(image_path, root_dir, docker_window)
            finally:
                # Destroy the main window after Docker operations are complete
                if self.root:
                    self.root.destroy()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ContainerSelectorGUI()
    app.run()
