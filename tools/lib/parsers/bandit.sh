#!/bin/bash
# parsers/bandit.sh - Parse bandit JSON output to standard tool format
#
# Input: Raw JSON from bandit -f json
# Output: Standard tool results JSON array
#
# Converts bandit output format to:
# [{
#   "file": "src/file.py",
#   "line": 42,
#   "severity": "error|warning|info",
#   "message": "description",
#   "rule": "test-id"
# }]

set -euo pipefail

parse_bandit_json() {
    local bandit_json="$1"

    # Use Python to parse and transform bandit JSON to standard format
    python3 -c "
import json

try:
    bandit_json = '''$bandit_json'''

    if not bandit_json.strip():
        print('[]')
    else:
        # Parse bandit JSON report
        report = json.loads(bandit_json)

        results = []

        # Process security findings from the report
        results_list = report.get('results', [])
        for finding in results_list:
            filename = finding.get('filename', 'unknown')
            lineno = finding.get('line_number', 0)
            test_id = finding.get('test_id', 'unknown')
            issue_text = finding.get('issue_text', '')
            severity = finding.get('severity', 'MEDIUM').lower()

            # Map bandit severity to standard format
            if severity == 'high':
                severity_mapped = 'error'
            elif severity == 'medium':
                severity_mapped = 'warning'
            else:  # low
                severity_mapped = 'info'

            result = {
                'file': filename,
                'line': lineno,
                'severity': severity_mapped,
                'message': issue_text,
                'rule': test_id
            }
            results.append(result)

        print(json.dumps(results, indent=2))

except json.JSONDecodeError as e:
    print('[]')
except Exception as e:
    print('[]')
"
}

# Main entry point
main() {
    local bandit_json="${1:-}"

    if [[ -z "$bandit_json" ]]; then
        echo "[]"
        return 0
    fi

    parse_bandit_json "$bandit_json"
}

main "$@"
