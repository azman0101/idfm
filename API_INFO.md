# Usage de l'API PRIM

Cette intégration utilise la librairie `idfm-api` pour communiquer avec les services d'Île-de-France Mobilités.

## Endpoints Authentifiés (PRIM)

Ces appels nécessitent une clé d'API (token) configurée dans l'intégration.

### 1. Temps Réel (Stop Monitoring)
Récupère les prochains passages pour un arrêt donné.
- **URL**: `https://prim.iledefrance-mobilites.fr/marketplace/stop-monitoring`
- **Méthode**: `GET`
- **Paramètres**:
  - `MonitoringRef`: ID de l'arrêt (ex: `STIF:StopPoint:Q:41178:`)
  - `LineRef`: (Optionnel) ID de la ligne pour filtrer.

### 2. Info Trafic (Navitia)
Récupère les perturbations et alertes trafic pour une ligne.
- **URL**: `https://prim.iledefrance-mobilites.fr/marketplace/v2/navitia/lines/line:IDFM:{line_id}/line_reports`
- **Méthode**: `GET`

## Données Open Data (Non Authentifié)

L'intégration (via la librairie) télécharge également des référentiels statiques depuis `data.iledefrance-mobilites.fr`. Ces appels n'utilisent pas la clé API PRIM.

- Référentiel des lignes
- Référentiel des arrêts
- Relations arrêts/lignes
