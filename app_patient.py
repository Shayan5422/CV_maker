import streamlit as st
import pandas as pd
import plotly.express as px
from collections import deque
import datetime
import random
import math

# لیست پیش‌فرض بیماران
patients_operations = [
    [['C1*2'], ['C1', 'C2'], ['C1', 'C3'], ['C1', 'C2*2'], ['C4', 'C5*2', 'C6']],
    [['C2', 'C3'], ['C2', 'C3'], ['C2'], [], []],
    [['C3*2'], ['C3'], [], [], []],
    [['C4*2'], ['C5', 'C6'], ['C6*2'], ['C4*2'], ['C1', 'C2']],
    [['C2*2'], ['C5'], ['C5', 'C6'], ['C4', 'C5'], ['C3']],
    [['C1'], ['C4'], ['C6'], [], []],
    [['C6*2'], ['C1'], ['C5', 'C6'], ['C3'], []],
    [['C3', 'C5'], ['C2', 'C5'], ['C3', 'C6'], ['C6'], []],
    [['C5'], ['C4'], ['C1'], [], []],
    [['C4'], ['C4', 'C5'], ['C1', 'C2'], ['C4'], []]
]

# Configuration de la page
st.set_page_config(page_title="Planificateur de Tâches", layout="wide")

if 'tasks' not in st.session_state:
    st.session_state.tasks = ['C1', 'C2', 'C3', 'C4', 'C5', 'C6']
if 'task_capacities' not in st.session_state:
    st.session_state.task_capacities = {task: 5 for task in st.session_state.tasks}
if 'patients' not in st.session_state:
    st.session_state.patients = []
if len(st.session_state.patients) == 0:
    for i, ops in enumerate(patients_operations):
        st.session_state.patients.append({
            'id': i + 1,
            'operations': ops
        })

class Task:
    def __init__(self, name, patient_id, operation_idx, start=None, end=None):
        self.name = name
        self.patient_id = patient_id
        self.operation_idx = operation_idx
        self.start = start
        self.end = end

    def to_dict(self):
        return {
            'Patient': f'Patient {self.patient_id}',
            'Tâche': self.name,
            'Opération': f'Op {self.operation_idx + 1}',
            'Début': self.start,
            'Fin': self.end
        }

def parse_task(task_str):
    if '*' in task_str:
        task_name, multiplier = task_str.split('*')
        return task_name, int(multiplier)
    return task_str, 1

def calculate_schedule_cost(tasks_list, capacities):
    tasks_list.sort(key=lambda t: (t.patient_id, t.operation_idx))
    resource_usage = {task: deque() for task in capacities.keys()}
    patient_end_time = {}
    schedule = []
    
    for task in tasks_list:
        base_time = patient_end_time.get(task.patient_id, 0)
        while resource_usage[task.name] and resource_usage[task.name][0] <= base_time:
            resource_usage[task.name].popleft()
        if len(resource_usage[task.name]) >= capacities[task.name]:
            start_time = resource_usage[task.name][0]
        else:
            start_time = base_time
        task.start = start_time
        task.end = start_time + 1
        resource_usage[task.name].append(task.end)
        patient_end_time[task.patient_id] = task.end
        schedule.append(task.to_dict())
    
    total_cost = max(patient_end_time.values()) if patient_end_time else 0
    return total_cost, schedule

def create_gantt_chart(schedule_data):
    if not schedule_data:
        return None
    df = pd.DataFrame(schedule_data)
    base_date = datetime.datetime.today()
    df['Start'] = df['Début'].apply(lambda x: base_date + datetime.timedelta(hours=x))
    df['Finish'] = df['Fin'].apply(lambda x: base_date + datetime.timedelta(hours=x))
    fig = px.timeline(df,
                      x_start='Start',
                      x_end='Finish',
                      y='Tâche',
                      color='Patient',
                      title="Planning des Tâches",
                      text='Opération')
    fig.update_layout(
        height=600,
        showlegend=True,
        xaxis_title="Temps",
        yaxis_title="Tâches"
    )
    return fig

