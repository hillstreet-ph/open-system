---
name: open-influencer-organize
description: Use when consolidating influencer/contact lists from multiple files, sheets, documents, or connected resources into one deduplicated master spreadsheet organized by platform and country.
---

# Open Influencer Organize

## Goal
Create and maintain one canonical influencer workbook named **Influencer Master List Contacts**. Consolidate all supplied or authorized-source influencer records, normalize fields, deduplicate contacts, and place every influencer in the correct tab.

## Canonical Tabs and Columns

### FB-PH
`Name | Followers | Facebook Link | Telegram | Email | Reference Price | Status | Philippines | Notes`

### IG-PH
`Name | Followers | Instagram Link | Telegram | Email | Reference Price | Status | Philippines | Notes`

### YT-PH
`Name | Followers | YouTube Link | Telegram | Email | Reference Price | Status | Philippines | Notes`

### OTHER COUNTRY_FB-IG-YT
`Name | Followers | Facebook Link | Instagram Link | YouTube Link | Telegram | Email | Reference Price | Status | Country | Notes`

Do not create extra platform tabs unless explicitly requested.

## Workflow

1. **Inspect first.** Search all supplied files/resources before editing.
2. Inventory influencer/contact lists and identify source location.
3. Extract only influencer/contact records relevant to the master list.
4. Normalize names, follower counts, social links, Telegram handles, email addresses, price references, status, country, and notes.
5. Determine platform and country.
6. Deduplicate before inserting.
7. Merge complementary information into the strongest canonical row.
8. Place the row in the correct canonical tab.
9. Validate every source record is either migrated, merged as a duplicate, excluded with a reason, or flagged for review.
10. Produce an audit summary.

## Routing Rules

- Philippines + Facebook-focused record -> `FB-PH`
- Philippines + Instagram-focused record -> `IG-PH`
- Philippines + YouTube-focused record -> `YT-PH`
- Non-Philippines record -> `OTHER COUNTRY_FB-IG-YT`
- A Philippines influencer with genuinely separate platform-specific source records may appear in the relevant PH tabs, but do not duplicate the same platform identity within a tab.
- When a record contains several platforms and the correct PH primary platform cannot be established, flag it for review instead of guessing.

For PH tabs, `Philippines` should use a consistent value such as `Yes`.
For the other-country tab, populate the actual country when known; otherwise use `Unknown` and flag for review.

## Deduplication

Never deduplicate by display name alone.

Use strongest identifiers in this order:
1. Exact normalized social profile URL / platform username
2. Exact email
3. Exact Telegram username/ID
4. Strong combination of normalized name + platform + matching account details
5. Name similarity alone = review, not automatic merge

Normalize URLs before comparison:
- remove tracking query parameters where safe
- normalize protocol/domain casing
- trim whitespace
- treat trailing slash differences as equivalent when appropriate

Normalize Telegram:
- convert `https://t.me/name`, `@name`, and `name` to a consistent handle representation when clearly equivalent

Normalize email:
- trim whitespace
- lowercase for comparison

When duplicates contain complementary fields, merge into one row. Never discard a populated field unless a newer or more authoritative source clearly supersedes it.

If values conflict, preserve the strongest evidence and record the conflict/source context in Notes or review output.

## Followers
Keep follower values numeric when reliably parseable. Normalize common shorthand where unambiguous:
- `10K` -> `10000`
- `1.2M` -> `1200000`
Do not guess unreadable/ambiguous follower counts.

## Reference Price
Preserve currency. Do not silently convert currencies.
Examples: `₱6,000`, `USD 100`, `PHP 5,000`.
If the source is only a quote/reference rather than an agreed fee, keep that distinction in Notes.

## Status
Preserve meaningful source status. Normalize obvious synonyms only when safe.
Do not mark an influencer Contacted, Negotiating, Approved, Rejected, or Active without source evidence.

## Source Traceability
When practical, preserve source file/sheet/page information in Notes, especially when merging records or resolving conflicts. Do not fabricate provenance.

## Spreadsheet Quality
- One header row.
- Freeze header row.
- Enable filters.
- Use readable column widths.
- Wrap Notes and long links.
- Use consistent follower and text formatting.
- Avoid merged cells inside the data table.
- Keep one influencer record per row.
- Do not create blank duplicate rows.
- Do not overwrite existing stronger data with blanks.

## Safety
Do not delete source files or source sheets merely because migration is complete. Report migration status first. Destructive cleanup requires explicit authorization.

## Validation Report
Return:
- sources inspected
- source records found
- unique canonical influencer identities
- rows added by tab
- duplicates merged
- conflicts requiring review
- incomplete records
- excluded non-influencer records
- source records not yet migrated
- final status: `COMPLETE — VALIDATED`, `COMPLETE WITH REVIEW ITEMS`, or `INCOMPLETE — ACTION REQUIRED`
