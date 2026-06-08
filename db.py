import oracledb
from config import DB_CONFIG

# =========================================
# ORACLE MODE (THIN MODE - LINUX SAFE)
# =========================================
# TIDAK PERLU init_oracle_client di Linux

oracledb.defaults.fetch_lobs = False  # optional optimize


# =========================================
# CONNECTION
# =========================================
def get_connection():
    try:
        dsn = oracledb.makedsn(
            DB_CONFIG["host"],
            DB_CONFIG["port"],
            service_name=DB_CONFIG["service_name"]
        )

        conn = oracledb.connect(
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            dsn=dsn
        )

        return conn

    except Exception as e:
        print(f"[DB ERROR] {e}")
        raise


# =========================================
# FETCH DATA (SAFE VERSION)
# =========================================
def fetch_data():

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = """
        SELECT 
            d.episode_id,
            d.dokter_id,
            (SELECT nama FROM sr01_med_dokter_ms WHERE dokter_id=d.dokter_id) namadokter,

            d.keluhan_utama          AS dokter_keluhan,
            d.gejala_penyerta        AS dokter_gejala,
            d.riwayat_penyakit       AS dokter_riwayatps,
            d.riwayat_penyakit_dulu  AS dokter_riwayatpd,
            d.status                 AS dokter_status,
            d.indikasi_rawat         AS dokter_indikasi,
            d.vital                  AS dokter_vital,
            d.kontrol_ulang          AS dokter_kontrol,
            d.lainnya                AS dokter_expertise,
            d.segera_dibawa_bila     AS dokter_instruksi,

            ai.keluhan               AS ai_keluhan,
            ai.gejala                AS ai_gejala,
            ai.riwayatps             AS ai_riwayatps,
            ai.riwayatpd             AS ai_riwayatpd,
            ai.status                AS ai_status,
            ai.indikasi              AS ai_indikasi,
            ai.vital                 AS ai_vital,
            ai.kontrol               AS ai_kontrol,
            ai.lainnya               AS ai_expertise,
            ai.intruksi              AS ai_instruksi

        FROM (
            SELECT *
            FROM web_co_resume_ranap_ai
            WHERE show_item ='1'
            OR (show_item = 'Y' AND kontrol LIKE 'Kontrol ulang%')
        ) ai

        JOIN (
            SELECT *
            FROM (
                SELECT 
                    s.*,
                    ROW_NUMBER() OVER (
                        PARTITION BY s.episode_id
                        ORDER BY s.created_date DESC
                    ) rn
                FROM sr01_resume_medis s
                WHERE s.aktif in ('1','2','9')
                  AND s.poli_id is null
                  AND s.created_by like 'DR%'
            )
            WHERE rn = 1
        ) d
        ON d.episode_id = ai.episode_id

        """

        cursor.execute(query)

        columns = [col[0].lower() for col in cursor.description]

        data = [
            dict(zip(columns, row))
            for row in cursor
        ]

        return data

    except Exception as e:
        print(f"[FETCH ERROR] {e}")
        return []

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()