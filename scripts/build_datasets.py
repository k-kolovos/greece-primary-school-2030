"""
Greece's Primary School of 2030 — ETL
=====================================
Κατεβάζει δεδομένα από το Eurostat dissemination API και παράγει όλα τα CSV
που τροφοδοτούν το dashboard.

Σύμβαση ετών: τα έτη της Eurostat αναφέρονται στο σχολικό έτος που λήγει.
    2018 → σχολικό έτος 2017/18
    2024 → σχολικό έτος 2023/24
    2030 → σχολικό έτος 2029/30  (τελευταίο πλήρως προσδιορισμένο από
                                  δημοσιευμένες γεννήσεις)

Έξοδος:
    p2_enrolments_nuts2.csv    εγγραφές δημοτικού ανά περιφέρεια
    p2_births_nuts3.csv        γεννήσεις ανά νομό
    p2_funnel_nuts2.csv        χωνί: αναμενόμενοι (γεννήσεις) vs πραγματικοί
    p2_change_ranking.csv      δύο ίσες εξαετίες + σύνθετη δωδεκαετία
    p2_teachers_55plus.csv     σύνολο διδακτικού προσωπικού και 55+
    p2_nomoi_2024_full.csv     μαθητές/τμήματα/διδάσκοντες ανά Διεύθυνση  (*)
    p2_nomoi_2017_2024.csv     σύγκριση Διευθύνσεων 2017/18 vs 2023/24    (*)
    p2_diktyo_2017_2024.csv    μαθητές / τμήματα / σχολεία: η κλιμάκωση   (*)
    p2_oligothesia.csv         ποσοστό ολιγοθέσιων ανά Διεύθυνση          (**)

(*)  Απαιτεί τα xlsx του Υπουργείου Παιδείας στον τρέχοντα φάκελο (λήψη
     χειροκίνητα από statistics.minedu.gov.gr — μπλοκάρει προγραμματιστική
     πρόσβαση). Το τμήμα παραλείπεται αν λείπουν.
(**) Κατεβάζει αυτόματα από data.gov.gr.

Συγγραφέας: Κωνσταντίνος Κολοβός, 2026
"""

import urllib.request
import json
import csv
import os

BASE = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
UA = {"User-Agent": "Mozilla/5.0"}


# ----------------------------------------------------------------------------
# Βοηθητικά
# ----------------------------------------------------------------------------

def eurostat(dataset, query):
    """Κατεβάζει ένα dataset σε μορφή JSON-stat και επιστρέφει το dict."""
    url = f"{BASE}{dataset}?{query}&format=JSON&lang=EN"
    req = urllib.request.Request(url, headers=UA)
    return json.loads(urllib.request.urlopen(req).read())


def indexer(data):
    """
    Επιστρέφει συνάρτηση val(**dims) που διαβάζει τιμές από JSON-stat.
    Το JSON-stat αποθηκεύει τις τιμές σε επίπεδο πίνακα· η θέση κάθε τιμής
    υπολογίζεται με διαδοχικό πολλαπλασιασμό των μεγεθών των διαστάσεων,
    με τη σειρά που δίνει το data["id"].
    """
    dims, sizes = data["id"], data["size"]
    cat = {d: data["dimension"][d]["category"]["index"] for d in dims}

    def val(**kw):
        pos = 0
        for d, s in zip(dims, sizes):
            i = cat[d][kw[d]] if d in kw else 0
            pos = pos * s + i
        return data["value"].get(str(pos))

    return val, cat


GR = {
    "Attiki": "Αττική",
    "Voreio Aigaio": "Βόρειο Αιγαίο",
    "Notio Aigaio": "Νότιο Αιγαίο",
    "Kriti": "Κρήτη",
    "Anatoliki Makedonia, Thraki": "Αν. Μακεδονία & Θράκη",
    "Kentriki Makedonia": "Κεντρική Μακεδονία",
    "Dytiki Makedonia": "Δυτική Μακεδονία",
    "Ipeiros": "Ήπειρος",
    "Thessalia": "Θεσσαλία",
    "Ionia Nisia": "Ιόνια Νησιά",
    "Dytiki Elláda": "Δυτική Ελλάδα",
    "Sterea Elláda": "Στερεά Ελλάδα",
    "Peloponnisos": "Πελοπόννησος",
}


def greek(name):
    return GR.get(name, name)


