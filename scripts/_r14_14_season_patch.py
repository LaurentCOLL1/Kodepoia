from pathlib import Path

PATH = Path("src/kodepoia/backend/liveops.py")
text = PATH.read_text(encoding="utf-8")


def replace_once(old: str, new: str, label: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise AssertionError(f"{label}: expected exactly one occurrence, found {count}")
    text = text.replace(old, new, 1)


anchor = "\n\n@dataclass(frozen=True, slots=True)\nclass LiveOpsAudience:"
if text.count(anchor) != 1:
    raise AssertionError("season insertion anchor mismatch")
season_block = '''

@dataclass(frozen=True, slots=True)
class LiveOpsSeasonDefinition:
    season_id: str
    version: int
    environment: BackendEnvironmentKind
    schedule: LiveOpsScheduleWindow
    created_at_ms: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "season_id", _stable_id(self.season_id, field="season_id"))
        _positive_int(self.version, field="season_version")
        _environment(self.environment)
        if not isinstance(self.schedule, LiveOpsScheduleWindow):
            raise LiveOpsPolicyError("invalid_season_schedule")
        _timestamp(self.created_at_ms, field="season_created_at_ms")

    def canonical(self) -> dict[str, Any]:
        return {
            "season_id": self.season_id,
            "version": self.version,
            "environment": self.environment.value,
            "schedule": self.schedule.canonical(),
            "created_at_ms": self.created_at_ms,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class LiveOpsSeasonReference:
    season_id: str
    version: int
    digest: str
    environment: BackendEnvironmentKind

    def __post_init__(self) -> None:
        object.__setattr__(self, "season_id", _stable_id(self.season_id, field="season_id"))
        _positive_int(self.version, field="season_version")
        object.__setattr__(self, "digest", _sha256(self.digest, field="season_digest"))
        _environment(self.environment)

    @classmethod
    def from_season(cls, season: LiveOpsSeasonDefinition) -> LiveOpsSeasonReference:
        if not isinstance(season, LiveOpsSeasonDefinition):
            raise LiveOpsPolicyError("invalid_season")
        return cls(season.season_id, season.version, season.digest(), season.environment)

    def canonical(self) -> dict[str, Any]:
        return {
            "season_id": self.season_id,
            "version": self.version,
            "digest": self.digest,
            "environment": self.environment.value,
        }
'''
text = text.replace(anchor, season_block + anchor, 1)

replace_once(
'''class LiveOpsCampaignDefinition:
    campaign_id: str
    version: int
    season_id: str
    environment: BackendEnvironmentKind
''',
'''class LiveOpsCampaignDefinition:
    campaign_id: str
    version: int
    season: LiveOpsSeasonReference
    environment: BackendEnvironmentKind
''',
    "campaign season field",
)
replace_once(
'''        object.__setattr__(self, "campaign_id", _stable_id(self.campaign_id, field="campaign_id"))
        _positive_int(self.version, field="campaign_version")
        object.__setattr__(self, "season_id", _stable_id(self.season_id, field="season_id"))
        environment = _environment(self.environment)
''',
'''        object.__setattr__(self, "campaign_id", _stable_id(self.campaign_id, field="campaign_id"))
        _positive_int(self.version, field="campaign_version")
        if not isinstance(self.season, LiveOpsSeasonReference):
            raise LiveOpsPolicyError("invalid_season_reference")
        environment = _environment(self.environment)
''',
    "campaign season validation",
)
replace_once(
'''        backend_refs = (self.config_snapshot, self.content_manifest, *events)
''',
'''        backend_refs = (self.season, self.config_snapshot, self.content_manifest, *events)
''',
    "campaign backend refs",
)
replace_once(
'''            "season_id": self.season_id,
''',
'''            "season": self.season.canonical(),
''',
    "campaign canonical season",
)

replace_once(
'''class LiveOpsStateSnapshot:
    campaign_digests: tuple[str, ...]
''',
'''class LiveOpsStateSnapshot:
    season_digests: tuple[str, ...]
    campaign_digests: tuple[str, ...]
''',
    "state snapshot season field",
)
replace_once(
'''        return {
            "campaign_digests": list(self.campaign_digests),
''',
'''        return {
            "season_digests": list(self.season_digests),
            "campaign_digests": list(self.campaign_digests),
''',
    "state snapshot season canonical",
)

replace_once(
'''        max_campaigns: int = 4_096,
        max_dependencies: int = 16_384,
''',
'''        max_seasons: int = 1_024,
        max_campaigns: int = 4_096,
        max_dependencies: int = 16_384,
''',
    "service season capacity arg",
)
replace_once(
'''        for name, value in (
            ("max_campaigns", max_campaigns),
''',
'''        for name, value in (
            ("max_seasons", max_seasons),
            ("max_campaigns", max_campaigns),
''',
    "service season capacity validation",
)
replace_once(
'''        self.clock_ms = clock_ms
        self.max_campaigns = max_campaigns
''',
'''        self.clock_ms = clock_ms
        self.max_seasons = max_seasons
        self.max_campaigns = max_campaigns
''',
    "service season capacity assignment",
)
replace_once(
'''        self._lock = threading.RLock()
        self._campaigns: dict[tuple[str, int], LiveOpsCampaignDefinition] = {}
''',
'''        self._lock = threading.RLock()
        self._seasons: dict[tuple[str, int], LiveOpsSeasonDefinition] = {}
        self._campaigns: dict[tuple[str, int], LiveOpsCampaignDefinition] = {}
''',
    "service season registry",
)

insert_anchor = "    def register_campaign(self, actor: AuthorityActorContext, campaign: LiveOpsCampaignDefinition) -> LiveOpsCampaignDefinition:\n"
if text.count(insert_anchor) != 1:
    raise AssertionError("register_campaign insertion anchor mismatch")
season_methods = '''    def register_season(self, actor: AuthorityActorContext, season: LiveOpsSeasonDefinition) -> LiveOpsSeasonDefinition:
        if not isinstance(season, LiveOpsSeasonDefinition):
            raise LiveOpsPolicyError("invalid_season")
        self._authorize(actor, "liveops.season.register", season.season_id)
        key = (season.season_id, season.version)
        with self._lock:
            existing = self._seasons.get(key)
            if existing is not None:
                if existing != season:
                    raise LiveOpsStateError("season_version_rebind")
                return existing
            if len(self._seasons) >= self.max_seasons:
                raise LiveOpsCapacityError("season_capacity")
            if len(self._trace) >= self.max_trace_records:
                raise LiveOpsCapacityError("trace_capacity")
            self._seasons[key] = season
            self._append_trace(
                {
                    "event": "season_registered",
                    "season_id": season.season_id,
                    "season_version": season.version,
                    "season_digest": season.digest(),
                    "environment": season.environment.value,
                }
            )
            return season

    def season(self, season_id: str, version: int) -> LiveOpsSeasonDefinition:
        season_id = _stable_id(season_id, field="season_id")
        _positive_int(version, field="season_version")
        try:
            return self._seasons[(season_id, version)]
        except KeyError as exc:
            raise LiveOpsStateError("season_not_found") from exc

    def _validate_season(self, campaign: LiveOpsCampaignDefinition) -> str:
        season = self.season(campaign.season.season_id, campaign.season.version)
        if season.digest() != campaign.season.digest:
            raise LiveOpsStateError("season_dependency_unavailable")
        if season.environment is not campaign.environment:
            raise LiveOpsStateError("season_environment_mismatch")
        if (
            campaign.schedule.start_at_utc_ms < season.schedule.start_at_utc_ms
            or campaign.schedule.end_at_utc_ms > season.schedule.end_at_utc_ms
        ):
            raise LiveOpsStateError("campaign_outside_season_schedule")
        return season.digest()

'''
text = text.replace(insert_anchor, season_methods + insert_anchor, 1)
replace_once(
'''        self._authorize(actor, "liveops.campaign.register", campaign.campaign_id)
        self._validate_dependencies(campaign)
''',
'''        self._authorize(actor, "liveops.campaign.register", campaign.campaign_id)
        self._validate_season(campaign)
        self._validate_dependencies(campaign)
''',
    "campaign season dependency validation",
)

replace_once(
'''            return LiveOpsStateSnapshot(
                campaign_digests=tuple(sorted(item.digest() for item in self._campaigns.values())),
''',
'''            return LiveOpsStateSnapshot(
                season_digests=tuple(sorted(item.digest() for item in self._seasons.values())),
                campaign_digests=tuple(sorted(item.digest() for item in self._campaigns.values())),
''',
    "state snapshot season digests",
)

PATH.write_text(text, encoding="utf-8", newline="\n")
