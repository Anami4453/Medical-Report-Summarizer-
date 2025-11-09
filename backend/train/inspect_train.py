import os
import csv

p = 'train.csv'
if not os.path.exists(p):
    print('ERROR: train.csv not found in', os.getcwd())
    raise SystemExit(1)

size = os.path.getsize(p)
print('FILE:', p)
print('SIZE_BYTES:', size)

with open(p, encoding='utf-8', errors='replace', newline='') as f:
    reader = csv.reader(f)
    try:
        header = next(reader)
    except StopIteration:
        print('ERROR: train.csv is empty')
        raise SystemExit(1)

    print('HEADER_COLUMNS_COUNT:', len(header))
    print('HEADER:', header)
    print('\nSAMPLE ROWS (first 5):')
    for i, row in enumerate(reader):
        if i >= 5:
            break
        # Truncate fields for readability
        print(f'ROW {i+1} (len={len(row)}):', [ (c[:200] + '...') if len(c) > 200 else c for c in row[:10] ])

    # Count total rows (fast-ish)
    f.seek(0)
    total = sum(1 for _ in f) - 1
    print('\nTOTAL_ROWS (approx):', total)
