import streamlit as st
import pandas as pd
import plotly.express as px
from collections import deque
import datetime
import json

# Configuration de la page Streamlit
st.set_page_config(page_title="Planificateur de Tâches", layout="wide")

# Initialisation des états de session
if 'patients' not in st.session_state:
    st.session_state.patients = []
if 'tasks' not in st.session_state:
    st.session_state.tasks = ['C1', 'C2', 'C3', 'C4', 'C5', 'C6']
if 'task_capacities' not in st.session_state:
    st.session_state.task_capacities = {task: 5 for task in st.session_state.tasks}

# Classe Patient pour la gestion des données
class Patient:
    def __init__(self, id_patient):
        self.id = id_patient
        self.operations = []
        self.total_time = 0
    
    def add_operation(self):
        self.operations.append([])
    
    def to_dict(self):
        return {
            'id': self.id,
            'operations': self.operations,
            'total_time': self.total_time
        }

# Fonctions de planification
def parse_task(task_str):
    """Parse une chaîne de tâche pour obtenir le nom et le multiplicateur"""
    if '*' in task_str:
        task_name, multiplier = task_str.split('*')
        return task_name, int(multiplier)
    return task_str, 1

def calculate_schedule(patients_data):
    """Calcule le planning pour tous les patients"""
    schedule = []
    current_time = 0
    resources = {task: [] for task in st.session_state.tasks}
    
    # Création du planning initial
    for patient in patients_data:
        for op_idx, operation in enumerate(patient['operations']):
            for task_str in operation:
                task_name, count = parse_task(task_str)
                for _ in range(count):
                    # Trouver le premier créneau disponible
                    resource_available = max(resources[task_name]) if resources[task_name] else current_time
                    start_time = max(current_time, resource_available)
                    end_time = start_time + 1  # Durée fixe de 1 unité
                    
                    schedule.append({
                        'Patient': f'Patient {patient["id"]}',
                        'Tâche': task_name,
                        'Début': start_time,
                        'Fin': end_time,
                        'Opération': f'Op {op_idx + 1}'
                    })
                    
                    resources[task_name].append(end_time)
                    if len(resources[task_name]) > st.session_state.task_capacities[task_name]:
                        resources[task_name].pop(0)
                    current_time = end_time
    
    return schedule

def create_gantt_chart(schedule_data):
    """Crée un diagramme de Gantt avec Plotly"""
    if not schedule_data:
        return None
        
    df = pd.DataFrame(schedule_data)
    
    # Conversion en datetime pour Plotly
    base_date = datetime.datetime.today()
    df['Start'] = df['Début'].apply(lambda x: base_date + datetime.timedelta(hours=x))
    df['Finish'] = df['Fin'].apply(lambda x: base_date + datetime.timedelta(hours=x))
    
    fig = px.timeline(df,
                     x_start='Start',
                     x_end='Finish',
                     y='Tâche',
                     color='Patient',
                     title="Planning des Tâches",
                     text='Opération',
                     labels={'Task': 'Tâches', 
                            'Start': 'Début', 
                            'Finish': 'Fin'})
    
    fig.update_layout(
        height=600,
        showlegend=True,
        xaxis_title="Temps",
        yaxis_title="Tâches"
    )
    
    return fig

# Interface utilisateur Streamlit
st.title('🏥 Planificateur de Tâches Médicales')

# Barre latérale pour les contrôles
with st.sidebar:
    st.header("Configuration")
    
    # Ajout d'un nouveau patient
    if st.button("➕ Ajouter un Patient"):
        new_patient = Patient(len(st.session_state.patients) + 1)
        new_patient.add_operation()
        st.session_state.patients.append(new_patient.to_dict())
    
    # Configuration des capacités
    st.subheader("Capacités des Ressources")
    for task in st.session_state.tasks:
        st.session_state.task_capacities[task] = st.number_input(
            f"Capacité {task}",
            min_value=1,
            value=st.session_state.task_capacities[task],
            key=f"cap_{task}"
        )

# Zone principale
for idx, patient in enumerate(st.session_state.patients):
    col1, col2 = st.columns([6, 1])
    
    with col1:
        st.subheader(f"🤒 Patient {patient['id']}")
    
    with col2:
        if st.button("❌", key=f"del_patient_{idx}"):
            st.session_state.patients.pop(idx)
            st.rerun()
    
    # Gestion des opérations
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
                    # Mise à jour de l'opération
                    operation = [t for t in operation if t.split('*')[0] != task]
                    if new_count > 0:
                        operation.append(f"{task}*{new_count}" if new_count > 1 else task)
                    st.session_state.patients[idx]['operations'][op_idx] = operation
    
    if st.button("➕ Nouvelle Opération", key=f"add_op_{idx}"):
        st.session_state.patients[idx]['operations'].append([])
        st.rerun()
    
    st.divider()

# Bouton de planification
if st.session_state.patients:
    if st.button("🚀 Générer le Planning", type="primary"):
        schedule = calculate_schedule(st.session_state.patients)
        
        # Affichage des résultats
        st.subheader("📊 Résultats de la Planification")
        
        # Diagramme de Gantt
        fig = create_gantt_chart(schedule)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        
        # Tableau des détails
        st.subheader("📋 Détails du Planning")
        df = pd.DataFrame(schedule)
        st.dataframe(df, use_container_width=True)
        
        # Statistiques
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Temps Total", f"{max(df['Fin'])} heures")
        with col2:
            st.metric("Nombre de Tâches", len(df))
        with col3:
            st.metric("Patients Traités", len(df['Patient'].unique()))
else:
    st.info("👈 Commencez par ajouter des patients dans le menu latéral")