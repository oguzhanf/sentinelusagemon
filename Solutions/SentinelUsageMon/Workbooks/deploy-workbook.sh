#!/usr/bin/env bash
# Deploys the Sentinel Usage Velocity workbook.
# Usage:
#   ./deploy-workbook.sh <resource-group> <workspace-name> [workbook-display-name]
set -euo pipefail

RG="${1:?resource group required}"
WS="${2:?workspace name required}"
DISPLAY_NAME="${3:-Sentinel Usage Velocity}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKBOOK_JSON="$SCRIPT_DIR/UsageVelocity.workbook.json"
TEMPLATE="$SCRIPT_DIR/workbookTemplate.json"

if [[ ! -f "$WORKBOOK_JSON" ]]; then
  echo "Missing workbook JSON: $WORKBOOK_JSON" >&2
  exit 1
fi

# Serialize the workbook JSON to a single JSON string for the ARM parameter.
SERIALIZED=$(python3 -c 'import json,sys; print(json.dumps(open(sys.argv[1]).read()))' "$WORKBOOK_JSON")

az deployment group create \
  --resource-group "$RG" \
  --template-file "$TEMPLATE" \
  --parameters \
      workspaceName="$WS" \
      workbookDisplayName="$DISPLAY_NAME" \
      workbookSerializedData="$SERIALIZED"
