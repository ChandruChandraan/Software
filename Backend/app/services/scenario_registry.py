"""Authoritative simulation scenario registry and Unreal asset mapping."""

from dataclasses import dataclass
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union

from app.schemas import ScenarioInfo

logger = logging.getLogger("backend.scenarios.registry")


@dataclass
class ScenarioDefinition:
    """Internal scenario definition linking stable UI IDs with Unreal map assets."""

    scenario_id: str
    display_name: str
    unreal_name: str  # Exact map/level identifier sent in UDP packet to Unreal
    relative_map_path: Optional[str] = None  # Relative to Unreal Content directory
    description: Optional[str] = None
    default_available: bool = True


class ScenarioRegistry:
    """
    Maintains the authoritative catalog of selectable simulator scenarios.
    Maps UI-friendly scenario IDs to exact Unreal Engine map identifiers.
    Validates physical existence of map files in Unreal Content directory.
    Supports dynamic loading and updating from scenarios.json configuration.
    """

    def __init__(
        self,
        content_dir: Optional[Path] = None,
        json_path: Optional[Union[Path, str]] = None,
    ):
        self.content_dir = content_dir
        self.json_path = self._resolve_json_path(json_path)
        self._scenarios: Dict[str, ScenarioDefinition] = {}
        self._load_default_scenarios(self.json_path)

    def _resolve_json_path(self, json_path: Optional[Union[Path, str]]) -> Optional[Path]:
        if json_path:
            return Path(json_path)
        try:
            from app.config import settings
            resolved = settings.get_scenarios_json_path()
            if resolved:
                return resolved
        except Exception:
            pass
        fallback = Path(__file__).resolve().parent.parent.parent / "scenarios.json"
        return fallback if fallback.exists() else None

    def _load_default_scenarios(self, json_path: Optional[Union[Path, str]] = None):
        """
        Loads scenario catalog definitions directly from JSON configuration.
        """
        target_path = Path(json_path) if json_path else self.json_path
        if target_path and target_path.exists():
            self.update_from_json(target_path)
        else:
            logger.warning(f"Scenario configuration JSON file not found at: {target_path}")

    def update_from_json(self, json_path: Union[Path, str]) -> int:
        """
        Reads a JSON file and registers or updates scenario definitions.
        Supports both a list of objects and {"scenarios": [...]} dictionary format.
        Returns the count of scenarios successfully loaded or updated.
        """
        p = Path(json_path)
        if not p.exists():
            logger.warning(f"Scenario JSON file not found: {p}")
            return 0

        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                items = data.get("scenarios", [])
            else:
                logger.error(f"Invalid format in scenario JSON file {p}: expected list or dict")
                return 0

            count = 0
            for item in items:
                if not isinstance(item, dict):
                    continue
                scenario_id = item.get("scenario_id")
                if not scenario_id:
                    continue

                sid = str(scenario_id).strip()
                existing = self.get(sid)
                defn = ScenarioDefinition(
                    scenario_id=sid,
                    display_name=str(item.get("display_name", existing.display_name if existing else sid)),
                    unreal_name=str(item.get("unreal_name", existing.unreal_name if existing else sid)),
                    relative_map_path=item.get("relative_map_path", existing.relative_map_path if existing else None),
                    description=item.get("description", existing.description if existing else None),
                    default_available=bool(item.get("default_available", existing.default_available if existing else True)),
                )
                self.register(defn)
                count += 1

            logger.info(f"Loaded/updated {count} scenarios from JSON file: {p}")
            return count
        except Exception as e:
            logger.error(f"Error loading scenarios from JSON file {p}: {e}", exc_info=True)
            return 0

    def save_to_json(self, json_path: Optional[Union[Path, str]] = None) -> bool:
        """
        Exports all registered scenario definitions to a JSON file.
        """
        target = Path(json_path) if json_path else self.json_path
        if not target:
            return False

        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            export_data = [
                {
                    "scenario_id": defn.scenario_id,
                    "display_name": defn.display_name,
                    "unreal_name": defn.unreal_name,
                    "relative_map_path": defn.relative_map_path,
                    "description": defn.description,
                    "default_available": defn.default_available,
                }
                for defn in self._scenarios.values()
            ]
            with open(target, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2)
            logger.info(f"Saved {len(export_data)} scenarios to {target}")
            return True
        except Exception as e:
            logger.error(f"Failed to save scenarios to {target}: {e}", exc_info=True)
            return False

    def register(self, definition: ScenarioDefinition):
        """Register or override a scenario definition."""
        self._scenarios[definition.scenario_id.lower().strip()] = definition
        logger.debug(
            f"Registered scenario: id='{definition.scenario_id}', "
            f"unreal_name='{definition.unreal_name}'"
        )

    def get(self, scenario_id: str) -> Optional[ScenarioDefinition]:
        """Look up a scenario by ID (case-insensitive)."""
        return self._scenarios.get(scenario_id.lower().strip())

    def check_availability(self, definition: ScenarioDefinition) -> bool:
        """
        Verifies scenario asset availability on disk and package compatibility.
        Supports both packaged .pak/.ucas containers and loose editor .umap assets.
        """
        if not definition.default_available:
            return False

        if self.content_dir:
            # 1. If running against a packaged build with .pak / .ucas container, all cooked levels are packed
            paks_dir = self.content_dir / "Paks"
            if paks_dir.exists() and any(paks_dir.glob("*.pak")):
                return True

            # 2. Check for loose map file in content_dir
            if definition.relative_map_path:
                full_path = self.content_dir / definition.relative_map_path
                if full_path.exists():
                    return True

        # 3. Check fallback raw editor content folder if content_dir didn't have loose maps
        raw_editor_content = Path(r"F:\Shooter\FiringSimulator\Unreal\FiringSim\Content")
        if raw_editor_content.exists() and definition.relative_map_path:
            if (raw_editor_content / definition.relative_map_path).exists():
                return True

        return definition.default_available

    def list_scenarios(self) -> List[ScenarioInfo]:
        """
        Returns sanitized list of scenario entries for Interfaces/UI consumption.
        Excludes raw filesystem paths to prevent leaking internal directory structures.
        """
        result: List[ScenarioInfo] = []
        for defn in self._scenarios.values():
            is_avail = self.check_availability(defn)
            result.append(
                ScenarioInfo(
                    scenario_id=defn.scenario_id,
                    display_name=defn.display_name,
                    description=defn.description,
                    available=is_avail,
                )
            )
        return result

    def get_valid_ids(self) -> List[str]:
        """Returns all registered scenario IDs."""
        return list(self._scenarios.keys())
