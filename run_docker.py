import os
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk

def get_available_containers(container_dir):
    """Scanner container-mappen etter .tar filer"""
    containers = []
    for file in os.listdir(container_dir):
        if file.endswith('.tar'):
            containers.append(file)
    return containers

def load_and_run_docker_image(image_path, root_dir, root):
    docker_path = r"C:\Program Files\Docker\Docker\resources\bin\docker.exe"
    
    # Sjekk om Docker eksisterer
    if not os.path.isfile(docker_path):
        messagebox.showerror("Docker ikke funnet", "Docker ble ikke funnet på angitt sti.")
        return

    # Sjekk om Docker kjører
    try:
        subprocess.run([docker_path, "ps"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        messagebox.showerror("Docker Feil", "Docker kjører ikke. Vennligst start Docker Desktop først.")
        return
    
    try:
        # Last Docker image fra fil
        messagebox.showinfo("Fremdrift", f"Laster Docker image fra {image_path}...", parent=root)
        load_result = subprocess.run(
            [docker_path, "load", "-i", image_path],
            check=True, capture_output=True, text=True
        )
        
        # Hent ut image navn fra last-output
        # Docker load output inneholder vanligvis "Loaded image: image_name:tag"
        image_name = load_result.stdout.split("Loaded image: ")[-1].strip()
        
        # Kjør container
        messagebox.showinfo("Fremdrift", f"Kjører container {image_name}...", parent=root)
        result = subprocess.run(
            [docker_path, "run", "--rm", "-v", f"{root_dir}:/app/files", image_name],
            check=True, capture_output=True, text=True
        )
        
        print(result.stdout)
        messagebox.showinfo("Suksess", "Prosessen ble fullført!", parent=root)
        
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Feil", f"Prosessen feilet med feilmelding: {e.stderr}")
    except Exception as e:
        messagebox.showerror("Feil", f"En uventet feil oppstod: {str(e)}")
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
