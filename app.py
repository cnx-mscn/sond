import streamlit as st
import googlemaps
import folium
from streamlit_folium import st_folium

# Google Maps API Key
gmaps = googlemaps.Client(key="AIzaSyDwQVuPcON3rGSibcBrwhxQvz4HLTpF9Ws")  # ← kendi API anahtarınızı buraya yazın

st.set_page_config("Montaj Rota Planlayıcı", layout="wide")
st.title("🛠️ Montaj Rota Planlayıcı ve Rota Analizi")

# Session State Başlangıç
if "ekipler" not in st.session_state:
    st.session_state.ekipler = {}
if "aktif_ekip" not in st.session_state:
    st.session_state.aktif_ekip = None
if "sehirler" not in st.session_state:
    st.session_state.sehirler = []
if "baslangic_konum" not in st.session_state:
    st.session_state.baslangic_konum = None
if "baslangic_adres" not in st.session_state:
    st.session_state.baslangic_adres = None

# 🧑‍🤝‍🧑 Ekip Yönetimi
st.sidebar.header("👷 Ekip Yönetimi")
ekip_adi = st.sidebar.text_input("Yeni Ekip Adı")
if st.sidebar.button("➕ Ekip Oluştur") and ekip_adi:
    if ekip_adi not in st.session_state.ekipler:
        st.session_state.ekipler[ekip_adi] = {"members": []}
        st.session_state.aktif_ekip = ekip_adi
        st.success(f"{ekip_adi} oluşturuldu.")
    else:
        st.warning("Bu ekip zaten mevcut!")

# Aktif ekip seçimi
if st.session_state.ekipler:
    aktif_secim = st.sidebar.selectbox("Aktif Ekip Seç", list(st.session_state.ekipler.keys()))
    st.session_state.aktif_ekip = aktif_secim

# Üye ekle/çıkar
if st.session_state.aktif_ekip and st.session_state.aktif_ekip in st.session_state.ekipler:
    with st.sidebar.expander("👤 Ekip Üyeleri"):
        yeni_uye = st.text_input("Yeni Üye Adı")
        if st.button("✅ Üye Ekle"):
            st.session_state.ekipler[st.session_state.aktif_ekip]["members"].append(yeni_uye)
            st.success(f"{yeni_uye} eklendi.")

        for idx, uye in enumerate(st.session_state.ekipler[st.session_state.aktif_ekip]["members"]):
            col1, col2 = st.columns([5, 1])
            col1.markdown(f"- {uye}")
            if col2.button("❌", key=f"uye_sil_{idx}"):
                st.session_state.ekipler[st.session_state.aktif_ekip]["members"].pop(idx)
                st.experimental_rerun()

# 🧭 Başlangıç Noktası (sadece bir kere)
st.sidebar.subheader("📍 Başlangıç Noktası")
if not st.session_state.baslangic_konum:
    adres = st.sidebar.text_input("Başlangıç Adresi (örn: Gebze, Kocaeli)")
    if st.sidebar.button("🌍 Konumu Belirle") and adres:
        try:
            sonuc = gmaps.geocode(adres)
            if sonuc:
                konum = sonuc[0]['geometry']['location']
                st.session_state.baslangic_konum = konum
                st.session_state.baslangic_adres = adres
                st.success(f"Başlangıç adresi belirlendi: {adres}")
            else:
                st.error("Adres bulunamadı.")
        except:
            st.error("Google API bağlantısı başarısız.")

# 📌 Şehir / Bayi Ekleme
st.subheader("📍 Gidilecek Şehir Ekle")
with st.form("sehir_form"):
    sehir_adi = st.text_input("Şehir / Bayi Adı")
    onem = st.slider("Önem Derecesi", 1, 5, 3)
    is_suresi = st.number_input("Tahmini Montaj Süresi (saat)", 1, 24, 1)
    ek_maliyet = st.number_input("Ekstra Maliyet (TL)", 0, 100000, 0)
    gonder = st.form_submit_button("➕ Ekle")

    if gonder and st.session_state.aktif_ekip:
        try:
            sonuc = gmaps.geocode(sehir_adi)
            if sonuc:
                konum = sonuc[0]['geometry']['location']
                st.session_state.sehirler.append({
                    "sehir": sehir_adi,
                    "konum": konum,
                    "onem": onem,
                    "is_suresi": is_suresi,
                    "ek_maliyet": ek_maliyet,
                    "ekip": st.session_state.aktif_ekip
                })
                st.success(f"{sehir_adi} eklendi.")
            else:
                st.error("Konum bulunamadı.")
        except:
            st.error("Google API başarısız.")

# ⚙️ Maliyet Ayarları
st.sidebar.subheader("💰 Maliyet Ayarları")
benzin_fiyati = st.sidebar.number_input("Benzin Fiyatı (TL/Litre)", 1.0, 50.0, 10.0)
tuketim = st.sidebar.number_input("Araç Tüketimi (Litre / 100km)", 1.0, 20.0, 8.0)
saatlik_is_ucreti = st.sidebar.number_input("İşçilik Saat Ücreti (TL)", 10, 1000, 200)

# 🗺️ Harita ve Rota Hesaplama
st.subheader("🗺️ Rota ve Harita")
if st.session_state.baslangic_konum and st.session_state.sehirler:
    konumlar = [st.session_state.baslangic_konum] + [x["konum"] for x in st.session_state.sehirler]
    adresler = [st.session_state.baslangic_adres] + [x["sehir"] for x in st.session_state.sehirler]

    rota_harita = folium.Map(location=[konumlar[0]['lat'], konumlar[0]['lng']], zoom_start=6)

    toplam_km = 0
    toplam_sure = 0
    toplam_benzin = 0
    toplam_iscilik = 0
    toplam_ek = 0

    for i in range(len(konumlar) - 1):
        start = (konumlar[i]['lat'], konumlar[i]['lng'])
        end = (konumlar[i+1]['lat'], konumlar[i+1]['lng'])
        yol = gmaps.directions(start, end, mode="driving")
        if yol:
            km = yol[0]['legs'][0]['distance']['value'] / 1000
            sure = yol[0]['legs'][0]['duration']['value'] / 3600  # saat
            yakit = km * (tuketim / 100) * benzin_fiyati
            iscilik = st.session_state.sehirler[i]["is_suresi"] * saatlik_is_ucreti
            ek = st.session_state.sehirler[i]["ek_maliyet"]

            toplam_km += km
            toplam_sure += sure
            toplam_benzin += yakit
            toplam_iscilik += iscilik
            toplam_ek += ek

            folium.Marker(
                location=end,
                popup=f"{i+1}. {adresler[i+1]}",
                tooltip=f"{adresler[i+1]}",
                icon=folium.Icon(color="blue", icon="info-sign")
            ).add_to(rota_harita)

            folium.PolyLine(locations=[start, end], color="green", weight=3).add_to(rota_harita)

    st_folium(rota_harita, width=1000, height=600)

    # Sonuçlar
    st.markdown("### 💡 Rota Özeti")
    st.markdown(f"**Toplam KM:** {toplam_km:.1f} km")
    st.markdown(f"**Tahmini Süre:** {toplam_sure:.1f} saat")
    st.markdown(f"**Benzin Maliyeti:** {toplam_benzin:.0f} TL")
    st.markdown(f"**İşçilik Maliyeti:** {toplam_iscilik:.0f} TL")
    st.markdown(f"**Ekstra Maliyet:** {toplam_ek:.0f} TL")
    st.markdown(f"**💰 Toplam Maliyet:** {toplam_benzin + toplam_iscilik + toplam_ek:.0f} TL")
