"""
🍮 FLAN Protocol Server v1.0
Flan Layered Access Network - Une implémentation pédagogique

Ce serveur simule le protocole FLAN pour enseigner les concepts réseau
à travers la métaphore de la pâtisserie.
"""

from flask import Flask, jsonify, request, render_template, Response
from flask_cors import CORS
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
from enum import Enum
import time
import random
import json
import hashlib
import threading
from datetime import datetime
from queue import Queue

app = Flask(__name__)
CORS(app)

# ═══════════════════════════════════════════════════════════════════════════════
# 📋 DÉFINITIONS DU PROTOCOLE FLAN
# ═══════════════════════════════════════════════════════════════════════════════

class FlanStatus(Enum):
    """Codes de statut FLAN (équivalent HTTP)"""
    # Succès (2xx)
    FLAN_PARFAIT = (200, "Flan Parfait", "Succès total, texture idéale")
    FLAN_CREE = (201, "Flan Créé", "Ressource créée avec succès")
    MOULE_VIDE = (204, "Moule Vide", "Succès mais pas de contenu")
    
    # Redirections (3xx)
    DEMENAGEMENT = (301, "Déménagement", "Redirection permanente")
    FOUR_OCCUPE = (302, "Four Occupé", "Redirection temporaire")
    
    # Erreurs client (4xx)
    MAUVAISE_RECETTE = (400, "Mauvaise Recette", "Requête mal formée")
    CUISINE_INTERDITE = (401, "Cuisine Interdite", "Authentification requise")
    RECETTE_SECRETE = (403, "Recette Secrète", "Accès refusé")
    FLAN_INTROUVABLE = (404, "Flan Introuvable", "Ressource non trouvée")
    CUISSON_TIMEOUT = (408, "Cuisson Timeout", "Délai dépassé")
    FLAN_TROP_GROS = (413, "Flan Trop Gros", "Payload trop volumineux")
    JE_SUIS_THEIERE = (418, "Je Suis Théière", "Easter egg RFC 2324")
    TROP_DE_COMMANDES = (429, "Trop de Commandes", "Rate limiting")
    
    # Erreurs serveur (5xx)
    FOUR_EN_PANNE = (500, "Four en Panne", "Erreur serveur interne")
    MAUVAIS_FOUR = (502, "Mauvais Four", "Bad gateway")
    CUISINE_FERMEE = (503, "Cuisine Fermée", "Service indisponible")
    FOUR_TIMEOUT = (504, "Four Timeout", "Gateway timeout")

    def __init__(self, code: int, nom: str, description: str):
        self._code = code
        self._nom = nom
        self._description = description
    
    @property
    def code(self) -> int:
        return self._code
    
    @property
    def nom(self) -> str:
        return self._nom
    
    @property
    def description(self) -> str:
        return self._description


class TypeMoule(Enum):
    """Types de moules (formats d'encapsulation)"""
    INDIVIDUEL = 0x01
    FAMILIAL = 0x02
    GEANT = 0x03
    MINI = 0x04


class TypeGarniture(Enum):
    """Types de garniture (options de métadonnées)"""
    CARAMEL = 0x01      # Priorité
    CHANTILLY = 0x02    # Compression
    FRUITS = 0x03       # Données supplémentaires
    COULIS = 0x04       # Certificat de sécurité
    FIN_DEC = 0xFF      # Fin de garniture


@dataclass
class EnteteFlan:
    """En-tête du paquet FLAN (Le Moule)"""
    version: str = "1.0"
    type_requete: str = "REQUETE"
    taille_ml: int = 0
    moule: str = "INDIVIDUEL"
    recette_id: str = "0x00"
    portion: str = "1/1"
    temperature: int = 180
    ttl_minutes: int = 30
    source_four: str = "127.0.0.1"
    dest_assiette: str = "127.0.0.1"
    checksum: str = ""
    
    def calculer_checksum(self, corps: str) -> str:
        """Calcule le checksum de texture"""
        data = f"{self.version}{self.type_requete}{corps}"
        return hashlib.md5(data.encode()).hexdigest()[:8].upper()


