import json

def calculate_match_score(job_description, my_profile):
    score = 0
    keywords = []
    
    # Extraction de toutes les compétences du JSON
    all_skills = [skill.lower() for category in my_profile['competences'].values() for skill in category]
    
    # On ajoute les titres de poste recherchés
    target_titles = ["soc", "cyber", "réseau", "système", "infrastructure", "administrateur"]
    
    desc_lower = job_description.lower()
    
    # 1. Check des compétences techniques
    for skill in all_skills:
        if skill in desc_lower:
            score += 10
            keywords.append(skill)
            
    # 2. Check des mots-clés stratégiques
    for title in target_titles:
        if title in desc_lower:
            score += 15
            
    return score, keywords

# Test rapide
job_desc = "Recherche alternant pour monitoring SOC, connaissance de Wazuh et Linux requise."
with open('data/profile.json', 'r', encoding='utf-8') as f:
    profile = json.load(f)

score, found = calculate_match_score(job_desc, profile)
print(f"Match Score: {score} | Points communs : {found}")