#GUI Simulation der TU Sofia Mensa während der Mittagspause: Analyse und Optimierungsvorschläge
#Authorin: Ivayla Markova, Technische Universität - Sofia, Fakultät für deutsche Ingenieur- und Betriebswirtschaftsausbildung
import simpy
import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random

# Parameter
SIM_TIME = 120  # Minuten
MEAN_ARRIVAL = 2
MEAN_SERVICE = 3

#GUI
root=tk.Tk()
root.title("Simulation der TU Sofia Mensa während der Mittagspause")
root.geometry("600x600")

#Animation
canvas=tk.Canvas(root, width=400, height=200, bg="white")
canvas.pack()

#List, wartende Menschen als Kreise
people=[]

#Bereich
output_text=tk.Text(root, height=5, width=60)
output_text.pack()

#Eingabefelder
tk.Label(root, text="Simulationszeit (Minuten):").pack()
entry_time = tk.Entry(root)
entry_time.pack()
entry_time.insert(0, str(SIM_TIME))

tk.Label(root, text="Mittlere Ankunftszeit:").pack()
entry_arrival = tk.Entry(root)
entry_arrival.pack()
entry_arrival.insert(0, str(MEAN_ARRIVAL))

tk.Label(root, text="Mittlere Servicezeit").pack()
entry_service = tk.Entry(root)
entry_service.pack()
entry_service.insert(0, str(MEAN_SERVICE))

#Dynamisch var für Live-Updates
wait_times=[]
queue_lenghts =[]
queue_count=0 #Menschen in der Schlange
running =False #Flag

def update_animation():#Position der Wartenden auf dem Canvas
    if not running:
        return
    canvas.delete("all")
    #Personen als Kreise
    for i, person in enumerate(people):
        x=50 +i*30
        y=100
        canvas.create_oval(x,y,x+20, y+20, fill='green')
    root.after(500, update_animation)#ms wiederholen

def run_simulation():
    global queue_count, people, running
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
        def student(env, food_counter, cashier):
            global queue_count
            arrival_time = env.now

            queue_count+=1
            people.append(queue_count)

            # Phase 1: Essensausgabe
            with food_counter.request() as req:
                yield req
                yield env.timeout(np.random.exponential(mean_service / 2))
            # Phase 2: Kasse
            with cashier.request() as req:
                queue_lenghts.append(len(cashier.queue))  # Warteschlangenlänge
                yield req
                yield env.timeout(np.random.exponential(mean_service))
            wait_times.append(env.now - arrival_time)  # Gesamtwartezeit
            #verlässt die Warteschlange
            queue_count-=1
            if people:
                people.pop(0)

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

        avg_wait=np.mean(wait_times) if wait_times else 0
        max_queue=max(queue_lenghts) if queue_lenghts else 0

        output_text.delete(1.0, tk.END)
        output_text.insert(tk.END, f"Wartezeit: {avg_wait:.1f}Min. \n")
        output_text.insert(tk.END, f"Max. Warteschlange: {max_queue} Personen \n")

        # Visualisierung
        fig, ax = plt.subplots(figsize=(5,3))
        ax.hist(wait_times, bins=20, edgecolor='black')
        ax.set_title("Verteilung der Wartezeiten ")
        ax.set_xlabel("Minuten")
        ax.set_ylabel("Anzahl Studierende")

        canvas_plot=FigureCanvasTkAgg(fig, master=root)
        canvas_plot.draw()
        canvas_plot.get_tk_widget().pack()

    except ValueError as e:
        messagebox.showerror("Fehler", str(e))


tk.Button(root, text="Simulation starten", command=run_simulation).pack()

root.mainloop()
