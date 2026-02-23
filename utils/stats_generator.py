import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from settings import GRAPH_FOLDER
import os

def generate_stats_graph(stats):
    """
    Génère un graphique de statistiques de l'exécution du bot.
    'stats' doit être un dictionnaire de ce format :
    {
        "HelloWork": {"scannées": 45, "pertinentes": 2},
        "LBA": {"scannées": 17, "pertinentes": 5},
        "LinkedIn": {"scannées": 120, "pertinentes": 0},
        "WTTJ": {"scannées": 60, "pertinentes": 3},
        "APEC": {"scannées": 33, "pertinentes": 9}
    }
    """
    plateformes = list(stats.keys())
    scannees = [stats[p]["scannées"] for p in plateformes]
    pertinentes = [stats[p]["pertinentes"] for p in plateformes]

    # --- Configuration globale de la figure ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle(f'Rapport de Chasse d\'Alternance - {datetime.now().strftime("%d/%m/%Y %H:%M")}', fontsize=16, fontweight='bold')

    # --- 1er Graphique : Barres par plateforme ---
    x = np.arange(len(plateformes))
    width = 0.35

    rects1 = ax1.bar(x - width/2, scannees, width, label='Offres scannées', color='#B0BEC5')
    rects2 = ax1.bar(x + width/2, pertinentes, width, label='Offres pertinentes (Deep Scan +)', color='#4CAF50')

    ax1.set_ylabel('Nombre d\'offres')
    ax1.set_title('Performances par Plateforme')
    ax1.set_xticks(x)
    ax1.set_xticklabels(plateformes)
    ax1.legend()

    # Ajouter les nombres au-dessus des barres
    ax1.bar_label(rects1, padding=3)
    ax1.bar_label(rects2, padding=3)

    # --- 2ème Graphique : Statistiques Globales ---
    total_scannees = sum(scannees)
    total_pertinentes = sum(pertinentes)
    total_rejetees = total_scannees - total_pertinentes

    labels = ['Rejetées (Hors-cible/Doublon)', 'Pertinentes (Match)']
    sizes = [total_rejetees, total_pertinentes]
    colors = ["#DA2335", '#66BB6A']
    explode = (0, 0.1)  # Faire ressortir la part des offres pertinentes

    # On ne dessine le camembert que s'il y a des offres scannées
    if total_scannees > 0:
        ax2.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
                shadow=True, startangle=90)
        ax2.axis('equal')  # Pour que le camembert soit bien rond
    
    ax2.set_title(f'Bilan Global : {total_scannees} offres analysées')

    # --- Sauvegarde de l'image ---
    plt.tight_layout()
    filename = f'rapport_stats_{datetime.now().strftime("%Y%m%d_%H%M")}.png'
    filename = os.path.join(GRAPH_FOLDER, filename)
    if not os.path.exists(GRAPH_FOLDER):
        os.makedirs(GRAPH_FOLDER)
    plt.savefig(filename)
    print(f"📊 Graphique généré avec succès : {filename}")
    
    return filename