@dataclass
class CorpsFlan:
    """Corps du paquet FLAN (L'Appareil)"""
    action: str = ""
    recette: str = ""
    ingredients: Dict[str, Any] = None
    cuisson: Dict[str, Any] = None
    donnees: Any = None
    
    def __post_init__(self):
        if self.ingredients is None:
            self.ingredients = {}
        if self.cuisson is None:
            self.cuisson = {}


@dataclass
class GarnitureFlan:
    """Garniture du paquet FLAN (Le Caramel)"""
    priorite: str = "NORMAL"
    compression: bool = False
    donnees_supplementaires: Dict[str, Any] = None
    certificat: Optional[str] = None
    
    def __post_init__(self):
        if self.donnees_supplementaires is None:
            self.donnees_supplementaires = {}


@dataclass
class PaquetFlan:
    """Paquet FLAN complet (PDU - Pastry Data Unit)"""
    entete: EnteteFlan
    corps: CorpsFlan
    garniture: GarnitureFlan
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        # Calculer la taille et le checksum
        corps_json = json.dumps(asdict(self.corps))
        self.entete.taille_ml = len(corps_json)
        self.entete.checksum = self.entete.calculer_checksum(corps_json)
    
    def to_dict(self) -> Dict:
        return {
            "entete": asdict(self.entete),
            "corps": asdict(self.corps),
            "garniture": asdict(self.garniture),
            "timestamp": self.timestamp,
            "timestamp_lisible": datetime.fromtimestamp(self.timestamp).isoformat()
        }


# ═══════════════════════════════════════════════════════════════════════════════
# 🍳 CUISINE FLAN (État du serveur)
# ═══════════════════════════════════════════════════════════════════════════════

class CuisineFlan:
    """Gestionnaire de la cuisine FLAN (État du serveur)"""
    
    def __init__(self):
        self.fours: Dict[str, Dict] = {}
        self.commandes: Dict[str, Dict] = {}
        self.historique: List[Dict] = []
        self.events_queue = Queue()
        self.compteur_commandes = 0
        
        # Recettes disponibles
        self.recettes = {
            "flan_vanille": {
                "nom": "Flan à la Vanille",
                "ingredients": {"oeufs": 4, "lait": "500mL", "sucre": "100g", "vanille": "1 gousse"},
                "cuisson": {"mode": "bain-marie", "temperature": 150, "duree": "40min"},
                "emoji": "🍮"
            },
            "flan_orange": {
                "nom": "Flan à l'Orange",
                "ingredients": {"oeufs": 4, "lait": "500mL", "sucre": "100g", "oranges": 2, "vanille": "1 gousse"},
                "cuisson": {"mode": "bain-marie", "temperature": 150, "duree": "45min"},
                "emoji": "🍊"
            },
            "flan_chocolat": {
                "nom": "Flan au Chocolat",
                "ingredients": {"oeufs": 4, "lait": "500mL", "sucre": "80g", "chocolat": "150g"},
                "cuisson": {"mode": "bain-marie", "temperature": 160, "duree": "50min"},
                "emoji": "🍫"
            },
            "flan_caramel": {
                "nom": "Flan au Caramel",
                "ingredients": {"oeufs": 6, "lait": "750mL", "sucre": "150g", "caramel": "100g"},
                "cuisson": {"mode": "bain-marie", "temperature": 150, "duree": "55min"},
                "emoji": "🥧"
            }
        }
        
        # Initialiser quelques fours
        for i in range(1, 4):
            self.fours[f"four_{i}"] = {
                "id": f"four_{i}",
                "statut": "disponible",
                "temperature": 0,
                "commande_en_cours": None
            }
    
    def nouvelle_commande_id(self) -> str:
        self.compteur_commandes += 1
        return f"CMD-{self.compteur_commandes:04d}"
    
    def trouver_four_disponible(self) -> Optional[str]:
        for four_id, four in self.fours.items():
            if four["statut"] == "disponible":
                return four_id
        return None
    
    def ajouter_event(self, event_type: str, data: Dict):
        event = {
            "type": event_type,
            "data": data,
            "timestamp": time.time()
        }
        self.events_queue.put(event)
        self.historique.append(event)
        # Garder seulement les 100 derniers événements
        if len(self.historique) > 100:
            self.historique = self.historique[-100:]


