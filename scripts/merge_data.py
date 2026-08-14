import pandas as pd
import re
import sqlite3
import os
naukri =pd.read_csv("data/source1_naukri_applicants.csv")
gig =pd.read_csv("data/source2_gig_workers.csv")
cbnexus =pd.read_csv("data/source3_cbnexus_contacts.csv")

os.makedirs("database", exist_ok=True)

db_path = "database/consultbae.db"
conn = sqlite3.connect(db_path)

print("Naukri Data")
print(naukri.head())
print("Rows:",len(naukri))

print("\n GIG Workers Data")
print(gig.head())
print("Rows:",len(gig))

print("\n CBNEXUS Data")
print(cbnexus.head())
print("Rows:",len(cbnexus))

# ----------------------------------//cleaning//-----------
def clean_name(name):
    if pd.isna(name):
        return None

    name =str(name).strip().lower()
    name =re.sub(r"\s+"," ",name)
    return name.title()
def clean_email(email):
    if pd.isna(email):
        return None

    email = str(email).strip().lower()

    return email

def clean_phone(phone):
    if pd.isna(phone):
        return None
    phone = re.sub(r"\D", "", str(phone))

    if len(phone) == 12 and phone.startswith("91"):
        phone = phone[2:]

    if len(phone) > 10:
        phone = phone[-10:]

    return phone if phone else None
def clean_city(city):
    if pd.isna(city):
        return None

    city =str(city).strip().lower()

    city_mapping = {
    "gurgaon": "Gurugram",
    "gurugram": "Gurugram",

    "bangalore": "Bengaluru",
    "bengaluru": "Bengaluru",

    "new delhi": "Delhi",
    "delhi ncr": "Delhi",
    "delhi": "Delhi",

    "noida": "Noida",
    "pune": "Pune",
}
    return city_mapping.get(city,city.title())

naukri["clean_name"] = naukri["Full Name"].apply(clean_name)
naukri["clean_email"] = naukri["Email"].apply(clean_email)
naukri["clean_phone"] = naukri["Phone"].apply(clean_phone)
naukri["clean_city"] = naukri["City"].apply(clean_city)

# ----------------// cleaing gig workers//-------------
gig["clean_name"]=gig["worker_name"].apply(clean_name)
gig["clean_email"]=gig["email_id"].apply(clean_email)
gig["clean_city"]=gig["location"].apply(clean_city)

# ----------------// cleaing gig CBNEXUS//-------------
cbnexus = cbnexus[
    cbnexus["Name"].astype(str).str.strip().str.lower() != "name"
].copy()

cbnexus["clean_name"] = cbnexus["Name"].apply(clean_name)
cbnexus["clean_phone"] = cbnexus["Phone Number"].apply(clean_phone)
cbnexus["clean_city"] = cbnexus["City"].apply(clean_city)

# Removing completely empty rows

gig= gig.dropna(how="all")
gig = gig[
    gig["email_id"]
    .astype(str)
    .str.contains("@", na=False)
].copy()

print("\n DATA QUALITY SUMMARY ")
print("Valid Naukri rows :", len(naukri))
print("Valid Gig rows    :", len(gig))
print("Valid CBNexus rows:", len(cbnexus))

print("\n CLEANED NAUKRI ")
print(
    naukri[
        [
            "Full Name",
            "Email",
            "Phone",
            "City",
            "clean_name",
            "clean_email",
            "clean_phone",
            "clean_city",
        ]
    ].head(10)
)

print("\n ==Cleaned gig workers")
print(
    gig[
        [
            "worker_name",
            "email_id",
            "location",
            "clean_name",
            "clean_email",
            "clean_city",
        ]
    ].head(10)
)

print("\n===== CLEANED CBNEXUS =====")
print(
    cbnexus[
        [
            "Name",
            "Phone Number",
            "City",
            "clean_name",
            "clean_phone",
            "clean_city",
        ]
    ].head(10)
)

# =========================
# STANDARDIZE COLUMN NAMES
# =========================

naukri_std = pd.DataFrame({
    "name": naukri["clean_name"],
    "email": naukri["clean_email"],
    "phone": naukri["clean_phone"],
    "city": naukri["clean_city"],
    "skills": naukri["Skills"],
    "source": "naukri"
})

gig_std = pd.DataFrame({
    "name": gig["clean_name"],
    "email": gig["clean_email"],
    "phone": None,
    "city": gig["clean_city"],
    "skills": gig["skill_tags"],
    "source": "gig"
})

cbnexus_std = pd.DataFrame({
    "name": cbnexus["clean_name"],
    "email": None,
    "phone": cbnexus["clean_phone"],
    "city": cbnexus["clean_city"],
    "skills": None,
    "source": "cbnexus"
})


# Combine all sources
all_people = pd.concat(
    [naukri_std, gig_std, cbnexus_std],
    ignore_index=True
)

print("\n===== STANDARDIZED DATA =====")
print(all_people.head(20))

