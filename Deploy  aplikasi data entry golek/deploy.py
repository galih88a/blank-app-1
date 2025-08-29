import streamlit as st
import pandas as pd
import re
from io import BytesIO
import matplotlib.pyplot as plt

st.set_page_config(page_title="Aplikasi Data Entry Golek Raijo", layout="wide")
st.title("📋 Aplikasi Data Entry Golek Raijo")

# Inisialisasi session_state dengan urutan kolom baru
if "parsed_data" not in st.session_state:
    st.session_state.parsed_data = pd.DataFrame(columns=[
        "No tiket SQM", 
        "No inet", 
        "Status real pelanggan", 
        "Nama Teknisi", 
        "Contact Person", 
        "Datek", 
        "Alamat"
    ])

# Fungsi parsing
def parse_text(raw_text):
    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
    data = {
        "No tiket SQM": "",
        "No inet": "",
        "Status real pelanggan": "",
        "Nama Teknisi": "",
        "Contact Person": "",
        "Datek": "",
        "Alamat": ""
    }
    nomor_hp = ""
    nama_pelanggan = ""

    if len(lines) >= 1:
        first_line = lines[0]
        tiket_match = re.search(r"(INC\d+)", first_line)
        if tiket_match:
            data["No tiket SQM"] = tiket_match.group(1)

        inet_match = re.search(r"\[SQM\]\s*(\d+)", first_line)
        if inet_match:
            data["No inet"] = inet_match.group(1)

        hp_match = re.search(r"(?:\+62|62)\d{8,13}", first_line)
        if hp_match:
            nomor_hp = hp_match.group(0)

        odp_match = re.search(r"(ODP[^\s]*)", raw_text, re.IGNORECASE)
        if odp_match:
            data["Datek"] = odp_match.group(1)

    if len(lines) >= 2:
        nama_line = lines[1]
        nama_pelanggan = nama_line.split("/")[0].strip()

    if nama_pelanggan or nomor_hp:
        data["Contact Person"] = f"{nama_pelanggan} ({nomor_hp})" if nomor_hp else nama_pelanggan

    if len(lines) >= 5:
        data["Alamat"] = lines[4]

    if lines:
        data["Nama Teknisi"] = lines[-1]

    return pd.DataFrame([data])


# Tabs
tab1, tab2 = st.tabs(["✍️ Data Entry", "📊 Visualisasi"])

