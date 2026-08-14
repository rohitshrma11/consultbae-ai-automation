## Task 4 - Data Quality Issues Report

During ingestion and entity resolution, multiple data quality issues were identified across the three source files.

### 1. Inconsistent phone number formats

Phone numbers were stored in different formats, including:

- 9000000143
- 919000000143
- +91-9000000131

Resolution:
All non-numeric characters were removed. Indian country code `91` was removed where present, and phone numbers were normalized to the last 10 digits.

Example:

`+91-9000000131` → `9000000131`

---

### 2. Inconsistent email casing

Some email addresses appeared in different uppercase/lowercase formats.

Example:

`ISHA.CHOPRA95@MAILTEST.EXAMPLE.ORG`

and

`isha.chopra95@mailtest.example.org`

Resolution:
All email addresses were stripped of surrounding whitespace and converted to lowercase before matching.

---

### 3. Inconsistent city names

Cities appeared using different spellings and capitalization.

Examples:

- Gurgaon
- GURGAON
- Gurugram
- Bangalore
- Bengaluru
- New Delhi
- Delhi NCR
- PUNE
- pune

Resolution:
A city normalization mapping was created.

Examples:

- Gurgaon → Gurugram
- Bangalore → Bengaluru
- New Delhi → Delhi
- Delhi NCR → Delhi
- PUNE → Pune

---

### 4. Inconsistent name casing and whitespace

Names appeared with inconsistent capitalization and spacing.

Examples:

- `RITU SHARMA`
- `Ritu Sharma`
- `  Tanvi Gupta  `

Resolution:
Names were trimmed, multiple spaces were collapsed, converted to lowercase, and then standardized to title case.

---

### 5. Completely empty rows

The Gig Workers source contained completely empty rows.

Resolution:
Rows where every field was missing were removed using `dropna(how="all")`.

---

### 6. Malformed Gig Worker row

At least one row in the Gig Workers dataset had shifted or malformed data, causing values such as an email address or skills to appear in incorrect columns.

Resolution:
Gig Worker records were validated using the email field. Rows without a valid-looking email containing `@` were excluded from the cleaned dataset.

Original Gig rows: 32  
Valid Gig rows after cleaning: 30

---

### 7. Repeated header row inside CBNexus data

The CBNexus CSV contained a row where values such as `Name` and `City` appeared as actual data, indicating that the CSV header had been repeated inside the file.

Resolution:
Rows where the normalized `Name` value was equal to `"name"` were removed.

Original CBNexus rows: 31  
Valid CBNexus rows after cleaning: 30

---

### 8. Duplicate records within the same source

The Naukri dataset contained duplicate candidates, including repeated records for the same person.

Resolution:
Records were not deduplicated only within individual files. Instead, all cleaned records were passed through the same entity-resolution process so duplicates inside a source and across sources were handled consistently.

---

### 9. Same person appearing across multiple systems

The same individual appeared in more than one source with different available attributes.

Resolution:
A hierarchical entity-resolution strategy was used:

1. Exact normalized email match
2. Exact normalized phone match
3. Name + city fallback match

Email and phone were treated as stronger identifiers. Name + city was used only as a fallback because names alone are not unique.

---

### 10. Missing fields across different systems

Not every source contained the same attributes.

For example:

- Gig Workers did not contain phone numbers.
- CBNexus did not contain email addresses.
- Source-specific fields such as salary, skills, rates, availability, verification, and project counts differed between systems.

Resolution:
A canonical master `people` table was created containing common identity fields, while separate source tables were retained to preserve source-specific information.

---

### 11. Source-specific schema differences

The three CSV files used different column names for similar concepts.

Examples:

- `Full Name`
- `worker_name`
- `Name`

Resolution:
Each source was transformed into a standardized schema:

- name
- email
- phone
- city
- skills
- source

This standardized representation was then used for entity resolution.

---

### 12. Data lineage and match explainability

After merging records, it would otherwise be difficult to know which source systems contributed to a master record.

Resolution:
The master table stores:

- `sources`
- `match_reasons`

For example:

`Tanvi Gupta`  
Sources: `naukri, gig, cbnexus`  
Match reasons: `email, phone`

This makes the merge process easier to audit and explain.

---

## Final Cleaning Summary

- Naukri valid rows: 42
- Gig Worker valid rows: 30
- CBNexus valid rows: 30
- Total valid source records: 102
- Final unique people: 54
- Duplicate records merged: 48
- People found across multiple systems: 29
