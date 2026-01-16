# 🍮 FLAN Protocol — Web Application

## Flan Layered Access Network
### RFC 3141 (Request For Caramel)

Une application web pédagogique qui enseigne les concepts réseau à travers la métaphore de la préparation d'un flan.

---

## 🎯 Objectif

Cette application implémente le protocole FLAN, un protocole de communication fictif qui utilise la pâtisserie comme métaphore pour expliquer les concepts fondamentaux des réseaux :

| Concept Réseau | Métaphore FLAN |
|----------------|----------------|
| TCP Handshake | Préchauffage du four |
| Envoi de données | Commande d'un flan |
| Payload | Appareil à flan |
| Header | Moule |
| Métadonnées | Garniture / Caramel |
| Codes HTTP | Codes de cuisson |
| Latence | Temps de cuisson |
| Timeout | Surcuisson |
| Serveur | Four |
| Checksum | Vérification de texture |

---

## 🚀 Installation

### Prérequis
- Python 3.8+
- pip

### Installation des dépendances

```bash
cd flan-protocol
pip install -r requirements.txt
```

### Lancement du serveur

```bash
python app.py
```

Le serveur démarre sur `http://localhost:5000`

---

## 📡 API Endpoints

### Phase 1 : Préchauffage (Établissement de connexion)

```http
POST /api/flan/prechauffage
Content-Type: application/json

{
    "temperature": 180,
    "moule": "INDIVIDUEL"
}
```

**Équivalent réseau** : TCP SYN → SYN-ACK

### Phase 2 : Commander (Envoi de données)

```http
POST /api/flan/commander
Content-Type: application/json

{
    "recette": "flan_orange",
    "four_id": "four_1",
    "portions": 4,
    "options": {
        "priorite": "NORMAL"
    }
}
```

**Équivalent réseau** : DATA packet

### Vérifier le statut

```http
GET /api/flan/commande/{commande_id}
```

**Équivalent réseau** : Status polling / ACK

### Autres endpoints

| Endpoint | Méthode | Description | Équivalent |
|----------|---------|-------------|------------|
| `/api/flan/recettes` | GET | Liste des recettes | Service discovery |
| `/api/flan/fours` | GET | État des serveurs | Health check |
| `/api/flan/ping` | GET | Test de connectivité | ICMP Ping |
| `/api/flan/events` | GET | Stream SSE | WebSocket |
| `/api/flan/historique` | GET | Logs des événements | Logs système |
| `/api/flan/documentation` | GET | Documentation API | OpenAPI/Swagger |
| `/api/flan/theiere` | GET | Easter egg 418 | RFC 2324 😄 |

---

## 📦 Structure d'un paquet FLAN

```
┌─────────────────────────────────────────────────────────┐
│                    PAQUET FLAN (PDU)                    │
├─────────────────┬───────────────────┬───────────────────┤
│    EN-TÊTE      │      CORPS        │    GARNITURE      │
│    (MOULE)      │    (APPAREIL)     │    (CARAMEL)      │
├─────────────────┼───────────────────┼───────────────────┤
│ • Version       │ • Action          │ • Priorité        │
│ • Type requête  │ • Recette         │ • Compression     │
│ • Taille (mL)   │ • Ingrédients     │ • Certificat      │
│ • Température   │ • Cuisson         │ • Options         │
│ • TTL           │                   │                   │
│ • Source/Dest   │                   │                   │
│ • Checksum      │                   │                   │
└─────────────────┴───────────────────┴───────────────────┘
```

---

## 🔥 Codes de statut FLAN

### Succès (2xx)
- **200 FLAN_PARFAIT** : Succès total, texture idéale
- **201 FLAN_CRÉÉ** : Ressource créée avec succès
- **204 MOULE_VIDE** : Succès mais pas de contenu

### Redirections (3xx)
- **301 DÉMÉNAGEMENT** : Redirection permanente
- **302 FOUR_OCCUPÉ** : Redirection temporaire

### Erreurs Client (4xx)
- **400 MAUVAISE_RECETTE** : Requête mal formée
- **401 CUISINE_INTERDITE** : Authentification requise
- **403 RECETTE_SECRÈTE** : Accès refusé
- **404 FLAN_INTROUVABLE** : Ressource non trouvée
- **408 CUISSON_TIMEOUT** : Délai dépassé
- **418 JE_SUIS_THÉIÈRE** : Easter egg RFC 2324
- **429 TROP_DE_COMMANDES** : Rate limiting

### Erreurs Serveur (5xx)
- **500 FOUR_EN_PANNE** : Erreur interne
- **503 CUISINE_FERMÉE** : Service indisponible
- **504 FOUR_TIMEOUT** : Gateway timeout

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CLIENT (Navigateur)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Commander   │  │   Monitor   │  │  Statut     │         │
│  │   Panel     │  │   Screen    │  │  Fours      │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
└─────────┼────────────────┼────────────────┼─────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│                   API FLAN (Flask)                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ /prechauff. │  │ /commander  │  │   /fours    │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
└─────────┼────────────────┼────────────────┼─────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│                   CUISINE FLAN (État)                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Four 1    │  │   Four 2    │  │   Four 3    │         │
│  │  🔥 180°C   │  │  ✅ Dispo   │  │  🍮 Cuisson │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎓 Utilisation pédagogique

### Scénario 1 : Expliquer TCP/IP

1. **Préchauffage** = Three-way handshake
   - Client envoie SYN (demande de préchauffage)
   - Serveur répond SYN-ACK (four prêt)
   - Client confirme ACK (tablier mis)

2. **Commande** = Transmission de données
   - Les données sont encapsulées dans un paquet FLAN
   - Le header (moule) contient les métadonnées de routage
   - Le payload (appareil) contient les données utiles

3. **Cuisson** = Processing
   - Le serveur traite la requête
   - Des ACK intermédiaires (progression) sont envoyés
   - Timeout si la cuisson prend trop de temps

### Scénario 2 : Expliquer les codes HTTP

Montrez aux étudiants comment les erreurs de cuisson correspondent aux erreurs HTTP :

- Recette inconnue → 404 Not Found
- Four occupé → 503 Service Unavailable
- Cuisson trop longue → 408 Timeout

### Scénario 3 : Expliquer la sécurité

Le protocole FLANS (FLAN Secure) utilise :
- Certificats = Diplôme de pâtissier
- Chiffrement = Recette secrète
- Authentification = Badge de cuisine

---

## 🧪 Tests avec curl

```bash
# Ping
curl http://localhost:5000/api/flan/ping

# Liste des recettes
curl http://localhost:5000/api/flan/recettes

# Préchauffage
curl -X POST http://localhost:5000/api/flan/prechauffage \
  -H "Content-Type: application/json" \
  -d '{"temperature": 180}'

# Commander un flan
curl -X POST http://localhost:5000/api/flan/commander \
  -H "Content-Type: application/json" \
  -d '{"recette": "flan_orange", "four_id": "four_1"}'

# Easter egg
curl http://localhost:5000/api/flan/theiere
```

---

## 📁 Structure du projet

```
flan-protocol/
├── app.py              # Application Flask principale
├── requirements.txt    # Dépendances Python
├── README.md          # Ce fichier
└── templates/
    └── index.html     # Interface web
```

---

## 🍊 Crédits

Développé avec 💛 pour **La Pâtisserie de l'Orange**

*"Un bon flan, comme un bon paquet, doit être bien équilibré, cuit à point et se démouler sans accroc."*

---

## 📜 Licence

RFC 3141 — Request For Caramel
Open Source sous licence "Partage de Recettes" 🍮
