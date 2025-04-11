import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic
import googlemaps
from uuid import uuid4

# Google Maps API Key
gmaps = googlemaps.Client(key="AIzaSyDwQVuPcON3rGSibcBrwhxQvz4HLTpF9Ws")

st.set_page_config("Montaj Rota Planlayıcı", layout="wide")
st.title("🛠️ Montaj Rota Planlayıcı ve Maliyet Hesaplayıcı")

# Şehir koordinatları
sehir_koordinatlari = {
    "Gebze": (40.8028, 29.4307),
    "İstanbul": (41.0082, 28.9784),
    "Ankara": (39.9208, 32.8541),
    "İzmir": (38.4192, 27.1287),
    "Konya": (37.8746, 32.4932),
    "Bursa": (40.1956, 29.0601),
    "Adana": (37.0000, 35.3213),
    "Antalya": (36.8969, 30.7133),
    "Samsun": (41.2867, 36.33),
    "Gaziantep": (37.0662, 37.3833),
}

sehir_listesi = list(sehir_koordinatlari.keys())

if "girisler" not in st.session_state:
    st.session_state.girisler = []
if "ekipler" not in st.session_state:
    st.session_state.ekipler = {}

with st.sidebar:
    st.header("⚙️ Genel Ayarlar")
    ekip_sayisi = st.number_input("Ekip Sayısı", 1, 10, 2)
    for i in range(ekip_sayisi):
        ekip_adi = st.text_input(f"👥 Ekip {i+1} Adı", f"Ekip {i+1}")
        ekip_uyeleri = st.text_area(f"👨‍🔧 {ekip_adi} Üyeleri (virgülle ayırın)", key=f"uyeler_{i}")
        st.session_state.ekipler[ekip_adi] = ekip_uyeleri.split(",")

    yakit_tuketim = st.number_input("Araç Yakıt Tüketimi (L/100km)", 4.0, 20.0, 8.0)
    benzin_fiyati = st.number_input("Benzin Litre Fiyatı (TL)", 10.0, 100.0, 43.50)
    iscilik_saat_ucreti = st.number_input("İşçilik Saatlik Ücreti (TL)", 50, 1000, 150)
    baslangic_sehri = st.selectbox("Yola Çıkılacak Şehir", options=sehir_listesi, index=sehir_listesi.index("Gebze"))

st.subheader("➕ Şehir ve İş Ekleme")
with st.form("sehir_form"):
    col1, col2 = st.columns(2)
    with col1:
        secilen_sehir = st.selectbox("📍 Şehir Seç", options=sehir_listesi)
        secilen_ekip = st.selectbox("👷 Ekip Seç", list(st.session_state.ekipler.keys()))
        montaj_suresi = st.number_input("Montaj Süresi (saat)", 1, 72, 4)
        onem = st.slider("🔢 Önem Derecesi (1-10)", 1, 10, 5)
    with col2:
        bayi_adi = st.text_input("🏢 Bayi Adı", placeholder="Örn: Konya Merkez")
        is_tanimi = st.text_area("📝 İş Tanımı", height=100)
        ek_maliyet = st.number_input("Ekstra Maliyet (TL)", 0, 100000, 0)

    gonder_btn = st.form_submit_button("✅ Şehri Ekle")

    if gonder_btn:
        st.session_state.girisler.append({
            "id": str(uuid4()),
            "Ekip": secilen_ekip,
            "Şehir": secilen_sehir,
            "Montaj Süresi": montaj_suresi,
            "Önem": onem,
            "Bayi": bayi_adi,
            "İş Tanımı": is_tanimi,
            "Ek Maliyet": ek_maliyet
        })
        st.success(f"{secilen_sehir} şehri {secilen_ekip} için eklendi.")

if st.session_state.girisler:
    st.subheader("📋 Montaj Planı")
    for giris in st.session_state.girisler:
        st.markdown(f"#### 🏙️ {giris['Şehir']} - {giris['Ekip']} (Önem: {giris['Önem']})")
        st.markdown(f"**Bayi:** {giris['Bayi']}  ")
        st.markdown(f"**İş Tanımı:** {giris['İş Tanımı']}  ")
        st.markdown(f"**Montaj Süresi:** {giris['Montaj Süresi']} saat | **Ek Maliyet:** {giris['Ek Maliyet']} TL")
        if st.button("❌ Sil", key=giris["id"]):
            st.session_state.girisler = [g for g in st.session_state.girisler if g["id"] != giris["id"]]
            st.experimental_rerun()

    st.subheader("📍 Öneme Göre Rota Oluştur")
    for ekip, uyeler in st.session_state.ekipler.items():
        st.markdown(f"### 👷 {ekip} Üyeleri: {', '.join(uyeler)}")
        ekip_sehirler = sorted([g for g in st.session_state.girisler if g["Ekip"] == ekip], key=lambda x: -x["Önem"])
        rota = [baslangic_sehri] + [g["Şehir"] for g in ekip_sehirler]

        m = folium.Map(location=sehir_koordinatlari[baslangic_sehri], zoom_start=6)
        for i in range(len(rota)-1):
            g1 = rota[i]
            g2 = rota[i+1]
            coords1 = sehir_koordinatlari[g1]
            coords2 = sehir_koordinatlari[g2]
            folium.Marker(coords1, popup=g1, icon=folium.Icon(color='blue')).add_to(m)
            folium.Marker(coords2, popup=g2, icon=folium.Icon(color='blue')).add_to(m)

            # Google Maps Directions API ile rota çizimi
            directions = gmaps.directions(g1, g2, mode="driving")
            steps = directions[0]['legs'][0]['steps']
            route_coords = [(step['end_location']['lat'], step['end_location']['lng']) for step in steps]
            folium.PolyLine(route_coords, color="green", weight=4, opacity=0.7).add_to(m)
            folium.Marker(route_coords[-1], 
                          popup=f"Mesafe: {directions[0]['legs'][0]['distance']['text']} | Süre: {directions[0]['legs'][0]['duration']['text']}").add_to(m)

        st_folium(m, width=700, height=500)
else:
    st.info("Henüz şehir girilmedi.")