cuisine = CuisineFlan()


# ═══════════════════════════════════════════════════════════════════════════════
# 🔌 API FLAN (Endpoints)
# ═══════════════════════════════════════════════════════════════════════════════

def creer_reponse_flan(status: FlanStatus, data: Any = None, message: str = None) -> Dict:
    """Crée une réponse formatée selon le protocole FLAN"""
    reponse = {
        "protocole": "FLAN/1.0",
        "statut": {
            "code": status.code,
            "nom": status.nom,
            "description": status.description
        },
        "timestamp": time.time(),
        "timestamp_lisible": datetime.now().isoformat()
    }
    if data is not None:
        reponse["donnees"] = data
    if message:
        reponse["message"] = message
    return reponse


@app.route('/')
def index():
    """Page principale avec l'interface FLAN"""
    return render_template('index.html')


@app.route('/api/flan/prechauffage', methods=['POST'])
def prechauffage():
    """
    Phase 1: PRÉCHAUFFAGE (SYN)
    Équivalent: Établissement de connexion TCP
    """
    data = request.get_json() or {}
    temperature = data.get('temperature', 180)
    moule = data.get('moule', 'INDIVIDUEL')
    
    four_id = cuisine.trouver_four_disponible()
    
    if not four_id:
        cuisine.ajouter_event("erreur", {
            "phase": "prechauffage",
            "erreur": "Tous les fours sont occupés"
        })
        return jsonify(creer_reponse_flan(
            FlanStatus.FOUR_OCCUPE,
            message="🔥 Tous les fours sont occupés, veuillez patienter"
        )), 302
    
    # Réserver le four
    cuisine.fours[four_id]["statut"] = "prechauffage"
    cuisine.fours[four_id]["temperature"] = temperature
    
    # Créer le paquet SYN
    paquet = PaquetFlan(
        entete=EnteteFlan(
            type_requete="SYN",
            temperature=temperature,
            moule=moule,
            source_four=request.remote_addr or "127.0.0.1"
        ),
        corps=CorpsFlan(action="PRECHAUFFAGE"),
        garniture=GarnitureFlan()
    )
    
    cuisine.ajouter_event("prechauffage", {
        "four_id": four_id,
        "temperature": temperature,
        "paquet": paquet.to_dict()
    })
    
    # Simuler le temps de préchauffage
    time.sleep(0.3)
    
    cuisine.fours[four_id]["statut"] = "pret"
    
    return jsonify(creer_reponse_flan(
        FlanStatus.FLAN_PARFAIT,
        data={
            "four_id": four_id,
            "temperature": temperature,
            "statut": "FOUR_PRET",
            "message": f"🔥 Four {four_id} préchauffé à {temperature}°C",
            "paquet_syn_ack": {
                "type": "SYN-ACK",
                "four_id": four_id,
                "capacite": "disponible"
            }
        }
    ))


