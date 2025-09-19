import json

# Read existing JSON
with open(r"C:\Users\79818\Downloads\ppc US - Canada, 11-20 _ 4 Sep   - Us - founders.json", 'r', encoding='utf-8') as f:
    data = json.load(f)

# Extract all leads and combine small segments
all_leads = []
for segment_name, segment_data in data["segments"].items():
    all_leads.extend(segment_data["leads"])

print(f"Total leads: {len(all_leads)}")

# Create new segments with 200-300 leads each
new_segments = {}
segment_size = 250  # Target size
current_segment = 1

for i in range(0, len(all_leads), segment_size):
    segment_leads = all_leads[i:i+segment_size]

    if len(segment_leads) >= 200:  # Only create if >= 200 leads
        segment_name = f"segment_{current_segment:02d}"
        new_segments[segment_name] = {
            "description": f"Lead segment {current_segment} ({len(segment_leads)} leads)",
            "criteria": "Mixed company sizes and seniority levels for balanced testing",
            "count": len(segment_leads),
            "leads": segment_leads
        }
        current_segment += 1

# Update metadata
data["metadata"]["description"] = "Optimized segmentation with 200-300 leads per segment for balanced A/B testing. Mixed company sizes and seniority levels."
data["metadata"]["segmentation_logic"] = {
    "strategy": "Balanced Distribution",
    "segment_size_range": "200-300 leads",
    "approach": "Mixed company sizes for statistical validity"
}
data["metadata"]["segments_count"] = len(new_segments)
data["segments"] = new_segments

# Save updated JSON
with open(r"C:\Users\79818\Downloads\ppc US - Canada, 11-20 _ 4 Sep   - Us - founders.json", 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Created {len(new_segments)} segments:")
for name, seg in new_segments.items():
    print(f"  {name}: {seg['count']} leads")