with tab1:
    # Input textarea
    raw_input = st.text_area("Masukkan teks mentah di sini:", height=200)

    # Tombol parse
    if st.button("Parse Input"):
        if raw_input.strip():
            new_df = parse_text(raw_input)
            st.session_state.parsed_data = pd.concat([st.session_state.parsed_data, new_df], ignore_index=True)
            st.success("✅ Parsing berhasil!")
        else:
            st.warning("⚠️ Harap masukkan teks terlebih dahulu.")

    # Editor data
    if not st.session_state.parsed_data.empty:
        st.session_state.parsed_data["Hapus"] = False

        edited_df = st.data_editor(
            st.session_state.parsed_data,
            num_rows="dynamic",
            use_container_width=True
        )

        st.session_state.parsed_data = edited_df

        if st.button("🗑️ Hapus Baris Terpilih"):
            st.session_state.parsed_data = st.session_state.parsed_data[~st.session_state.parsed_data["Hapus"]].drop(columns=["Hapus"])
            st.success("✅ Baris terpilih berhasil dihapus!")

    # Tombol download sebagai Excel
    if not st.session_state.parsed_data.empty:
        text_columns = ["No tiket SQM", "No inet", "Contact Person", "Datek"]
        for col in text_columns:
            if col in st.session_state.parsed_data.columns:
                st.session_state.parsed_data[col] = st.session_state.parsed_data[col].astype(str)

        # Simpan ke Excel di memory
        output = BytesIO()
        st.session_state.parsed_data.drop(columns=["Hapus"], errors="ignore").to_excel(output, index=False)
        output.seek(0)

        st.download_button(
            label="📥 Download Excel",
            data=output,
            file_name="data_entry_sqm.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # Tombol reset
    if st.button("♻️ Reset Data"):
        st.session_state.parsed_data = pd.DataFrame(columns=[
            "No tiket SQM", 
            "No inet", 
            "Status real pelanggan", 
            "Nama Teknisi", 
            "Contact Person", 
            "Datek", 
            "Alamat"
        ])
        st.success("✅ Data berhasil direset!")


with tab2:
    if not st.session_state.parsed_data.empty:
        # Visualisasi Nama Teknisi
        st.subheader("📊 Peringkat Nama Teknisi")
        teknisi_counts = st.session_state.parsed_data["Nama Teknisi"].value_counts()

        fig, ax = plt.subplots()
        teknisi_counts.plot(kind="bar", ax=ax)
        ax.set_ylabel("Jumlah")
        ax.set_xlabel("Nama Teknisi")
        ax.set_title("Jumlah Pekerjaan per Teknisi")
        st.pyplot(fig)

        # 🔹 Tambahan: Tabel Rekap Peringkat Teknisi
        st.subheader("📋 Rekap Jumlah Tiket per Teknisi")
        rekap_teknisi = teknisi_counts.reset_index()
        rekap_teknisi.columns = ["Nama Teknisi", "Jumlah Tiket"]

        # Tambahkan total baris
        total_teknisi = pd.DataFrame([{"Nama Teknisi": "TOTAL", "Jumlah Tiket": rekap_teknisi["Jumlah Tiket"].sum()}])
        rekap_teknisi = pd.concat([rekap_teknisi, total_teknisi], ignore_index=True)

        st.dataframe(rekap_teknisi)

        # Tombol download tabel peringkat teknisi
        rekap_teknisi_output = BytesIO()
        rekap_teknisi.to_excel(rekap_teknisi_output, index=False)
        rekap_teknisi_output.seek(0)
        st.download_button(
            label="📥 Download Rekap Teknisi",
            data=rekap_teknisi_output,
            file_name="rekap_peringkat_teknisi.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Tabel Jumlah Tiket SQM
        st.subheader("📋 Jumlah Tiket SQM")
        tiket_counts = st.session_state.parsed_data["No tiket SQM"].value_counts().reset_index()
        tiket_counts.columns = ["No tiket SQM", "Jumlah"]

        # Tambahkan total
        total_tiket = pd.DataFrame([{"No tiket SQM": "TOTAL", "Jumlah": tiket_counts["Jumlah"].sum()}])
        tiket_counts = pd.concat([tiket_counts, total_tiket], ignore_index=True)

        st.dataframe(tiket_counts)

        # Download tombol
        tiket_output = BytesIO()
        tiket_counts.to_excel(tiket_output, index=False)
        tiket_output.seek(0)
        st.download_button(
            label="📥 Download Jumlah Tiket SQM",
            data=tiket_output,
            file_name="jumlah_tiket_sqm.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Tabel Jumlah Datek
        st.subheader("📋 Jumlah Datek")
        datek_counts = st.session_state.parsed_data["Datek"].value_counts().reset_index()
        datek_counts.columns = ["Datek", "Jumlah"]

        # Tambahkan total
        total_datek = pd.DataFrame([{"Datek": "TOTAL", "Jumlah": datek_counts["Jumlah"].sum()}])
        datek_counts = pd.concat([datek_counts, total_datek], ignore_index=True)

        st.dataframe(datek_counts)

        # Download tombol
        datek_output = BytesIO()
        datek_counts.to_excel(datek_output, index=False)
        datek_output.seek(0)
        st.download_button(
            label="📥 Download Jumlah Datek",
            data=datek_output,
            file_name="jumlah_datek.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("⚠️ Belum ada data untuk divisualisasikan.")
