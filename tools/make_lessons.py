"""Writes data/lessons.js from the course plan below. Edit START, BREAKS or the PLAN list (topics, slides, titles, kind) and run:
    python tools/make_lessons.py
status: 'published' = visible with notes and exercises, 'planned' = shown greyed in the lesson log."""
import datetime, json, pathlib

TOPICS = {
 "3.01": ("Electron theory", "Θεωρία ηλεκτρονίων"),
 "3.02": ("Static electricity and conduction", "Στατικός ηλεκτρισμός και αγωγή"),
 "3.03": ("Electrical terminology", "Ηλεκτρική ορολογία"),
 "3.04": ("Generation of electricity", "Παραγωγή ηλεκτρισμού"),
 "3.05": ("DC sources of electricity", "Πηγές DC"),
 "3.06": ("DC circuits", "Κυκλώματα DC"),
 "3.07": ("Resistance / resistor", "Αντίσταση / αντιστάτης"),
 "3.08": ("Power", "Ισχύς"),
 "3.09": ("Capacitance / capacitor", "Χωρητικότητα / πυκνωτής"),
 "3.10": ("Magnetism", "Μαγνητισμός"),
 "3.11": ("Inductance / inductor", "Αυτεπαγωγή / πηνίο"),
 "3.12": ("DC motor / generator theory", "Κινητήρες και γεννήτριες DC"),
 "3.13": ("AC theory", "Θεωρία AC"),
 "3.14": ("R, C and L circuits", "Κυκλώματα R, C, L"),
 "3.15": ("Transformers", "Μετασχηματιστές"),
 "3.16": ("Filters", "Φίλτρα"),
 "3.17": ("AC generators", "Γεννήτριες AC"),
 "3.18": ("AC motors", "Κινητήρες AC"),
}

# The six units of the course (L01 notes: "The course in one picture") plus the final revision.
# Each lesson goes to the unit of its last topic; a lesson that covers the whole syllabus goes to "R".
UNITS = {
 "A": (["3.01", "3.02", "3.03", "3.04"], "Electrons, charge and sources", "Ηλεκτρόνια, φορτίο και πηγές"),
 "B": (["3.05", "3.06", "3.07", "3.08"], "DC sources and circuits", "Πηγές και κυκλώματα DC"),
 "C": (["3.09", "3.10", "3.11"], "Capacitance, magnetism, inductance", "Χωρητικότητα, μαγνητισμός, αυτεπαγωγή"),
 "D": (["3.12"], "DC machines", "Μηχανές DC"),
 "E": (["3.13", "3.14", "3.16"], "AC theory and circuits", "Θεωρία και κυκλώματα AC"),
 "F": (["3.15", "3.17", "3.18"], "Transformers and AC machines", "Μετασχηματιστές και μηχανές AC"),
 "R": ([], "Final revision", "Τελική επανάληψη"),
}
UNIT_OF = {t: u for u, (ts, _, _) in UNITS.items() for t in ts}

def unit_of(topics):
    if len(topics) == len(TOPICS):
        return "R"
    return UNIT_OF[max(topics)]

# Dates are not written here: lessons run on weekdays from START, one per day, skipping BREAKS.
START = "2026-12-02"
BREAKS = [("2026-12-24", "2027-01-06", "Christmas break")]

def schedule(n):
    """The first n teaching days: Monday to Friday from START, outside the breaks."""
    d, out = datetime.date.fromisoformat(START), []
    while len(out) < n:
        iso = d.isoformat()
        if d.weekday() < 5 and not any(a <= iso <= b for a, b, _ in BREAKS):
            out.append(iso)
        d += datetime.timedelta(days=1)
    return out

