import streamlit as st
import pandas as pd
import time
from threading import Thread

# Funktion zur Normalisierung der Gewichtungen
def normalize_weights(weights):
    total = sum(weights)
    if total > 0:
        return [w / total * 100 for w in weights]
    return weights

# Funktion zur Anpassung der Gewichtungen, wenn eine geändert wird
def adjust_weights(df, changed_index, new_weight):
    df.at[changed_index, 'Gewichtung'] = new_weight
    return df

# Titel der Anwendung
st.title("Make-or-Buy Nutzwertanalyse")

st.markdown("---")

# Beurteilungskriterien
st.header("Beurteilungskriterien und Gewichtungen")

# Vordefinierte Kriterien
default_criteria = ['Kosten', 'Kapazität', 'Qualität', 'Zuverlässigkeit']

# Zustand für ausgewählte Kriterien und Gewichtungen
if 'selected_criteria' not in st.session_state:
    st.session_state.selected_criteria = pd.DataFrame(columns=['Kriterium', 'Gewichtung'])

# Auswahl vordefinierter Kriterien oder Eingabe eines neuen Kriteriums
st.write("Wählen Sie ein vordefiniertes Kriterium oder geben Sie ein eigenes Kriterium ein:")
option = st.radio("Auswahl", ("Vordefiniertes Kriterium", "Eigenes Kriterium"))
selected_criterion = None

if option == "Vordefiniertes Kriterium":
    selected_default_criterion = st.selectbox("Vordefiniertes Kriterium auswählen", default_criteria)
    if selected_default_criterion:
        selected_criterion = selected_default_criterion
elif option == "Eigenes Kriterium":
    selected_criterion = st.text_input("Eigenes Kriterium hinzufügen")

# Button zum Hinzufügen des ausgewählten oder eingegebenen Kriteriums
if st.button("Kriterium hinzufügen") and selected_criterion:
    if selected_criterion not in st.session_state.selected_criteria['Kriterium'].values:
        new_row = pd.DataFrame({'Kriterium': [selected_criterion], 'Gewichtung': [1]})
        st.session_state.selected_criteria = pd.concat([st.session_state.selected_criteria, new_row], ignore_index=True)

# Anzeige der ausgewählten Kriterien und Gewichtungen mit Checkboxen
st.write("Ausgewählte Kriterien:")
selected_criteria_indices = []
for index, row in st.session_state.selected_criteria.iterrows():
    selected = st.checkbox("", key=f"checkbox_{index}")
    if selected:
        selected_criteria_indices.append(index)
    weight = st.slider(f"{row['Kriterium']} Gewichtung", min_value=0, max_value=10, value=5, key=f"slider_{index}")
    
    # # Hier wird eine Debounce-Funktion angewendet
    # def debounce(func, wait=1):
    #     def debounced(*args, **kwargs):
    #         def call_it():
    #             time.sleep(wait)
    #             func(*args, **kwargs)
    #         Thread(target=call_it).start()
    #     return debounced
    
    # # Funktion zur Aktualisierung der Gewichtung mit Verzögerung
    # @debounce
    def update_weight(new_weight, index):
        st.session_state.selected_criteria = adjust_weights(st.session_state.selected_criteria, index, new_weight)
    
    update_weight(weight, index)

# Button zum Entfernen der ausgewählten Kriterien
if len(selected_criteria_indices) > 0:
    if st.button("Ausgewählte Kriterien löschen"):
        st.session_state.selected_criteria = st.session_state.selected_criteria.drop(selected_criteria_indices).reset_index(drop=True)
        st.experimental_rerun()


st.markdown("---")

# Varianten
st.header("Varianten und deren Bewertungen")
st.write("Geben Sie die Bewertungen für die verschiedenen Alternativen ein.")

# Anzahl der Varianten
num_variants = st.number_input("Anzahl der Varianten (bis zu 5)", min_value=1, max_value=5, value=2, step=1)

# Namen der Varianten
variant_names = []
for i in range(num_variants):
    variant_names.append(st.text_input(f"Name der Variante {i+1}", value=f"Variante {i+1}"))

# Bewertung der Varianten
variant_ratings = {}
for name in variant_names:
    st.subheader(f"Bewertungen für {name}")
    ratings = {}
    for criterion in st.session_state.selected_criteria['Kriterium']:
        ratings[criterion] = st.slider(f"{criterion} Bewertung für {name}", min_value=0, max_value=10, value=5, key=f"{name}_{criterion}")
    variant_ratings[name] = ratings

st.markdown("---")


# Berechnung des Gesamtnutzens
if st.button("Nutzwertanalyse durchführen"):
    # Normalisieren der Gewichtungen nur zur Berechnung
    normalized_weights = normalize_weights(st.session_state.selected_criteria['Gewichtung'].tolist())

    # Berechnung der gewichteten Bewertungen und Nutzwerte
    results = []
    for name, ratings in variant_ratings.items():
        total_score = sum(ratings[criterion] * weight / 100 for criterion, weight in zip(st.session_state.selected_criteria['Kriterium'], normalized_weights))
        results.append((name, {criterion: ratings[criterion] * weight / 100 for criterion, weight in zip(st.session_state.selected_criteria['Kriterium'], normalized_weights)}, total_score))

    # Sortierung der Ergebnisse nach Nutzwert
    results.sort(key=lambda x: x[2], reverse=True)

    # Erstellen der Ergebnis-Tabelle
    st.write("Ergebnis der Nutzwertanalyse:")
    variant_names = [result[0] for result in results]
    criteria = st.session_state.selected_criteria['Kriterium'].tolist()
    weights = st.session_state.selected_criteria['Gewichtung'].tolist()
    df_results = pd.DataFrame(index=variant_names, columns=[f"{criterion} (gewichtet)" for criterion in criteria] + ['Nutzwert'])

    for result in results:
        variant_name = result[0]
        weighted_scores = result[1]
        total_utility = result[2]
        for criterion in criteria:
            df_results.at[variant_name, f"{criterion} (gewichtet)"] = weighted_scores[criterion]
        df_results.at[variant_name, 'Nutzwert'] = total_utility

    st.write(df_results)


