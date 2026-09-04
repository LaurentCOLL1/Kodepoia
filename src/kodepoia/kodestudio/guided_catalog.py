from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True, slots=True)
class GuidedOption:
    value: str
    label_fr: str
    label_en: str
    help_fr: str
    help_en: str

    def label(self, locale: str) -> str:
        return self.label_fr if locale.lower().startswith("fr") else self.label_en

    def help(self, locale: str) -> str:
        return self.help_fr if locale.lower().startswith("fr") else self.help_en


GENRE_OPTIONS: tuple[GuidedOption, ...] = (
    GuidedOption("rpg", "RPG / jeu de rôle", "RPG / role-playing", "Progression, personnages, quêtes et choix.", "Progression, characters, quests and choices."),
    GuidedOption("simulation", "Simulation", "Simulation", "Reproduire ou modéliser un système, une activité ou une vie.", "Model a system, activity or life."),
    GuidedOption("adult_sex", "Sexe / adulte", "Sex / adult", "Projet adulte centré sur des thèmes ou mécaniques sexuelles. Réservé à un public adulte.", "Adult project centered on sexual themes or mechanics. Adults only."),
    GuidedOption("strategy", "Stratégie", "Strategy", "Planification, gestion de ressources et décisions à moyen/long terme.", "Planning, resource management and medium/long-term decisions."),
    GuidedOption("action", "Action", "Action", "Réflexes, combat, mouvement et rythme soutenu.", "Reflexes, combat, movement and fast pacing."),
    GuidedOption("adventure", "Aventure", "Adventure", "Exploration, narration, énigmes et découverte.", "Exploration, story, puzzles and discovery."),
    GuidedOption("management", "Gestion", "Management", "Construire, optimiser et administrer des systèmes.", "Build, optimize and administer systems."),
    GuidedOption("sandbox", "Bac à sable / Sandbox", "Sandbox", "Objectifs ouverts et forte liberté d'expérimentation.", "Open-ended goals and strong freedom to experiment."),
    GuidedOption("survival", "Survie", "Survival", "Ressources limitées, risques et progression sous contrainte.", "Limited resources, risks and constrained progression."),
    GuidedOption("horror", "Horreur", "Horror", "Tension, peur, vulnérabilité et atmosphère.", "Tension, fear, vulnerability and atmosphere."),
    GuidedOption("fps_tps", "FPS / TPS", "FPS / TPS", "Action et tir à la première ou troisième personne.", "First- or third-person action and shooting."),
    GuidedOption("platformer", "Plateforme", "Platformer", "Déplacements précis, sauts et parcours.", "Precise movement, jumps and traversal."),
    GuidedOption("puzzle", "Puzzle / réflexion", "Puzzle", "Résolution de problèmes, logique et énigmes.", "Problem-solving, logic and puzzles."),
    GuidedOption("visual_novel", "Visual novel / fiction interactive", "Visual novel / interactive fiction", "Narration, dialogues, choix et embranchements.", "Narrative, dialogue, choices and branching."),
    GuidedOption("racing", "Course", "Racing", "Conduite, vitesse, compétition et véhicules.", "Driving, speed, competition and vehicles."),
    GuidedOption("sports", "Sport", "Sports", "Simulation ou interprétation d'une discipline sportive.", "Simulation or interpretation of a sport."),
    GuidedOption("educational", "Éducatif / serious game", "Educational / serious game", "Apprendre, former ou sensibiliser par l'interaction.", "Learn, train or raise awareness through interaction."),
)


