#GUI Simulation der TU Sofia Mensa während der Mittagspause: Analyse und Optimierungsvorschläge
#Authorin: Ivayla Markova, Technische Universität - Sofia, Fakultät für deutsche Ingenieur- und Betriebswirtschaftsausbildung
import simpy
import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import time
import queue

# Parameter
SIM_TIME = 120  # Minuten
MEAN_ARRIVAL = 2
MEAN_SERVICE = 3

#GUI
root=tk.Tk()
root.title("Simulation der TU Sofia Mensa während der Mittagspause - IVAYLA MARKOVA, FDIBA, TU-Sofia")
root.geometry("850x750")


#Animation
canvas=tk.Canvas(root, width=600, height=200, bg="white")
canvas.pack(pady=10)

control_frame=tk.Frame(root)
control_frame.pack(pady=10)

#List, wartende Menschen als Kreise
people=[]
student_objects=[]

#Bereich
output_text=tk.Text(root, height=5, width=80)
output_text.pack(pady=10)

input_frame=tk.Frame(root)
input_frame.pack()

#Eingabefelder
tk.Label(input_frame, text="Simulationszeit (Minuten):").grid(row=0, column=0, padx=5)
entry_time = tk.Entry(input_frame)
entry_time.grid(row=0, column=1, padx=5)
entry_time.insert(0, str(SIM_TIME))

tk.Label(input_frame, text="Mittlere Ankunftszeit:").grid(row=1, column=0, padx=5)
entry_arrival = tk.Entry(input_frame)
entry_arrival.grid(row=1, column=1, padx=5)
entry_arrival.insert(0, str(MEAN_ARRIVAL))

tk.Label(input_frame, text="Mittlere Servicezeit:").grid(row=2, column=0, padx=5)
entry_service = tk.Entry(input_frame)
entry_service.grid(row=2, column=1, padx=5)
entry_service.insert(0, str(MEAN_SERVICE))

#Dynamisch var für Live-Updates
wait_times=[]
queue_lenghts =[]
queue_count=0 #Menschen in der Schlange
running =False #Flag
paused=False
canvas_plot=None
simulation_speed=1500#ms zw. Updates

plot_queue = queue.Queue()

speed_frame=tk.Frame(root)
speed_frame.pack(pady=5)
tk.Label(speed_frame, text="Animationsgeschwindigkeit:").pack(side=tk.LEFT)
speed_slider = tk.Scale(speed_frame, from_=500, to=3000, orient=tk.HORIZONTAL,
                        command=lambda v: set_speed(int(float(v))))
speed_slider.set(simulation_speed)
speed_slider.pack(side=tk.LEFT)

def set_speed(value):
    global simulation_speed
    simulation_speed = value

def update_animation():#Position der Wartenden auf dem Canvas
    if not running:
        return
    canvas.delete("all")
    canvas.config(height=250)
    visible_people = people[:10] #nur die erste 10 Menschen zeigen

    #statische Elemente
    canvas.create_rectangle(50,100,150,200, fill="lightgreen", outline="black")#Mensaarbeiter
    canvas.create_rectangle(400,100,500,200, fill="pink", outline="black")#Kasse
    canvas.create_text(100,90, text="Kellner")
    canvas.create_text(450,90,text="Kasse")
    #Weg
    canvas.create_line(150, 150, 400, 150, width=3, fill="gray")

    canvas.create_rectangle(180, 120, 370, 180, outline="orange", dash=(2,2))
    canvas.create_text(275, 110, text="Warteschlange")
    #Personen als Kreise
    for i, person in enumerate(visible_people):
        x=200 +i*40
        if x>350:
            x=350
        y=150
        head=canvas.create_oval(x-10,y-25,x+10, y-5, fill='green', outline="black")
        body = canvas.create_line(x, y-5, x, y+15, width=2)

        left_arm = canvas.create_line(x-10, y, x-5, y+5, width=2)
        right_arm = canvas.create_line(x+10, y, x+5, y+5, width=2)

        left_leg = canvas.create_line(x, y+15, x-5, y+25, width=2)
        right_leg = canvas.create_line(x, y+15, x+5, y+25, width=2)
        student_objects.append([head, body, left_arm, right_arm, left_leg, right_leg])
    if not paused:
        root.after(simulation_speed, update_animation)
def toggle_pause():
    global paused
    paused = not paused
    if not paused and running:
        update_animation()
    pause_button.config(text="Fortsetzen" if paused else "Pause")

def stop_simulation():
    global running
    running = False
    output_text.insert(tk.END, "\nSimulation gestoppt")