print("\nTotal raw records:", len(all_people))

# ENTITY RESOLUTION

unique_people = []


def find_existing_person(row):

    # Rule 1: Exact email match
    if pd.notna(row["email"]):

        for person in unique_people:

            if (
                person["email"] is not None
                and person["email"] == row["email"]
            ):
                return person, "email"


    # Rule 2: Exact phone match
    if pd.notna(row["phone"]):

        for person in unique_people:

            if (
                person["phone"] is not None
                and person["phone"] == row["phone"]
            ):
                return person, "phone"


    # Rule 3: Name + city fallback
    if pd.notna(row["name"]) and pd.notna(row["city"]):

        for person in unique_people:

            if (
                person["name"] == row["name"]
                and person["city"] == row["city"]
            ):
                return person, "name_city"


    return None, None
# BUILD MASTER PEOPLE LIST
for _, row in all_people.iterrows():

    existing_person, match_reason = find_existing_person(row)

    if existing_person:

        # Fill missing information
        if existing_person["email"] is None and pd.notna(row["email"]):
            existing_person["email"] = row["email"]

        if existing_person["phone"] is None and pd.notna(row["phone"]):
            existing_person["phone"] = row["phone"]

        if existing_person["city"] is None and pd.notna(row["city"]):
            existing_person["city"] = row["city"]

        # Combine skills
        if pd.notna(row["skills"]):

            if existing_person["skills"] is None:
                existing_person["skills"] = row["skills"]

            elif row["skills"] not in existing_person["skills"]:
                existing_person["skills"] += ", " + row["skills"]

        # Track all source systems
        if row["source"] not in existing_person["sources"]:
            existing_person["sources"].append(row["source"])

        existing_person["match_reasons"].append(match_reason)

    else:

        new_person = {
            "person_id": len(unique_people) + 1,

            "name": row["name"],

            "email": (
                row["email"]
                if pd.notna(row["email"])
                else None
            ),

            "phone": (
                row["phone"]
                if pd.notna(row["phone"])
                else None
            ),

            "city": (
                row["city"]
                if pd.notna(row["city"])
                else None
            ),

            "skills": (
                row["skills"]
                if pd.notna(row["skills"])
                else None
            ),

            "sources": [row["source"]],

            "match_reasons": []
        }

        unique_people.append(new_person)

# CREATE MASTER DATAFRAME
master_df = pd.DataFrame(unique_people)

master_df["sources"] = master_df["sources"].apply(
    lambda x: ", ".join(x)
)

master_df["match_reasons"] = master_df["match_reasons"].apply(
    lambda x: ", ".join(x)
)


print("\n===== MASTER PEOPLE =====")

print(
    master_df[
        [
            "person_id",
            "name",
            "email",
            "phone",
            "city",
            "sources",
            "match_reasons"
        ]
    ].to_string(index=False)
)


print("\n================================")
print("ENTITY RESOLUTION SUMMARY")
print("================================")

print("Valid raw records :", len(all_people))
print("Unique people     :", len(master_df))
print(
    "Duplicates merged:",
    len(all_people) - len(master_df)
)

print("\n===== MULTI-SOURCE PEOPLE =====")

multi_source = master_df[
    master_df["sources"].str.contains(",")
]

print(
    multi_source[
        [
            "person_id",
            "name",
            "sources",
            "match_reasons"
        ]
    ].to_string(index=False)
)

print(
    "\nPeople found in multiple systems:",
    len(multi_source)
)

master_df.to_sql(
    "people",
    conn,
    if_exists="replace",
    index=False
)
# =========================
# SAVE SOURCE TABLES
# =========================

# -------- NAUKRI --------

naukri_source = naukri[
    [
        "Full Name",
        "Email",
        "Phone",
        "City",
        "Experience (Years)",
        "Current CTC",
        "Applied Date",
        "Skills"
    ]
].copy()

naukri_source.to_sql(
    "naukri_applicants",
    conn,
    if_exists="replace",
    index=False
)


# -------- GIG WORKERS --------

gig_source = gig[
    [
        "email_id",
        "worker_name",
        "rate",
        "location",
        "status",
        "skill_tags"
    ]
].copy()

gig_source.to_sql(
    "gig_workers",
    conn,
    if_exists="replace",
    index=False
)


# -------- CBNEXUS --------

cbnexus_source = cbnexus[
    [
        "Name",
        "Phone Number",
        "City",
        "Verified",
        "Projects Completed"
    ]
].copy()

cbnexus_source.to_sql(
    "cbnexus_contacts",
    conn,
    if_exists="replace",
    index=False
)

conn.close()


print("\n================================")
print("DATABASE SAVED SUCCESSFULLY")
print("================================")
print("Database file :", db_path)
print("Master people :", len(master_df))
print("Naukri rows   :", len(naukri_source))
print("Gig rows      :", len(gig_source))
print("CBNexus rows  :", len(cbnexus_source))