@app.route('/api/flan/commander', methods=['POST'])
def commander():
    """
    Phase 2: COMMANDE
    Équivalent: Envoi de données (DATA)
    """
    data = request.get_json() or {}
    
    recette = data.get('recette', 'flan_vanille')
    portions = data.get('portions', 1)
    four_id = data.get('four_id')
    options = data.get('options', {})
    
    # Vérifier que la recette existe
    if recette not in cuisine.recettes:
        cuisine.ajouter_event("erreur", {
            "phase": "commande",
            "erreur": f"Recette inconnue: {recette}"
        })
        return jsonify(creer_reponse_flan(
            FlanStatus.FLAN_INTROUVABLE,
            message=f"📖 Recette '{recette}' introuvable dans le livre de recettes"
        )), 404
    
    # Vérifier le four
    if not four_id or four_id not in cuisine.fours:
        four_id = cuisine.trouver_four_disponible()
        if not four_id:
            return jsonify(creer_reponse_flan(
                FlanStatus.CUISINE_FERMEE,
                message="👨‍🍳 Aucun four disponible"
            )), 503
    
    if cuisine.fours[four_id]["statut"] not in ["pret", "disponible"]:
        return jsonify(creer_reponse_flan(
            FlanStatus.FOUR_OCCUPE,
            message=f"🔥 Le four {four_id} n'est pas prêt"
        )), 302
    
    # Créer la commande
    commande_id = cuisine.nouvelle_commande_id()
    recette_details = cuisine.recettes[recette]
    
    commande = {
        "id": commande_id,
        "recette": recette,
        "details": recette_details,
        "portions": portions,
        "options": options,
        "four_id": four_id,
        "statut": "en_preparation",
        "progression": 0,
        "etapes": [],
        "debut": time.time()
    }
    
    cuisine.commandes[commande_id] = commande
    cuisine.fours[four_id]["statut"] = "cuisson"
    cuisine.fours[four_id]["commande_en_cours"] = commande_id
    
    # Créer le paquet de commande
    paquet = PaquetFlan(
        entete=EnteteFlan(
            type_requete="DATA",
            recette_id=commande_id,
            temperature=recette_details["cuisson"]["temperature"]
        ),
        corps=CorpsFlan(
            action="PREPARER",
            recette=recette,
            ingredients=recette_details["ingredients"],
            cuisson=recette_details["cuisson"]
        ),
        garniture=GarnitureFlan(
            priorite=options.get("priorite", "NORMAL"),
            donnees_supplementaires=options
        )
    )
    
    cuisine.ajouter_event("commande", {
        "commande_id": commande_id,
        "recette": recette,
        "paquet": paquet.to_dict()
    })
    
    # Lancer la cuisson en arrière-plan
    thread = threading.Thread(target=simuler_cuisson, args=(commande_id,))
    thread.daemon = True
    thread.start()
    
    return jsonify(creer_reponse_flan(
        FlanStatus.FLAN_CREE,
        data={
            "commande_id": commande_id,
            "recette": recette_details["nom"],
            "emoji": recette_details["emoji"],
            "four_id": four_id,
            "statut": "PREPARATION_EN_COURS",
            "message": f"👨‍🍳 Commande {commande_id} en préparation"
        }
    )), 201


def simuler_cuisson(commande_id: str):
    """Simule les étapes de cuisson d'un flan"""
    if commande_id not in cuisine.commandes:
        return
    
    commande = cuisine.commandes[commande_id]
    etapes = [
        ("rassemblement_ingredients", "📦 Rassemblement des ingrédients", 10, 0.5),
        ("caramelisation", "🍯 Caramélisation du moule", 25, 0.8),
        ("melange_appareil", "🥣 Mélange de l'appareil", 50, 0.6),
        ("versement", "🫗 Versement dans le moule", 60, 0.3),
        ("cuisson", "🔥 Cuisson au bain-marie", 85, 1.5),
        ("refroidissement", "❄️ Refroidissement", 95, 0.7),
        ("demoulage", "🍽️ Démoulage", 100, 0.4)
    ]
    
    for etape_id, description, progression, duree in etapes:
        if commande_id not in cuisine.commandes:
            return
        
        commande["statut"] = etape_id
        commande["progression"] = progression
        commande["etapes"].append({
            "id": etape_id,
            "description": description,
            "timestamp": time.time()
        })
        
        cuisine.ajouter_event("progression", {
            "commande_id": commande_id,
            "etape": etape_id,
            "description": description,
            "progression": progression
        })
        
        time.sleep(duree)
    
    # Cuisson terminée
    commande["statut"] = "termine"
    commande["progression"] = 100
    commande["fin"] = time.time()
    
    # Libérer le four
    four_id = commande["four_id"]
    if four_id in cuisine.fours:
        cuisine.fours[four_id]["statut"] = "disponible"
        cuisine.fours[four_id]["commande_en_cours"] = None
    
    cuisine.ajouter_event("termine", {
        "commande_id": commande_id,
        "duree_totale": commande["fin"] - commande["debut"],
        "recette": commande["recette"]
    })


