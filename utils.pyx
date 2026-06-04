import re

def normalize(text):

    if text is None:
        return ""

    text = text.lower()

    # ====================================
    # PERTAHANKAN PEMISAH PENTING
    # ====================================
    # tetap simpan:
    # :
    # /
    # ,
    # ;
    # newline
    # -
    # %
    # ()
    # ====================================
    text = re.sub(r"[^\w\s:/,;\-\n%()]", "", text)

    # rapikan spasi
    text = re.sub(r"[ \t]+", " ", text)

    # rapikan newline berlebih
    text = re.sub(r"\n+", "\n", text)

    return text.strip()