# الگوریتم‌های بهینه‌سازی با منطق اصلاح‌شده (مثلاً در Recuit Simulé فقط تغییر در داخل یک عملیات)
def simulated_annealing(tasks_list, capacities, T=1000, T_min=1, alpha=0.95):
    current = tasks_list.copy()
    current_cost, current_schedule = calculate_schedule_cost(current, capacities)
    best_cost = current_cost
    best_schedule = current_schedule
    temp = T
    while temp > T_min:
        for _ in range(100):
            new_solution = current.copy()
            # انتخاب تصادفی یک بیمار
            patient_ids = list(set(task.patient_id for task in new_solution))
            patient = random.choice(patient_ids)
            # انتخاب تصادفی تسک‌های همان عملیات
            op_tasks = [ (i, task) for i, task in enumerate(new_solution) 
                         if task.patient_id == patient ]
            if op_tasks:
                op_index = op_tasks[0][1].operation_idx
                same_op_tasks = [ (i, task) for i, task in enumerate(new_solution) 
                                  if task.patient_id == patient and task.operation_idx == op_index ]
                if len(same_op_tasks) >= 2:
                    i, _ = random.choice(same_op_tasks)
                    j, _ = random.choice(same_op_tasks)
                    while j == i:
                        j, _ = random.choice(same_op_tasks)
                    new_solution[i], new_solution[j] = new_solution[j], new_solution[i]
            new_cost, new_schedule = calculate_schedule_cost(new_solution, capacities)
            delta = new_cost - current_cost
            if delta < 0 or random.random() < math.exp(-delta / temp):
                current = new_solution
                current_cost = new_cost
                current_schedule = new_schedule
                if current_cost < best_cost:
                    best_cost = current_cost
                    best_schedule = current_schedule
        temp *= alpha
    return best_schedule, best_cost

def tabu_search(tasks_list, capacities, max_iterations=1000, tabu_size=50):
    current = tasks_list.copy()
    current_cost, current_schedule = calculate_schedule_cost(current, capacities)
    best_cost = current_cost
    best_schedule = current_schedule
    tabu_list = []
    for _ in range(max_iterations):
        neighborhood = []
        for i in range(len(current)):
            for j in range(i + 1, len(current)):
                neighbor = current.copy()
                neighbor[i], neighbor[j] = neighbor[j], neighbor[i]
                move = (neighbor[i].patient_id, neighbor[i].operation_idx,
                        neighbor[j].patient_id, neighbor[j].operation_idx)
                if move not in tabu_list:
                    cost, schedule = calculate_schedule_cost(neighbor, capacities)
                    neighborhood.append((cost, neighbor, schedule))
        if not neighborhood:
            break
        best_neighbor_cost, best_neighbor, best_neighbor_schedule = min(neighborhood, key=lambda x: x[0])
        current = best_neighbor
        current_cost = best_neighbor_cost
        current_schedule = best_neighbor_schedule
        if current_cost < best_cost:
            best_cost = current_cost
            best_schedule = current_schedule
        move = (current[0].patient_id, current[0].operation_idx,
                current[1].patient_id, current[1].operation_idx)
        tabu_list.append(move)
        if len(tabu_list) > tabu_size:
            tabu_list.pop(0)
    return best_schedule, best_cost

