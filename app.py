import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import googlemaps

# Google Maps API
gmaps = googlemaps.Client(key="AIzaSyDwQVuPcON3rGSibcBrwhxQvz4HLTpF9Ws")

st.set_page_config("Montaj Rota Planlayıcı", layout="wide")
st.title("🛠️ Montaj Rota Planlayıcı")

# Veriler
if "sehirler" not in st.session_state:
    st.session_state.sehirler = []
if "ekipler" not in st.session_state:
    st.session_state.ekipler = {}

# Sidebar - Ekip Bilgileri
with st.sidebar:
    st.header("👷‍♂️ Ekip Bilgileri")
    ekip_adi = st.text_input("Ekip Adı", "Ekip 1")
    ekip_uyeleri = st.text_area("Ekip Üyeleri (virgülle ayır)", "Ali, Ayşe")
    if st.button("Ekip Ekle"):
        st.session_state.ekipler[ekip_adi] = ekip_uyeleri.split(",")
        st.success(f"{ekip_adi} eklendi")

# Şehir Girişi
st.header("📍 Gidilecek Şehir Ekle")
with st.form("sehir_form"):
    sehir_adi = st.text_input("Şehir veya Bayi Adı")
    onem = st.slider("Önem Derecesi", 1, 5, 3)
    secilen_ekip = st.selectbox("Ekip Seç", list(st.session_state.ekipler.keys()) or ["Ekip 1"])
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
                st.success(f"{sehir_adi} eklendi")
        except Exception as e:
            st.error("Konum bilgisi alınamadı. API veya bağlantı sorunu olabilir.")

# Şehir Listesi ve Silme
st.header("📋 Şehir Listesi")
for i, veri in enumerate(sorted(st.session_state.sehirler, key=lambda x: -x["onem"])):
    col1, col2 = st.columns([9, 1])
    with col1:
        st.markdown(f"**{veri['sehir']}** | Ekip: {veri['ekip']} | Önem: {veri['onem']} ⭐ | Süre: {veri['montaj_suresi']} saat | Maliyet: {veri['ek_maliyet']} TL")
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

    for sehir in sirali_sehirler:
        folium.Marker(
            [sehir['konum']['lat'], sehir['konum']['lng']],
            popup=f"{sehir['sehir']} ({sehir['ekip']})"
        ).add_to(harita)

    st_folium(harita, width=700, height=500)
else:
    st.info("Henüz rota oluşturulmadı.")
