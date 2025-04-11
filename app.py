import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import googlemaps

# Google Maps API
gmaps = googlemaps.Client(key="AIzaSyDwQVuPcON3rGSibcBrwhxQvz4HLTpF9Ws")  # Buraya kendi API anahtarını gir

st.set_page_config("Montaj Rota Planlayıcı", layout="wide")
st.title("🛠️ Montaj Rota Planlayıcı")

# Veriler
if "sehirler" not in st.session_state:
    st.session_state.sehirler = []

if "ekipler" not in st.session_state:
    st.session_state.ekipler = {"Ekip 1": []}

if "aktif_ekip" not in st.session_state or st.session_state.aktif_ekip not in st.session_state.ekipler:
    st.session_state.aktif_ekip = "Ekip 1"

# Sidebar - Ekip Bilgileri
with st.sidebar:
    st.header("👷‍♂️ Ekip Bilgileri")
    ekip_adi = st.text_input("Yeni Ekip Adı", "")
    if st.button("➕ Yeni Ekip Oluştur") and ekip_adi:
        if ekip_adi not in st.session_state.ekipler:
            st.session_state.ekipler[ekip_adi] = []
            st.session_state.aktif_ekip = ekip_adi
            st.success(f"{ekip_adi} oluşturuldu")
        else:
            st.warning("Bu ekip zaten var.")

    aktif_ekip = st.selectbox("Ekip Seç", list(st.session_state.ekipler.keys()))
    st.session_state.aktif_ekip = aktif_ekip

    st.subheader("👥 Ekip Üyeleri")
    yeni_uye = st.text_input("Yeni Üye Ekle", key="uye_ekle")
    if st.button("Üye Ekle"):
        if yeni_uye and yeni_uye not in st.session_state.ekipler[aktif_ekip]:
            st.session_state.ekipler[aktif_ekip].append(yeni_uye)
    for idx, uye in enumerate(st.session_state.ekipler[aktif_ekip]):
        col1, col2 = st.columns([4, 1])
        col1.write(uye)
        if col2.button("❌", key=f"uye_sil_{idx}"):
            st.session_state.ekipler[aktif_ekip].pop(idx)
            st.experimental_rerun()

# Şehir Girişi
st.header("📍 Gidilecek Şehir Ekle")
with st.form("sehir_form"):
    sehir_adi = st.text_input("Şehir veya Bayi Adı")
    onem = st.slider("Önem Derecesi", 1, 5, 3)
    secilen_ekip = st.selectbox("Ekip Ata", list(st.session_state.ekipler.keys()))
    montaj_suresi = st.number_input("Montaj Süresi (saat)", 1, 48, 4)
    ek_maliyet = st.number_input("Ekstra Maliyet (TL)", 0, 10000, 0)
    gonder = st.form_submit_button("➕ Şehri Ekle")

    if gonder:
        try:
            sonuc = gmaps.geocode(sehir_adi)
            if not sonuc:
                st.error("Şehir/Bayi adı bulunamadı.")
            else:
                konum = sonuc[0]["geometry"]["location"]
                st.session_state.sehirler.append({
                    "sehir": sehir_adi,
                    "ekip": secilen_ekip,
                    "konum": konum,
                    "onem": onem,
                    "montaj_suresi": montaj_suresi,
                    "ek_maliyet": ek_maliyet
                })
                st.success(f"{sehir_adi} başarıyla eklendi.")
        except Exception as e:
            st.error("Konum bilgisi alınamadı. API anahtarı veya bağlantı sorunu olabilir.")

# Şehir Listesi
st.header("📋 Şehir Listesi (Önem Sırasına Göre)")
for i, veri in enumerate(sorted(st.session_state.sehirler, key=lambda x: -x["onem"])):
    col1, col2 = st.columns([9, 1])
    with col1:
        st.markdown(f"**{i+1}. {veri['sehir']}** | Ekip: {veri['ekip']} | Önem: {veri['onem']} ⭐ | Süre: {veri['montaj_suresi']} saat | Maliyet: {veri['ek_maliyet']} TL")
    with col2:
        if st.button("❌", key=f"sil_{i}"):
            st.session_state.sehirler.pop(i)
            st.experimental_rerun()

# Harita
st.header("🗺️ Rota Haritası")
if st.session_state.sehirler:
    merkez = st.session_state.sehirler[0]['konum']
    harita = folium.Map(location=[merkez['lat'], merkez['lng']], zoom_start=6)

    sirali_sehirler = sorted(st.session_state.sehirler, key=lambda x: -x["onem"])

    for i in range(len(sirali_sehirler)-1):
        baslangic = sirali_sehirler[i]['konum']
        bitis = sirali_sehirler[i+1]['konum']
        yol = gmaps.directions(
            (baslangic['lat'], baslangic['lng']),
            (bitis['lat'], bitis['lng']),
            mode="driving"
        )
        if yol:
            steps = yol[0]['legs'][0]['steps']
            rota_coords = [(step['end_location']['lat'], step['end_location']['lng']) for step in steps]
            folium.PolyLine(rota_coords, color="blue", weight=4).add_to(harita)

    for i, sehir in enumerate(sirali_sehirler):
        folium.Marker(
            [sehir['konum']['lat'], sehir['konum']['lng']],
            popup=f"{i+1}. {sehir['sehir']} ({sehir['ekip']})",
            tooltip=f"{i+1}"
        ).add_to(harita)

    st_folium(harita, width=700, height=500)
else:
    st.info("Henüz rota oluşturulmadı.")
