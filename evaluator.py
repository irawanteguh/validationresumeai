import re
from rapidfuzz import fuzz
from collections import Counter


# =========================
# FIELD
# =========================
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


# =========================
# STOPWORDS
# =========================
STOPWORDS = {
    "dan",
    "atau",
    "dengan",
    "yang",
    "pada",
    "pasien"
}

# =========================
# CONFIG
# =========================
IGNORE_FP_IF_DOCTOR_EMPTY = True

# =========================
# SAFE TEXT
# =========================
def safe_text(x):
    return x if isinstance(x, str) else ""


# =========================
# NORMALIZE
# =========================
def normalize(text):

    if text is None:
        return ""

    text = text.lower()

    text = re.sub(
        r"[^\w\s:/,;\-\n%()]",
        "",
        text
    )

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n+", "\n", text)

    return text.strip()


# =========================
# CLEAN TEXT
# =========================
def clean_text(text):

    text = safe_text(text)

    if not text:
        return ""

    text = normalize(text)

    # hapus (+) dan (-)
    text = re.sub(r"\(\+\)|\(\-\)", " ", text)

    # hapus simbol + -
    text = re.sub(r"[+-]", " ", text)

    # hapus kurung kosong
    text = re.sub(r"\(\s*\)", " ", text)

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n+", "\n", text)

    return text.strip()


# =========================
# TOKENIZE
# =========================
def tokenize(text):

    text = clean_text(text)

    # pecah vital sign jadi token sendiri
    text = re.sub(
        r"(gcs\s*:|tekanan darah\s*:|frekuensi nadi\s*:|frekuensi napas\s*:|suhu\s*:|saturasi\s*:|bb\s*/\s*tb\s*:)",
        r"|\1",
        text,
        flags=re.I
    )

    # split tambahan untuk istilah medis
    tokens = re.split(
        r"[\n,;|]+|\s+(?:dan|serta|disertai)\s+",
        text
    )

    cleaned = set()

    for t in tokens:

        t = t.strip()

        # hapus bullet
        t = re.sub(r"^[\-\*\•]+", "", t).strip()

        # normalisasi spasi
        t = re.sub(r"\s+", " ", t)

        if (
            not t
            or t.lower() in STOPWORDS
            or len(t) <= 2
        ):
            continue

        cleaned.add(t)

    return cleaned


# =========================
# SIMILARITY
# =========================
def is_similar(a, b, threshold=85):

    a = a.strip()
    b = b.strip()

    if not a or not b:
        return False

    if a == b:
        return True

    score = max(
        fuzz.ratio(a, b),
        fuzz.token_sort_ratio(a, b),
        fuzz.token_set_ratio(a, b)
    )

    return score >= threshold


# =========================
# MATCH ENGINE DETAIL
# =========================
def evaluate_pair_detail(dokter, ai):

    dokter_tokens = tokenize(dokter)
    ai_tokens = tokenize(ai)

    matched = []
    fp = []
    fn = []

    used_ai = set()

    # =====================================
    # IGNORE FP
    # dokter kosong tapi AI isi
    # =====================================
    if (
        IGNORE_FP_IF_DOCTOR_EMPTY
        and not dokter_tokens
        and ai_tokens
    ):

        return matched, [], fn

    # =====================================
    # MATCH ENGINE
    # =====================================
    for d in dokter_tokens:

        best_match = None
        best_score = 0

        for a in ai_tokens:

            if a in used_ai:
                continue

            score = max(
                fuzz.ratio(d, a),
                fuzz.token_sort_ratio(d, a),
                fuzz.token_set_ratio(d, a)
            )

            if score > best_score:

                best_score = score
                best_match = a

        # threshold
        if best_match and best_score >= 85:

            matched.append((d, best_match))
            used_ai.add(best_match)

        else:
            fn.append(d)

    # =====================================
    # FP
    # =====================================
    for a in ai_tokens:

        if a not in used_ai:
            fp.append(a)

    return matched, fp, fn


# =========================
# COUNT WRAPPER
# =========================
def evaluate_pair(dokter, ai):

    matched, fp, fn = evaluate_pair_detail(dokter, ai)

    return len(matched), len(fp), len(fn)


# =========================
# METRICS
# =========================
def calculate_metrics(TP, FP, FN):

    precision = TP / (TP + FP) if (TP + FP) else 0

    recall = TP / (TP + FN) if (TP + FN) else 0

    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0
    )

    return precision, recall, f1


# =========================
# MAIN EVALUATION ENGINE
# =========================
def evaluate_dataset(data, debug_sample=3):

    results = {}
    details = {}

    fp_counter = {
        f: Counter() for f in FIELDS
    }

    fn_counter = {
        f: Counter() for f in FIELDS
    }

    # init
    for field in FIELDS:

        results[field] = {
            "TP": 0,
            "FP": 0,
            "FN": 0
        }

        details[field] = []

    # loop data
    for row in data:

        for field in FIELDS:

            dokter_val = safe_text(
                row.get(f"dokter_{field}")
            )

            ai_val = safe_text(
                row.get(f"ai_{field}")
            )

            matched, fp, fn = evaluate_pair_detail(
                dokter_val,
                ai_val
            )

            TP = len(matched)
            FP = len(fp)
            FN = len(fn)

            results[field]["TP"] += TP
            results[field]["FP"] += FP
            results[field]["FN"] += FN

            fp_counter[field].update(fp)
            fn_counter[field].update(fn)

            # simpan sample error
            if (
                (fp or fn)
                and len(details[field]) < debug_sample
            ):

                details[field].append({

                    "episode_id":
                        row.get("episode_id"),

                    "doctor_preview":
                        dokter_val,

                    "ai_preview":
                        ai_val,

                    "matched":
                        matched,

                    "missing_fn":
                        fn,

                    "extra_fp":
                        fp,
                })

    # =========================
    # FINAL RESULT
    # =========================
    final_results = {}

    TP_total = 0
    FP_total = 0
    FN_total = 0

    for field in FIELDS:

        TP = results[field]["TP"]
        FP = results[field]["FP"]
        FN = results[field]["FN"]

        p, r, f1 = calculate_metrics(
            TP,
            FP,
            FN
        )

        final_results[field] = {

            "TP": TP,
            "FP": FP,
            "FN": FN,

            "precision": p,
            "recall": r,
            "f1": f1,

            "top_fp":
                fp_counter[field].most_common(5),

            "top_fn":
                fn_counter[field].most_common(5),

            "sample":
                details[field]
        }

        TP_total += TP
        FP_total += FP
        FN_total += FN

    # overall
    p_total, r_total, f1_total = calculate_metrics(
        TP_total,
        FP_total,
        FN_total
    )

    final_results["overall"] = {

        "TP": TP_total,
        "FP": FP_total,
        "FN": FN_total,

        "precision": p_total,
        "recall": r_total,
        "f1": f1_total
    }

    return final_results