from datetime import datetime
import os
import time

from db import fetch_data
from evaluator import evaluate_dataset


# ====================================
# COLOR
# ====================================
GREEN  = "\033[92m"
CYAN   = "\033[96m"
YELLOW = "\033[93m"
RED    = "\033[91m"
RESET  = "\033[0m"
BOLD   = "\033[1m"


# ====================================
# FIELD
# ====================================
FIELDS = [
    "keluhan",
    "gejala",
    "riwayatps",
    "riwayatpd",
    "status",
    "indikasi",
    "vital",
    "kontrol",
    "expertise",
    "instruksi"
]


# ====================================
# STATE (TREND MEMORY)
# ====================================
PREV = {
    "field": {},
    "overall": {},
    "meta": {}
}


# ====================================
# TIME
# ====================================
def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ====================================
# LOG
# ====================================
def log(message, color=CYAN):
    print(f"{color}[{now()}]{RESET} {BOLD}{message}{RESET}")


# ====================================
# CLEAR SCREEN
# ====================================
def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


# ====================================
# FIXED TREND
# ====================================
def trend_fixed(new, old, width=10):

    if old is None:
        txt = "• 0.00"
        return f"{YELLOW}{txt:<{width}}{RESET}"

    diff = round(new - old, 2)

    if diff > 0:
        txt = f"⬆ {diff:.2f}"
        return f"{GREEN}{txt:<{width}}{RESET}"

    elif diff < 0:
        txt = f"⬇ {abs(diff):.2f}"
        return f"{RED}{txt:<{width}}{RESET}"

    else:
        txt = "• 0.00"
        return f"{YELLOW}{txt:<{width}}{RESET}"


# ====================================
# MATCHED
# ====================================
def print_matched(matched):

    if not matched:
        print("  -")
        return

    for m in matched:

        print("  --------------------------------")

        if isinstance(m, dict):

            print(f"  ✓ DOCTOR : {m.get('doctor', '-')}")
            print(f"    AI     : {m.get('ai', '-')}")
            print(f"    SCORE  : {m.get('score', '-')}")

        elif isinstance(m, tuple):

            doctor = m[0] if len(m) > 0 else "-"
            ai = m[1] if len(m) > 1 else "-"

            print(f"  ✓ DOCTOR : {doctor}")
            print(f"    AI     : {ai}")

        else:
            print(f"  ✓ {str(m)}")


# ====================================
# MATCH DETAIL
# ====================================
def print_match_detail(field_name, r):

    if not r.get("sample"):
        return

    print("\n" + "=" * 120)

    log(f"FIELD : {field_name.upper()}", CYAN)

    print("=" * 120)

    for s in r["sample"]:

        print("\n" + "*" * 120)

        log(f"EPISODE ID : {s['episode_id']}", CYAN)

        print()

        print(f"{GREEN}{BOLD}DOCTOR{RESET}")
        print(f"  {s.get('doctor_preview', '-')}")

        print()

        print(f"{YELLOW}{BOLD}AI{RESET}")
        print(f"  {s.get('ai_preview', '-')}")

        print()

        print(f"{CYAN}{BOLD}MATCHED{RESET}")

        print_matched(s.get("matched", []))

        print()

        print(f"{RED}{BOLD}FN (Missing){RESET}")

        missing = s.get("missing_fn", [])

        if missing:
            for item in missing:
                print(f"  ✗ {item}")
        else:
            print("  -")

        print()

        print(f"{YELLOW}{BOLD}FP (Extra){RESET}")

        extra = s.get("extra_fp", [])

        if extra:
            for item in extra:
                print(f"  + {item}")
        else:
            print("  -")

        print("*" * 120)


