# Data Dictionary

Required columns:
- `record_id`: unique record identifier
- `archive_name`: institution/archive name
- `collection`: collection grouping
- `record_title`: record title
- `archive_date`: source record date
- `document_language`: primary language
- `format_type`: physical record format
- `condition_score`: 0–100, higher means better physical condition
- `historical_value_score`: 0–100 screening value signal
- `public_demand_score`: 0–100 demand signal
- `language_rarity_score`: 0–100 rarity/limited-access signal
- `digitization_cost_index`: 0–100 relative cost signal
- `physical_risk_index`: 0–100 physical preservation risk signal
- `page_count`: approximate pages/items
- `catalog_completeness_pct`: 0–100
- `metadata_quality_pct`: 0–100
- `digitization_status`: Not Digitized / Partially Digitized / Digitized
- `storage_location`: local storage description

All scores are screening inputs, not official archival determinations.
