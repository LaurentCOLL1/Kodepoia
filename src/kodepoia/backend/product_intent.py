from __future__ import annotations

from kodepoia.product.spec import AcceptanceCriterion, ProductSpec, Requirement

from .contracts import BackendServiceKind
from .intent import BACKEND_SERVICE_DEPENDENCIES, BackendProjectProfile

BACKEND_PRODUCT_REQUIREMENT_ID = "BACKEND-SERVICE-INTENT"
_BACKEND_CONSTRAINT_PREFIX = "backend.service="


def backend_product_constraints(
    profile: BackendProjectProfile | None,
) -> tuple[str, ...]:
    if profile is None or not profile.enabled:
        return ()
    return tuple(f"{_BACKEND_CONSTRAINT_PREFIX}{service.value}" for service in profile.services)


def backend_service_requirement(
    profile: BackendProjectProfile | None,
) -> Requirement | None:
    if profile is None or not profile.enabled:
        return None

    acceptance: list[AcceptanceCriterion] = []
    for index, service in enumerate(profile.services, start=1):
        acceptance.append(
            AcceptanceCriterion(
                f"{BACKEND_PRODUCT_REQUIREMENT_ID}-AC-{index}",
                (
                    f"Project DNA declares backend service intent {service.value}; "
                    "this requirement does not provision or execute the service."
                ),
            )
        )
    dependency_offset = len(acceptance)
    for service in profile.services:
        dependencies = BACKEND_SERVICE_DEPENDENCIES.get(service, ())
        if not dependencies:
            continue
        dependency_offset += 1
        acceptance.append(
            AcceptanceCriterion(
                f"{BACKEND_PRODUCT_REQUIREMENT_ID}-AC-{dependency_offset}",
                (
                    f"Backend service intent {service.value} is valid only with "
                    + ", ".join(item.value for item in dependencies)
                    + "."
                ),
            )
        )

    return Requirement(
        id=BACKEND_PRODUCT_REQUIREMENT_ID,
        title="Backend service intent",
        description=(
            "Generated from optional Project DNA backend intent so product acceptance "
            "remains traceable without selecting providers, credentials, deployment "
            "targets or concrete service implementations."
        ),
        priority="P0",
        acceptance=acceptance,
    )


def apply_backend_product_intent(
    product: ProductSpec,
    profile: BackendProjectProfile | None,
) -> None:
    retained_constraints = [
        item
        for item in product.constraints
        if not item.startswith(_BACKEND_CONSTRAINT_PREFIX)
    ]
    product.constraints[:] = retained_constraints + list(backend_product_constraints(profile))

    retained_requirements = [
        item for item in product.requirements if item.id != BACKEND_PRODUCT_REQUIREMENT_ID
    ]
    requirement = backend_service_requirement(profile)
    if requirement is not None:
        retained_requirements.append(requirement)
    product.requirements[:] = retained_requirements

    product.validate()