# ====================================
# SUMMARY
# ====================================
def print_summary(result, total_data):

    print("\n" + "=" * 120)

    log("SUMMARY FIELD", CYAN)

    print("=" * 120)

    print(
        f"{'FIELD':12} | "
        f"{'PRECISION':19} | "
        f"{'RECALL':19} | "
        f"{'F1 SCORE':19}"
    )

    print("-" * 120)

    for field in FIELDS:

        if field not in result:

            print(
                f"{field.upper():12} | "
                f"{'NO DATA':24} | "
                f"{'NO DATA':24} | "
                f"{'NO DATA':24}"
            )

            continue

        r = result[field]

        p  = round(r["precision"] * 100, 2)
        rc = round(r["recall"] * 100, 2)
        f1 = round(r["f1"] * 100, 2)

        prev = PREV["field"].get(field)

        if prev:

            p_tr = trend_fixed(p, prev["p"])
            r_tr = trend_fixed(rc, prev["r"])
            f_tr = trend_fixed(f1, prev["f1"])

        else:

            p_tr = trend_fixed(p, None)
            r_tr = trend_fixed(rc, None)
            f_tr = trend_fixed(f1, None)

        PREV["field"][field] = {
            "p": p,
            "r": rc,
            "f1": f1
        }

        precision_text = f"{p:7.2f}% {p_tr}"
        recall_text    = f"{rc:7.2f}% {r_tr}"
        f1_text        = f"{f1:7.2f}% {f_tr}"

        print(
            f"{field.upper():12} | "
            f"{precision_text:24} | "
            f"{recall_text:24} | "
            f"{f1_text:24}"
        )

    # ====================================
    # OVERALL
    # ====================================
    o = result["overall"]

    print("\n" + "=" * 120)

    log("OVERALL", CYAN)

    print("=" * 120)

    tp = o["TP"]
    fp = o["FP"]
    fn = o["FN"]

    prev_o = PREV["overall"]

    tp_tr = trend_fixed(tp, prev_o.get("TP"))
    fp_tr = trend_fixed(fp, prev_o.get("FP"))
    fn_tr = trend_fixed(fn, prev_o.get("FN"))

    PREV["overall"] = {
        "TP": tp,
        "FP": fp,
        "FN": fn
    }

    total_tr = trend_fixed(
        total_data,
        PREV["meta"].get("total_data")
    )

    PREV["meta"]["total_data"] = total_data

    p = round(o["precision"] * 100, 2)
    r = round(o["recall"] * 100, 2)
    f = round(o["f1"] * 100, 2)

    p_tr = trend_fixed(
        p,
        PREV["meta"].get("precision")
    )

    r_tr = trend_fixed(
        r,
        PREV["meta"].get("recall")
    )

    f_tr = trend_fixed(
        f,
        PREV["meta"].get("f1")
    )

    PREV["meta"].update({
        "precision": p,
        "recall": r,
        "f1": f
    })

    print(
        f"{'METRIC':25} | "
        f"{'VALUE':15} | "
        f"{'TREND':15}"
    )

    print("-" * 120)

    print(
        f"{'Precision':25} | "
        f"{f'{p:.2f}%':15} | "
        f"{p_tr:15}"
    )

    print(
        f"{'Recall':25} | "
        f"{f'{r:.2f}%':15} | "
        f"{r_tr:15}"
    )

    print(
        f"{'F1 Score':25} | "
        f"{f'{f:.2f}%':15} | "
        f"{f_tr:15}"
    )

    print()

    print(
        f"{'TOTAL DATA':25} | "
        f"{f'{total_data:,}':15} | "
        f"{total_tr:15}"
    )

    print(
        f"{'TP (True Positive)':25} | "
        f"{f'{tp:,}':15} | "
        f"{tp_tr:15}"
    )

    print(
        f"{'FP (False Positive)':25} | "
        f"{f'{fp:,}':15} | "
        f"{fp_tr:15}"
    )

    print(
        f"{'FN (False Negative)':25} | "
        f"{f'{fn:,}':15} | "
        f"{fn_tr:15}"
    )


