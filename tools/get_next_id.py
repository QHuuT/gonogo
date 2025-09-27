#!/usr/bin/env python3
"""
Script fiable pour obtenir le prochain ID disponible.
Usage: python tools/get_next_id.py [epic|us|defect]
"""

import requests
import sys


def get_next_epic_id() -> str:
    """Récupère le prochain ID Epic disponible via l'API."""
    try:
        response = requests.get("http://localhost:8000/api/rtm/epics/", timeout=5)
        response.raise_for_status()
        epics = response.json()

        # Extraire tous les numéros d'Epic
        epic_numbers = []
        for epic in epics:
            epic_id = epic.get("epic_id", "")
            if epic_id.startswith("EP-"):
                try:
                    # Extraire le numéro (EP-00007 -> 7)
                    num = int(epic_id.replace("EP-", "").lstrip("0") or "0")
                    epic_numbers.append(num)
                except ValueError:
                    continue

        # Prochain numéro disponible
        if epic_numbers:
            next_num = max(epic_numbers) + 1
        else:
            next_num = 1

        return f"EP-{next_num:05d}"

    except Exception as e:
        print(f"Erreur API, utilisation de EP-00008 par défaut: {e}", file=sys.stderr)
        return "EP-00008"


def get_next_us_id() -> str:
    """Récupère le prochain ID User Story disponible via l'API."""
    try:
        response = requests.get(
            "http://localhost:8000/api/rtm/user-stories/", timeout=5
        )
        response.raise_for_status()
        user_stories = response.json()

        # Extraire tous les numéros de User Story (depuis title si us_id est None)
        us_numbers = []
        for us in user_stories:
            us_id = us.get("us_id", "")
            title = us.get("title", "")

            # Vérifier d'abord us_id, puis title
            source_id = us_id if us_id else title

            if source_id and "US-" in source_id:
                try:
                    # Extraire le numéro (US-00047 -> 47)
                    start_idx = source_id.find("US-")
                    if start_idx >= 0:
                        id_part = source_id[start_idx : start_idx + 8]  # US-00047
                        if ":" in id_part:
                            id_part = id_part.split(":")[
                                0
                            ]  # Enlever le titre après ':'
                        num = int(id_part.replace("US-", "").lstrip("0") or "0")
                        us_numbers.append(num)
                except ValueError:
                    continue

        # Prochain numéro disponible
        if us_numbers:
            next_num = max(us_numbers) + 1
        else:
            next_num = 1

        return f"US-{next_num:05d}"

    except Exception as e:
        print(f"Erreur API, utilisation de US-00047 par défaut: {e}", file=sys.stderr)
        return "US-00047"


def get_next_defect_id() -> str:
    """Récupère le prochain ID Defect disponible via l'API."""
    try:
        response = requests.get("http://localhost:8000/api/rtm/defects/", timeout=5)
        response.raise_for_status()
        defects = response.json()

        # Extraire tous les numéros de Defect
        defect_numbers = []
        for defect in defects:
            defect_id = defect.get("defect_id", "")
            if defect_id and defect_id.startswith("DEF-"):
                try:
                    # Extraire le numéro (DEF-00001 -> 1)
                    num = int(defect_id.replace("DEF-", "").lstrip("0") or "0")
                    defect_numbers.append(num)
                except ValueError:
                    continue

        # Prochain numéro disponible
        if defect_numbers:
            next_num = max(defect_numbers) + 1
        else:
            next_num = 1

        return f"DEF-{next_num:05d}"

    except Exception as e:
        print(f"Erreur API, utilisation de DEF-00001 par défaut: {e}", file=sys.stderr)
        return "DEF-00001"


def main():
    """Point d'entrée principal."""
    if len(sys.argv) != 2:
        print("Usage: python tools/get_next_id.py [epic|us|defect]")
        sys.exit(1)

    entity_type = sys.argv[1].lower()

    if entity_type == "epic":
        print(get_next_epic_id())
    elif entity_type == "us":
        print(get_next_us_id())
    elif entity_type == "defect":
        print(get_next_defect_id())
    else:
        print("Type invalide. Utilisez: epic, us, ou defect")
        sys.exit(1)


if __name__ == "__main__":
    main()
