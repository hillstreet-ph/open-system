---
name: organizing-numbered-year-month-files
description: Use when organizing files into numbered categories that require a consistent year, January-to-December, and file-type folder hierarchy, especially when existing folders must be reused and duplicates avoided.
---

# Organizing Numbered Year/Month Files

## Overview
Use one deterministic storage hierarchy for every numbered category. Preserve existing matching folders, normalize near-duplicates, and route each file to exactly one canonical location.

## Required hierarchy
For every numbered category `{NN - Name}` create/reuse:

```text
{NN - Name}/
└── {YYYY}/
    ├── 01 - January/
    ├── 02 - February/
    ├── 03 - March/
    ├── 04 - April/
    ├── 05 - May/
    ├── 06 - June/
    ├── 07 - July/
    ├── 08 - August/
    ├── 09 - September/
    ├── 10 - October/
    ├── 11 - November/
    └── 12 - December/
```

Every month MUST contain exactly these canonical file-type folders:

```text
01 - Images/
02 - Videos/
03 - Spreadsheets/
04 - Documents/
05 - PDFs/
06 - Presentations/
07 - ZIP & Archives/
08 - Other Files/
```

## Operating rules
1. Inspect the existing tree before creating or moving anything.
2. Inventory folders/files and detect duplicates or near-duplicates.
3. Reuse an existing folder when its semantic purpose matches the canonical folder, even if capitalization or spacing differs.
4. Never create a second canonical folder for the same purpose.
5. Determine the file's owning numbered category first, then year, month, then file type.
6. Use the file's authoritative business/document date when known; otherwise use a reliable created/modified date. Do not guess dates from filenames when evidence conflicts.
7. Preserve originals until copy/move verification succeeds. Never delete solely because names match; verify identity/content first.
8. Keep one canonical copy. Cross-category reuse should use a reference/link when supported rather than duplicate copies.
9. Record ambiguous files for review rather than forcing a risky classification.
10. Before destructive cleanup, produce a validation report listing canonical file, duplicate candidate, evidence, and proposed action.

## File routing
| Type | Destination |
|---|---|
| JPG, JPEG, PNG, WEBP, GIF, SVG, HEIC | `01 - Images` |
| MP4, MOV, AVI, MKV, WEBM | `02 - Videos` |
| Google Sheets, XLS, XLSX, CSV, ODS | `03 - Spreadsheets` |
| Google Docs, DOC, DOCX, TXT, RTF, ODT, MD | `04 - Documents` |
| PDF | `05 - PDFs` |
| Google Slides, PPT, PPTX, ODP | `06 - Presentations` |
| ZIP, RAR, 7Z, TAR, GZ | `07 - ZIP & Archives` |
| Everything else | `08 - Other Files` |

## Validation checklist
- All numbered categories use the same hierarchy.
- Correct year exists.
- All 12 month folders exist exactly once.
- All 8 file-type folders exist exactly once inside every applicable month.
- No duplicate/near-duplicate canonical folders remain.
- Every moved file resolves to one category/year/month/type path.
- File counts before and after reconcile.
- Destructive actions are separated from organization actions and require explicit approval.

## References
See `references/full-blueprint.md` for reusable prompts and `templates/validation-report.md` for the audit output.