# ====================================
# PROBLEM EPISODE
# ====================================
def collect_problem_episodes(result):

    grouped = {}

    for field in FIELDS:

        r = result.get(field, {})

        for s in r.get("sample", []):

            fn = s.get("missing_fn", [])
            fp = s.get("extra_fp", [])

            if not fn and not fp:
                continue

            eid = s["episode_id"]

            if eid not in grouped:

                grouped[eid] = {
                    "episode_id": eid,
                    "fn": 0,
                    "fp": 0,
                    "total": 0,
                    "fields": set()
                }

            grouped[eid]["fn"] += len(fn)
            grouped[eid]["fp"] += len(fp)
            grouped[eid]["total"] += len(fn) + len(fp)

            grouped[eid]["fields"].add(field)

    rows = []

    for v in grouped.values():

        rows.append({
            "episode_id": v["episode_id"],
            "fn": v["fn"],
            "fp": v["fp"],
            "total": v["total"],
            "fields": ", ".join(sorted(v["fields"]))
        })

    return rows


# ====================================
# PRINT PROBLEM TABLE
# ====================================
def print_problem_table(rows):

    print("\n" + "=" * 120)

    log(
        "EPISODE BERMASALAH (TOP 10 SORTED BY TOTAL DESC)",
        CYAN
    )

    print("=" * 120)

    if not rows:
        print("Tidak ada episode bermasalah 🎉")
        return

    rows = sorted(
        rows,
        key=lambda x: x["total"],
        reverse=True
    )

    # ambil 10 tertinggi
    rows = rows[:10]

    print(
        f"{'EPISODE ID':15} | "
        f"{'FN':5} | "
        f"{'FP':5} | "
        f"{'TOTAL':6} | "
        f"FIELDS"
    )

    print("-" * 120)

    for r in rows:

        print(
            f"{str(r['episode_id']):15} | "
            f"{r['fn']:5} | "
            f"{r['fp']:5} | "
            f"{r['total']:6} | "
            f"{r['fields']}"
        )


