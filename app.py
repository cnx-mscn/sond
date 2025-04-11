import streamlit as st
import googlemaps
import folium
from streamlit_folium import st_folium

# Google Maps API Anahtarınızı buraya girin
gmaps = googlemaps.Client(key="AIzaSyDwQVuPcON3rGSibcBrwhxQvz4HLTpF9Ws")

st.set_page_config(page_title="Montaj Rota Planlayıcı", layout="wide")
st.title("🛠️ Montaj Rota Planlayıcı ve Rota Analizi")

# Session State başlangıcı
if "ekipler" not in st.session_state:
    st.session_state.ekipler = {}
if "aktif_ekip" not in st.session_state:
    st.session_state.aktif_ekip = None
if "sehirler" not in st.session_state:
    st.session_state.sehirler = []
if "baslangic_konum" not in st.session_state:
    st.session_state.baslangic_konum = None

# Sidebar - Ekip yönetimi
st.sidebar.header("👷 Ekip Yönetimi")
ekip_adi = st.sidebar.text_input("Yeni Ekip Adı")
if st.sidebar.button("➕ Ekip Oluştur") and ekip_adi:
    if ekip_adi not in st.session_state.ekipler:
        st.session_state.ekipler[ekip_adi] = {"members": []}
        st.session_state.aktif_ekip = ekip_adi
        st.success(f"{ekip_adi} oluşturuldu.")
    else:
        st.warning("Bu ekip zaten mevcut!")

# Sidebar - Aktif ekip seçimi
if st.session_state.ekipler:
    st.session_state.aktif_ekip = st.sidebar.selectbox("Aktif Ekip Seç", list(st.session_state.ekipler.keys()))

# Sidebar - Üye ekleme/çıkarma
with st.sidebar.expander("👤 Ekip Üyeleri"):
    yeni_uye = st.text_input("Yeni Üye Adı")
    if st.button("✅ Üye Ekle") and yeni_uye:
        st.session_state.ekipler[st.session_state.aktif_ekip]["members"].append(yeni_uye)
    for idx, uye in enumerate(st.session_state.ekipler[st.session_state.aktif_ekip]["members"]):
        col1, col2 = st.columns([5, 1])
        col1.markdown(f"- {uye}")
        if col2.button("❌", key=f"uye_sil_{idx}"):
            st.session_state.ekipler[st.session_state.aktif_ekip]["members"].pop(idx)
            st.experimental_rerun()

# Başlangıç konumu haritadan belirleme
st.subheader("📍 Başlangıç Noktası Seç")
st.markdown("Harita üzerinden montaj ekibinin yola çıkacağı noktayı bir kere tıklayarak seçiniz.")
start_map = folium.Map(location=[39.0, 35.0], zoom_start=6)
start_location = st_folium(start_map, height=350, width=700, returned_objects=["last_clicked"])

if start_location and "last_clicked" in start_location:
    try:
        lat = start_location["last_clicked"]['lat']
        lng = start_location["last_clicked"]['lng']
        st.session_state.baslangic_konum = {'lat': lat, 'lng': lng}
        st.success(f"Başlangıç noktası olarak ({lat}, {lng}) seçildi.")
    except KeyError:
        st.error("Harita üzerinden konum bilgisi alınamadı.")

# Şehir ekleme formu
st.subheader("🏙️ Bayi / Şehir Ekle")
with st.form("sehir_form"):
    sehir_adi = st.text_input("Şehir veya Bayi Adı")
    onem = st.slider("Önem Derecesi", 1, 5, 3)
    is_suresi = st.number_input("Tahmini İş Süresi (saat)", 1, 24, 1)
    ek_maliyet = st.number_input("Ekstra Maliyet (TL)", 0, 100000, 0)
    sehir_ekle_btn = st.form_submit_button("➕ Şehir Ekle")

    if sehir_ekle_btn:
        try:
            sonuc = gmaps.geocode(sehir_adi)
            if sonuc:
                konum = sonuc[0]["geometry"]["location"]
                st.session_state.sehirler.append({
                    "sehir": sehir_adi,
                    "konum": konum,
                    "onem": onem,
                    "is_suresi": is_suresi,
                    "ek_maliyet": ek_maliyet
                })
                st.success(f"{sehir_adi} başarıyla eklendi.")
            else:
                st.error("Şehir bulunamadı.")
        except Exception as e:
            st.error("Google API hatası oluştu.")

# Benzin ve işçilik maliyeti hesaplama
st.sidebar.subheader("💰 Maliyet Parametreleri")
benzin_fiyati = st.sidebar.number_input("Benzin Fiyatı (TL/Litre)", 0.0, 100.0, 35.0)
tuketim = st.sidebar.number_input("Araç Tüketimi (Litre/100km)", 0.0, 50.0, 8.0)
iscilik_saati = st.sidebar.number_input("İşçilik Saat Ücreti (TL)", 0.0, 1000.0, 150.0)

# Rota ve maliyet gösterimi
if st.session_state.baslangic_konum and st.session_state.sehirler:
    rota_harita = folium.Map(location=[st.session_state.baslangic_konum['lat'], st.session_state.baslangic_konum['lng']], zoom_start=6)

    onceki_konum = st.session_state.baslangic_konum
    toplam_km = 0
    toplam_maliyet = 0

    for i, sehir in enumerate(sorted(st.session_state.sehirler, key=lambda x: x['onem'], reverse=True)):
        hedef_konum = (sehir['konum']['lat'], sehir['konum']['lng'])
        try:
            yol = gmaps.directions((onceki_konum['lat'], onceki_konum['lng']), hedef_konum, mode="driving")
            if yol:
                km = yol[0]['legs'][0]['distance']['value'] / 1000  # metre -> km
                sure_dk = yol[0]['legs'][0]['duration']['value'] / 60  # saniye -> dakika
                benzin_maliyeti = (km * tuketim / 100) * benzin_fiyati
                iscilik_maliyeti = (sure_dk / 60 + sehir['is_suresi']) * iscilik_saati
                toplam_maliyet += benzin_maliyeti + iscilik_maliyeti + sehir['ek_maliyet']
                toplam_km += km

                folium.Marker(
                    location=[hedef_konum[0], hedef_konum[1]],
                    popup=f"{i+1}. {sehir['sehir']}\nSüre: {int(sure_dk)} dk\nKM: {int(km)}\nMaliyet: {int(benzin_maliyeti + iscilik_maliyeti)} TL",
                    tooltip=f"{i+1}. {sehir['sehir']}"
                ).add_to(rota_harita)

                onceki_konum = {'lat': hedef_konum[0], 'lng': hedef_konum[1]}
        except Exception as e:
            st.error(f"Yol bilgisi alınamadı: {e}")

    st.subheader("📌 Rota Haritası")
    st_folium(rota_harita, height=500, width=1000)

    st.info(f"Toplam Mesafe: {int(toplam_km)} km | Tahmini Toplam Maliyet: {int(toplam_maliyet)} TL")
