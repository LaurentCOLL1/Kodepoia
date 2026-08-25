from __future__ import annotations

from collections.abc import Iterable

from kodepoia.product.spec import AcceptanceCriterion, ProductSpec, Requirement
from kodepoia.project.dna import MobileProjectProfile, Platform


def mobile_product_constraints(profile: MobileProjectProfile) -> tuple[str, ...]:
    values = [
        f"mobile.source={profile.source_kind.value}",
        "mobile.form_factors=" + ",".join(item.value for item in profile.form_factors),
        f"mobile.network={profile.network_intent.value}",
        f"mobile.release_channel={profile.release_channel.value}",
        f"mobile.signing={profile.signing_intent.value}",
        "mobile.packages=" + ",".join(item.value for item in profile.package_kinds),
        f"mobile.budget.package_mb={profile.budget.max_package_mb}",
        f"mobile.budget.build_seconds={profile.budget.max_build_seconds}",
        f"mobile.budget.device_matrix_runs={profile.budget.max_device_matrix_runs}",
    ]
    if profile.android_application_id is not None:
        values.extend(
            [
                f"mobile.android.application_id={profile.android_application_id}",
                f"mobile.android.min_api={profile.android_min_api}",
                f"mobile.android.target_api={profile.android_target_api}",
            ]
        )
    if profile.apple_bundle_id is not None:
        values.extend(
            [
                f"mobile.apple.bundle_id={profile.apple_bundle_id}",
                f"mobile.apple.min_version={profile.apple_min_version}",
                f"mobile.apple.target_version={profile.apple_target_version}",
            ]
        )
    if profile.permissions:
        values.append("mobile.permissions=" + ",".join(profile.permissions))
    if profile.requested_capabilities:
        values.append(
            "mobile.capabilities=" + ",".join(profile.requested_capabilities)
        )
    return tuple(values)


def mobile_target_requirement(
    profile: MobileProjectProfile,
    platforms: Iterable[Platform],
) -> Requirement:
    targets = tuple(
        sorted(
            {
                item.value
                for item in platforms
                if item in {Platform.ANDROID, Platform.IOS}
            }
        )
    )
    if not targets:
        raise ValueError("mobile product mapping requires Android and/or iOS")
    identities: list[str] = []
    if profile.android_application_id:
        identities.append(f"Android {profile.android_application_id}")
    if profile.apple_bundle_id:
        identities.append(f"Apple {profile.apple_bundle_id}")
    return Requirement(
        id="MOBILE-TARGET",
        title="Mobile target and release intent",
        description=(
            "Generated from Project DNA so product acceptance remains traceable to "
            "mobile identities, supported targets and release intent without executing a build."
        ),
        priority="P0",
        acceptance=[
            AcceptanceCriterion(
                "MOBILE-TARGET-AC-1",
                f"Application targets {', '.join(targets)} from {profile.source_kind.value} source.",
            ),
            AcceptanceCriterion(
                "MOBILE-TARGET-AC-2",
                f"Identity intent is {'; '.join(identities)}.",
            ),
            AcceptanceCriterion(
                "MOBILE-TARGET-AC-3",
                (
                    f"Release channel={profile.release_channel.value}; "
                    f"signing={profile.signing_intent.value}; network={profile.network_intent.value}."
                ),
            ),
        ],
    )


def apply_mobile_product_intent(
    product: ProductSpec,
    profile: MobileProjectProfile,
    platforms: Iterable[Platform],
) -> None:
    for constraint in mobile_product_constraints(profile):
        if constraint not in product.constraints:
            product.constraints.append(constraint)
    requirement = mobile_target_requirement(profile, platforms)
    existing = [item for item in product.requirements if item.id == requirement.id]
    if existing:
        if existing[0] != requirement:
            raise ValueError("MOBILE-TARGET requirement is reserved for Project DNA mapping")
        return
    product.requirements.append(requirement)