# ====================================
# PER DOCTOR PERFORMANCE ANALYSIS
# ====================================
def print_doctor_performance(data):

    from collections import defaultdict

    from evaluator import (
        evaluate_pair_detail,
        calculate_metrics
    )

    # ====================================
    # CONFIG
    # ====================================
    MIN_DOC = 5

    # ====================================
    # AGGREGATE
    # ====================================
    doctor_stats = defaultdict(lambda: {

        "TP": 0,
        "FP": 0,
        "FN": 0,

        "TOTAL_DOC": 0,

        "FIELDS": defaultdict(lambda: {
            "TP": 0,
            "FP": 0,
            "FN": 0
        })
    })

    # ====================================
    # LOOP DATA
    # ====================================
    for row in data:

        doctor = (
            row.get("namadokter")
            or "UNKNOWN"
        )

        doctor = doctor.strip().upper()

        doctor_stats[doctor]["TOTAL_DOC"] += 1

        # ====================================
        # FIELD LOOP
        # ====================================
        for field in FIELDS:

            dokter_val = row.get(
                f"dokter_{field}"
            )

            ai_val = row.get(
                f"ai_{field}"
            )

            matched, fp, fn = evaluate_pair_detail(
                dokter_val,
                ai_val
            )

            TP = len(matched)
            FP = len(fp)
            FN = len(fn)

            # overall
            doctor_stats[doctor]["TP"] += TP
            doctor_stats[doctor]["FP"] += FP
            doctor_stats[doctor]["FN"] += FN

            # per field
            doctor_stats[doctor]["FIELDS"][field]["TP"] += TP
            doctor_stats[doctor]["FIELDS"][field]["FP"] += FP
            doctor_stats[doctor]["FIELDS"][field]["FN"] += FN

    # ====================================
    # BUILD RESULT
    # ====================================
    rows = []

    for doctor, stat in doctor_stats.items():

        total_doc = stat["TOTAL_DOC"]

        if total_doc < MIN_DOC:
            continue

        TP = stat["TP"]
        FP = stat["FP"]
        FN = stat["FN"]

        precision, recall, f1 = calculate_metrics(
            TP,
            FP,
            FN
        )

        # ====================================
        # WORST FIELD
        # ====================================
        worst_field = "-"
        worst_f1 = 999

        for field, fs in stat["FIELDS"].items():

            fp_, rc_, f1_ = calculate_metrics(
                fs["TP"],
                fs["FP"],
                fs["FN"]
            )

            f1_percent = f1_ * 100

            if f1_percent < worst_f1:

                worst_f1 = f1_percent
                worst_field = field.upper()

        rows.append({

            "doctor": doctor,

            "total_doc": total_doc,

            "precision": precision * 100,
            "recall": recall * 100,
            "f1": f1 * 100,

            "TP": TP,
            "FP": FP,
            "FN": FN,

            "worst_field": worst_field,
            "worst_f1": worst_f1
        })

    # ====================================
    # SORT
    # ====================================
    rows = sorted(
        rows,
        key=lambda x: x["f1"]
    )

    # ====================================
    # PRINT
    # ====================================
    print("\n" + "=" * 150)

    log(
        "PER DOCTOR PERFORMANCE ANALYSIS",
        CYAN
    )

    print("=" * 150)

    print(
        f"{'RANK':5} | "
        f"{'DOCTOR':30} | "
        f"{'DOC':6} | "
        f"{'PRECISION':10} | "
        f"{'RECALL':10} | "
        f"{'F1 SCORE':10} | "
        f"{'FP':7} | "
        f"{'FN':7} | "
        f"{'WORST FIELD':15}"
    )

    print("-" * 150)

    for idx, r in enumerate(rows, start=1):

        # ====================================
        # COLOR BASED ON F1
        # ====================================
        if r["f1"] >= 95:
            color = GREEN

        elif r["f1"] >= 90:
            color = CYAN

        elif r["f1"] >= 85:
            color = YELLOW

        else:
            color = RED

        print(
            f"{color}"
            f"{idx:<5} | "
            f"{r['doctor'][:30]:30} | "
            f"{r['total_doc']:6} | "
            f"{r['precision']:9.2f}% | "
            f"{r['recall']:9.2f}% | "
            f"{r['f1']:9.2f}% | "
            f"{r['FP']:7} | "
            f"{r['FN']:7} | "
            f"{r['worst_field']:15}"
            f"{RESET}"
        )

    # ====================================
    # WORST DOCTOR
    # ====================================
    if rows:

        worst = rows[0]

        print("\n" + "=" * 150)

        log(
            "WORST DOCTOR INSIGHT",
            RED
        )

        print("=" * 150)

        print(f"{RED}DOCTOR        : {worst['doctor']}{RESET}")

        print(f"TOTAL DOC     : {worst['total_doc']}")
        print(f"PRECISION     : {worst['precision']:.2f}%")
        print(f"RECALL        : {worst['recall']:.2f}%")
        print(f"F1 SCORE      : {worst['f1']:.2f}%")

        print(f"FP            : {worst['FP']}")
        print(f"FN            : {worst['FN']}")

        print(
            f"WORST FIELD   : "
            f"{worst['worst_field']} "
            f"({worst['worst_f1']:.2f}%)"
        )

        print()

        print("POSSIBLE CAUSE:")

        if worst["recall"] < 85:
            print("- Banyak FN / extraction miss")

        if worst["precision"] < 85:
            print("- Banyak FP / hallucination")

        if worst["worst_field"] == "INSTRUKSI":
            print("- Instruksi kemungkinan terlalu variatif")

        if worst["worst_field"] == "GEJALA":
            print("- Gejala kemungkinan ambigu / singkatan tinggi")

        print()

        print("RECOMMENDATION:")
        print("- Tambahkan preprocessing singkatan medis")
        print("- Tambahkan typo normalization")
        print("- Tambahkan training sample doctor ini")

