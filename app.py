import streamlit as st
import folium
import googlemaps
from folium.plugins import AntPath
from streamlit_folium import st_folium

# Google Maps API Key (buraya kendi anahtarınızı eklemelisiniz)
gmaps = googlemaps.Client(key="AIzaSyDwQVuPcON3rGSibcBrwhxQvz4HLTpF9Ws")

# Şehirler ve koordinatlar
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

# Streamlit kullanıcı girişi
st.set_page_config("Rota ve Süre Hesaplayıcı", layout="wide")
st.title("🚗 Rota ve Süre Hesaplayıcı")

# Başlangıç ve varış şehirlerini seç
sehirler = list(sehir_koordinatlari.keys())
baslangic_sehri = st.selectbox("Başlangıç Şehri", options=sehirler)
varis_sehri = st.selectbox("Varış Şehri", options=sehirler)

if baslangic_sehri and varis_sehri:
    # Google Maps API ile rota almak
    route = gmaps.directions(
        baslangic_sehri,
        varis_sehri,
        mode="driving",
        departure_time="now"
    )

    if route:
        # Rota bilgilerini al
        steps = route[0]['legs'][0]['steps']
        toplam_mesafe = route[0]['legs'][0]['distance']['text']
        toplam_sure = route[0]['legs'][0]['duration']['text']

        # Rota üzerinde şehirler arası yol bilgisi
        st.subheader("🚙 Rota Bilgisi")
        st.markdown(f"**Mesafe:** {toplam_mesafe}")
        st.markdown(f"**Süre:** {toplam_sure}")

        # Yol üzerindeki adımları ve mesafeleri göster
        for step in steps:
            st.markdown(f"- {step['html_instructions']} ({step['distance']['text']})")

        # Harita üzerinde rota çizimi
        m = folium.Map(location=sehir_koordinatlari[baslangic_sehri], zoom_start=6)
        koordinatlar = [(sehir_koordinatlari[baslangic_sehri],)]
        
        for step in steps:
            # Her adımı işaretlemek için koordinatlar ekleyelim
            lat_lng = step['end_location']
            koordinatlar.append((lat_lng['lat'], lat_lng['lng']))

        # Rota çizimini yapalım
        AntPath(locations=koordinatlar, color="blue").add_to(m)
        
        # Başlangıç ve varış şehirlerini işaretleyelim
        folium.Marker(
            sehir_koordinatlari[baslangic_sehri],
            popup=baslangic_sehri,
            icon=folium.Icon(color="green")
        ).add_to(m)

        folium.Marker(
            sehir_koordinatlari[varis_sehri],
            popup=varis_sehri,
            icon=folium.Icon(color="red")
        ).add_to(m)

        st.subheader("📍 Rota Haritası")
        st_folium(m, width=700, height=400)
    else:
        st.error("Rota alınamadı. Lütfen şehirleri tekrar kontrol edin.")
