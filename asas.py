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

# Initialisation
if 'tasks' not in st.session_state:
    st.session_state.tasks = ['C1', 'C2', 'C3', 'C4', 'C5', 'C6']
if 'task_capacities' not in st.session_state:
    st.session_state.task_capacities = {task: 5 for task in st.session_state.tasks}
if 'patients' not in st.session_state:
    st.session_state.patients = []

# اگر لیست بیماران خالی است، مقادیر پیش‌فرض را اضافه کن
if len(st.session_state.patients) == 0:
    for i, ops in enumerate(patients_operations):
        st.session_state.patients.append({
            'id': i + 1,
            'operations': ops
        })

# کلاس Task برای تعریف وظایف
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
    """
    Calcule le coût du planning avec les contraintes suivantes:
    - Les tâches d'un même patient dans une opération sont séquentielles
    - Les patients différents peuvent être traités en parallèle si les ressources le permettent
    - Les opérations d'un patient sont séquentielles
    """
    resource_usage = {task: deque() for task in capacities.keys()}
    patient_operation_end_times = {}  # Temps de fin de la dernière opération de chaque patient
    patient_current_task_time = {}    # Temps de fin de la dernière tâche du patient dans l'opération courante
    schedule = []
    current_time = 0
    
    # Grouper les tâches par patient et opération
    tasks_by_patient = {}
    for task in tasks_list:
        if task.patient_id not in tasks_by_patient:
            tasks_by_patient[task.patient_id] = {}
        if task.operation_idx not in tasks_by_patient[task.patient_id]:
            tasks_by_patient[task.patient_id][task.operation_idx] = []
        tasks_by_patient[task.patient_id][task.operation_idx].append(task)

    # Continuer tant qu'il reste des patients à traiter
    active_patients = set(tasks_by_patient.keys())
    
    while active_patients:
        # برای هر بیمار، پیدا کردن وظیفه بعدی آماده اجرا
        available_tasks = []
        patients_to_remove = set()
        
        for patient_id in active_patients:
            if not tasks_by_patient[patient_id]:  # اگر تمام عملیات‌های بیمار به پایان رسیده
                patients_to_remove.add(patient_id)
                continue

            # پیدا کردن عملیات جاری (کمترین ایندکس)
            current_op_idx = min(tasks_by_patient[patient_id].keys())
            
            # چک کردن پایان عملیات قبلی
            if current_op_idx > 0:
                if (patient_id, current_op_idx - 1) not in patient_operation_end_times:
                    continue
                
            # تعیین شروع اولیه برای اجرای وظیفه
            earliest_start = max(
                current_time,
                patient_current_task_time.get(patient_id, 0),
                patient_operation_end_times.get((patient_id, current_op_idx - 1), 0)
            )
            
            # انتخاب اولین وظیفه از عملیات جاری که هنوز برنامه‌ریزی نشده
            if tasks_by_patient[patient_id][current_op_idx]:
                task = tasks_by_patient[patient_id][current_op_idx][0]
                available_tasks.append((task, earliest_start))
        
        # حذف بیماران خاتمه‌یافته
        active_patients.difference_update(patients_to_remove)

        if not available_tasks:
            if active_patients:  # اگر بیمارانی وجود دارند اما وظیفه‌ای آماده نیست
                current_time += 1
                continue
            else:
                break

        # انتخاب وظیفه‌ای که بتواند زودتر شروع شود
        selected_task = None
        best_start_time = float('inf')
        
        for task, earliest_start in available_tasks:
            available_time = earliest_start
            if resource_usage[task.name]:
                # پاکسازی زمان‌های استفاده‌شده که گذشته‌اند
                while resource_usage[task.name] and resource_usage[task.name][0] <= earliest_start:
                    resource_usage[task.name].popleft()
                
                if len(resource_usage[task.name]) >= capacities[task.name]:
                    continue
            
            if available_time < best_start_time:
                best_start_time = available_time
                selected_task = task
        
        if selected_task is None:
            current_time += 1
            continue
            
        # برنامه‌ریزی وظیفه انتخاب شده
        task = selected_task
        task.start = best_start_time
        task.end = best_start_time + 1
        
        # به‌روز رسانی زمان‌ها
        resource_usage[task.name].append(task.end)
        patient_current_task_time[task.patient_id] = task.end
        
        # اضافه کردن وظیفه به برنامه‌ریزی
        schedule.append(task.to_dict())
        
        # حذف وظیفه برنامه‌ریزی شده از فهرست بیمار
        tasks_by_patient[task.patient_id][task.operation_idx].pop(0)
        
        # در صورت اتمام تمامی وظایف یک عملیات، ثبت زمان پایان عملیات
        if not tasks_by_patient[task.patient_id][task.operation_idx]:
            patient_operation_end_times[(task.patient_id, task.operation_idx)] = task.end
            del tasks_by_patient[task.patient_id][task.operation_idx]
        
        # به‌روز رسانی زمان کنونی
        current_time = max(current_time, best_start_time)
    
    # هزینه نهایی برابر با زمان پایان بیشینه در میان تمامی عملیات‌هاست
    total_cost = max(patient_operation_end_times.values()) if patient_operation_end_times else 0
    
    return total_cost, schedule