# ====================================
# KONTROL MISSING PHRASE ANALYSIS
# ====================================
def print_kontrol_missing_phrase(data):

    from collections import defaultdict, Counter

    from evaluator import (
        evaluate_pair_detail,
        safe_text
    )

    # ====================================
    # STORAGE
    # ====================================
    missing_counter = defaultdict(Counter)

    missing_episode = defaultdict(
        lambda: defaultdict(set)
    )

    # ====================================
    # LOOP DATA
    # ====================================
    for row in data:

        doctor = (
            row.get("namadokter")
            or "UNKNOWN"
        )

        doctor = doctor.strip().upper()

        episode_id = row.get("episode_id")

        dokter_text = safe_text(
            row.get("dokter_kontrol")
        )

        ai_text = safe_text(
            row.get("ai_kontrol")
        )

        # ====================================
        # MATCH ENGINE
        # ====================================
        matched, fp, fn = evaluate_pair_detail(
            dokter_text,
            ai_text
        )

        # ====================================
        # FN = missing dari dokter
        # ====================================
        for item in fn:

            item = item.strip().lower()

            # skip terlalu pendek
            if len(item) <= 3:
                continue

            missing_counter[doctor][item] += 1

            missing_episode[doctor][item].add(
                episode_id
            )

    # ====================================
    # HEADER
    # ====================================
    print("\n" + "=" * 140)

    log(
        "KONTROL MISSING PHRASE ANALYSIS",
        CYAN
    )

    print("=" * 140)

    print(
        f"{'DOCTOR':30} | "
        f"{'MISSING PHRASE':70} | "
        f"{'TOTAL EPISODE':15}"
    )

    print("-" * 140)

    # ====================================
    # BUILD RESULT
    # ====================================
    rows = []

    for doctor, counter in missing_counter.items():

        if not counter:
            continue

        phrase, total = counter.most_common(1)[0]

        total_episode = len(
            missing_episode[doctor][phrase]
        )

        rows.append({

            "doctor": doctor,

            "phrase": phrase,

            "total_episode": total_episode
        })

    # ====================================
    # SORT BY EPISODE DESC
    # ====================================
    rows = sorted(
        rows,
        key=lambda x: x["total_episode"],
        reverse=True
    )

    # ====================================
    # PRINT RESULT
    # ====================================
    for r in rows:

        print(
            f"{r['doctor'][:30]:30} | "
            f"{r['phrase'][:70]:70} | "
            f"{r['total_episode']:15}"
        )

# ====================================
# MAIN
# ====================================
def main():

    clear_screen()

    # ====================================
    # FETCH DATA
    # ====================================
    data = fetch_data()

    total_data = len(data)

    # ====================================
    # EVALUATE
    # ====================================
    result = evaluate_dataset(data)

    # ====================================
    # DETAIL MATCH (PALING ATAS)
    # ====================================
    print("\n" + "=" * 120)

    log("DETAIL MATCH", CYAN)

    print("=" * 120)

    for field in FIELDS:

        if field not in result:
            continue

        r = result[field]

        # tampilkan hanya yg tidak perfect
        if (
            r["precision"] < 1
            or r["recall"] < 1
            or r["f1"] < 1
        ):

            print_match_detail(field, r)

    # ====================================
    # SUMMARY
    # ====================================
    print_summary(result, total_data)

    # ====================================
    # PROBLEM TABLE
    # ====================================
    problems = collect_problem_episodes(result)
    print_problem_table(problems)

    # ====================================
    # PER DOCTOR PERFORMANCE
    # ====================================
    print_doctor_performance(data)

    # ====================================
    # KONTROL MISSING PHRASE
    # ====================================
    print_kontrol_missing_phrase(data)

    # print()


# ====================================
# RUN LOOP
# ====================================
if __name__ == "__main__":

    AUTO_RUN = False

    if AUTO_RUN:

        while True:

            try:
                main()

            except Exception as e:

                print(f"{RED}ERROR:{RESET} {e}")

            time.sleep(10)

    else:
        main()