def create_plot():
    try:
        # Get data from queue
        wait_times = plot_queue.get_nowait()

        if canvas_plot:
            canvas_plot.get_tk_widget().pack_forget()

        fig, ax = plt.subplots(figsize=(7, 6))
        plt.subplots_adjust(bottom=0.15, left=0.15, top=0.95)
        ax.hist(wait_times, bins=15, edgecolor='black', color='#4CAF50', alpha=0.9)
        ax.set_title("Verteilung der Wartezeiten", pad=15, fontsize=12)
        ax.set_xlabel("Wartezeit (Minuten)", fontsize=10)
        ax.set_ylabel("Anzahl Studierende", fontsize=10)
        ax.grid(axis='y', alpha=0.3)

        canvas_plot = FigureCanvasTkAgg(fig, master=root)
        plt.tight_layout()
        canvas_plot.draw()
        canvas_plot.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=20)

    except queue.Empty:
        pass
    finally:
        if running:
            root.after(100, create_plot)

def simulation_thread():
    global queue_count, people, running, canvas_plot
    try:
        sim_time=int(entry_time.get())
        mean_arrival=float(entry_arrival.get())
        mean_service=float(entry_service.get())

        if sim_time <= 0 or mean_arrival <=0 or mean_service <=0:
            raise ValueError("Alle Werte müssen positiv sein!")
        # Metriken
        wait_times.clear()
        queue_lenghts.clear()
        queue_count=0
        people.clear()
        student_objects.clear()

        running=True #Start
        paused=False
        root.after(0, update_animation)
        root.after(0, create_plot)

        def student(env, food_counter, cashier):
            global queue_count
            arrival_time = env.now

            queue_count+=1
            people.append(queue_count)
            root.after(0, update_animation)
            while paused and running:
                time.sleep(0.1)
                if not running:
                    return
            # Phase 1: Essensausgabe
            with food_counter.request() as req:
                yield req
                yield env.timeout(np.random.exponential(mean_service / 2)*2)
            # Phase 2: Kasse
            with cashier.request() as req:
                queue_lenghts.append(len(cashier.queue))  # Warteschlangenlänge
                yield req
                yield env.timeout(np.random.exponential(mean_service)*2)
            wait_times.append(env.now - arrival_time)  # Gesamtwartezeit
            #verlässt die Warteschlange
            queue_count-=1
            if people:
                people.pop(0)
            root.after(0, update_animation)

        def setup(env):
            food_counter = simpy.Resource(env, capacity=2)
            cashier = simpy.Resource(env, capacity=1)
            while True:
                yield env.timeout(np.random.exponential(mean_arrival))
                env.process(student(env, food_counter, cashier))
        # Simulation
        env = simpy.Environment()
        env.process(setup(env))
        env.run(until=sim_time)

        running=False#Stop Animation nach der Simulation

        avg_wait=np.mean(wait_times) if wait_times else 0
        max_queue=max(queue_lenghts) if queue_lenghts else 0

        root.after(
            0, lambda:output_text.delete(1.0, tk.END))
        root.after(0, lambda: output_text.insert(tk.END,
            f"Durchschnittliche Wartezeit: {avg_wait:.1f} Minuten\n" +
            f"Maximale Warteschlangenlänge: {max_queue} Personen\n" +
            f"Gesamtzahl der Kunden: {len(wait_times)}"))
        plot_queue.put(wait_times.copy())
        # Visualisierung
        if canvas_plot:
            canvas_plot.get_tk_widget().pack_forget()#Alte Grafik
        fig, ax = plt.subplots(figsize=(6,5))
        ax.hist(wait_times, bins=20, edgecolor='black', color='yellow')
        ax.set_title("Verteilung der Wartezeiten ")
        ax.set_xlabel("Minuten")
        ax.set_ylabel("Anzahl Studierende", fontsize=10)
        ax.margins(y=0.1)

        canvas_plot=FigureCanvasTkAgg(fig, master=root)
        canvas_plot.draw()
        root.after(0, lambda:canvas_plot.get_tk_widget().pack())

    except ValueError as e:
        root.after(0,lambda:messagebox.showerror("Fehler", str(e)))
def run_simulation():
    if not running:
        thread = threading.Thread(target=simulation_thread, daemon=True)
        thread.start()

# Buttons
button_frame = tk.Frame(root)
button_frame.pack(pady=10)

start_button = tk.Button(button_frame, text="Simulation starten", command=run_simulation)
start_button.pack(side=tk.LEFT, padx=5)

pause_button = tk.Button(button_frame, text="Pause", command=toggle_pause)
pause_button.pack(side=tk.LEFT, padx=5)

stop_button = tk.Button(button_frame, text="Stopp", command=stop_simulation)
stop_button.pack(side=tk.LEFT, padx=5)

root.mainloop()
