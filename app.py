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
        for idx, uye in enumerate(st.session_state.ekipler[st.session_state.aktif_ekip]["members"]):
            col1, col2 = st.columns([5, 1])
            col1.markdown(f"- {uye}")
            if col2.button("❌", key=f"uye_sil_{idx}"):
                st.session_state.ekipler[st.session_state.aktif_ekip]["members"].pop(idx)
                st.experimental_rerun()

# Başlangıç Noktası Seçimi
st.sidebar.subheader("🛣️ Ekip Başlangıç Noktası")
if st.session_state.aktif_ekip:
    baslangic_sehir = st.selectbox("Başlangıç Şehri", ["Seçiniz"] + [sehir['sehir'] for sehir in st.session_state.sehirler])
    if baslangic_sehir != "Seçiniz":
        st.session_state.ekipler[st.session_state.aktif_ekip]["baslangic"] = baslangic_sehir
        st.success(f"{baslangic_sehir} başlangıç noktası olarak seçildi.")

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
for i, veri in enumerate(sorted(st.session_state.sehirler, key=lambda x: (x['yol_ucreti'], -x['onem']))):
    col1, col2 = st.columns([10, 1])
    with col1:
        st.markdown(f"**{veri['sehir']}** | Ekip: {veri['ekip']} | Önem: {veri['onem']} ⭐ | Süre: {veri['yol_suresi']} saat | Maliyet: {veri['yol_ucreti']} TL")
    with col2:
        if st.button("❌", key=f"sil_{i}"):
            st.session_state.sehirler.pop(i)
            st.experimental_rerun()

# Harita Oluşturma
st.subheader("🗺️ Oluşturulan Rota Haritası")
if st.session_state.sehirler:
    # Başlangıç noktası
    baslangic_sehir = st.session_state.ekipler[st.session_state.aktif_ekip].get("baslangic")
    if baslangic_sehir:
        baslangic_konum = None
        for sehir in st.session_state.sehirler:
            if sehir['sehir'] == baslangic_sehir:
                baslangic_konum = sehir['konum']
                break

        if baslangic_konum:
            harita = folium.Map(location=[baslangic_konum['lat'], baslangic_konum['lng']], zoom_start=6)

            for i, sehir in enumerate(sorted(st.session_state.sehirler, key=lambda x: (x['yol_ucreti'], -x['onem']))):
                folium.Marker(
                    [sehir['konum']['lat'], sehir['konum']['lng']],
                    popup=f"{i+1}. {sehir['sehir']} ({sehir['ekip']})",
                    tooltip=f"{i+1}. Durak",
                    icon=folium.DivIcon(html=f"""<div style="font-size: 12pt; color: white; background-color: blue; border-radius: 5px; padding: 2px;">{i+1}</div>""")
                ).add_to(harita)

                if i < len(st.session_state.sehirler) - 1:
                    baslangic = sehir['konum']
                    bitis = st.session_state.sehirler[i+1]['konum']
                    yol = gmaps.directions(
                        (baslangic['lat'], baslangic['lng']),
                        (bitis['lat'], bitis['lng']),
                        mode="driving"
                    )
                    if yol:
                        steps = yol[0]['legs'][0]['steps']
                        rota_coords = [(step['end_location']['lat'], step['end_location']['lng']) for step in steps]
                        folium.PolyLine(rota_coords, color="blue", weight=4).add_to(harita)

            st_folium(harita, width=800, height=600)
        else:
            st.error("Başlangıç noktası seçilmedi.")
    else:
        st.error("Başlangıç noktası seçilmedi.")
else:
    st.info("Henüz şehir eklenmedi.")
