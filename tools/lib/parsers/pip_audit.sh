#!/bin/bash
# parsers/pip_audit.sh - Parse pip-audit JSON output to standard tool format
#
# Input: Raw JSON from pip-audit -r requirements.txt --format=json
# Output: Standard tool results JSON array
#
# Converts pip-audit output format to:
# [{
#   "file": "package_name",
#   "line": "version",
#   "severity": "error|warning|info",
#   "message": "description",
#   "rule": "cve-id"
# }]

set -euo pipefail

parse_pip_audit_json() {
    local pip_audit_json="$1"

    # Use Python to parse and transform pip-audit JSON to standard format
    python3 -c "
import json

try:
    pip_audit_json = '''$pip_audit_json'''

    if not pip_audit_json.strip():
        print('[]')
    else:
        # Parse pip-audit JSON report
        report = json.loads(pip_audit_json)

        results = []

        # Process vulnerability findings
        # pip-audit format: {\"vulnerabilities\": [{...}]}
        vulns = report.get('vulnerabilities', [])
        for vuln in vulns:
            package_name = vuln.get('name', 'unknown')
            package_version = vuln.get('version', '')
            description = vuln.get('description', '')
            cve_id = vuln.get('id', 'UNKNOWN')

            # Check if there are fix versions available
            fix_versions = vuln.get('fix_versions', [])
            severity = 'warning' if fix_versions else 'error'

            # Include fix info in message if available
            if fix_versions:
                message = f'{description} Fix available in: {\", \".join(fix_versions)}'
            else:
                message = description

            result = {
                'file': package_name,
                'line': package_version,
                'severity': severity,
                'message': message,
                'rule': cve_id
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
    local pip_audit_json="${1:-}"

    if [[ -z "$pip_audit_json" ]]; then
        echo "[]"
        return 0
    fi

    parse_pip_audit_json "$pip_audit_json"
}

main "$@"