def create_gantt_chart(schedule_data):
    if not schedule_data:
        return None
    
    df = pd.DataFrame(schedule_data)
    base_date = datetime.datetime.today()
    df['Start'] = df['Début'].apply(lambda x: base_date + datetime.timedelta(hours=x))
    df['Finish'] = df['Fin'].apply(lambda x: base_date + datetime.timedelta(hours=x))
    
    fig = px.timeline(
        df,
        x_start='Start',
        x_end='Finish',
        y='Tâche',
        color='Patient',
        title="Planning des Tâches",
        text='Opération'
    )
    
    fig.update_layout(
        height=600,
        showlegend=True,
        xaxis_title="Temps",
        yaxis_title="Tâches"
    )
    
    return fig

def genetic_algorithm(tasks_list, capacities, population_size=50, generations=100):
    """Algorithme génétique amélioré"""
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
        # Évaluer la population
        evaluations = []
        for individual in population:
            cost, schedule = calculate_schedule_cost(individual, capacities)
            evaluations.append((cost, individual))
            if cost < best_cost:
                best_cost = cost
                best_schedule = schedule
        
        # Trier par coût (ordre croissant)
        evaluations.sort(key=lambda x: x[0])
        
        # Sélection et reproduction
        elite = [ind for cost, ind in evaluations[:population_size//5]]
        new_population = elite.copy()
        
        while len(new_population) < population_size:
            parents = random.sample(elite, 2)
            child = crossover(parents[0], parents[1])
            if random.random() < 0.1:  # Mutation
                i, j = random.sample(range(len(child)), 2)
                child[i], child[j] = child[j], child[i]
            new_population.append(child)
        
        population = new_population
    
    return best_schedule, best_cost

def tabu_search(tasks_list, capacities, max_iterations=1000, tabu_size=50):
    """Algorithme de recherche tabou amélioré"""
    current = tasks_list.copy()
    current_cost, current_schedule = calculate_schedule_cost(current, capacities)
    best_cost = current_cost
    best_schedule = current_schedule
    
    tabu_list = []
    
    for _ in range(max_iterations):
        # Générer le voisinage
        neighborhood = []
        for i in range(len(current)):
            for j in range(i + 1, len(current)):
                neighbor = current.copy()
                neighbor[i], neighbor[j] = neighbor[j], neighbor[i]
                # Vérifier si le mouvement est autorisé
                move = (neighbor[i].patient_id, neighbor[i].operation_idx,
                        neighbor[j].patient_id, neighbor[j].operation_idx)
                if move not in tabu_list:
                    cost, schedule = calculate_schedule_cost(neighbor, capacities)
                    neighborhood.append((cost, neighbor, schedule))
        
        if not neighborhood:
            break
            
        # Sélectionner le meilleur voisin non tabou
        best_neighbor_cost, best_neighbor, best_neighbor_schedule = min(neighborhood, key=lambda x: x[0])
        
        # Mettre à jour la solution courante
        current = best_neighbor
        current_cost = best_neighbor_cost
        current_schedule = best_neighbor_schedule
        
        # Mettre à jour la meilleure solution
        if current_cost < best_cost:
            best_cost = current_cost
            best_schedule = current_schedule
        
        # Mettre à jour la liste tabou
        move = (current[0].patient_id, current[0].operation_idx,
                current[1].patient_id, current[1].operation_idx)
        tabu_list.append(move)
        if len(tabu_list) > tabu_size:
            tabu_list.pop(0)
    
    return best_schedule, best_cost

def simulated_annealing(tasks_list, capacities, T=1000, T_min=1, alpha=0.95):
    """Recuit simulé amélioré"""
    current = tasks_list.copy()
    current_cost, current_schedule = calculate_schedule_cost(current, capacities)
    best_cost = current_cost
    best_schedule = current_schedule
    
    temp = T
    while temp > T_min:
        for _ in range(100):
            new_solution = current.copy()
            i, j = random.sample(range(len(new_solution)), 2)
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

# Interface utilisateur
st.title('🏥 Planificateur de Tâches Médicales')

# Barre latérale
with st.sidebar:
    st.header("Configuration")
    
    # تنظیم ظرفیت‌های منابع
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

# نمایش اطلاعات بیماران و عملیات‌های آن‌ها در رابط اصلی
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
                    # حذف موارد مربوط به این تسک از عملیات فعلی
                    operation = [t for t in operation if t.split('*')[0] != task]
                    if new_count > 0:
                        operation.append(f"{task}*{new_count}" if new_count > 1 else task)
                    st.session_state.patients[idx]['operations'][op_idx] = operation
    
    if st.button("➕ Nouvelle Opération", key=f"add_op_{idx}"):
        st.session_state.patients[idx]['operations'].append([])
        st.experimental_rerun()
    
    st.divider()

# اجرای الگوریتم‌های بهینه‌سازی
if st.session_state.patients and selected_algorithms:
    if st.button("🚀 Optimiser le Planning", type="primary"):
        # آماده‌سازی وظایف
        all_tasks = []
        for patient in st.session_state.patients:
            for op_idx, operation in enumerate(patient['operations']):
                for task_str in operation:
                    task_name, count = parse_task(task_str)
                    for _ in range(count):
                        all_tasks.append(Task(task_name, patient['id'], op_idx))
        
        results = []
        
        if "Recuit Simulé" in selected_algorithms:
            rs_schedule, rs_cost = simulated_annealing(
                all_tasks, 
                st.session_state.task_capacities
            )
            results.append(("Recuit Simulé", rs_schedule, rs_cost))
        
        if "Algorithme Génétique" in selected_algorithms:
            ga_schedule, ga_cost = genetic_algorithm(
                all_tasks,
                st.session_state.task_capacities
            )
            results.append(("Algorithme Génétique", ga_schedule, ga_cost))
            
        if "Recherche Tabou" in selected_algorithms:
            ts_schedule, ts_cost = tabu_search(
                all_tasks,
                st.session_state.task_capacities
            )
            results.append(("Recherche Tabou", ts_schedule, ts_cost))
        
        # نمایش نتایج مقایسه‌ای
        st.subheader("📊 Comparaison des Résultats")
        comparison_df = pd.DataFrame({
            'Algorithme': [r[0] for r in results],
            'Coût Total': [r[2] for r in results]
        })
        st.dataframe(comparison_df)
        
        # انتخاب بهترین راه‌حل
        best_algo, best_schedule, best_cost = min(results, key=lambda x: x[2])
        st.success(f"Meilleure solution trouvée par {best_algo} avec un coût de {best_cost}")
        
        # نمایش نمودار گانت
        fig = create_gantt_chart(best_schedule)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("📋 Détails du Planning")
            schedule_df = pd.DataFrame(best_schedule)
            st.dataframe(schedule_df)
            
            # آمار استفاده از منابع
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
