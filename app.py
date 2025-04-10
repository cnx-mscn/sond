import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic
import googlemaps

# Google Maps API key
gmaps = googlemaps.Client(key="AIzaSyDwQVuPcON3rGSibcBrwhxQvz4HLTpF9Ws")

st.set_page_config("Montaj Rota Planlayıcı", layout="wide")
st.title("🛠️ Montaj Rota Planlayıcı ve Maliyet Hesaplayıcı")

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

with st.sidebar:
    st.header("⚙️ Genel Ayarlar")
    ekip_sayisi = st.number_input("Ekip Sayısı", 1, 10, 2)
    yakit_tuketim = st.number_input("Araç Yakıt Tüketimi (L/100km)", 4.0, 20.0, 8.0)
    benzin_fiyati = st.number_input("Benzin Litre Fiyatı (TL)", 10.0, 100.0, 43.50)
    iscilik_saat_ucreti = st.number_input("İşçilik Saatlik Ücreti (TL)", 50, 1000, 150)
    baslangic_sehri = st.selectbox("Yola Çıkılacak Şehir", options=sehir_listesi, index=sehir_listesi.index("Gebze"))

st.subheader("➕ Şehir ve İş Ekleme")
with st.form("sehir_form"):
    col1, col2 = st.columns(2)
    with col1:
        secilen_sehir = st.selectbox("📍 Şehir Seç", options=sehir_listesi)
        secilen_ekip = st.selectbox("👷 Ekip Seç", [f"Ekip {i+1}" for i in range(ekip_sayisi)])
        montaj_suresi = st.number_input("Montaj Süresi (saat)", 1, 72, 4)
    with col2:
        bayi_adi = st.text_input("🏢 Bayi Adı (Adres)", placeholder="Örn: Konya Merkez")
        is_tanimi = st.text_area("📝 İş Tanımı", height=100)
        ek_maliyet = st.number_input("Ekstra Maliyet (TL)", 0, 100000, 0)

    gonder_btn = st.form_submit_button("✅ Şehri Ekle")

    if gonder_btn:
        if secilen_sehir and secilen_ekip:
            veri = {
                "Ekip": secilen_ekip,
                "Şehir": secilen_sehir,
                "Montaj Süresi": montaj_suresi,
                "Bayi": bayi_adi,
                "İş Tanımı": is_tanimi,
                "Ek Maliyet": ek_maliyet
            }
            st.session_state.girisler.append(veri)
            st.success(f"{secilen_sehir} şehri {secilen_ekip} için eklendi.")

st.divider()

# Display the map and the calculated distances between the cities
if st.session_state.girisler:
    st.subheader("📋 Montaj Planı")
    df = pd.DataFrame(st.session_state.girisler)

    ekipler = df["Ekip"].unique()
    for ekip in ekipler:
        st.markdown(f"### 👷 {ekip}")
        ekip_df = df[df["Ekip"] == ekip].reset_index(drop=True)

        rota = [baslangic_sehri] + ekip_df["Şehir"].tolist()
        toplam_mesafe = 0
        yakit_maliyeti = 0
        mesafe_listesi = []

        for i in range(len(rota)-1):
            konum1 = sehir_koordinatlari[rota[i]]
            konum2 = sehir_koordinatlari[rota[i+1]]
            mesafe = geodesic(konum1, konum2).km
            mesafe_listesi.append(f"{rota[i]} → {rota[i+1]} = {mesafe:.1f} km")
            toplam_mesafe += mesafe
            yakit_maliyeti += (mesafe * yakit_tuketim / 100) * benzin_fiyati

        toplam_sure = ekip_df["Montaj Süresi"].sum()
        diger_maliyet = ekip_df["Ek Maliyet"].sum()
        iscilik_maliyeti = toplam_sure * iscilik_saat_ucreti
        toplam_maliyet = iscilik_maliyeti + yakit_maliyeti + diger_maliyet

        ekip_df["İşçilik Maliyeti"] = ekip_df["Montaj Süresi"] * iscilik_saat_ucreti
        ekip_df["Toplam Satır Maliyeti"] = ekip_df["İşçilik Maliyeti"] + ekip_df["Ek Maliyet"]

        st.dataframe(ekip_df.drop(columns=["İş Tanımı"]), use_container_width=True)

        with st.expander("📍 Mesafeler Arası Detaylar"):
            for m in mesafe_listesi:
                st.markdown(f"- {m}")

        st.markdown(f"**🧭 Toplam Mesafe:** {toplam_mesafe:.1f} km")
        st.markdown(f"**⛽ Yakıt Maliyeti:** {yakit_maliyeti:,.2f} TL")
        st.markdown(f"**🛠️ İşçilik Maliyeti:** {iscilik_maliyeti:,.2f} TL")
        st.markdown(f"**💰 Toplam Maliyet:** {toplam_maliyet:,.2f} TL")

        # Check if the Bayi address is not empty
        if bayi_adi:
            # Get route using Google Maps Directions API
            directions = gmaps.directions(baslangic_sehri, bayi_adi, mode="driving")

            # Create a map centered on the starting city
            m = folium.Map(location=sehir_koordinatlari[baslangic_sehri], zoom_start=6)

            # Add directions as a polyline on the map
            for step in directions[0]['legs'][0]['steps']:
                folium.Marker([step['end_location']['lat'], step['end_location']['lng']], 
                              popup=step['html_instructions']).add_to(m)

            # Add markers for the starting and destination cities
            folium.Marker(
                sehir_koordinatlari[baslangic_sehri],
                popup=baslangic_sehri,
                tooltip="Başlangıç Şehri"
            ).add_to(m)

            folium.Marker(
                directions[0]['legs'][0]['end_address'],
                popup=bayi_adi,
                tooltip="Bayi Adresi"
            ).add_to(m)

            # Display map
            st_folium(m, width=700, height=400)

else:
    st.info("Henüz şehir girilmedi.")
