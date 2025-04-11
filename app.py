import streamlit as st
import googlemaps
import folium
from streamlit_folium import st_folium

# Google Maps API Key
gmaps = googlemaps.Client(key="AIzaSyDwQVuPcON3rGSibcBrwhxQvz4HLTpF9Ws")  # <-- Buraya kendi Google API anahtarınızı yazın

st.set_page_config("Montaj Rota Planlayıcı", layout="wide")
st.title("🛠️ Montaj Rota Planlayıcı ve Rota Analizi")

# Session State
if "ekipler" not in st.session_state:
    st.session_state.ekipler = {}
if "aktif_ekip" not in st.session_state:
    st.session_state.aktif_ekip = None
if "sehirler" not in st.session_state:
    st.session_state.sehirler = []

# Ekip Ekleme
st.sidebar.header("👷 Ekip Yönetimi")
ekip_adi = st.text_input("Yeni Ekip Adı")
if st.button("➕ Ekip Oluştur") and ekip_adi:
    if ekip_adi not in st.session_state.ekipler:
        st.session_state.ekipler[ekip_adi] = {"members": [], "baslangic": None}
        st.session_state.aktif_ekip = ekip_adi
        st.success(f"{ekip_adi} oluşturuldu.")
    else:
        st.warning("Bu ekip zaten mevcut!")

# Aktif ekip seçimi
if st.session_state.ekipler:
    aktif_secim = st.sidebar.selectbox("Aktif Ekip Seç", list(st.session_state.ekipler.keys()))
    st.session_state.aktif_ekip = aktif_secim
else:
    st.warning("Henüz ekip oluşturulmadı. Lütfen bir ekip oluşturun.")

# Üye Ekle / Çıkar
with st.sidebar.expander("👤 Ekip Üyeleri"):
    yeni_uye = st.text_input("Yeni Üye Adı")
    if st.button("✅ Üye Ekle"):
        if yeni_uye and st.session_state.aktif_ekip:
            st.session_state.ekipler[st.session_state.aktif_ekip]["members"].append(yeni_uye)
            st.success(f"{yeni_uye} üye olarak eklendi.")
    if st.session_state.aktif_ekip:
        # Aktif ekip seçildiyse üyeler listelensin
        if "members" in st.session_state.ekipler[st.session_state.aktif_ekip]:
            for idx, uye in enumerate(st.session_state.ekipler[st.session_state.aktif_ekip]["members"]):
                col1, col2 = st.columns([5, 1])
                col1.markdown(f"- {uye}")
                if col2.button("❌", key=f"uye_sil_{idx}"):
                    st.session_state.ekipler[st.session_state.aktif_ekip]["members"].pop(idx)
                    st.experimental_rerun()
        else:
            st.warning("Bu ekip için üye bulunmamaktadır.")

# Başlangıç Noktası Seçimi
st.sidebar.subheader("🛣️ Ekip Başlangıç Noktası")
if st.session_state.aktif_ekip:
    baslangic_sehir = st.selectbox("Başlangıç Şehri", ["Seçiniz"] + [sehir['sehir'] for sehir in st.session_state.sehirler])
    if baslangic_sehir != "Seçiniz":
        st.session_state.ekipler[st.session_state.aktif_ekip]["baslangic"] = baslangic_sehir
        st.success(f"{baslangic_sehir} başlangıç noktası olarak seçildi.")

# Şehir/Bayi Ekleme
st.subheader("📍 Bayi / Şehir Ekle")
with st.form("sehir_ekle"):
    sehir_adi = st.text_input("Şehir veya Bayi Adı")
    onem = st.slider("Önem Derecesi", 1, 5, 3)
    yol_suresi = st.number_input("Yol Süresi (saat)", 1, 24, 1)
    yol_ucreti = st.number_input("Yol Ücreti (TL)", 0, 10000, 100)
    ek_maliyet = st.number_input("Ekstra Maliyet (TL)", 0, 100000, 0)
    gonder_btn = st.form_submit_button("➕ Ekle")

    if gonder_btn and st.session_state.aktif_ekip:
        try:
            sonuc = gmaps.geocode(sehir_adi)
            if not sonuc:
                st.error("Konum bulunamadı.")
            else:
                konum = sonuc[0]["geometry"]["location"]
                st.session_state.sehirler.append({
                    "sehir": sehir_adi,
                    "ekip": st.session_state.aktif_ekip,
                    "konum": konum,
                    "onem": onem,
                    "yol_suresi": yol_suresi,
                    "yol_ucreti": yol_ucreti,
                    "ek_maliyet": ek_maliyet
                })
                st.success(f"{sehir_adi} eklendi.")
        except Exception as e:
            st.error("Google API bağlantısı başar