# (topics, slides, title EN, title EL, kind)   kind: lesson | exercises | test
PLAN = [
 (["3.01"], "1–14", "Introduction and electron theory", "Εισαγωγή και θεωρία ηλεκτρονίων", "lesson"),
 (["3.02"], "1–17", "Static electricity and conduction", "Στατικός ηλεκτρισμός και αγωγή", "lesson"),
 (["3.03"], "1–21", "Electrical terminology and SI prefixes", "Ηλεκτρική ορολογία και προθέματα SI", "lesson"),
 (["3.04"], "1–9", "Generation of electricity + quiz A", "Παραγωγή ηλεκτρισμού + quiz Α", "lesson"),
 (["3.05"], "1–23", "Primary cells and lead-acid batteries", "Πρωτογενή στοιχεία και μπαταρίες μολύβδου", "lesson"),
 (["3.05"], "24–41", "NiCad, SLA, Li-ion, thermocouples, photocells", "NiCad, SLA, Li-ion, θερμοζεύγη, φωτοκύτταρα", "lesson"),
 (["3.06"], "1–26", "Series circuits, KVL, voltage dividers", "Κυκλώματα σε σειρά, KVL, διαιρέτες τάσης", "lesson"),
 (["3.06"], "27–45", "Parallel circuits, KCL, internal resistance", "Παράλληλα κυκλώματα, KCL, εσωτερική αντίσταση", "lesson"),
 (["3.07"], "1–24", "Resistance, resistivity, wire sizes", "Αντίσταση, ειδική αντίσταση, διατομές καλωδίων", "lesson"),
 (["3.07"], "25–60", "Variable resistors, Wheatstone bridge, colour code", "Μεταβλητές αντιστάσεις, γέφυρα Wheatstone, χρωματικός κώδικας", "lesson"),
 (["3.08"], "1–13", "Work, energy and power", "Έργο, ενέργεια και ισχύς", "lesson"),
 (["3.05", "3.06", "3.07", "3.08"], "", "DC exercises", "Ασκήσεις DC", "exercises"),
 (["3.01", "3.02", "3.03", "3.04", "3.05", "3.06", "3.07", "3.08"], "", "Test 1: units A and B", "Τεστ 1: ενότητες Α και Β", "test"),
 (["3.09"], "1–23", "Capacitors: function, factors, types", "Πυκνωτές: λειτουργία, παράγοντες, τύποι", "lesson"),
 (["3.09"], "24–39", "Capacitors in circuits, RC, reactance", "Πυκνωτές σε κυκλώματα, RC, χωρητική αντίσταση", "lesson"),
 (["3.10"], "1–23", "Magnetism and magnetic materials", "Μαγνητισμός και μαγνητικά υλικά", "lesson"),
 (["3.10"], "24–47", "Electromagnets, hand rules, hysteresis", "Ηλεκτρομαγνήτες, κανόνες χεριού, υστέρηση", "lesson"),
 (["3.11"], "1–27", "Induction, Lenz, inductors", "Επαγωγή, Lenz, πηνία", "lesson"),
 (["3.09", "3.10", "3.11"], "", "Review C + test 2", "Επανάληψη Γ + τεστ 2", "test"),
 (["3.13"], "1–25", "AC theory and AC values", "Θεωρία AC και τιμές AC", "lesson"),
 (["3.14"], "1–15", "Impedance, series RLC", "Σύνθετη αντίσταση, RLC σε σειρά", "lesson"),
 (["3.14"], "16–35", "Parallel AC, resonance, power factor", "Παράλληλα AC, συντονισμός, συντελεστής ισχύος", "lesson"),
 (["3.16"], "1–18", "Filters", "Φίλτρα", "lesson"),
 (["3.13", "3.14", "3.16"], "", "AC exercises + test 3", "Ασκήσεις AC + τεστ 3", "test"),
 (["3.12"], "1–28", "DC generator: principle and construction", "Γεννήτρια DC: αρχή και κατασκευή", "lesson"),
 (["3.12"], "29–46", "DC generator types, armature reaction", "Τύποι γεννητριών DC, αντίδραση τυμπάνου", "lesson"),
 (["3.12"], "47–83", "DC motors", "Κινητήρες DC", "lesson"),
 (["3.12"], "84–98", "Losses, maintenance, starter-generator", "Απώλειες, συντήρηση, starter-generator", "lesson"),
 (["3.15"], "1–12", "Transformers: construction and turns ratio", "Μετασχηματιστές: κατασκευή και λόγος σπειρών", "lesson"),
 (["3.15"], "13–30", "Transformer losses, three-phase, autotransformer", "Απώλειες, τριφασικά, αυτομετασχηματιστής", "lesson"),
 (["3.17"], "1–30", "AC generators", "Γεννήτριες AC", "lesson"),
 (["3.18"], "1–32", "AC motors", "Κινητήρες AC", "lesson"),
 (["3.12", "3.15", "3.17", "3.18"], "", "Machines exercises", "Ασκήσεις μηχανών", "exercises"),
 (["3.12", "3.15", "3.17", "3.18"], "", "Test 4: machines", "Τεστ 4: μηχανές", "test"),
 (list(TOPICS), "", "Mock exam 1", "Mock exam 1", "test"),
]
# Extra "going deeper" pages that belong to no single lesson: (id, title EN, title EL, related topics). File: deep/<id>.md
EXTRAS = [
 ("maxwell", "Maxwell's equations", "Οι εξισώσεις του Maxwell", ["3.02", "3.10", "3.11", "3.13", "3.15"]),
 ("em-poynting", "Where the energy really flows: the Poynting vector", "Πού ρέει η ενέργεια: το διάνυσμα Poynting", ["3.03", "3.08", "3.13"]),
 ("em-skin", "Skin effect, eddy currents and eddy-current NDT", "Επιδερμικό φαινόμενο, δινορρεύματα και έλεγχος NDT", ["3.11", "3.13", "3.15"]),
 ("em-hysteresis", "Ferromagnetism and the hysteresis loop", "Σιδηρομαγνητισμός και βρόχος υστέρησης", ["3.10", "3.15"]),
 ("em-paschen", "Arcing at altitude: Paschen's law", "Τόξα σε ύψος: ο νόμος του Paschen", ["3.02", "3.03"]),
 ("em-lightning", "Lightning strikes on aircraft", "Κεραυνός σε αεροσκάφος", ["3.02", "3.11"]),
 ("em-antennas", "Antennas and radar", "Κεραίες και ραντάρ", ["3.13"]),
 ("em-tdr", "Transmission lines and finding wire faults (TDR)", "Γραμμές μεταφοράς και εντοπισμός βλαβών (TDR)", ["3.06", "3.14"]),
 ("em-emc", "EMI, HIRF and shielding", "EMI, HIRF και θωράκιση", ["3.11", "3.13"]),
 ("em-relativity", "Magnetism as relativistic electricity", "Ο μαγνητισμός ως σχετικιστικός ηλεκτρισμός", ["3.02", "3.10"]),
 ("em-laplace", "Solving Laplace's equation with Python", "Επίλυση της εξίσωσης Laplace με Python", ["3.02", "3.09"]),
]
PUBLISHED = {"L01", "L02", "L03", "L04", "L05", "L06"}

