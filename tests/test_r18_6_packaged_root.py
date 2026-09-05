from __future__ import annotations

import hashlib

import pytest
from tuf.api.metadata import Metadata, Root

from kodepoia.release.tuf_security import TufVerificationError
from kodepoia.update.bootstrap import load_synthetic_packaged_root

EXPECTED_ROOT_SHA256 = "885bc87c3a5e9fe8b378cac85eb89fc37f99fcd8ba0bc7c494ee1e407da96670"


def test_synthetic_packaged_root_requires_explicit_opt_in() -> None:
    with pytest.raises(TufVerificationError, match="acceptance-only"):
        load_synthetic_packaged_root()


def test_synthetic_packaged_root_is_self_signed_versioned_and_digest_pinned() -> None:
    material = load_synthetic_packaged_root(allow_synthetic=True)
    assert material.purpose == "synthetic-acceptance-only"
    assert not material.production_trust_claim
    assert not material.private_keys_persisted
    assert material.pin.version == 1
    assert material.pin.sha256 == EXPECTED_ROOT_SHA256
    assert hashlib.sha256(material.root_bytes).hexdigest() == EXPECTED_ROOT_SHA256
    material.pin.verify(material.root_bytes)

    metadata = Metadata.from_bytes(material.root_bytes)
    assert isinstance(metadata.signed, Root)
    assert metadata.signed.version == 1
    assert metadata.signed.roles["root"].threshold == 2
