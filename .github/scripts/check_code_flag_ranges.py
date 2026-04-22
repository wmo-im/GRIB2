

# This script checks changed GRIB2_CodeFlag_.*_CodeTable_en.csv files.
# It validates changed CodeFlag values as either:
# - numeric values (<192 or 255 with MeaningParameterDescription_en='Missing')
# - numeric ranges (e.g. 192-254)

import re
import sys
import csv
import subprocess


def get_changed_files():
    """Get list of changed files."""
    result = subprocess.run(
        ['git', 'diff', '--name-only', 'origin/master..HEAD'],
        capture_output=True,
        text=True,
        check=True
    )
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def get_changed_lines(changed_file):
    """Get changed line numbers by tracking modified rows in new file."""
    changed_file = changed_file.strip().replace('\\', '/')
    result = subprocess.run(
        ['git', 'diff', '--unified=0', 'origin/master..HEAD', '--', changed_file],
        capture_output=True,
        text=True,
        check=True
    )

    changed_lines = set()
    current_line = None
    
    for line in result.stdout.splitlines():
        # Parse hunk headers (new-file side)
        hunk_match = re.match(r'^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@', line)
        if hunk_match:
            current_line = int(hunk_match.group(1))
            continue

        if current_line is None:
            continue

        if line.startswith('+') and not line.startswith('+++'):
            if re.search(r',\d{6}[,]', line):
                changed_lines.add(current_line)
            current_line += 1
        elif line.startswith(' ') and not line.startswith('@@'):
            current_line += 1

    return changed_lines

def validate_codeflag(file_path, table_name):
    errors = []
    with open(file_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=2):
            codeflag = row.get('CodeFlag', '').strip()
            meaning = row.get('MeaningParameterDescription_en', '').strip()
            if re.match(r'^\d+$', codeflag):
                value = int(codeflag)
                if value < 192:
                    continue
                elif value == 255:
                    if meaning != 'Missing':
                        errors.append(f"{table_name} Line {i}: CodeFlag '255' must have MeaningParameterDescription_en set to 'Missing', found '{meaning}'")
                else:
                    errors.append(f"{table_name} Line {i}: Invalid CodeFlag value '{codeflag}'")
            elif re.match(r'^\d+-\d+$', codeflag):
                continue
    return errors

# Get changed files
changed_files = get_changed_files()
codeTablefiles = [
    f for f in changed_files
    if f.replace('\\', '/').split('/')[-1].startswith('GRIB2_CodeFlag_')
    and f.replace('\\', '/').split('/')[-1].endswith('_CodeTable_en.csv')
]

errors = []
for file in sorted(codeTablefiles):
    match = re.search(r'GRIB2_CodeFlag_(.*?)_CodeTable_en\.csv$', file)
    version_str = f" ({match.group(1)})" if match else ""
    errors.extend(validate_codeflag(file, f'GRIB2_CodeFlag{version_str}'))

if errors:
    for err in errors:
        print(err)
    sys.exit(1)
else:
    sys.exit(0)