@app.route('/api/flan/commande/<commande_id>', methods=['GET'])
def statut_commande(commande_id: str):
    """
    Vérifie le statut d'une commande
    Équivalent: Polling / Status check
    """
    if commande_id not in cuisine.commandes:
        return jsonify(creer_reponse_flan(
            FlanStatus.FLAN_INTROUVABLE,
            message=f"🔍 Commande {commande_id} introuvable"
        )), 404
    
    commande = cuisine.commandes[commande_id]
    recette_details = cuisine.recettes.get(commande["recette"], {})
    
    if commande["statut"] == "termine":
        return jsonify(creer_reponse_flan(
            FlanStatus.FLAN_PARFAIT,
            data={
                "commande_id": commande_id,
                "statut": "FLAN_PRET",
                "emoji": recette_details.get("emoji", "🍮"),
                "flan": {
                    "recette": commande["recette"],
                    "texture": "onctueuse",
                    "caramel": "brillant",
                    "portions": commande["portions"]
                },
                "metadonnees": {
                    "chef": "Claude",
                    "temps_total": f"{commande['fin'] - commande['debut']:.1f}s",
                    "etapes_completees": len(commande["etapes"])
                }
            },
            message="🍮 Votre flan est prêt ! Bonne dégustation !"
        ))
    
    derniere_etape = commande["etapes"][-1] if commande["etapes"] else None
    
    return jsonify(creer_reponse_flan(
        FlanStatus.FLAN_PARFAIT,
        data={
            "commande_id": commande_id,
            "statut": "EN_COURS",
            "progression": commande["progression"],
            "etape_actuelle": derniere_etape,
            "emoji": recette_details.get("emoji", "🍮")
        },
        message=f"⏳ Cuisson en cours... {commande['progression']}%"
    ))


@app.route('/api/flan/recettes', methods=['GET'])
def liste_recettes():
    """Liste toutes les recettes disponibles"""
    return jsonify(creer_reponse_flan(
        FlanStatus.FLAN_PARFAIT,
        data={
            "recettes": cuisine.recettes,
            "total": len(cuisine.recettes)
        }
    ))


@app.route('/api/flan/fours', methods=['GET'])
def liste_fours():
    """Liste l'état de tous les fours"""
    return jsonify(creer_reponse_flan(
        FlanStatus.FLAN_PARFAIT,
        data={
            "fours": cuisine.fours,
            "disponibles": sum(1 for f in cuisine.fours.values() if f["statut"] == "disponible"),
            "total": len(cuisine.fours)
        }
    ))


@app.route('/api/flan/historique', methods=['GET'])
def historique():
    """Retourne l'historique des événements"""
    limit = request.args.get('limit', 50, type=int)
    return jsonify(creer_reponse_flan(
        FlanStatus.FLAN_PARFAIT,
        data={
            "evenements": cuisine.historique[-limit:],
            "total": len(cuisine.historique)
        }
    ))


