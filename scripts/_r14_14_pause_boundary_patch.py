from pathlib import Path

path = Path('src/kodepoia/backend/liveops.py')
text = path.read_text(encoding='utf-8')
old = '''    def pause_campaign(self, actor: AuthorityActorContext, *, campaign_id: str, version: int) -> LiveOpsRuntimeRecord:\n        campaign_id = _stable_id(campaign_id, field="campaign_id")\n        self._authorize(actor, "liveops.campaign.pause", campaign_id)\n        campaign = self.campaign(campaign_id, version)\n        current = self._advance_campaign(actor, campaign)\n        if current.state not in {LiveOpsCampaignState.SCHEDULED, LiveOpsCampaignState.ACTIVE}:\n            raise LiveOpsStateError("campaign_not_pausable")\n        return self._transition(actor=actor, campaign=campaign, state=LiveOpsCampaignState.PAUSED, action="campaign_paused")\n'''
new = '''    def pause_campaign(self, actor: AuthorityActorContext, *, campaign_id: str, version: int) -> LiveOpsRuntimeRecord:\n        campaign_id = _stable_id(campaign_id, field="campaign_id")\n        self._authorize(actor, "liveops.campaign.pause", campaign_id)\n        campaign = self.campaign(campaign_id, version)\n        current = self.runtime(campaign_id, version)\n        if _server_now_ms(self.clock_ms) >= campaign.schedule.end_at_utc_ms:\n            raise LiveOpsStateError("campaign_not_pausable")\n        if current.state not in {LiveOpsCampaignState.SCHEDULED, LiveOpsCampaignState.ACTIVE}:\n            raise LiveOpsStateError("campaign_not_pausable")\n        return self._transition(actor=actor, campaign=campaign, state=LiveOpsCampaignState.PAUSED, action="campaign_paused")\n'''
if text.count(old) != 1:
    raise SystemExit('pause_campaign anchor mismatch')
path.write_text(text.replace(old, new), encoding='utf-8')
