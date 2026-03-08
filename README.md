# 🤖 Moteur de Recherche d'Alternance Automatisé

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Selenium](https://img.shields.io/badge/Selenium-Automated_Browser-green.svg)
![Linux](https://img.shields.io/badge/Linux-Supported-yellow.svg)
![Discord](https://img.shields.io/badge/Discord-Webhooks-5865F2.svg)

Un robot de web scraping et d'alerte automatisé conçu pour optimiser et centraliser la recherche d'alternance en Infrastructure IT et Cybersécurité. Ce projet interroge 5 plateformes majeures, filtre les offres selon un profil de compétences précis, élimine les spams, et envoie des alertes en temps réel sur Discord.

## ✨ Fonctionnalités Principales

* **Scraping Multi-Plateformes** : Extraction de données sur *APEC, LinkedIn, HelloWork, Welcome to the Jungle* (via Selenium) et *La Bonne Alternance* (via API gouvernementale).
* **Scoring Intelligent** : Analyse sémantique (Deep Scan) du texte de l'offre pour détecter les compétences cibles (ex: *Wazuh, Active Directory, Linux, Python*) et attribuer un score de pertinence.
* **Mémoire Anti-Spam** : Enregistrement des offres déjà vues et détection des entreprises qui "spamment" la même offre en boucle (`seen_jobs.txt` et `seen_titles.json`).
* **Extracteur de Durée** : Analyse du texte via expressions régulières (Regex) pour déduire automatiquement la durée du contrat (12, 24, 36 mois).
* **Alertes Discord en Temps Réel** : Notification immédiate avec lien direct, entreprise, lieu, durée et mots-clés détectés.
* **Génération de Rapports Visuels** : Création automatique d'un tableau de bord statistique (Matplotlib) envoyé en fin d'exécution.
* **Exécution Autonome** : Prêt à être déployé en tâche de fond (Cron) pour une veille silencieuse 24h/24.

## 🛠️ Technologies Utilisées

* **Langage** : Python 3
* **Bibliothèques** : Selenium (navigation & contournement anti-bot), Requests (API REST), BeautifulSoup, Matplotlib (DataViz).
* **Déploiement** : Bash Scripting, Linux Cron.

---

##  Installation & Déploiement

Ce projet a été pensé pour être déployé facilement sur un environnement Linux (Ubuntu/Debian).

### 1. Cloner le dépôt
```bash
git clone [https://github.com/Patrice404/alternance_search_engine.git]
cd alternance_search_engine
```
### 2. Installation automatique (Script Bash)
```bash
chmod +x install.sh
./install.sh
```

### 3. Configuration

Avant de lancer le bot, vous devez configurer vos variables et votre profil :

#### 1. Discord Webhook : Ouvrez le fichier settings.py et insérez l'URL de votre Webhook Discord dans la variable DISCORD_WEBHOOK.

#### 2. Profil de Compétences : Remplissez le fichier data/profile.json avec vos propres mots-clés techniques pour calibrer l'algorithme de scoring.

#### 3. Mots-clés de recherche : Ajustez les variables de recherche (ex: HELLOWORK_QUERIES, LINKEDIN_QUERIES) dans settings.py.

### 4. Utilisation
```bash
python3 main.py
```