def genetic_algorithm(tasks_list, capacities, population_size=50, generations=100):
    def create_individual():
        ind = tasks_list.copy()
        random.shuffle(ind)
        return ind
    
    def crossover(p1, p2):
        point = random.randint(1, len(p1) - 1)
        child = p1[:point] + [t for t in p2 if t not in p1[:point]]
        return child
    
    population = [create_individual() for _ in range(population_size)]
    best_schedule = None
    best_cost = float('inf')
    for gen in range(generations):
        evaluations = []
        for individual in population:
            cost, schedule = calculate_schedule_cost(individual, capacities)
            evaluations.append((cost, individual))
            if cost < best_cost:
                best_cost = cost
                best_schedule = schedule
        evaluations.sort(key=lambda x: x[0])
        elite = [ind for cost, ind in evaluations[:population_size//5]]
        new_population = elite.copy()
        while len(new_population) < population_size:
            parents = random.sample(elite, 2)
            child = crossover(parents[0], parents[1])
            if random.random() < 0.1:
                i, j = random.sample(range(len(child)), 2)
                child[i], child[j] = child[j], child[i]
            new_population.append(child)
        population = new_population
    return best_schedule, best_cost

# واسط کاربری Streamlit
st.title('🏥 Planificateur de Tâches Médicales')
with st.sidebar:
    st.header("Configuration")
    st.subheader("Capacités des Ressources")
    for task in st.session_state.tasks:
        st.session_state.task_capacities[task] = st.number_input(
            f"Capacité {task}",
            min_value=1,
            value=st.session_state.task_capacities[task],
            key=f"cap_{task}"
        )
    if st.button("➕ Ajouter un Patient"):
        st.session_state.patients.append({
            'id': len(st.session_state.patients) + 1,
            'operations': [[]]
        })
    st.subheader("Algorithmes")
    selected_algorithms = st.multiselect(
        "Sélectionner les algorithmes",
        ["Recuit Simulé", "Recherche Tabou", "Algorithme Génétique"],
        default=["Recuit Simulé"]
    )

for idx, patient in enumerate(st.session_state.patients):
    col1, col2 = st.columns([6, 1])
    with col1:
        st.subheader(f"🤒 Patient {patient['id']}")
    with col2:
        if st.button("❌", key=f"del_patient_{idx}"):
            st.session_state.patients.pop(idx)
            st.experimental_rerun()
    for op_idx, operation in enumerate(patient['operations']):
        st.write(f"📋 Opération {op_idx + 1}")
        cols = st.columns(len(st.session_state.tasks))
        for task_idx, task in enumerate(st.session_state.tasks):
            with cols[task_idx]:
                current_count = sum(1 for t in operation if t.split('*')[0] == task)
                new_count = st.number_input(
                    task,
                    min_value=0,
                    value=current_count,
                    key=f"task_{patient['id']}_{op_idx}_{task}"
                )
                if new_count != current_count:
                    operation = [t for t in operation if t.split('*')[0] != task]
                    if new_count > 0:
                        operation.append(f"{task}*{new_count}" if new_count > 1 else task)
                    st.session_state.patients[idx]['operations'][op_idx] = operation
    if st.button("➕ Nouvelle Opération", key=f"add_op_{idx}"):
        st.session_state.patients[idx]['operations'].append([])
        st.experimental_rerun()
    st.divider()

if st.session_state.patients and selected_algorithms:
    if st.button("🚀 Optimiser le Planning", type="primary"):
        all_tasks = []
        for patient in st.session_state.patients:
            for op_idx, operation in enumerate(patient['operations']):
                for task_str in operation:
                    task_name, count = parse_task(task_str)
                    for _ in range(count):
                        all_tasks.append(Task(task_name, patient['id'], op_idx))
        results = []
        if "Recuit Simulé" in selected_algorithms:
            rs_schedule, rs_cost = simulated_annealing(all_tasks, st.session_state.task_capacities)
            results.append(("Recuit Simulé", rs_schedule, rs_cost))
        if "Algorithme Génétique" in selected_algorithms:
            ga_schedule, ga_cost = genetic_algorithm(all_tasks, st.session_state.task_capacities)
            results.append(("Algorithme Génétique", ga_schedule, ga_cost))
        if "Recherche Tabou" in selected_algorithms:
            ts_schedule, ts_cost = tabu_search(all_tasks, st.session_state.task_capacities)
            results.append(("Recherche Tabou", ts_schedule, ts_cost))
        
        st.subheader("📊 Comparaison des Résultats")
        comparison_df = pd.DataFrame({
            'Algorithme': [r[0] for r in results],
            'Coût Total': [r[2] for r in results]
        })
        st.dataframe(comparison_df)
        
        best_algo, best_schedule, best_cost = min(results, key=lambda x: x[2])
        st.success(f"Meilleure solution trouvée par {best_algo} avec un coût de {best_cost}")
        
        fig = create_gantt_chart(best_schedule)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("📋 Détails du Planning")
        schedule_df = pd.DataFrame(best_schedule)
        st.dataframe(schedule_df)
        
        st.subheader("📈 Statistiques d'Utilisation des Ressources")
        usage_stats = schedule_df.groupby('Tâche').agg({
            'Patient': 'count',
            'Début': 'min',
            'Fin': 'max'
        }).rename(columns={
            'Patient': 'Nombre de tâches',
            'Début': 'Première utilisation',
            'Fin': 'Dernière utilisation'
        })
        st.dataframe(usage_stats)
else:
    st.info("👈 Commencez par ajouter des patients et sélectionner les algorithmes d'optimisation")
