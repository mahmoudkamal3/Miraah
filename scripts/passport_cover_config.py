#!/usr/bin/env python3
"""Passport-cover display and licensing configuration.

REAL_PASSPORT_COVERS_ENABLED must stay False until an explicit human decision
clears emblem/passport-reproduction review for public commercial deployment.
Photo-license approval alone is never enough to clear deployment.
"""

from __future__ import annotations

# Gate for public HTML/JSON references to real passport-cover photographs.
# While False: Mir’ah fallback only; no visitor downloads of real covers.
REAL_PASSPORT_COVERS_ENABLED = False

IMAGE_LICENSE_STATUSES = ("approved", "rejected", "unclear")
DEPLOYMENT_STATUSES = (
    "cleared",
    "editorial_review_required",
    "emblem_review_required",
    "blocked",
)

# Staged derivatives live outside public/ until deployment is cleared AND the gate is on.
STAGED_ASSETS_SUBDIR = "staged"
REVIEW_TOOL_SUBDIR = "review/tool"
