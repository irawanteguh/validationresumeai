import oracledb
from config import DB_CONFIG

# =========================================
# INIT ORACLE CLIENT (WINDOWS)
# =========================================

# oracledb.init_oracle_client(
#     lib_dir=DB_CONFIG["oracleclient"]
# )

# =========================================
# CONNECTION
# =========================================
def get_connection():

    dsn = oracledb.makedsn(
        DB_CONFIG["host"],
        DB_CONFIG["port"],
        service_name = DB_CONFIG["service_name"]
    )

    conn = oracledb.connect(
        user     = DB_CONFIG["user"],
        password = DB_CONFIG["password"],
        dsn      = dsn
    )

    return conn


# =========================================
# FETCH DATA
# =========================================
def fetch_data():
    

    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT 
            d.episode_id,
            d.dokter_id,

            (SELECT nama FROM sr01_med_dokter_ms WHERE dokter_id=d.dokter_id)namadokter,

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
            OR (show_item = 'Y' AND kontrol = 'Kontrol ulang ke POLI PENYAKIT DALAM')
            OR (show_item = 'Y' AND kontrol = 'Kontrol ulang ke POLI PARU')
            OR (show_item = 'Y' AND kontrol = 'Kontrol ulang ke POLI ANAK')
            OR (show_item = 'Y' AND kontrol = 'Kontrol ulang ke POLI JANTUNG')
            OR (show_item = 'Y' AND kontrol = 'Kontrol ulang ke POLI SARAF')
            OR (show_item = 'Y' AND kontrol = 'Kontrol ulang ke POLI KEBIDANAN')
            OR (show_item = 'Y' AND kontrol = 'Kontrol ulang ke POLI ORTHOPEDI')
            OR (show_item = 'Y' AND kontrol = 'Kontrol ulang ke POLI BEDAH UMUM')
            OR (show_item = 'Y' AND kontrol = 'Kontrol ulang ke POLI UROLOGI')
        ) ai

        JOIN (
            SELECT *
            FROM (
                SELECT 
                    s.*,
                    ROW_NUMBER() OVER (
                        PARTITION BY s.episode_id
                        ORDER BY s.created_date DESC, s.rowid DESC
                    ) rn
                FROM sr01_resume_medis s
                WHERE s.aktif in ('1','2','9')
                and   s.poli_id is null
                and   s.created_by like 'DR%'
            )
            WHERE rn = 1
        ) d
        ON d.episode_id = ai.episode_id
        where EXISTS (
                        SELECT 1
                        FROM sr01_keu_episode e
                        WHERE e.lokasi_id = '001'
                        AND e.aktif = '1'
                        AND e.jenis_episode = 'I'
                        AND e.status_episode = '55'
                        AND e.pasien_id = ai.pasien_id
                        AND e.episode_id = ai.episode_id
                    )
        AND NOT EXISTS (
        				SELECT 1
        				FROM web_co_registrasi_online_hd
        				WHERE lokasi_id='001'
        				AND show_item='1'
        				AND pasien_id=ai.pasien_id
        				AND episode_id=ai.episode_id
        			)
        -- AND ai.created_date <= TO_DATE('26-05-2026 23:59:59','DD-MM-YYYY HH24:MI:SS')
        -- AND ai.created_date >= TO_DATE('26-05-2026 23:59:59','DD-MM-YYYY HH24:MI:SS')
        --AND ai.episode_id='126053153330'
        -- AND d.dokter_id='DR. H0000000005'
    """

    cursor.execute(query)

    # =========================================
    # AMBIL NAMA KOLOM OTOMATIS
    # =========================================
    columns = [col[0].lower() for col in cursor.description]

    data = []

    # =========================================
    # DYNAMIC MAPPING
    # =========================================
    for row in cursor:

        item = {
            column: value
            for column, value in zip(columns, row)
        }

        data.append(item)

    # =========================================
    # CLOSE
    # =========================================
    cursor.close()
    conn.close()

    return data