@app.route('/api/flan/events')
def events_stream():
    """
    Stream SSE des événements en temps réel
    Équivalent: WebSocket / Server-Sent Events
    """
    def generate():
        while True:
            try:
                event = cuisine.events_queue.get(timeout=30)
                yield f"data: {json.dumps(event)}\n\n"
            except:
                # Heartbeat pour garder la connexion
                yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': time.time()})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')


@app.route('/api/flan/ping', methods=['GET'])
def ping():
    """
    FLAN-PING: Vérifie la connectivité
    Équivalent: ICMP ping
    """
    debut = time.time()
    # Simuler un petit délai réseau
    time.sleep(random.uniform(0.01, 0.05))
    latence = (time.time() - debut) * 1000
    
    return jsonify(creer_reponse_flan(
        FlanStatus.FLAN_PARFAIT,
        data={
            "pong": True,
            "latence_ms": round(latence, 2),
            "texture": "onctueuse",
            "message": f"🍮 Pong! Latence: {latence:.2f}ms"
        }
    ))


@app.route('/api/flan/theiere', methods=['GET'])
def theiere():
    """Easter egg RFC 2324"""
    return jsonify(creer_reponse_flan(
        FlanStatus.JE_SUIS_THEIERE,
        message="🫖 Je suis une théière, pas un four à flan !"
    )), 418


# ═══════════════════════════════════════════════════════════════════════════════
# 📚 DOCUMENTATION API
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/flan/documentation', methods=['GET'])
def documentation():
    """Retourne la documentation de l'API FLAN"""
    return jsonify(creer_reponse_flan(
        FlanStatus.FLAN_PARFAIT,
        data={
            "protocole": "FLAN/1.0",
            "nom_complet": "Flan Layered Access Network",
            "rfc": "RFC 3141 (Request For Caramel)",
            "endpoints": [
                {
                    "methode": "POST",
                    "chemin": "/api/flan/prechauffage",
                    "description": "Phase 1: Établir la connexion (SYN)",
                    "equivalent_reseau": "TCP Handshake - SYN"
                },
                {
                    "methode": "POST",
                    "chemin": "/api/flan/commander",
                    "description": "Phase 2: Envoyer une commande de flan",
                    "equivalent_reseau": "Envoi de données - DATA"
                },
                {
                    "methode": "GET",
                    "chemin": "/api/flan/commande/<id>",
                    "description": "Vérifier le statut d'une commande",
                    "equivalent_reseau": "Status polling"
                },
                {
                    "methode": "GET",
                    "chemin": "/api/flan/recettes",
                    "description": "Liste des recettes disponibles",
                    "equivalent_reseau": "Service discovery"
                },
                {
                    "methode": "GET",
                    "chemin": "/api/flan/fours",
                    "description": "État des fours (serveurs)",
                    "equivalent_reseau": "Health check"
                },
                {
                    "methode": "GET",
                    "chemin": "/api/flan/events",
                    "description": "Stream d'événements en temps réel",
                    "equivalent_reseau": "SSE / WebSocket"
                },
                {
                    "methode": "GET",
                    "chemin": "/api/flan/ping",
                    "description": "Test de connectivité",
                    "equivalent_reseau": "ICMP Ping"
                }
            ],
            "codes_statut": [
                {"code": s.code, "nom": s.nom, "description": s.description}
                for s in FlanStatus
            ]
        }
    ))


if __name__ == '__main__':
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║     🍮 FLAN Protocol Server v1.0                              ║
    ║     Flan Layered Access Network                               ║
    ║                                                               ║
    ║     RFC 3141 (Request For Caramel)                            ║
    ║                                                               ║
    ╠═══════════════════════════════════════════════════════════════╣
    ║                                                               ║
    ║     Interface:    http://localhost:5000                       ║
    ║     API Docs:     http://localhost:5000/api/flan/documentation║
    ║                                                               ║
    ║     🔥 Fours disponibles: 3                                   ║
    ║     📖 Recettes chargées: 4                                   ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
