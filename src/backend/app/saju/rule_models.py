"""YAML 해석 규칙 타입 모델."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RuleCondition(BaseModel):
    fact: str
    op: str
    value: Any


class RuleConditionGroup(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    all_conditions: list[RuleCondition] = Field(default_factory=list, alias="all")
    any_conditions: list[RuleCondition] = Field(default_factory=list, alias="any")


class RuleEmission(BaseModel):
    signal: str
    section: str
    weight: int = 1


class InterpretationRule(BaseModel):
    id: str
    description: str = ""
    priority: int = 50
    conditions: RuleConditionGroup
    emits: list[RuleEmission]


class SignalMeta(BaseModel):
    section: str
    conflict_group: str | None = None
    sort_order: int = 50
