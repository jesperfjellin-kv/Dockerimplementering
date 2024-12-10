# TODO: endre self.container_dir = r"C:\FKKOslo\PyScripts\Docker\Containers" når man finner ut av hvor .TAR-filer skal ligge

import os
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
import json

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
        
        image_name = load_result.stdout.split("Loaded image: ")[-1].strip()
        print(f"\nDEBUG - Loaded image name: {image_name}")

        # Inspiser image for å finne labels
        inspect_result = subprocess.run(
            [docker_path, "image", "inspect", image_name, "--format", "{{json .Config.Labels}}"],
            check=True, capture_output=True, text=True
        )

        labels = json.loads(inspect_result.stdout) if inspect_result.stdout.strip() else {}
        required_args = labels.get("required_args", "")
        print(f"\nDEBUG - Required arguments from labels: {required_args}")

        # Inspiser image for å finne miljøvariabler
        inspect_env_result = subprocess.run(
            [docker_path, "image", "inspect", image_name, "--format", "{{json .Config.Env}}"],
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

        # Hvis det er nødvendige argumenter, spør brukeren om dem og legg dem til kommandoen
        if required_args:
            arg_list = [arg.strip() for arg in required_args.split(',')]
            user_inputs = []
            for arg in arg_list:
                user_input = simpledialog.askstring("Input nødvendig", f"Vennligst oppgi verdi for {arg}:", parent=root)
                if user_input is None:
                    messagebox.showwarning("Avbrutt", f"Du avbrøt input for {arg}. Container vil ikke kjøre.")
                    root.destroy()
                    return
                
                print(f"\nDEBUG - Processing argument '{arg}':")
                print(f"Original input: {user_input}")
                
                # Hvis dette er sti-argumentet
                if arg == "Sti_til_SOSI-filer":
                    if '\\' in user_input:
                        # Konverter til / (unix-snash)
                        user_input = user_input.replace('\\', '/')
                        print(f"Etter backslash-konvertering: {user_input}")
                        
                        # Hent stien til montering (parent av SOSI-filer)
                        mount_path = os.path.dirname(user_input)
                        # Juster brukerens input til å bruke containerens sti
                        user_input = os.path.join(container_path, os.path.basename(user_input))
                        user_input = user_input.replace('\\', '/')
                        print(f"Mount path: {mount_path}")
                        print(f"Container path: {user_input}")
                
                user_inputs.append(user_input)
                print(f"Final argument value: {user_input}")
            
            # Legg til volummontering hvis vi fant en sti
            if mount_path:
                # Monter katalogen for både input og output
                command.extend(["-v", f"{mount_path}:{container_path}"])
            
            # Legg til image navn og kommando
            command.extend([
                image_name,
                "python",
                "/app/stikkproveomrade.py"  
            ])
            
            # Legg til de behandlede argumentene
            command.extend(user_inputs)
            
            print(f"\nDEBUG - Final command with all arguments: {' '.join(command)}")

        # Kjør container
        messagebox.showinfo("Fremdrift", f"Kjører container {image_name}...", parent=root)
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
            
            # Kjør docker-kommandoene
            load_and_run_docker_image(image_path, root_dir, docker_window)
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ContainerSelectorGUI()
    app.run()
