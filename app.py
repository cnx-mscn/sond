import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import googlemaps

gmaps = googlemaps.Client(key="AIzaSyDwQVuPcON3rGSibcBrwhxQvz4HLTpF9Ws")  # Kendi API key’inizi girin

st.set_page_config("Montaj Rota Planlayıcı", layout="wide")
st.title("🛠️ Montaj Rota Planlayıcı")

# Veriler
if "sehirler" not in st.session_state:
    st.session_state.sehirler = []
if "ekipler" not in st.session_state:
    st.session_state.ekipler = {}
if "aktif_ekip" not in st.session_state:
    st.session_state.aktif_ekip = "Ekip 1"

# Sidebar - Ekip Yönetimi
with st.sidebar:
    st.header("👷‍♂️ Ekip Yönetimi")

    ekip_adi = st.text_input("Yeni Ekip Adı", "Ekip 1")
    if st.button("Ekip Oluştur"):
        if ekip_adi not in st.session_state.ekipler:
            st.session_state.ekipler[ekip_adi] = []
            st.session_state.aktif_ekip = ekip_adi
        else:
            st.warning("Bu ekip zaten var.")

    st.selectbox("Aktif Ekip", options=st.session_state.ekipler.keys(), key="aktif_ekip")

    st.text("👥 Ekip Üyeleri")
    yeni_uye = st.text_input("İsim Ekle", key="uye_ekle")
    if st.button("➕ Üye Ekle"):
        st.session_state.ekipler[st.session_state.aktif_ekip].append(yeni_uye)

    for idx, uye in enumerate(st.session_state.ekipler[st.session_state.aktif_ekip]):
        col1, col2 = st.columns([4, 1])
        col1.write(f"- {uye}")
        if col2.button("❌", key=f"uye_sil_{idx}"):
            st.session_state.ekipler[st.session_state.aktif_ekip].pop(idx)
            st.experimental_rerun()

# Şehir Girişi
st.header("📍 Gidilecek Şehir Ekle")
with st.form("sehir_form"):
    sehir_adi = st.text_input("Şehir veya Bayi Adı")
    onem = st.slider("Önem Derecesi", 1, 5, 3)
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
                    "ekip": st.session_state.aktif_ekip,
                    "konum": konum,
                    "onem": onem,
                    "montaj_suresi": montaj_suresi,
                    "ek_maliyet": ek_maliyet
                })
                st.success(f"{sehir_adi} eklendi")
        except Exception as e:
            st.error("Konum bilgisi alınamadı. API veya bağlantı sorunu olabilir.")

# Şehir Listesi
st.header("📋 Şehir Listesi")
for i, veri in enumerate(sorted(st.session_state.sehirler, key=lambda x: -x["onem"])):
    col1, col2 = st.columns([9, 1])
    with col1:
        st.markdown(f"**Bayi {i+1}: {veri['sehir']}** | Ekip: {veri['ekip']} | Önem: {veri['onem']} ⭐ | Süre: {veri['montaj_suresi']} saat | Maliyet: {veri['ek_maliyet']} TL")
    with col2:
        if st.button("❌", key=f"sil_{i}"):
            st.session_state.sehirler.pop(i)
            st.experimental_rerun()

# Harita
st.header("🗺️ Rota Haritası")
if st.session_state.sehirler:
    sirali = sorted(st.session_state.sehirler, key=lambda x: -x["onem"])
    merkez = sirali[0]['konum']
    harita = folium.Map(location=[merkez['lat'], merkez['lng']], zoom_start=6)

    for idx, veri in enumerate(sirali):
        folium.Marker(
            location=[veri["konum"]["lat"], veri["konum"]["lng"]],
            popup=f"Bayi {idx+1}: {veri['sehir']}",
            tooltip=f"{idx+1}",
            icon=folium.DivIcon(html=f"""<div style="font-size:16px;color:red;"><b>{idx+1}</b></div>""")
        ).add_to(harita)

    for i in range(len(sirali)-1):
        start = sirali[i]["konum"]
        end = sirali[i+1]["konum"]
        directions = gmaps.directions(
            (start["lat"], start["lng"]),
            (end["lat"], end["lng"]),
            mode="driving"
        )
        if directions:
            steps = directions[0]["legs"][0]["steps"]
            coords = [(step["end_location"]["lat"], step["end_location"]["lng"]) for step in steps]
            folium.PolyLine(coords, color="blue", weight=4).add_to(harita)

    st_folium(harita, width=800, height=600)
else:
    st.info("Henüz şehir girilmedi.")
