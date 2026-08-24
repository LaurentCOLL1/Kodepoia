from __future__ import annotations

from collections.abc import Iterable

from kodepoia.product.spec import AcceptanceCriterion, ProductSpec, Requirement
from kodepoia.project.dna import DesktopProjectProfile, Platform


def desktop_product_constraints(profile: DesktopProjectProfile) -> tuple[str, ...]:
    """Deterministic KodeProduct constraints derived from desktop Project DNA."""
    return (
        f"desktop.framework={profile.framework.value}",
        f"desktop.architecture={profile.architecture.value}",
        f"desktop.package={profile.package_kind.value}",
        f"desktop.persistence={profile.persistence.value}",
        f"desktop.ipc={profile.ipc.value}",
        f"desktop.updates={profile.updates.value}",
    )


def desktop_target_requirement(
    profile: DesktopProjectProfile,
    platforms: Iterable[Platform],
) -> Requirement:
    targets = tuple(sorted({item.value for item in platforms}))
    if not targets:
        raise ValueError("desktop product mapping requires at least one target")
    return Requirement(
        id="DESKTOP-TARGET",
        title="Desktop target and deployment intent",
        description=(
            "Generated from Project DNA so product acceptance remains traceable to the "
            "selected desktop framework, targets and deployment decisions."
        ),
        priority="P0",
        acceptance=[
            AcceptanceCriterion(
                "DESKTOP-TARGET-AC-1",
                f"Application targets {', '.join(targets)} using {profile.framework.value} on {profile.architecture.value}.",
            ),
            AcceptanceCriterion(
                "DESKTOP-TARGET-AC-2",
                (
                    f"Package intent is {profile.package_kind.value}; "
                    f"persistence={profile.persistence.value}; ipc={profile.ipc.value}; "
                    f"updates={profile.updates.value}."
                ),
            ),
        ],
    )


def apply_desktop_product_intent(
    product: ProductSpec,
    profile: DesktopProjectProfile,
    platforms: Iterable[Platform],
) -> None:
    for constraint in desktop_product_constraints(profile):
        if constraint not in product.constraints:
            product.constraints.append(constraint)
    requirement = desktop_target_requirement(profile, platforms)
    existing = [item for item in product.requirements if item.id == requirement.id]
    if existing:
        if existing[0] != requirement:
            raise ValueError("DESKTOP-TARGET requirement is reserved for Project DNA mapping")
        return
    product.requirements.append(requirement)
