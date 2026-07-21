"""Debug: test PL filter extraction."""
import sys
sys.path.insert(0, r"D:\planning-project\paijo\eduquery-ai")

from app.ai.keyword_classifier import classify_by_keyword
from app.ai.filter_resolver import FilterResolver

msg = "Berapa total izin PL?"

# Step 1: keyword classifier
kw = classify_by_keyword(msg)
print(f"Keyword classifier: {kw}")

# Step 2: filter resolver (regex)
resolver = FilterResolver()
temporal = resolver.resolve(msg)
entities = resolver.resolve_entities(msg)
print(f"Temporal: {temporal}")
print(f"Entities: {entities}")

# Step 3: apply
intent_id = kw["intent"] if kw else "bp_all_kpi_card"
resolved = resolver.apply(msg, intent_id)
print(f"apply() result: {resolved}")

# Step 4: map_to_sql directly
all_filters = {**temporal, **entities}
mapped = resolver.map_to_sql(all_filters, intent_id)
print(f"map_to_sql() result: {mapped}")
