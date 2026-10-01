#!/usr/bin/env bash
# Mirror a ticket's status to its GitHub issue and project board card.
# Called by the skills, not by hooks.
# Usage: board.sh status <issue-number> <Todo|In Progress|Done>
#        board.sh close  <issue-number> <comment>
set -euo pipefail
source "$(dirname "$0")/../hooks/config.sh"

repo="$GH_OWNER/$GH_REPO"

case "${1:-}" in
  status)
    issue="$2"; status="$3"
    project_id="$(gh project view "$GH_PROJECT_NUMBER" --owner "$GH_OWNER" --format json --jq '.id')"
    read -r field_id option_id < <(gh project field-list "$GH_PROJECT_NUMBER" --owner "$GH_OWNER" --format json \
      --jq ".fields[] | select(.name==\"Status\") | \"\(.id) \(.options[] | select(.name==\"$status\") | .id)\"")
    item_id="$(gh project item-list "$GH_PROJECT_NUMBER" --owner "$GH_OWNER" --limit 500 --format json \
      --jq ".items[] | select(.content.number==$issue and .content.repository==\"$repo\") | .id")"
    if [ -z "$item_id" ]; then
      item_id="$(gh project item-add "$GH_PROJECT_NUMBER" --owner "$GH_OWNER" \
        --url "https://github.com/$repo/issues/$issue" --format json --jq '.id')"
    fi
    [ -n "$option_id" ] || { echo "board.sh: no Status option named '$status'" >&2; exit 1; }
    gh project item-edit --id "$item_id" --project-id "$project_id" \
      --field-id "$field_id" --single-select-option-id "$option_id" >/dev/null
    echo "#$issue -> $status"
    ;;
  close)
    issue="$2"; comment="$3"
    gh issue close "$issue" --repo "$repo" --reason completed --comment "$comment" >/dev/null
    echo "#$issue closed"
    ;;
  *)
    echo "usage: board.sh status <issue> <Todo|In Progress|Done> | board.sh close <issue> <comment>" >&2
    exit 1
    ;;
esac
