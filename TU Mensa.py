#Simulation der TU Sofia Mensa während der Mittagspause: Analyse und Optimierungsvorschläge
#Authorin: Ivayla Markova, Technische Universität - Sofia, Fakultät für deutsche Ingenieur- und Betriebswirtschaftsausbildung
import simpy
import numpy as np
import matplotlib.pyplot as plt

# Parameter
SIM_TIME = 120  # Minuten
MEAN_ARRIVAL = 2
MEAN_SERVICE = 3

# Metriken
wait_times = []
queue_lengths = []


def student(env, food_counter, cashier):
    arrival_time = env.now
    # Phase 1: Essensausgabe
    with food_counter.request() as req:
        yield req
        yield env.timeout(np.random.exponential(MEAN_SERVICE / 2))

    # Phase 2: Kasse
    with cashier.request() as req:
        queue_lengths.append(len(cashier.queue))  # Warteschlangenlänge
        yield req
        yield env.timeout(np.random.exponential(MEAN_SERVICE))

    wait_times.append(env.now - arrival_time)  # Gesamtwartezeit


def setup(env):
    food_counter = simpy.Resource(env, capacity=2)
    cashier = simpy.Resource(env, capacity=1)
    while True:
        yield env.timeout(np.random.exponential(MEAN_ARRIVAL))
        env.process(student(env, food_counter, cashier))


# Simulation
env = simpy.Environment()
env.process(setup(env))
env.run(until=SIM_TIME)

# Ergebnisse
print(f"⌀ Wartezeit: {np.mean(wait_times):.1f} Min.")
print(f"Max. Warteschlange: {max(queue_lengths)} Personen")

# Visualisierung
plt.hist(wait_times, bins=20)
plt.title("Verteilung der Wartezeiten (Ist-Zustand)")
plt.xlabel("Minuten")
plt.ylabel("Anzahl Studierende")
plt.show()