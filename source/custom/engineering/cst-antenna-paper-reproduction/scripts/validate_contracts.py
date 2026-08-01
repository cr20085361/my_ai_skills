from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


EVIDENCE_GRADES = {
    "paper_exact",
    "author_source_exact",
    "derived",
    "engineering_assumption",
}


def load_object(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: 顶层必须是 JSON 对象。")
    return value


def require_keys(value: dict[str, Any], keys: tuple[str, ...], label: str) -> None:
    missing = [key for key in keys if key not in value]
    if missing:
        raise ValueError(f"{label}: 缺少字段 {', '.join(missing)}。")


def validate_evidence(data: dict[str, Any]) -> set[str]:
    require_keys(data, ("schema_version", "target_design", "sources", "records"), "evidence")
    source_ids = {str(source.get("id", "")) for source in data["sources"]}
    if "" in source_ids or not source_ids:
        raise ValueError("evidence.sources: 每个来源必须具有非空 id。")
    record_ids: set[str] = set()
    for index, record in enumerate(data["records"]):
        label = f"evidence.records[{index}]"
        require_keys(
            record,
            ("id", "feature", "grade", "source_id", "locator", "interpretation", "affects"),
            label,
        )
        record_id = str(record["id"])
        if not record_id or record_id in record_ids:
            raise ValueError(f"{label}: id 为空或重复。")
        record_ids.add(record_id)
        if record["grade"] not in EVIDENCE_GRADES:
            raise ValueError(f"{label}: 未知 evidence grade {record['grade']!r}。")
        if str(record["source_id"]) not in source_ids:
            raise ValueError(f"{label}: source_id 未在 sources 中定义。")
        if record["grade"] in {"derived", "engineering_assumption"} and "uncertainty" not in record:
            raise ValueError(f"{label}: 推导值或工程假设必须声明 uncertainty。")
    if not record_ids:
        raise ValueError("evidence.records: 至少需要一条证据记录。")
    return record_ids


def validate_geometry(data: dict[str, Any], evidence_ids: set[str]) -> None:
    require_keys(
        data,
        ("schema_version", "coordinate_system", "dimension_reference", "frequency_band_ghz", "components", "modeling_scope", "unresolved_high_impact_items"),
        "geometry",
    )
    require_keys(data["coordinate_system"], ("origin", "x_axis", "y_axis", "z_axis"), "geometry.coordinate_system")
    band = data["frequency_band_ghz"]
    if not isinstance(band, list) or len(band) != 2 or float(band[0]) <= 0 or float(band[1]) <= float(band[0]):
        raise ValueError("geometry.frequency_band_ghz: 必须是递增的两个正数。")
    if data["unresolved_high_impact_items"]:
        raise ValueError("geometry: 仍有未解决的高影响项目，不能开始 CST 构建。")
    for index, component in enumerate(data["components"]):
        label = f"geometry.components[{index}]"
        require_keys(component, ("name", "material", "topology", "contacts", "open_interfaces", "evidence_record_ids"), label)
        unknown = set(component["evidence_record_ids"]) - evidence_ids
        if unknown:
            raise ValueError(f"{label}: 引用了未知证据记录 {sorted(unknown)}。")


def validate_parameters(data: dict[str, Any], evidence_ids: set[str]) -> None:
    require_keys(
        data,
        ("schema_version", "parameters", "derived", "dynamic_topology", "regression_states", "invalid_states"),
        "parameters",
    )
    names: set[str] = set()
    for index, parameter in enumerate(data["parameters"]):
        label = f"parameters.parameters[{index}]"
        require_keys(parameter, ("name", "default", "unit", "description", "evidence_record_ids", "constraints", "affects"), label)
        name = str(parameter["name"])
        if not name or name in names:
            raise ValueError(f"{label}: name 为空或重复。")
        names.add(name)
        unknown = set(parameter["evidence_record_ids"]) - evidence_ids
        if unknown:
            raise ValueError(f"{label}: 引用了未知证据记录 {sorted(unknown)}。")
    labels = {str(state.get("label", "")) for state in data["regression_states"]}
    required_labels = {"baseline", "nominal", "smaller", "larger"}
    if data["dynamic_topology"]:
        required_labels.add("topology_change")
    if not required_labels.issubset(labels):
        missing = sorted(required_labels - labels)
        raise ValueError(f"parameters.regression_states: 缺少 {missing}。")
    if not data["invalid_states"]:
        raise ValueError("parameters.invalid_states: 至少需要一个非法状态。")


def main() -> None:
    parser = argparse.ArgumentParser(description="验证论文到 CST 复现的证据、几何和参数合同。")
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--geometry", type=Path, required=True)
    parser.add_argument("--parameters", type=Path, required=True)
    args = parser.parse_args()

    evidence = load_object(args.evidence)
    geometry = load_object(args.geometry)
    parameters = load_object(args.parameters)
    evidence_ids = validate_evidence(evidence)
    validate_geometry(geometry, evidence_ids)
    validate_parameters(parameters, evidence_ids)
    print("CONTRACTS_OK")


if __name__ == "__main__":
    main()
