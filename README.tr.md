# opsaudit — kendi sayılarını denetleyen operasyon analitiği

![Python](https://img.shields.io/badge/python-3.10+-blue) ![License](https://img.shields.io/badge/license-MIT-green) ![Tests](https://img.shields.io/badge/tests-8%20passing-brightgreen)

🇬🇧 English version: [README.md](README.md)

> Her operasyon metriği, slayta giderken nadiren hayatta kalan tanım tercihlerine dayanır. `opsaudit` klasik analizleri hesaplar — OTIF, tahmin doğruluğu, ABC-XYZ, Pareto — ve hiçbir sayıyı **dürüstlük bloğu** olmadan geri vermez: ne düşürüldü, hangi tanımlar kullanıldı ve sonuç neyi *göstermiyor*.
>
> Yalnızca JSON çıktı. Yapay zeka ajanları, veri hatları ve dipnot okuyan insanlar için.

## Ajan sözleşmesi

1. **Yalnızca JSON stdout.** Sonuçlar da veri hataları da JSON'dır (`{"error": {...}}` + sıfır-dışı çıkış kodu). Kullanım hataları stderr'e gider (çıkış 2). Başka hiçbir şey asla basılmaz.
2. **Kendini belgeleyen.** Her yerde örnekli `--help`; `opsaudit schema <komut>` beklenen girdi sütunlarını JSON olarak basar.
3. **Asla etkileşimli değil.** Soru yok, onay yok, TTY varsayımı yok.
4. **Durumsuz.** Aynı girdi, aynı çıktı. Hiçbir yere hiçbir şey yazılmaz.

## Komutlar

| Komut | Ne hesaplar |
|-------|-------------|
| `opsaudit otif score orders.csv [--by carrier] [--tolerance 3]` | 5 basamaklı OTIF metrik merdiveni (toleranslıdan katıya), vaat dolgusu, kuyruk istatistikleri, segment kırılımı |
| `opsaudit forecast backtest demand.csv [--horizon 6]` | Beş kıyas modelinin kayan-orijin testi; WMAPE, yanlılık, ifşalı MAPE ve naive'e karşı FVA |
| `opsaudit abc segment demand.csv [--cv-x 0.5 --cv-z 1.0]` | Açık ve değiştirilebilir eşiklerle ABC-XYZ sınıflandırması + 9-kutu özeti |
| `opsaudit pareto rank events.csv --category reason [--weight minutes] [--exposure machine_hours]` | Karar kalitesinde Pareto: etiket hijyeni, birim disiplini, maruziyet normalizasyonu |
| `opsaudit schema <komut>` | Beklenen girdi şeması, JSON olarak |

## Çıktı neye benziyor?

`otif score` örneği (kırpılmış): sonuç bölümünde 5 basamaklı merdiven (%99,0 → %52,3), rapor-OTIF farkı (44,1 puan) ve taşıyıcı kırılımı; **honesty** bölümünde ise 300 satırın 286'sının kullanıldığı, 14 iptalin hangi basamaklarda hariç tutulduğu, hangi tarih çıpalarının ve toleransın kullanıldığı ve sonucun neyi göstermediği (kalem bazlı dolum oranı, tarih yeniden müzakereleri, --by dışındaki kök nedenler) açıkça yazar. Tam örnek İngilizce README'dedir.

`honesty` bloğu opsiyonel değildir ve kapatılamaz. Mesele zaten budur.

## Kurulum

```bash
pip install git+https://github.com/gulmezeren2-byte/opsaudit
# veya geliştirme için:
git clone https://github.com/gulmezeren2-byte/opsaudit && cd opsaudit && pip install -e .
python -m pytest tests/   # uçtan uca 8 test
```

Python 3.10+ gerekir. Bağımlılıklar: pandas, numpy — başka hiçbir şey.

## Yapay zeka ajanları için

Tipik ajan iş akışı:

1. `opsaudit schema otif.score` → beklenen sütunları öğren
2. Kullanıcının export'unu şemaya eşle/yeniden adlandır
3. `opsaudit otif score data.csv --by carrier` → JSON'u ayrıştır
4. Sonucu **dürüstlük bloğuyla birlikte** raporla — tanımlar ve `not_shown` maddeleri, ajanın özetinin abartıya kaçmasını engelleyen şeydir

[industrial-engineering-ai-skills](https://github.com/gulmezeren2-byte/industrial-engineering-ai-skills) yöntem paketiyle birlikte çalışır: beceriler yargıyı, `opsaudit` hesabı taşır.

## Neden dürüstlük bloğu?

Çünkü sayı hiçbir zaman bulgunun tamamı değildir. "%99 zamanında" ile "%55 OTIF" aynı siparişleri anlatır — fark dört tanım tercihidir ve tanımları kontrol eden, hikayeyi kontrol eder. Bu aracın duruşu: dürüstçe hesapla, yüksek sesle ifşa et ve çekinceleri makine-okur yap ki çıktıyı özetleyen bir yapay zeka bile onları görmek zorunda kalsın. Her komutun arkasındaki metodoloji, grafikler ve sentetik verilerle *ölçüm dürüstlüğü* serisinde gösterilmiştir: [otif-analytics](https://github.com/gulmezeren2-byte/otif-analytics) · [forecast-accuracy-lab](https://github.com/gulmezeren2-byte/forecast-accuracy-lab) · [abc-xyz-inventory](https://github.com/gulmezeren2-byte/abc-xyz-inventory) · [auto-report-pipeline](https://github.com/gulmezeren2-byte/auto-report-pipeline)

## Yol haritası

- [ ] PyPI yayını
- [ ] `opsaudit report weekly` — haftalık rapor sözleşmesinin tamamı tek komutta
- [ ] MCP sunucu sarmalayıcısı (aynı motorlar, araç-çağrısı arayüzü)
- [ ] Kesikli talep için Croston/SBA kıyasları
- [ ] Excel (`.xlsx`) girdi desteği

## Hakkında

**[Eren Gülmez](https://www.linkedin.com/in/erengulmez)** tarafından tasarlandı ve geliştirildi — endüstri mühendisi, İstanbul. Ölçüm sistemleri tasarlar ve onları hayata geçirmek için modern araçları yönetirim; bu CLI serinin makine dairesidir — yeniden kullanım için paketlenmiş hali.

## Lisans

[MIT](LICENSE)