GRAPHICS_OPTIONS: tuple[GuidedOption, ...] = (
    GuidedOption("realistic", "Réaliste", "Realistic", "Proportions, matériaux et éclairage proches du réel.", "Real-world proportions, materials and lighting."),
    GuidedOption("photorealistic", "Photoréaliste", "Photorealistic", "Recherche d'un rendu très proche d'une photographie, coûteux en production.", "Targets a photographic look and is production-heavy."),
    GuidedOption("stylized", "Stylisé", "Stylized", "Formes et couleurs volontairement interprétées pour une identité forte.", "Deliberately interpreted forms and colors for a strong identity."),
    GuidedOption("anime", "Anime / manga", "Anime / manga", "Codes visuels inspirés de l'animation et du manga japonais.", "Visual language inspired by Japanese animation and manga."),
    GuidedOption("cel_shaded", "Cel shading", "Cel shaded", "Ombres franches et rendu proche de l'illustration/animation.", "Hard shading bands with an illustration/animation look."),
    GuidedOption("hand_painted", "Peint à la main", "Hand-painted", "Textures et surfaces avec une esthétique picturale.", "Textures and surfaces with a painterly aesthetic."),
    GuidedOption("pixel_art", "Pixel art", "Pixel art", "Esthétique basée sur des pixels visibles et une résolution maîtrisée.", "Visible-pixel aesthetic with controlled resolution."),
    GuidedOption("low_poly", "Low poly", "Low poly", "Géométrie simplifiée, lisible et généralement légère.", "Simplified readable geometry, usually lightweight."),
    GuidedOption("isometric", "Isométrique", "Isometric", "Vue oblique stable adaptée à la stratégie, RPG et gestion.", "Stable oblique view well suited to strategy, RPG and management."),
    GuidedOption("cartoon", "Cartoon", "Cartoon", "Formes exagérées, lisibilité et identité graphique forte.", "Exaggerated forms, readability and strong visual identity."),
    GuidedOption("retro", "Rétro", "Retro", "Référence esthétique à une génération ou une époque de jeu.", "Aesthetic reference to an earlier game generation or era."),
    GuidedOption("minimal", "Minimaliste", "Minimal", "Peu d'éléments, formes simples et hiérarchie visuelle claire.", "Few elements, simple shapes and clear visual hierarchy."),
)


SCOPE_OPTIONS: tuple[GuidedOption, ...] = (
    GuidedOption("prototype", "Prototype", "Prototype", "Prouver une idée ou un risque technique avec le minimum nécessaire.", "Prove an idea or technical risk with the minimum necessary."),
    GuidedOption("vertical_slice", "Vertical slice", "Vertical slice", "Une petite portion représentative de la qualité finale.", "A small slice representative of final quality."),
    GuidedOption("indie_small", "Petit projet indépendant", "Small indie", "Périmètre réduit, équipe petite, priorité au cœur de l'expérience.", "Reduced scope, small team, focus on the core experience."),
    GuidedOption("indie_large", "Projet indépendant ambitieux", "Large indie", "Plusieurs systèmes et contenu substantiel, à cadrer par étapes.", "Several systems and substantial content, requiring staged scope."),
    GuidedOption("aa", "AA", "AA", "Production structurée, équipe et contenu importants.", "Structured production with a larger team and content scope."),
    GuidedOption("aaa", "AAA / très ambitieux", "AAA / highly ambitious", "Très forte exigence de contenu, technologie, art, QA et budget.", "Very high content, technology, art, QA and budget demands."),
)


AUDIENCE_OPTIONS: tuple[GuidedOption, ...] = (
    GuidedOption("general", "Grand public", "General audience", "Accessible à un public large.", "Accessible to a broad audience."),
    GuidedOption("family", "Famille", "Family", "Contenu et difficulté adaptés à un usage familial.", "Content and difficulty suited to family use."),
    GuidedOption("core", "Joueurs expérimentés", "Core players", "Systèmes plus profonds et courbe d'apprentissage assumée.", "Deeper systems with an intentional learning curve."),
    GuidedOption("adult", "Adultes", "Adults", "Public adulte pour thèmes, complexité ou contenu mature.", "Adult audience for themes, complexity or mature content."),
    GuidedOption("professional", "Professionnels / métier", "Professional", "Outil ou expérience visant un contexte professionnel.", "Tool or experience targeting a professional context."),
    GuidedOption("students", "Éducation / étudiants", "Education / students", "Apprentissage, formation ou contexte académique.", "Learning, training or academic use."),
)


def option_by_value(options: Iterable[GuidedOption], value: str) -> GuidedOption | None:
    for option in options:
        if option.value == value:
            return option
    return None


__all__ = [
    "AUDIENCE_OPTIONS",
    "GENRE_OPTIONS",
    "GRAPHICS_OPTIONS",
    "SCOPE_OPTIONS",
    "GuidedOption",
    "option_by_value",
]
