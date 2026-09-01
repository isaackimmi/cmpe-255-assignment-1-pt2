"""Typed request-domain contracts for analytical row filtering."""

from dataclasses import dataclass

from fastapi import HTTPException

VALID_PLANS = {"all", "basic", "pro", "enterprise"}
VALID_RENEWAL = {"all", "0", "1"}
VALID_CLUSTERS = {"all", "0", "1", "2", "3"}


@dataclass(frozen=True)
class RowFilters:
    plan: str = "all"
    renewal: str = "all"
    cluster: str = "all"

    def validate(self) -> "RowFilters":
        if self.plan not in VALID_PLANS:
            raise HTTPException(status_code=422, detail="plan must be one of: all, basic, pro, enterprise")
        if self.renewal not in VALID_RENEWAL:
            raise HTTPException(status_code=422, detail="renewal must be one of: all, 0, 1")
        if self.cluster not in VALID_CLUSTERS:
            raise HTTPException(status_code=422, detail="cluster must be all or a supported cluster index")
        return self
