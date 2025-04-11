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

# Başlangıç Noktası Seçimi
st.sidebar.subheader("🛣️ Ekip Başlangıç Noktası")
if st.session_state.aktif_ekip:
    # Kullanıcıya başlangıç adresini manuel olarak girme fırsatı veriliyor
    baslangic_adresi = st.text_input("Başlangıç Adresi (Örn: İstanbul, Türkiye)")

    if baslangic_adresi:
        # Kullanıcı adresi girdiğinde bu adresi ekip için kaydediyoruz
        st.session_state.ekipler[st.session_state.aktif_ekip]["baslangic"] = baslangic_adresi
        st.success(f"{baslangic_adresi} başlangıç noktası olarak seçildi.")
    else:
        if "baslangic" not in st.session_state.ekipler[st.session_state.aktif_ekip]:
            st.warning("Başlangıç adresi seçmediniz.")

# Şehir/Bayi Ekleme
st.subheader("📍 Bayi / Şehir Ekle")
with st.form("sehir_ekle"):
    sehir_adi = st.text_input("Şehir veya Bayi Adı")
    onem = st.slider("Önem Derecesi", 1, 5, 3)
    yol_suresi = st.number_input("Yol Süresi (saat)", 1, 24, 1)
    yol_ucreti = st.number_input("Yol Ücreti (TL)", 0, 10000, 100)
    ek_maliyet = st.number_input("Ekstra Maliyet (TL)", 0, 100000, 0)
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
                    "onem": onem,
                    "yol_suresi": yol_suresi,
                    "yol_ucreti": yol_ucreti,
                    "ek_maliyet": ek_maliyet
                })
                st.success(f"{sehir_adi} eklendi.")
        except Exception as e:
            st.error("Google API bağlantısı başarısız.")

# Şehir Listesi ve Silme
st.subheader("📋 Eklenen Bayiler")
for i, veri in enumerate(st.session_state.sehirler):
    col1, col2 = st.columns([10, 1])
    with col1:
        st.markdown(f"**{veri['sehir']}** | Ekip: {veri['ekip']} | Önem: {veri['onem']} ⭐ | Süre: {veri['yol_suresi']} saat | Maliyet: {veri['yol_ucreti']} TL")
    with col2:
        if st.button("❌", key=f"sil_{i}"):
            st.session_state.sehirler.pop(i)
            st.experimental_rerun()

# Benzin Maliyeti ve Km Başına Fiyat
st.sidebar.subheader("🚗 Benzin Maliyeti Hesaplama")
benzin_fiyati = st.number_input("Benzin Fiyatı (TL/Litre)", 0, 20, 10)
km_basi_maliyet = st.number_input("Kilometre Başına Maliyet (TL/km)", 0, 10, 5)

# Harita Oluşturma ve Önem Sırasını Güncelleme
st.subheader("🗺️ Oluşturulan Rota Haritası")
if st.session_state.sehirler:
    baslangic_adresi = st.session_state.ekipler[st.session_state.aktif_ekip].get("baslangic")
    if baslangic_adresi:
        baslangic_konum = None
        try:
            # Başlangıç adresini geocode ederek koordinatları alıyoruz
            geocode_result = gmaps.geocode(baslangic_adresi)
            if geocode_result:
                baslangic_konum = geocode_result[0]["geometry"]["location"]
            else:
                st.error("Başlangıç adresi bulunamadı.")
        except Exception as e:
            st.error("Google API bağlantısı başarısız.")

        if baslangic_konum:
            harita = folium.Map(location=[baslangic_konum['lat'], baslangic_konum['lng']], zoom_start=6)

            for i, sehir in enumerate(st.session_state.sehirler):
                # Mesafe ve süre hesaplaması
                if baslangic_konum:
                    yol = gmaps.directions(
                        (baslangic_konum['lat'], baslangic_konum['lng']),
                        (sehir['konum']['lat'], sehir['konum']['lng']),
                        mode="driving"
                    )
                    if yol:
                        distance = yol[0]['legs'][0]['distance']['value'] / 1000  # km cinsinden
                        time = yol[0]['legs'][0]['duration']['value'] / 60  # dakika cinsinden

                        # Km başına maliyet hesaplaması
                        maliyet = distance * km_basi_maliyet  # km * fiyat

                        # Mesafe ve maliyet hesaplamalarını yaptıktan sonra
                        folium.Marker(
                            [sehir['konum']['lat'], sehir['konum']['lng']],
                            popup=f"{i+1}. {sehir['sehir']} | Mesafe: {distance:.2f} km | Süre: {time:.2f} dk | Maliyet: {maliyet:.2f} TL"
                        ).add_to(harita)

                        # Başlangıç noktasını son gittiğimiz şehir olarak güncelliyoruz
                        baslangic_adresi = sehir['sehir']
                        baslangic_konum = sehir['konum']

            # Haritayı Streamlit içinde göster
            st_folium(harita, width=700)
