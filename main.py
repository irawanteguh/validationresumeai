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
# MAIN
# ====================================
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