lessons = []
for i, (date, (topics, slides, en, el, kind)) in enumerate(zip(schedule(len(PLAN)), PLAN), 1):
    lid = f"L{i:02d}"
    lessons.append({"id": lid, "n": i, "date": date, "topics": topics, "slides": slides,
                    "unit": unit_of(topics), "title": {"en": en, "el": el}, "kind": kind,
                    "status": "published" if lid in PUBLISHED else "planned",
                    "notes": f"lessons/{lid}.md",
                    "deep": f"deep/{lid}.md" if (pathlib.Path(__file__).resolve().parent.parent / "deep" / f"{lid}.md").exists() else ""})
data = {"course": "M03", "breaks": [{"from": a, "to": b, "label": l} for a, b, l in BREAKS],
        "topics": {k: {"en": v[0], "el": v[1]} for k, v in TOPICS.items()},
        "units": {k: {"topics": v[0], "title": {"en": v[1], "el": v[2]}} for k, v in UNITS.items()},
        "lessons": lessons,
        "extras": [{"id": i, "title": {"en": en, "el": el}, "topics": t, "deep": f"deep/{i}.md"} for i, en, el, t in EXTRAS]}
out = pathlib.Path(__file__).resolve().parent.parent / "data" / "lessons.js"
out.write_text("// Generated by tools/make_lessons.py. Edit the plan there, not here.\nwindow.M3_LESSONS = " +
               json.dumps(data, ensure_ascii=False, indent=1) + ";\n", encoding="utf-8")
print("wrote", out, len(lessons), "lessons")
