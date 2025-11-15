#!/usr/bin/env python3
"""
Demo version - shows expected output format for Soviet boots emails
"""

import json
from pathlib import Path
from datetime import datetime

# Example outputs for different languages
demo_results = [
    {
        "name": "Belgrade Antiques",
        "email": "nikolakolekcionar@gmail.com",
        "website": "https://belgradeantiques.rs/",
        "short_company_name": "Belgrade antiques",
        "subject_line": "brzo pitanje",
        "email_1": "hej {{firstName | default(\"tamo\")}},\n\nPogledao sam Belgrade antiques, zaista mi se svidela militarija sekcija.\n\nPrijatelj mi dobavlja originalne sovjetske čizme od veterana, pomislio sam da bi mogle odgovarati vašoj kolekciji, ljudi obično vole autentične stvari poput te.\n\nMislio sam da bi bilo vredno da vas povezem.\n\npozdrav,\nLeo",
        "email_2": "Pozdrav {{firstName}}\n\nDa li još uvek vredi napraviti tu vezu ili je loše vreme?\n\nSrdačan pozdrav,\nLeo",
        "email_3": "Nisam dobio odgovor, pa pretpostavljam da trenutno ne odgovara\n\nZadržaću {{companyName}} na umu ako se pojavi nešto slično",
        "language": "sr",
        "summary": "Belgrade Antiques is an online antique store specializing in militaria",
        "personalization_hooks": "Strong focus on militaria, extensive experience in military antiques"
    },
    {
        "name": "German-Historica An- Verkauf Orden & Ehrenzeichen, Militaria",
        "email": "info@german-historica.de",
        "website": "http://ankaufmilitaria.de/",
        "short_company_name": "German historica",
        "subject_line": "kurze frage",
        "email_1": "hey {{firstName | default(\"dort\")}},\n\nHabe mir German historica angeschaut, besonders die Militaria-Abteilung hat mir gefallen.\n\nEin Freund von mir bekommt original sowjetische Stiefel von Veteranen, dachte es könnte für Ihre Sammlung interessant sein, Leute lieben normalerweise so authentisches Zeug.\n\nDachte, es wäre vielleicht wert, euch beide zu verbinden.\n\nbeste Grüße,\nLeo",
        "email_2": "Hallo {{firstName}}\n\nLohnt sich die Verbindung noch oder ist es schlechtes Timing?\n\nBeste Grüße,\nLeo",
        "email_3": "Habe nichts gehört, also nehme ich an, es passt momentan nicht\n\nWerde {{companyName}} im Hinterkopf behalten falls etwas Ähnliches aufkommt",
        "language": "de",
        "summary": "German-Historica specializes in buying and selling military historical antiques",
        "personalization_hooks": "Over 30 years of experience in militaria, focus on responsible handling"
    },
    {
        "name": "Treasure Hunt",
        "email": "info@treasure-hunt.nl",
        "website": "https://www.treasure-hunt.nl/",
        "short_company_name": "Treasure hunt",
        "subject_line": "snelle vraag",
        "email_1": "hey {{firstName | default(\"daar\")}},\n\nHeb naar Treasure hunt gekeken, vooral het WO1 Duitse Keizerrijk gedeelte vond ik mooi.\n\nEen vriend van mij krijgt originele Sovjet laarzen van veteranen, dacht dat het bij je collectie zou passen, mensen houden meestal van zulke authentieke spullen.\n\nLeek me de moeite waard om jullie met elkaar te verbinden.\n\ngroetjes,\nLeo",
        "email_2": "Hoi {{firstName}}\n\nNog steeds de moeite waard om de verbinding te maken of is het slecht getimed?\n\nGroetjes,\nLeo",
        "email_3": "Heb niks gehoord, dus ik neem aan dat het nu niet past\n\nZal {{companyName}} in gedachten houden als er iets soortgelijks opkomt",
        "language": "nl",
        "summary": "Treasure Hunt Militaria specializes in WWI artifacts, particularly German Empire",
        "personalization_hooks": "Strong focus on WWI German artifacts, 100% authenticity guarantee"
    }
]

# Save demo output
OUTPUT_DIR = Path(__file__).parent.parent / "results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# JSON output
output_json = OUTPUT_DIR / f"soviet_boots_emails_DEMO_{timestamp}.json"
with open(output_json, 'w', encoding='utf-8') as f:
    json.dump({
        'metadata': {
            'generated_at': timestamp,
            'total_organizations': len(demo_results),
            'test_mode': True,
            'note': 'This is DEMO data showing expected output format',
            'languages': ['Serbian', 'German', 'Dutch']
        },
        'results': demo_results
    }, f, indent=2, ensure_ascii=False)

# CSV output
import pandas as pd
df = pd.DataFrame(demo_results)
output_csv = OUTPUT_DIR / f"soviet_boots_emails_DEMO_{timestamp}.csv"
df.to_csv(output_csv, index=False, encoding='utf-8-sig')

print("=== DEMO OUTPUT CREATED ===")
print(f"JSON: {output_json}")
print(f"CSV: {output_csv}")
print("\n=== SAMPLE (Belgrade Antiques - Serbian) ===")
print(f"Organization: {demo_results[0]['name']}")
print(f"Email: {demo_results[0]['email']}")
print(f"Language: {demo_results[0]['language']}")
print(f"Short Name: {demo_results[0]['short_company_name']}")
print(f"Subject: {demo_results[0]['subject_line']}")
print(f"\nEmail 1:\n{demo_results[0]['email_1']}")
print(f"\nEmail 2:\n{demo_results[0]['email_2']}")
print(f"\nEmail 3:\n{demo_results[0]['email_3']}")
