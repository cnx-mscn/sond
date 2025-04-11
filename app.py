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
if "baslangic_sehri" not in st.session_state:
    st.session_state.baslangic_sehri = None  # Başlangıç şehri için başlangıç değeri

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

# Başlangıç Noktası Seçimi (manuel giriş)
st.sidebar.subheader("🛣️ Başlangıç Konumunu Girin")
if st.session_state.aktif_ekip:
    baslangic_sehir = st.text_input("Başlangıç Şehri")
    if baslangic_sehir:
        st.session_state.baslangic_sehri = baslangic_sehri
        st.session_state.ekipler[st.session_state.aktif_ekip]["baslangic"] = baslangic_sehri
        st.success(f"{baslangic_sehir} başlangıç noktası olarak seçildi.")

# Şehir/Bayi Ekleme
st.subheader("📍 Bayi / Şehir Ekle")
with st.form("sehir_ekle"):
    sehir_adi = st.text_input("Şehir veya Bayi Adı")
    onem = st.slider("Önem Derecesi", 1, 5, 3)
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
                    "onem": onem
                })
                st.success(f"{sehir_adi} eklendi.")
        except Exception as e:
            st.error("Google API bağlantısı başarısız.")

# Şehir Listesi ve Silme
st.subheader("📋 Eklenen Bayiler")
for i, veri in enumerate(st.session_state.sehirler):
    col1, col2 = st.columns([10, 1])
    with col1:
        st.markdown(f"**{veri['sehir']}** | Ekip: {veri['ekip']} | Önem: {veri['onem']} ⭐")
    with col2:
        if st.button("❌", key=f"sil_{i}"):
            st.session_state.sehirler.pop(i)
            st.experimental_rerun()

# Harita ve Rota Oluşturma
st.subheader("🗺️ Oluşturulan Rota Haritası")
if st.session_state.sehirler and st.session_state.baslangic_sehri:
    # Başlangıç noktasını bulalım
    baslangic_konum = None
    for sehir in st.session_state.sehirler:
        if sehir['sehir'] == st.session_state.baslangic_sehri:
            baslangic_konum = sehir['konum']
            break

    if baslangic_konum:
        harita = folium.Map(location=[baslangic_konum['lat'], baslangic_konum['lng']], zoom_start=6)

        toplam_maliyet = 0
        toplam_sure = 0
        toplam_mesafe = 0

        # Rotayı ve maliyet hesaplamayı yapalım
        for sehir in st.session_state.sehirler:
            # Mesafe ve süre hesaplaması
            yol = gmaps.directions(
                (baslangic_konum['lat'], baslangic_konum['lng']),
                (sehir['konum']['lat'], sehir['konum']['lng']),
                mode="driving"
            )
            if yol:
                distance = yol[0]['legs'][0]['distance']['value'] / 1000  # km cinsinden
                time = yol[0]['legs'][0]['duration']['value'] / 60  # dakika cinsinden

                # Benzin maliyeti hesaplama (örneğin 1 km başına 0.5 TL yakıt maliyeti)
                benzin_maliyeti = distance * 0.5  # km başına yakıt maliyeti

                # İşçilik maliyeti hesaplama (örneğin, saatte 100 TL işçilik ücreti)
                iscilik_maliyeti = time * 100 / 60  # dakika başına işçilik ücreti (100 TL/saat)

                # Toplam maliyet hesaplama
                toplam_maliyet += iscilik_maliyeti + benzin_maliyeti
                toplam_sure += time
                toplam_mesafe += distance

                folium.Marker(
                    [sehir['konum']['lat'], sehir['konum']['lng']],
                    popup=f"{sehir['sehir']} | {distance} km | {time} dk | Benzin: {benzin_maliyeti} TL | İşçilik: {iscilik_maliyeti} TL",
                    icon=folium.Icon(color="blue")
                )

        # Harita render et
        st_folium(harita, width=800, height=600)

        # Toplam maliyet ve süreyi göster
        st.subheader("🔢 Toplam Maliyet ve Süre")
        st.write(f"Toplam Mesafe: {toplam_mesafe:.2f} km")
        st.write(f"Toplam Süre: {toplam_sure:.2f} dakika")
        st.write(f"Toplam Benzin Maliyeti: {benzin_maliyeti:.2f} TL")
        st.write(f"Toplam İşçilik Maliyeti: {iscilik_maliyeti:.2f} TL")
        st.write(f"Toplam Maliyet: {toplam_maliyet:.2f} TL")
