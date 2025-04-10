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

# City coordinates
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
        bayi_adi = st.text_input("🏢 Bayi Adı", placeholder="Örn: Konya Merkez")
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

# Handling user inputs for teams and team members
if "team_members" not in st.session_state:
    st.session_state.team_members = {}

with st.sidebar:
    st.header("👷‍♂️ Ekip Üyeleri")
    for i in range(ekip_sayisi):
        team_name = f"Ekip {i+1}"
        team_members = st.text_area(f"{team_name} Üyeleri", placeholder="Adları virgülle ayırarak girin")
        st.session_state.team_members[team_name] = team_members.split(",") if team_members else []

st.divider()

# Display the map and the calculated distances between the cities
if st.session_state.girisler:
    st.subheader("📋 Montaj Planı")
    df = pd.DataFrame(st.session_state.girisler)

    ekipler = df["Ekip"].unique()
    for ekip in ekipler:
        st.markdown(f"### 👷 {ekip} - Ekip Üyeleri: {', '.join(st.session_state.team_members.get(ekip, []))}")
        ekip_df = df[df["Ekip"] == ekip].reset_index(drop=True)

        # Add a delete button for each row
        delete_buttons = []
        for i in range(len(ekip_df)):
            delete_button = st.button(f"❌ Sil", key=f"delete_{ekip}_{i}")
            if delete_button:
                st.session_state.girisler.remove(ekip_df.iloc[i].to_dict())

        # Update DataFrame and display the table without the deleted rows
        ekip_df = pd.DataFrame(st.session_state.girisler)
        st.dataframe(ekip_df.drop(columns=["İş Tanımı"]), use_container_width=True)

        # Calculate and display other details (distance, cost, etc.)
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

        st.markdown(f"**🧭 Toplam Mesafe:** {toplam_mesafe:.1f} km")
        st.markdown(f"**⛽ Yakıt Maliyeti:** {yakit_maliyeti:,.2f} TL")
        st.markdown(f"**🛠️ İşçilik Maliyeti:** {iscilik_maliyeti:,.2f} TL")
        st.markdown(f"**💰 Toplam Maliyet:** {toplam_maliyet:,.2f} TL")

        st.markdown("📍 Rota Haritası")

        # If the user has provided a bayi name, geocode it
        if bayi_adi:
            geocode_result = gmaps.geocode(bayi_adi)
            if geocode_result:
                bayi_koordinatlari = geocode_result[0]['geometry']['location']
                if bayi_koordinatlari:
                    m = folium.Map(location=sehir_koordinatlari[baslangic_sehri], zoom_start=6)
                    folium.Marker(
                        [bayi_koordinatlari['lat'], bayi_koordinatlari['lng']],
                        popup=bayi_adi,
                        icon=folium.Icon(color="red")
                    ).add_to(m)
                    st.markdown(f"🏢 Bayi {bayi_adi} haritada işaretlendi.")

                    # Get directions with alternatives
                    directions_bayi = gmaps.directions(baslangic_sehri, bayi_adi, mode="driving", alternatives=True)
                    
                    for route in directions_bayi:
                        steps = route['legs'][0]['steps']
                        route_coords = [(step['end_location']['lat'], step['end_location']['lng']) for step in steps]
                        
                        # For each route, highlight it in different colors
                        if "toll" in route['legs'][0]:
                            toll_route = folium.PolyLine(route_coords, color="red", weight=4, opacity=0.7).add_to(m)
                        else:
                            free_route = folium.PolyLine(route_coords, color="green", weight=4, opacity=0.7).add_to(m)

                        # Add step information
