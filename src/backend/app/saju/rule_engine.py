"""차트 메트릭을 해석 시그널로 변환하는 규칙 엔진."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

from app.saju.lunar_chart_models import CalculationResult, InterpretationResult, SignalHit
from app.saju.rule_models import InterpretationRule, SignalMeta


class RuleEngine:
    """YAML 정의 규칙을 결정론적으로 평가한다."""

    def __init__(self) -> None:
        rules_dir = Path(__file__).resolve().parent / "rules"
        rules_path = rules_dir / "interpretation_rules.yaml"
        catalog_path = rules_dir / "signal_catalog.yaml"
        self._rules: list[InterpretationRule] = [
            InterpretationRule.model_validate(item)
            for item in self._load_yaml(rules_path)
        ]
        self._signal_catalog: dict[str, SignalMeta] = {
            code: SignalMeta.model_validate(meta)
            for code, meta in self._load_yaml(catalog_path).items()
        }

    def evaluate(self, calculation: CalculationResult) -> InterpretationResult:
        raw_hits: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)

        for rule in self._rules:
            if not self._matches(rule.conditions.model_dump(by_alias=True), calculation.metrics):
                continue

            for emission in rule.emits:
                signal_meta = self._signal_catalog[emission.signal]
                section_hits = raw_hits[emission.section]
                signal_hit = section_hits.setdefault(
                    emission.signal,
                    {
                        "score": 0,
                        "priority": rule.priority,
                        "source_rule_ids": set(),
                        "conflict_group": signal_meta.conflict_group,
                        "sort_order": signal_meta.sort_order,
                    },
                )
                signal_hit["score"] += emission.weight
                signal_hit["priority"] = max(signal_hit["priority"], rule.priority)
                signal_hit["source_rule_ids"].add(rule.id)

        resolved_hits = {
            section: self._resolve_conflicts(section, section_hits)
            for section, section_hits in raw_hits.items()
        }
        explanations = {
            hit.code: hit.source_rule_ids
            for section_hits in resolved_hits.values()
            for hit in section_hits
        }
        return InterpretationResult(hits=resolved_hits, explanations=explanations)

    def _resolve_conflicts(
        self,
        section: str,
        raw_section_hits: dict[str, dict[str, Any]],
    ) -> list[SignalHit]:
        grouped: dict[str, list[tuple[str, dict[str, Any]]]] = defaultdict(list)

        for code, payload in raw_section_hits.items():
            conflict_group = payload["conflict_group"] or f"__{code}"
            grouped[conflict_group].append((code, payload))

        resolved: list[SignalHit] = []
        for entries in grouped.values():
            code, payload = max(
                entries,
                key=lambda entry: (
                    entry[1]["score"],
                    entry[1]["priority"],
                    -entry[1]["sort_order"],
                    entry[0],
                ),
            )
            resolved.append(
                SignalHit(
                    code=code,
                    section=section,
                    score=payload["score"],
                    priority=payload["priority"],
                    source_rule_ids=sorted(payload["source_rule_ids"]),
                )
            )

        resolved.sort(
            key=lambda hit: (
                -hit.score,
                -hit.priority,
                self._signal_catalog[hit.code].sort_order,
                hit.code,
            )
        )
        return resolved

    def _matches(self, conditions: dict[str, Any], facts: dict[str, Any]) -> bool:
        all_conditions = conditions.get("all", [])
        any_conditions = conditions.get("any", [])

        all_ok = all(self._evaluate_condition(condition, facts) for condition in all_conditions)
        any_ok = True if not any_conditions else any(
            self._evaluate_condition(condition, facts) for condition in any_conditions
        )
        return all_ok and any_ok

    def _evaluate_condition(self, condition: dict[str, Any], facts: dict[str, Any]) -> bool:
        actual = self._resolve_fact(facts, condition["fact"])
        expected = condition["value"]
        op = condition["op"]

        if op == "eq":
            return actual == expected
        if op == "neq":
            return actual != expected
        if op == "gt":
            return actual > expected
        if op == "gte":
            return actual >= expected
        if op == "lt":
            return actual < expected
        if op == "lte":
            return actual <= expected
        if op == "in":
            return actual in expected
        if op == "not_in":
            return actual not in expected
        if op == "contains":
            return expected in actual
        if op == "contains_any":
            return any(item in actual for item in expected)
        if op == "contains_all":
            return all(item in actual for item in expected)

        raise ValueError(f"Unsupported rule operator: {op}")

    @staticmethod
    def _resolve_fact(facts: dict[str, Any], fact_path: str) -> Any:
        current: Any = facts
        for segment in fact_path.split("."):
            if isinstance(current, dict):
                current = current[segment]
                continue
            raise KeyError(f"Unable to resolve fact path: {fact_path}")
        return current

    @staticmethod
    def _load_yaml(path: Path) -> Any:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
