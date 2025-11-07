"""
Icebreaker templates for cold outreach
Each template has conditions for when to use it
"""

ICEBREAKER_TEMPLATES = [
    {
        "id": "review_focus",
        "template": "Hey {{first_name}}, impressive seeing {{company}} maintain {{rating}} stars across {{review_count}} reviews in {{city}} - I'm in the Texas market too. Quick thing to run by you.",
        "conditions": "Use when: 100+ reviews AND rating 4.5+",
        "style": "Achievement-based compliment"
    },
    {
        "id": "review_focus_no_name",
        "template": "Impressive track record at {{company}} - {{review_count}} reviews maintaining {{rating}} stars in {{city}}. I'm in the Texas market too. Wanted to run something by you.",
        "conditions": "Use when: 100+ reviews AND rating 4.5+ AND no first name",
        "style": "Achievement-based without name"
    },
    {
        "id": "service_quality",
        "template": "Hey {{first_name}}, cool to see how {{company}} serves the {{city}} area - I work with Texas businesses as well. Figured I'd reach out.",
        "conditions": "Use when: moderate reviews (20-100) OR no standout features",
        "style": "Simple quality compliment"
    },
    {
        "id": "service_quality_no_name",
        "template": "Cool to see how {{company}} serves the {{city}} area - I work with Texas businesses as well. Figured I'd reach out.",
        "conditions": "Use when: moderate reviews (20-100) AND no first name",
        "style": "Simple quality without name"
    },
    {
        "id": "unique_service",
        "template": "Hey {{first_name}}, love how {{company}} {{unique_hook}} in {{city}} - I'm active in Texas too. Had something interesting to share.",
        "conditions": "Use when: unique_service or specialization found on website (24/7, veteran-owned, family business, specialty service)",
        "style": "Unique differentiator focus"
    },
    {
        "id": "unique_service_no_name",
        "template": "Love how {{company}} {{unique_hook}} in {{city}} - I'm active in Texas too. Had something interesting to share.",
        "conditions": "Use when: unique service AND no first name",
        "style": "Unique differentiator without name"
    },
    {
        "id": "growth_success",
        "template": "Hey {{first_name}}, awesome to see {{company}} growing in {{city}} - I'm in the Texas {{industry}} space too. Quick thing to run by you.",
        "conditions": "Use when: growing company indicators (good reviews, active website)",
        "style": "Growth-oriented"
    },
    {
        "id": "reputation",
        "template": "Hey {{first_name}}, love the reputation {{company}} built in {{city}} - I'm in the Texas {{industry}} space as well. Wanted to share something quickly.",
        "conditions": "Use when: solid reputation (4.0+ rating, 50+ reviews)",
        "style": "Reputation-based"
    },
    {
        "id": "direct_simple",
        "template": "Hey {{first_name}}, saw {{company}} in {{city}} - I'm in the Texas market as well. Worth a quick conversation?",
        "conditions": "Use when: minimal data or want direct approach",
        "style": "Direct and simple"
    },
    {
        "id": "direct_simple_no_name",
        "template": "Saw {{company}} in {{city}} - I'm in the Texas market as well. Worth a quick conversation?",
        "conditions": "Use when: minimal data AND no first name",
        "style": "Direct without name"
    },
    {
        "id": "casual_generic",
        "template": "Hey {{first_name}}, came across {{company}} - looks like you're doing well in {{city}}. I'm local too. Quick thing to share.",
        "conditions": "Use when: fallback option, generic case",
        "style": "Casual fallback"
    },
    {
        "id": "casual_generic_no_name",
        "template": "Came across {{company}} - looks like you're doing well in {{city}}. I'm local too. Quick thing to share.",
        "conditions": "Use when: fallback AND no first name",
        "style": "Casual fallback without name"
    }
]

# CTA variations (for reference)
CTA_OPTIONS = [
    "Wanted to run something by you",
    "Quick thing to share",
    "Figured I'd reach out",
    "Had something interesting",
    "Worth a quick conversation?",
    "Thought I'd reach out quickly",
    "Quick thing to run by you"
]
