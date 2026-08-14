import streamlit as st
import sqlite3
import os
import wave
import math
import numpy as np
from datetime import datetime
import soundfile as sf

# =========================
# PATHS
# =========================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_PATH = os.path.join(BASE_DIR, "database", "consultbae.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "app", "uploads")

os.makedirs(UPLOAD_DIR, exist_ok=True)


# =========================
# DATABASE
# =========================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audio_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            audio_path TEXT NOT NULL,
            duration REAL,
            sample_rate INTEGER,
            bitrate REAL,
            loudness REAL,
            submitted_at TEXT
        )
    """)

    conn.commit()
    conn.close()


# =========================
# AUDIO ANALYSIS
# =========================
def analyze_audio(file_path):

    # Read audio
    audio_data, sample_rate = sf.read(file_path)

    # Duration
    duration = len(audio_data) / sample_rate

    # File size for approximate bitrate
    file_size = os.path.getsize(file_path)

    bitrate = (
        (file_size * 8) / duration / 1000
        if duration > 0 else 0
    )

    # RMS loudness in dBFS
    audio_array = np.asarray(audio_data, dtype=float)

    rms = np.sqrt(np.mean(audio_array ** 2))

    if rms > 0:
        loudness = 20 * math.log10(rms)
    else:
        loudness = -100.0

    return duration, sample_rate, bitrate, loudness

# =========================
# SAVE SUBMISSION
# =========================
def save_submission(
    name,
    phone,
    audio_path,
    duration,
    sample_rate,
    bitrate,
    loudness
):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO audio_submissions
        (
            name,
            phone,
            audio_path,
            duration,
            sample_rate,
            bitrate,
            loudness,
            submitted_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        name,
        phone,
        audio_path,
        duration,
        sample_rate,
        bitrate,
        loudness,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()


# =========================
# STREAMLIT UI
# =========================
init_db()

st.set_page_config(
    page_title="Audio Collection App",
    page_icon="🎙️",
    layout="wide"
)

st.title("🎙️ Mini Audio Collection App")

page = st.sidebar.radio(
    "Navigation",
    ["Submit Audio", "View Submissions"]
)


# =========================
# PAGE 1
# =========================
if page == "Submit Audio":

    st.header("Submit Audio Sample")

    name = st.text_input("Name")

    phone = st.text_input("Phone Number")

    audio_file = st.file_uploader(
        "Upload Audio",
        type=["wav"]
    )

    if audio_file is not None:

        st.audio(audio_file)

        if st.button("Submit Audio"):

            if not name.strip():
                st.error("Please enter name.")

            elif not phone.strip():
                st.error("Please enter phone number.")

            else:

                timestamp = datetime.now().strftime(
                    "%Y%m%d_%H%M%S"
                )

                safe_phone = "".join(
                    c for c in phone if c.isdigit()
                )

                filename = (
                    f"{safe_phone}_{timestamp}_{audio_file.name}"
                )

                file_path = os.path.join(
                    UPLOAD_DIR,
                    filename
                )

                with open(file_path, "wb") as f:
                    f.write(audio_file.getbuffer())

                try:

                    duration, sample_rate, bitrate, loudness = (
                        analyze_audio(file_path)
                    )

                    save_submission(
                        name.strip(),
                        phone.strip(),
                        file_path,
                        duration,
                        sample_rate,
                        bitrate,
                        loudness
                    )

                    st.success(
                        "Audio submitted successfully!"
                    )

                    col1, col2, col3, col4 = st.columns(4)

                    col1.metric(
                        "Duration",
                        f"{duration:.2f} sec"
                    )

                    col2.metric(
                        "Sample Rate",
                        f"{sample_rate} Hz"
                    )

                    col3.metric(
                        "Bitrate",
                        f"{bitrate:.2f} kbps"
                    )

                    if loudness is not None:
                        col4.metric(
                            "Loudness",
                            f"{loudness:.2f} dBFS"
                        )
                    else:
                        col4.metric(
                            "Loudness",
                            "N/A"
                        )

                except Exception as e:

                    st.error(
                        f"Audio processing error: {e}"
                    )


# =========================
# PAGE 2
# =========================
elif page == "View Submissions":

    st.header("Audio Submissions")

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            name,
            phone,
            audio_path,
            duration,
            sample_rate,
            bitrate,
            loudness,
            submitted_at
        FROM audio_submissions
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    if not rows:

        st.info(
            "No audio submissions available."
        )

    else:

        for row in rows:

            (
                submission_id,
                name,
                phone,
                audio_path,
                duration,
                sample_rate,
                bitrate,
                loudness,
                submitted_at
            ) = row

            with st.container(border=True):

                st.subheader(
                    f"{name} — {phone}"
                )

                st.caption(
                    f"Submission ID: {submission_id} | "
                    f"Submitted: {submitted_at}"
                )

                col1, col2, col3, col4 = st.columns(4)

                col1.metric(
                    "Duration",
                    f"{duration:.2f} sec"
                )

                col2.metric(
                    "Sample Rate",
                    f"{sample_rate} Hz"
                )

                col3.metric(
                    "Bitrate",
                    f"{bitrate:.2f} kbps"
                )

                if loudness is not None:

                    col4.metric(
                        "Loudness",
                        f"{loudness:.2f} dBFS"
                    )

                else:

                    col4.metric(
                        "Loudness",
                        "N/A"
                    )

                if os.path.exists(audio_path):

                    with open(audio_path, "rb") as f:
                        audio_bytes = f.read()

                    st.audio(
                        audio_bytes,
                        format="audio/wav"
                    )

                else:

                    st.warning(
                        "Audio file not found."
                    )