# sentinelusagemon

Solution-hub-style content for Microsoft Sentinel that monitors hourly ingestion velocity from the `Usage` table, surfaces anomalies, projects end-of-month ingestion, and ships scheduled detection rules for alerting.

## Deploy

One-click deploy — pick a target. Each button opens the Azure portal’s Custom Deployment blade with a **workspace picker** (powered by [createUiDefinition.json](Solutions/SentinelUsageMon/Package/createUiDefinition.json)) — no typing workspace names or IDs.

| What | Deploy |
|---|---|
| **Everything** (4 rules + workbook) | [![Deploy](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#blade/Microsoft_Azure_CreateUIDef/CustomDeploymentBlade/uri/https%3A%2F%2Fraw.githubusercontent.com%2Foguzhanf%2Fsentinelusagemon%2Frootbranch%2FSolutions%2FSentinelUsageMon%2FPackage%2Fazuredeploy.json/uiFormDefinitionUri/https%3A%2F%2Fraw.githubusercontent.com%2Foguzhanf%2Fsentinelusagemon%2Frootbranch%2FSolutions%2FSentinelUsageMon%2FPackage%2FcreateUiDefinition.json) |
| Analytics rules only | [![Deploy](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#blade/Microsoft_Azure_CreateUIDef/CustomDeploymentBlade/uri/https%3A%2F%2Fraw.githubusercontent.com%2Foguzhanf%2Fsentinelusagemon%2Frootbranch%2FSolutions%2FSentinelUsageMon%2FPackage%2FmainTemplate.json/uiFormDefinitionUri/https%3A%2F%2Fraw.githubusercontent.com%2Foguzhanf%2Fsentinelusagemon%2Frootbranch%2FSolutions%2FSentinelUsageMon%2FPackage%2FcreateUiDefinition.rules.json) |
| Workbook only | [![Deploy](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#blade/Microsoft_Azure_CreateUIDef/CustomDeploymentBlade/uri/https%3A%2F%2Fraw.githubusercontent.com%2Foguzhanf%2Fsentinelusagemon%2Frootbranch%2FSolutions%2FSentinelUsageMon%2FPackage%2FworkbookTemplate.portal.json/uiFormDefinitionUri/https%3A%2F%2Fraw.githubusercontent.com%2Foguzhanf%2Fsentinelusagemon%2Frootbranch%2FSolutions%2FSentinelUsageMon%2FPackage%2FcreateUiDefinition.workbook.json) |

You will be prompted for:

- **Subscription / Region** — the picker below filters workspaces to this scope. Choose the region of your Sentinel workspace.
- **Sentinel workspace** — a dropdown of existing Log Analytics workspaces in the selected subscription + region. The resource group is inferred from the workspace you pick.
- **Enable analytics rules on deploy** (rules / everything) — checked by default.
- **Workbook display name** (workbook / everything) — defaults to *Sentinel Usage Velocity*.

> Tip: if you’d rather use the bare templates (text-box workspace input), browse to `https://portal.azure.com/#create/Microsoft.Template/uri/<RAW_TEMPLATE_URL>`.

> The portal-ready templates ([azuredeploy.json](Solutions/SentinelUsageMon/Package/azuredeploy.json) and [workbookTemplate.portal.json](Solutions/SentinelUsageMon/Package/workbookTemplate.portal.json)) embed the workbook JSON inline. If you edit [UsageVelocity.workbook.json](Solutions/SentinelUsageMon/Workbooks/UsageVelocity.workbook.json), regenerate them with `python3 Solutions/SentinelUsageMon/Package/build-portal-templates.py`.

## What's included

- Analytics rules (ARM):
  - [Solutions/SentinelUsageMon/Package/mainTemplate.json](Solutions/SentinelUsageMon/Package/mainTemplate.json)
  - [Solutions/SentinelUsageMon/Package/parameters.json](Solutions/SentinelUsageMon/Package/parameters.json)
- Analytics rule sources (YAML, one per rule):
  - [Solutions/SentinelUsageMon/AnalyticRules/Usage-HourlyIngestionSpike.yaml](Solutions/SentinelUsageMon/AnalyticRules/Usage-HourlyIngestionSpike.yaml)
  - [Solutions/SentinelUsageMon/AnalyticRules/Usage-TableIngestionAnomaly.yaml](Solutions/SentinelUsageMon/AnalyticRules/Usage-TableIngestionAnomaly.yaml)
  - [Solutions/SentinelUsageMon/AnalyticRules/Usage-PotentialIngestionDrop.yaml](Solutions/SentinelUsageMon/AnalyticRules/Usage-PotentialIngestionDrop.yaml)
  - [Solutions/SentinelUsageMon/AnalyticRules/Usage-VelocityAnomaly.yaml](Solutions/SentinelUsageMon/AnalyticRules/Usage-VelocityAnomaly.yaml)
- Workbook:
  - [Solutions/SentinelUsageMon/Workbooks/UsageVelocity.workbook.json](Solutions/SentinelUsageMon/Workbooks/UsageVelocity.workbook.json)
  - ARM template: [Solutions/SentinelUsageMon/Workbooks/workbookTemplate.json](Solutions/SentinelUsageMon/Workbooks/workbookTemplate.json)
  - Helper script: [Solutions/SentinelUsageMon/Workbooks/deploy-workbook.sh](Solutions/SentinelUsageMon/Workbooks/deploy-workbook.sh)

## Detection rules

All rules are scheduled and create incidents.

1. **Usage - Hourly billable ingestion spike** — last 1h vs rolling 8-day hourly baseline.
2. **Usage - Table-level ingestion anomaly** — per-`DataType` jump vs 14-day baseline.
3. **Usage - Potential ingestion drop** — last 6h significantly below 14-day baseline.
4. **Usage - Velocity anomaly (last hour vs 24h average)** — last-hour MB/hour > 2x prior-24h average; surfaces `ProjectedExtraMBIfSustained` as a custom detail.

## Workbook: Sentinel Usage Velocity

- Hourly ingestion (MB/hour) timechart with configurable lookback (billable or all).
- Anomaly detection via `series_decompose_anomalies` plus a grid of Increase/Decrease anomalies.
- Tiles: last-hour MB, 8-day hourly baseline MB, spike ratio.
- End-of-month projections:
  - Month-to-date (GB).
  - Projected EoM (GB) from last-24h average velocity sustained.
  - Projected EoM (GB) from last-1h velocity sustained.
  - Delta between the two — early warning when the current hour will blow the month.
- Cumulative MTD GB line with both projection trajectories drawn to end of month.
- Per-`DataType` hourly stacked timechart and "last hour vs 24h average" spike-ratio grid.

Projection math (computed inside the workbook):

- `hoursRemaining = (startofmonth(now + 1 month) − now) / 1h`
- `Projected_24h_GB = (MTD_MB + (Last24h_MB / 24) × hoursRemaining) / 1024`
- `Projected_1h_GB  = (MTD_MB +  Last1h_MB        × hoursRemaining) / 1024`

## Deployment

### Prerequisites

- Azure CLI 2.50+ (`az --version`) and `az login` completed.
- Owner / Contributor on the resource group containing the Sentinel workspace.
- Microsoft Sentinel enabled on the target Log Analytics workspace.
- Python 3 on the deployment machine (used by the workbook helper script to serialize JSON).

Set common variables once per session:

```bash
RG="<resource-group>"
WS="<sentinel-workspace-name>"
SUB="<subscription-id>"

az account set --subscription "$SUB"
```

### 1. Deploy the analytics rules

Edit [Solutions/SentinelUsageMon/Package/parameters.json](Solutions/SentinelUsageMon/Package/parameters.json) and set `workspace` to your Sentinel workspace name (or pass it inline as shown below). Optionally set `ruleEnabled` to `false` to deploy rules in a disabled state.

Validate first:

```bash
az deployment group validate \
  --resource-group "$RG" \
  --template-file Solutions/SentinelUsageMon/Package/mainTemplate.json \
  --parameters workspace="$WS" ruleEnabled=true
```

What-if (preview changes):

```bash
az deployment group what-if \
  --resource-group "$RG" \
  --template-file Solutions/SentinelUsageMon/Package/mainTemplate.json \
  --parameters workspace="$WS" ruleEnabled=true
```

Deploy:

```bash
az deployment group create \
  --name sentinelusagemon-rules \
  --resource-group "$RG" \
  --template-file Solutions/SentinelUsageMon/Package/mainTemplate.json \
  --parameters workspace="$WS" ruleEnabled=true
```

The rule resource names use stable GUIDs, so re-running the deployment is idempotent and will update rules in place rather than creating duplicates.

### 2. Deploy the workbook

Easiest path (helper script serializes the workbook JSON and submits the ARM deployment):

```bash
./Solutions/SentinelUsageMon/Workbooks/deploy-workbook.sh "$RG" "$WS"
# Optional custom display name:
./Solutions/SentinelUsageMon/Workbooks/deploy-workbook.sh "$RG" "$WS" "Sentinel Usage Velocity"
```

Manual ARM deployment (equivalent):

```bash
SERIALIZED=$(python3 -c 'import json,sys; print(json.dumps(open(sys.argv[1]).read()))' \
  Solutions/SentinelUsageMon/Workbooks/UsageVelocity.workbook.json)

az deployment group create \
  --name sentinelusagemon-workbook \
  --resource-group "$RG" \
  --template-file Solutions/SentinelUsageMon/Workbooks/workbookTemplate.json \
  --parameters workspaceName="$WS" workbookSerializedData="$SERIALIZED"
```

Portal import (no CLI):

1. Open Microsoft Sentinel → Workbooks → **+ Add workbook**.
2. Click **Edit** → the **</>** Advanced Editor icon.
3. Replace the contents with [Solutions/SentinelUsageMon/Workbooks/UsageVelocity.workbook.json](Solutions/SentinelUsageMon/Workbooks/UsageVelocity.workbook.json) and **Apply** → **Save**.

### 3. Verify

- Sentinel → **Analytics** → **Active rules**: confirm the four `Usage - …` rules are present and **Enabled**.
- Sentinel → **Workbooks** → **My workbooks**: open **Sentinel Usage Velocity** and confirm the hourly chart, anomaly grid, and projection tiles render.
- Smoke check in **Logs**:

  ```kql
  Usage
  | where TimeGenerated > ago(1h) and IsBillable == true
  | summarize Last1hMB = sum(Quantity)
  ```

### Tuning

Thresholds are intentionally conservative. Adjust per environment:

| Rule | Knob | Default | Where |
|---|---|---|---|
| Hourly ingestion spike | `CurrentMB > BaselineMB * 2.5` and `> 500 MB` floor | 2.5x / 500 MB | rule `query` |
| Table-level anomaly | `CurrentMB > BaselineMB * 3.0` and `> 200 MB` floor | 3.0x / 200 MB | rule `query` |
| Ingestion drop | `RecentMB < BaselineMB * 0.2`, `BaselineMB > 500 MB` floor | 20% / 500 MB | rule `query` |
| Velocity anomaly | `VelocityRatio > 2.0`, prior-24h velocity > 100 MB/h floor | 2.0x / 100 MB/h | rule `query` |

After tuning the YAML or ARM template, re-run the ARM deployment in step 1 — the rule GUIDs are stable so existing rules are updated in place.

### Uninstall

Delete the analytics rules and workbook via the portal, or via CLI using the rule GUIDs from `mainTemplate.json` (`variables.ruleId*`) and the workbook resource ID returned by the deployment:

```bash
az resource delete --ids \
  "/subscriptions/$SUB/resourceGroups/$RG/providers/Microsoft.OperationalInsights/workspaces/$WS/providers/Microsoft.SecurityInsights/alertRules/<ruleGuid>"
```

## Repository layout

```
Solutions/SentinelUsageMon/
├── AnalyticRules/
│   ├── Usage-HourlyIngestionSpike.yaml
│   ├── Usage-TableIngestionAnomaly.yaml
│   ├── Usage-PotentialIngestionDrop.yaml
│   └── Usage-VelocityAnomaly.yaml
├── Package/
│   ├── mainTemplate.json
│   └── parameters.json
└── Workbooks/
    ├── UsageVelocity.workbook.json
    ├── workbookTemplate.json
    └── deploy-workbook.sh
```