# ----------------------------------------------------------------------------
# 1. Εγγραφές δημοτικού ανά περιφέρεια (NUTS 2)
# ----------------------------------------------------------------------------

print("1/7  Εγγραφές δημοτικού ανά περιφέρεια…")

# Το dataset αφορά αποκλειστικά τη δημοτική εκπαίδευση (ISCED 1):
# διαστάσεις freq / unit / sex / geo / time — δεν δέχεται isced11 ή age.
enr = eurostat("educ_uoe_enrp06", "unit=NR&sex=T")
val_e, cat_e = indexer(enr)

# Οι 13 περιφέρειες (NUTS 2)· εξαιρείται το ELZZ (Extra-Regio, τεχνική
# κατηγορία της Eurostat για μη γεωγραφικά κατανεμημένες τιμές).
regions = [g for g in cat_e["geo"]
           if g.startswith("EL") and len(g) == 4 and g != "ELZZ"]
years_e = sorted(cat_e["time"], key=int)
labels_e = enr["dimension"]["geo"]["category"]["label"]

with open("p2_enrolments_nuts2.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["Geo", "Region", "Year", "Pupils"])
    for g in regions:
        for y in years_e:
            v = val_e(geo=g, time=y)
            if v is not None:
                w.writerow([g, greek(labels_e[g]), y, v])

print(f"      {len(regions)} περιφέρειες × {len(years_e)} έτη "
      f"({years_e[0]}–{years_e[-1]})")


# ----------------------------------------------------------------------------
# 2. Γεννήσεις ανά νομό (NUTS 3)
# ----------------------------------------------------------------------------

print("2/7  Γεννήσεις ανά νομό…")

bir = eurostat("demo_r_gind3", "indic_de=LBIRTH")
val_b, cat_b = indexer(bir)

nomoi = [g for g in cat_b["geo"] if g.startswith("EL") and len(g) == 5]
years_b = sorted(cat_b["time"], key=int)
labels_b = bir["dimension"]["geo"]["category"]["label"]

with open("p2_births_nuts3.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["Geo", "Nomos", "Region_code", "Year", "Births"])
    for g in nomoi:
        for y in years_b:
            v = val_b(geo=g, time=y)
            if v is not None:
                w.writerow([g, labels_b[g], g[:4], y, v])

chk = "2023"
tot_n = sum(val_b(geo=g, time=chk) or 0 for g in nomoi)
tot_el = val_b(geo="EL", time=chk)
print(f"      έλεγχος {chk}: άθροισμα νομών {tot_n:,} | εθνικό {tot_el:,}")


# ----------------------------------------------------------------------------
# 3. Το χωνί: γεννήσεις → εγγραφές
# ----------------------------------------------------------------------------

print("3/7  Χωνί γεννήσεων → εγγραφών…")

# Άθροισμα γεννήσεων ανά περιφέρεια, ΚΑΙ η εθνική γραμμή "EL"
births_r = {}
for g in nomoi:
    for y in years_b:
        v = val_b(geo=g, time=y)
        if v is not None:
            births_r[(g[:4], y)] = births_r.get((g[:4], y), 0) + v
for y in years_b:                      # <-- απαραίτητο για τους ελέγχους
    v = val_b(geo="EL", time=y)
    if v is not None:
        births_r[("EL", y)] = v


def cohort(region, school_year, off=6):
    """
    Οι έξι γενιές που συνθέτουν το δημοτικό το έτος t: γεννημένοι
    t-off-5 έως t-off. Επιστρέφει None αν λείπει έστω μία γενιά.
    """
    total = 0
    for b in range(school_year - off - 5, school_year - off + 1):
        v = births_r.get((region, str(b)))
        if v is None:
            return None
        total += v
    return total


# Εμπειρική επιλογή του παραθύρου: δοκιμάζονται τρεις αντιστοιχίσεις και
# κρατείται εκείνη με το μικρότερο μέσο απόλυτο σφάλμα.
print("      επιλογή παραθύρου γεννήσεων (εθνικό, 2015–2024):")
for o in (5, 6, 7):
    errs = []
    for y in range(2015, 2025):
        exp = cohort("EL", y, off=o)
        act = val_e(geo="EL", time=str(y)) if str(y) in cat_e["time"] else None
        if exp and act:
            errs.append(100 * (exp - act) / act)
    if errs:
        print(f"        t-{o+5}..t-{o}: μεροληψία {sum(errs)/len(errs):+5.1f}% | "
              f"MAE {sum(map(abs, errs))/len(errs):4.1f}%")

geo_list = ["EL"] + regions
with open("p2_funnel_nuts2.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["Geo", "Region", "Year", "Expected_pupils", "Actual_pupils"])
    for g in geo_list:
        name = "Ελλάδα" if g == "EL" else greek(labels_e.get(g, g))
        for y in range(2011, 2031):
            exp = cohort(g, y)
            act = val_e(geo=g, time=str(y)) if str(y) in cat_e["time"] else None
            if exp is not None or act is not None:
                w.writerow([g, name, y, exp or "", act or ""])

print("      p2_funnel_nuts2.csv")


# ----------------------------------------------------------------------------
# 4. Κατάταξη περιφερειών — δύο ΙΣΕΣ εξαετίες
#    απολογισμός 2017/18 → 2023/24  |  εκτίμηση 2023/24 → 2029/30
# ----------------------------------------------------------------------------

print("4/7  Κατάταξη περιφερειών (ίσες εξαετίες)…")

rank = []
for g in regions:
    a18, a24 = val_e(geo=g, time="2018"), val_e(geo=g, time="2024")
    e24, e30 = cohort(g, 2024), cohort(g, 2030)
    if not all([a18, a24, e24, e30]):
        continue
    ch_past = 100 * (a24 - a18) / a18
    ch_fut = 100 * (e30 - e24) / e24
    proj30 = a24 * (1 + ch_fut / 100)
    # σύνθετη μεταβολή δωδεκαετίας: πολλαπλασιαστικά, όχι αθροιστικά
    synol = 100 * ((1 + ch_past / 100) * (1 + ch_fut / 100) - 1)
    rank.append([g, greek(labels_e[g]), a18, a24, round(ch_past, 1),
                 round(proj30), round(ch_fut, 1), round(synol, 1)])

with open("p2_change_ranking.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["Geo", "Region", "Pupils_2018", "Pupils_2024",
                "Change_2018_2024_pct", "Projected_2030",
                "Change_2024_2030_pct", "Synoliki_2018_2030_pct"])
    w.writerows(rank)

rank.sort(key=lambda r: r[7])
print(f"      {'Περιφέρεια':<24}{'17/18→23/24':>13}{'23/24→29/30':>13}{'12ετία':>10}")
for r in rank:
    print(f"      {r[1]:<24}{r[4]:>12.1f}%{r[6]:>12.1f}%{r[7]:>9.1f}%")

a18, a24 = val_e(geo="EL", time="2018"), val_e(geo="EL", time="2024")
cp = 100 * (a24 - a18) / a18
cf = 100 * (cohort("EL", 2030) - cohort("EL", 2024)) / cohort("EL", 2024)
print(f"      {'ΕΛΛΑΔΑ':<24}{cp:>12.1f}%{cf:>12.1f}%"
      f"{100*((1+cp/100)*(1+cf/100)-1):>9.1f}%")


# ----------------------------------------------------------------------------
# 5. Εκπαιδευτικοί ανά ηλικιακή ομάδα → σύνολο και 55+
# ----------------------------------------------------------------------------

print("5/7  Εκπαιδευτικοί ανά ηλικία…")

AGES = ["Y_LT25", "Y25-29", "Y30-34", "Y35-39", "Y40-44",
        "Y45-49", "Y50-54", "Y55-59", "Y60-64", "Y_GE65"]
AGES_55 = ["Y55-59", "Y60-64", "Y_GE65"]

q = "geo=EL&isced11=ED1&sex=T&" + "&".join(f"age={a}" for a in AGES)
tea = eurostat("educ_uoe_perp01", q)
val_t, cat_t = indexer(tea)

years_t = sorted(cat_t["time"], key=int)
ages_ok = [a for a in AGES if a in cat_t["age"]]

with open("p2_teachers_55plus.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["Year", "Teachers_Total", "Teachers_55plus", "Share_55plus_pct"])
    print("      έτος  σύνολο    55+     %")
    for y in years_t:
        tot = sum(val_t(age=a, time=y) or 0 for a in ages_ok)
        f55 = sum(val_t(age=a, time=y) or 0 for a in AGES_55 if a in cat_t["age"])
        w.writerow([y, tot, f55, round(100 * f55 / tot, 1) if tot else ""])
        print(f"      {y} {tot:>7,} {f55:>6,} {100*f55/tot:>6.1f}")

# Κατανομή ηλικιών 2016 vs 2023/24 — το «καμπούρι» και η τρύπα πίσω του
GR_AGE = {"Y_LT25": "< 25", "Y25-29": "25–29", "Y30-34": "30–34",
          "Y35-39": "35–39", "Y40-44": "40–44", "Y45-49": "45–49",
          "Y50-54": "50–54", "Y55-59": "55–59", "Y60-64": "60–64",
          "Y_GE65": "65+"}

with open("p2_pyramida_ilikion.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["Seira", "Ilikia", "Etos", "Ekpaideutikoi"])
    for i, a in enumerate(AGES):
        if a not in cat_t["age"]:
            continue
        for y in ("2016", "2024"):
            v = val_t(age=a, time=y)
            if v:
                w.writerow([i, GR_AGE[a], y, v])

print("      κατανομή ηλικιών:   2016    2024")
for a in AGES:
    if a in cat_t["age"]:
        print(f"        {GR_AGE[a]:<7}{val_t(age=a, time='2016') or 0:>8,}"
              f"{val_t(age=a, time='2024') or 0:>8,}")
print("      p2_pyramida_ilikion.csv")


# Λόγοι επιβίωσης — η βάση της εκτίμησης αποχωρήσεων
def band(age, year):
    return val_t(age=age, time=str(year)) or 0

print("      λόγοι επιβίωσης:  50→55   55→60   60→65")
for t0 in range(2016, 2020):
    t1 = t0 + 5
    print(f"        {t0}→{t1}      "
          f"{band('Y55-59',t1)/band('Y50-54',t0):.3f}   "
          f"{band('Y60-64',t1)/band('Y55-59',t0):.3f}   "
          f"{band('Y_GE65',t1)/band('Y60-64',t0):.3f}")


# ----------------------------------------------------------------------------
# 6. Δεδομένα Υπουργείου Παιδείας ανά Διεύθυνση (προαιρετικό)
# ----------------------------------------------------------------------------

XLSX_2024 = "PRWTOBATHMIA_DHMOSIA_EKPSH_ANA_DIEFTHINSI_EKPSIS_2023_24.xlsx"
XLSX_2018 = "stats_pe_yppe8_dim_kata_nomo_2017_2018.xlsx"

COLS = ["AA", "Dieuthynsi",
        "Nip_Sxoleia", "Nip_Tmimata", "Nip_Mathites", "Nip_Ekpaideutikoi",
        "Dim_Sxoleia", "Dim_Tmimata", "Dim_Mathites", "Dim_Ekpaideutikoi"]


def fix_name(s):
    """
    Κανονικοποίηση ονομάτων Διευθύνσεων: τα αρχεία του υπουργείου περιέχουν
    λατινικούς χαρακτήρες μέσα σε ελληνικές λέξεις και διαφορετικές γραφές
    μεταξύ ετών.
    """
    s = str(s).strip().upper()
    for lat, gre in [("A", "Α"), ("B", "Β"), ("E", "Ε"), ("Z", "Ζ"),
                     ("H", "Η"), ("I", "Ι"), ("K", "Κ"), ("M", "Μ"),
                     ("N", "Ν"), ("O", "Ο"), ("P", "Ρ"), ("T", "Τ"),
                     ("X", "Χ"), ("Y", "Υ")]:
        s = s.replace(lat, gre)
    s = s.replace("ΔΙΕΥΘΥΝΣΗ Π.Ε. ", "").replace("Δ/ΝΣΗ Π.Ε. ", "")
    s = s.replace("ΑΡΓΟΛΙΔΑΣ", "ΑΡΓΟΛΙΔΟΣ").replace("ΡΕΘΥΜΝΗΣ", "ΡΕΘΥΜΝΟΥ")
    s = s.replace("ΔΥΤΙΚΗΣ ", "ΔΥΤ. ").replace("ΑΝΑΤΟΛΙΚΗΣ ", "ΑΝ. ")
    return " ".join(s.split())


if os.path.exists(XLSX_2024):
    print("6/7  Δεδομένα ανά Διεύθυνση (minedu)…")
    import pandas as pd

    def load(path):
        df = pd.read_excel(path, skiprows=6, header=None, names=COLS)
        df = df.dropna(subset=["Dieuthynsi"])
        df = df[~df["Dieuthynsi"].astype(str).str.contains("ΣΥΝΟΛΟ", na=False)]
        df["Dieuthynsi"] = df["Dieuthynsi"].apply(fix_name)
        return df

    df24 = load(XLSX_2024)
    df24["Analogia"] = df24["Dim_Mathites"] / df24["Dim_Ekpaideutikoi"]
    df24["Mathites_ana_Tmima"] = df24["Dim_Mathites"] / df24["Dim_Tmimata"]
    df24.to_csv("p2_nomoi_2024_full.csv", index=False, encoding="utf-8-sig")
    print(f"      {len(df24)} Διευθύνσεις | μαθητές "
          f"{df24['Dim_Mathites'].sum():,.0f}")

    if os.path.exists(XLSX_2018):
        df18 = load(XLSX_2018)
        m = df24.merge(df18, on="Dieuthynsi", suffixes=("_24", "_18"))
        m["Change_pct"] = (100 * (m["Dim_Mathites_24"] - m["Dim_Mathites_18"])
                           / m["Dim_Mathites_18"])
        m.to_csv("p2_nomoi_2017_2024.csv", index=False, encoding="utf-8-sig")
        print(f"      ταιριασμένες Διευθύνσεις: {len(m)}/{len(df24)}")

        # «Τα σχολεία μικραίνουν, δεν κλείνουν»
        print("      σχολικό έτος 2017/18 → 2023/24 (δημόσια δημοτικά):")
        with open("p2_diktyo_2017_2024.csv", "w", newline="",
                  encoding="utf-8-sig") as fh:
            wr = csv.writer(fh)
            wr.writerow(["Megethos", "Etos_2017_18", "Etos_2023_24",
                         "Metavoli_pct", "Diafora"])
            for lab, col in [("Μαθητές", "Dim_Mathites"),
                             ("Τμήματα", "Dim_Tmimata"),
                             ("Σχολικές μονάδες", "Dim_Sxoleia")]:
                a, b = df18[col].sum(), df24[col].sum()
                wr.writerow([lab, int(a), int(b),
                             round(100 * (b - a) / a, 1), int(b - a)])
                print(f"        {lab:<18}{a:>9,.0f} → {b:>9,.0f}"
                      f"   {100*(b-a)/a:+6.1f}%")
        print(f"        μέσο μέγεθος σχολείου: "
              f"{df18['Dim_Mathites'].sum()/df18['Dim_Sxoleia'].sum():.0f} → "
              f"{df24['Dim_Mathites'].sum()/df24['Dim_Sxoleia'].sum():.0f} μαθητές")
        print("        p2_diktyo_2017_2024.csv")
else:
    print("6/7  (παραλείπεται — λείπουν τα xlsx του υπουργείου)")


# ----------------------------------------------------------------------------
# 7. Ολιγοθέσια σχολεία ανά Διεύθυνση (data.gov.gr)
# ----------------------------------------------------------------------------

SCHOOLS_URL = ("https://data.gov.gr/dataset/e1f33fdb-addb-4cef-95aa-4becb0cfe408/"
               "resource/f99bc544-b2fe-42eb-9be6-91581ffda789/download/"
               "export_minedu_students_school.csv")

try:
    print("7/7  Ολιγοθέσια ανά Διεύθυνση…")
    import pandas as pd

    schools = pd.read_csv(SCHOOLS_URL)
    dim = schools[(schools["school_class"] == "Δημοτικά Σχολεία") &
                  (schools["year"] == 2019)].copy()
    dim["Students"] = (dim["registered_students_boys"] +
                       dim["registered_students_girls"])
    dim["Oligo"] = dim["school_type"].str.contains("Ολιγοθέσιο", na=False)
    dim["District"] = dim["district"].str.replace("ΔΙΕΥΘΥΝΣΗ Π.Ε. ", "",
                                                  regex=False)

    agg = dim.groupby("District").agg(
        Schools=("school_name", "count"),
        Oligothesia=("Oligo", "sum"),
        Students=("Students", "sum"),
    ).reset_index()
    agg["Oligo_pct"] = 100 * agg["Oligothesia"] / agg["Schools"]
    agg.to_csv("p2_oligothesia.csv", index=False, encoding="utf-8-sig")

    print(f"      {len(agg)} Διευθύνσεις | {dim['Oligo'].sum():,} ολιγοθέσια "
          f"από {len(dim):,} δημοτικά (στοιχεία 2019)")
except Exception as e:
    print(f"7/7  (παραλείπεται — {type(e).__name__}: {e})")


print("\nΌλα τα CSV δημιουργήθηκαν. ✔")
