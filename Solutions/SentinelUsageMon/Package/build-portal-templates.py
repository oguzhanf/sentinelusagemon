#!/usr/bin/env python3
"""Generate portal-ready ARM templates with the workbook serializedData embedded inline.

Inputs:
  Solutions/SentinelUsageMon/Workbooks/UsageVelocity.workbook.json   (human-edited)
  Solutions/SentinelUsageMon/Package/mainTemplate.json                (rules, hand-maintained)

Outputs (overwritten):
  Solutions/SentinelUsageMon/Package/workbookTemplate.portal.json    (workbook only, one-click)
  Solutions/SentinelUsageMon/Package/azuredeploy.json                (rules + workbook, one-click)

Run after editing the workbook JSON or the rules template:
  python3 Solutions/SentinelUsageMon/Package/build-portal-templates.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOLUTION = ROOT / "Solutions" / "SentinelUsageMon"
WORKBOOK_SRC = SOLUTION / "Workbooks" / "UsageVelocity.workbook.json"
RULES_SRC = SOLUTION / "Package" / "mainTemplate.json"
WORKBOOK_OUT = SOLUTION / "Package" / "workbookTemplate.portal.json"
COMBINED_OUT = SOLUTION / "Package" / "azuredeploy.json"


def workbook_resource(name_expr: str) -> dict:
    serialized = WORKBOOK_SRC.read_text(encoding="utf-8")
    # serializedData must be a JSON string; embed the raw workbook JSON as a string literal.
    return {
        "type": "Microsoft.Insights/workbooks",
        "apiVersion": "2022-04-01",
        "name": name_expr,
        "location": "[resourceGroup().location]",
        "kind": "shared",
        "properties": {
            "displayName": "[parameters('workbookDisplayName')]",
            "serializedData": serialized,
            "version": "1.0",
            "sourceId": "[resourceId('Microsoft.OperationalInsights/workspaces', parameters('workspace'))]",
            "category": "sentinel",
        },
    }


WORKBOOK_PARAMS = {
    "workspace": {
        "type": "string",
        "metadata": {"description": "Microsoft Sentinel workspace name."},
    },
    "workbookDisplayName": {
        "type": "string",
        "defaultValue": "Sentinel Usage Velocity",
        "metadata": {"description": "Display name shown in the Workbooks gallery."},
    },
    "workbookId": {
        "type": "string",
        "defaultValue": "[guid(resourceGroup().id, 'SentinelUsageVelocity')]",
        "metadata": {"description": "Stable GUID for the workbook resource."},
    },
}


def build_workbook_only() -> dict:
    return {
        "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
        "contentVersion": "1.0.0.0",
        "parameters": WORKBOOK_PARAMS,
        "resources": [workbook_resource("[parameters('workbookId')]")],
        "outputs": {
            "workbookResourceId": {
                "type": "string",
                "value": "[resourceId('Microsoft.Insights/workbooks', parameters('workbookId'))]",
            }
        },
    }


def build_combined() -> dict:
    rules = json.loads(RULES_SRC.read_text(encoding="utf-8"))
    params = dict(rules.get("parameters", {}))
    # Merge workbook params; workspace already exists in the rules template.
    for k, v in WORKBOOK_PARAMS.items():
        if k not in params:
            params[k] = v
    resources = list(rules.get("resources", []))
    resources.append(workbook_resource("[parameters('workbookId')]"))
    combined = {
        "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
        "contentVersion": "1.0.0.0",
        "parameters": params,
        "variables": rules.get("variables", {}),
        "resources": resources,
        "outputs": {
            "solutionName": {"type": "string", "value": "SentinelUsageMon"},
            "workbookResourceId": {
                "type": "string",
                "value": "[resourceId('Microsoft.Insights/workbooks', parameters('workbookId'))]",
            },
        },
    }
    return combined


def write(path: Path, obj: dict) -> None:
    path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)}")


def main() -> None:
    # Sanity: workbook source must be valid JSON.
    json.loads(WORKBOOK_SRC.read_text(encoding="utf-8"))
    write(WORKBOOK_OUT, build_workbook_only())
    write(COMBINED_OUT, build_combined())


if __name__ == "__main__":
    main()
