"""Writes data/lessons.js from the course plan below. Edit the PLAN list (title, date, status) and run:
    python tools/make_lessons.py
status: 'published' = visible with notes and exercises, 'planned' = shown greyed in the lesson log."""
import json, pathlib

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

# (date, topics, slides, title EN, title EL, kind)   kind: lesson | exercises | test
PLAN = [
 ("2026-11-30", ["3.01"], "1–14", "Introduction and electron theory", "Εισαγωγή και θεωρία ηλεκτρονίων", "lesson"),
 ("2026-12-01", ["3.02"], "1–17", "Static electricity and conduction", "Στατικός ηλεκτρισμός και αγωγή", "lesson"),
 ("2026-12-02", ["3.03"], "1–21", "Electrical terminology and SI prefixes", "Ηλεκτρική ορολογία και προθέματα SI", "lesson"),
 ("2026-12-03", ["3.04"], "1–9", "Generation of electricity + quiz A", "Παραγωγή ηλεκτρισμού + quiz Α", "lesson"),
 ("2026-12-04", ["3.05"], "1–23", "Primary cells and lead-acid batteries", "Πρωτογενή στοιχεία και μπαταρίες μολύβδου", "lesson"),
 ("2026-12-07", ["3.05"], "24–41", "NiCad, SLA, Li-ion, thermocouples, photocells", "NiCad, SLA, Li-ion, θερμοζεύγη, φωτοκύτταρα", "lesson"),
 ("2026-12-08", ["3.06"], "1–26", "Series circuits, KVL, voltage dividers", "Κυκλώματα σε σειρά, KVL, διαιρέτες τάσης", "lesson"),
 ("2026-12-09", ["3.06"], "27–45", "Parallel circuits, KCL, internal resistance", "Παράλληλα κυκλώματα, KCL, εσωτερική αντίσταση", "lesson"),
 ("2026-12-10", ["3.07"], "1–24", "Resistance, resistivity, wire sizes", "Αντίσταση, ειδική αντίσταση, διατομές καλωδίων", "lesson"),
 ("2026-12-11", ["3.07"], "25–60", "Variable resistors, Wheatstone bridge, colour code", "Μεταβλητές αντιστάσεις, γέφυρα Wheatstone, χρωματικός κώδικας", "lesson"),
 ("2026-12-14", ["3.08"], "1–13", "Work, energy and power", "Έργο, ενέργεια και ισχύς", "lesson"),
 ("2026-12-15", ["3.05", "3.06", "3.07", "3.08"], "", "DC exercises", "Ασκήσεις DC", "exercises"),
 ("2026-12-16", ["3.01", "3.02", "3.03", "3.04", "3.05", "3.06", "3.07", "3.08"], "", "Test 1: units A and B", "Τεστ 1: ενότητες Α και Β", "test"),
 ("2026-12-17", ["3.09"], "1–23", "Capacitors: function, factors, types", "Πυκνωτές: λειτουργία, παράγοντες, τύποι", "lesson"),
 ("2026-12-18", ["3.09"], "24–39", "Capacitors in circuits, RC, reactance", "Πυκνωτές σε κυκλώματα, RC, χωρητική αντίσταση", "lesson"),
 ("2026-12-21", ["3.10"], "1–23", "Magnetism and magnetic materials", "Μαγνητισμός και μαγνητικά υλικά", "lesson"),
 ("2026-12-22", ["3.10"], "24–47", "Electromagnets, hand rules, hysteresis", "Ηλεκτρομαγνήτες, κανόνες χεριού, υστέρηση", "lesson"),
 ("2026-12-23", ["3.11"], "1–27", "Induction, Lenz, inductors", "Επαγωγή, Lenz, πηνία", "lesson"),
 ("2027-01-07", ["3.09", "3.10", "3.11"], "", "Review C + test 2", "Επανάληψη Γ + τεστ 2", "test"),
 ("2027-01-08", ["3.13"], "1–25", "AC theory and AC values", "Θεωρία AC και τιμές AC", "lesson"),
 ("2027-01-11", ["3.14"], "1–15", "Impedance, series RLC", "Σύνθετη αντίσταση, RLC σε σειρά", "lesson"),
 ("2027-01-12", ["3.14"], "16–35", "Parallel AC, resonance, power factor", "Παράλληλα AC, συντονισμός, συντελεστής ισχύος", "lesson"),
 ("2027-01-13", ["3.16"], "1–18", "Filters", "Φίλτρα", "lesson"),
 ("2027-01-14", ["3.13", "3.14", "3.16"], "", "AC exercises + test 3", "Ασκήσεις AC + τεστ 3", "test"),
 ("2027-01-15", ["3.12"], "1–28", "DC generator: principle and construction", "Γεννήτρια DC: αρχή και κατασκευή", "lesson"),
 ("2027-01-18", ["3.12"], "29–46", "DC generator types, armature reaction", "Τύποι γεννητριών DC, αντίδραση τυμπάνου", "lesson"),
 ("2027-01-19", ["3.12"], "47–83", "DC motors", "Κινητήρες DC", "lesson"),
 ("2027-01-20", ["3.12"], "84–98", "Losses, maintenance, starter-generator", "Απώλειες, συντήρηση, starter-generator", "lesson"),
 ("2027-01-21", ["3.15"], "1–12", "Transformers: construction and turns ratio", "Μετασχηματιστές: κατασκευή και λόγος σπειρών", "lesson"),
 ("2027-01-22", ["3.15"], "13–30", "Transformer losses, three-phase, autotransformer", "Απώλειες, τριφασικά, αυτομετασχηματιστής", "lesson"),
 ("2027-01-25", ["3.17"], "1–30", "AC generators", "Γεννήτριες AC", "lesson"),
 ("2027-01-26", ["3.18"], "1–32", "AC motors", "Κινητήρες AC", "lesson"),
 ("2027-01-27", ["3.12", "3.15", "3.17", "3.18"], "", "Machines exercises", "Ασκήσεις μηχανών", "exercises"),
 ("2027-01-28", ["3.12", "3.15", "3.17", "3.18"], "", "Test 4: machines", "Τεστ 4: μηχανές", "test"),
 ("2027-01-29", list(TOPICS), "", "Mock exam 1", "Mock exam 1", "test"),
]
PUBLISHED = {"L01", "L02"}

lessons = []
for i, (date, topics, slides, en, el, kind) in enumerate(PLAN, 1):
    lid = f"L{i:02d}"
    lessons.append({"id": lid, "n": i, "date": date, "topics": topics, "slides": slides,
                    "title": {"en": en, "el": el}, "kind": kind,
                    "status": "published" if lid in PUBLISHED else "planned",
                    "notes": f"lessons/{lid}.md"})
data = {"course": "M03", "breaks": [{"from": "2026-12-24", "to": "2027-01-06", "label": "Christmas break"}],
        "topics": {k: {"en": v[0], "el": v[1]} for k, v in TOPICS.items()}, "lessons": lessons}
out = pathlib.Path(__file__).resolve().parent.parent / "data" / "lessons.js"
out.write_text("// Generated by tools/make_lessons.py. Edit the plan there, not here.\nwindow.M3_LESSONS = " +
               json.dumps(data, ensure_ascii=False, indent=1) + ";\n", encoding="utf-8")
print("wrote", out, len(lessons), "lessons")
