# opsaudit â€” kendi sayÄ±larÄ±nÄ± denetleyen operasyon analitiÄŸi

![Python](https://img.shields.io/badge/python-3.10+-blue) ![License](https://img.shields.io/badge/license-MIT-green)

ğŸ‡¬ğŸ‡§ English version: [README.md](README.md)

> Her operasyon metriÄŸi, slayta giderken nadiren hayatta kalan tanÄ±m tercihlerine dayanÄ±r. `opsaudit` klasik analizleri hesaplar â€” OTIF, tahmin doÄŸruluÄŸu, ABC-XYZ, Pareto â€” ve hiÃ§bir sayÄ±yÄ± **dÃ¼rÃ¼stlÃ¼k bloÄŸu** olmadan geri vermez: ne dÃ¼ÅŸÃ¼rÃ¼ldÃ¼, hangi tanÄ±mlar kullanÄ±ldÄ± ve sonuÃ§ neyi *gÃ¶stermiyor*.
>
> YalnÄ±zca JSON Ã§Ä±ktÄ±. Yapay zeka ajanlarÄ±, veri hatlarÄ± ve dipnot okuyan insanlar iÃ§in.

## Ajan sÃ¶zleÅŸmesi

1. **YalnÄ±zca JSON stdout.** SonuÃ§lar da veri hatalarÄ± da JSON'dÄ±r (`{"error": {...}}` + sÄ±fÄ±r-dÄ±ÅŸÄ± Ã§Ä±kÄ±ÅŸ kodu). KullanÄ±m hatalarÄ± stderr'e gider (Ã§Ä±kÄ±ÅŸ 2). BaÅŸka hiÃ§bir ÅŸey asla basÄ±lmaz.
2. **Kendini belgeleyen.** Her yerde Ã¶rnekli `--help`; `opsaudit schema <komut>` beklenen girdi sÃ¼tunlarÄ±nÄ± JSON olarak basar.
3. **Asla etkileÅŸimli deÄŸil.** Soru yok, onay yok, TTY varsayÄ±mÄ± yok.
4. **Durumsuz.** AynÄ± girdi, aynÄ± Ã§Ä±ktÄ±. HiÃ§bir yere hiÃ§bir ÅŸey yazÄ±lmaz.

## Komutlar

| Komut | Ne hesaplar |
|-------|-------------|
| `opsaudit otif score orders.csv [--by carrier] [--tolerance 3]` | 5 basamaklÄ± OTIF metrik merdiveni (toleranslÄ±dan katÄ±ya), vaat dolgusu, kuyruk istatistikleri, segment kÄ±rÄ±lÄ±mÄ± |
| `opsaudit forecast backtest demand.csv [--horizon 6]` | BeÅŸ kÄ±yas modelinin kayan-orijin testi; WMAPE, yanlÄ±lÄ±k, ifÅŸalÄ± MAPE ve naive'e karÅŸÄ± FVA |
| `opsaudit abc segment demand.csv [--cv-x 0.5 --cv-z 1.0]` | AÃ§Ä±k ve deÄŸiÅŸtirilebilir eÅŸiklerle ABC-XYZ sÄ±nÄ±flandÄ±rmasÄ± + 9-kutu Ã¶zeti |
| `opsaudit pareto rank events.csv --category reason [--weight minutes] [--exposure machine_hours]` | Karar kalitesinde Pareto: etiket hijyeni, birim disiplini, maruziyet normalizasyonu |
| `opsaudit schema <komut>` | Beklenen girdi ÅŸemasÄ±, JSON olarak |

## Ã‡Ä±ktÄ± neye benziyor?

`otif score` Ã¶rneÄŸi (kÄ±rpÄ±lmÄ±ÅŸ): sonuÃ§ bÃ¶lÃ¼mÃ¼nde 5 basamaklÄ± merdiven (%99,0 â†’ %52,3), rapor-OTIF farkÄ± (44,1 puan) ve taÅŸÄ±yÄ±cÄ± kÄ±rÄ±lÄ±mÄ±; **honesty** bÃ¶lÃ¼mÃ¼nde ise 300 satÄ±rÄ±n 286'sÄ±nÄ±n kullanÄ±ldÄ±ÄŸÄ±, 14 iptalin hangi basamaklarda hariÃ§ tutulduÄŸu, hangi tarih Ã§Ä±palarÄ±nÄ±n ve toleransÄ±n kullanÄ±ldÄ±ÄŸÄ± ve sonucun neyi gÃ¶stermediÄŸi (kalem bazlÄ± dolum oranÄ±, tarih yeniden mÃ¼zakereleri, --by dÄ±ÅŸÄ±ndaki kÃ¶k nedenler) aÃ§Ä±kÃ§a yazar. Tam Ã¶rnek Ä°ngilizce README'dedir.

`honesty` bloÄŸu opsiyonel deÄŸildir ve kapatÄ±lamaz. Mesele zaten budur.

## Kurulum

```bash
pip install git+https://github.com/gulmezeren2-byte/opsaudit
# veya geliÅŸtirme iÃ§in:
git clone https://github.com/gulmezeren2-byte/opsaudit && cd opsaudit && pip install -e .
python -m pytest tests/   # uÃ§tan uca 8 test
```

Python 3.10+ gerekir. BaÄŸÄ±mlÄ±lÄ±klar: pandas, numpy â€” baÅŸka hiÃ§bir ÅŸey.

## Yapay zeka ajanlarÄ± iÃ§in

Tipik ajan iÅŸ akÄ±ÅŸÄ±:

1. `opsaudit schema otif.score` â†’ beklenen sÃ¼tunlarÄ± Ã¶ÄŸren
2. KullanÄ±cÄ±nÄ±n export'unu ÅŸemaya eÅŸle/yeniden adlandÄ±r
3. `opsaudit otif score data.csv --by carrier` â†’ JSON'u ayrÄ±ÅŸtÄ±r
4. Sonucu **dÃ¼rÃ¼stlÃ¼k bloÄŸuyla birlikte** raporla â€” tanÄ±mlar ve `not_shown` maddeleri, ajanÄ±n Ã¶zetinin abartÄ±ya kaÃ§masÄ±nÄ± engelleyen ÅŸeydir

[industrial-engineering-ai-skills](https://github.com/gulmezeren2-byte/industrial-engineering-ai-skills) yÃ¶ntem paketiyle birlikte Ã§alÄ±ÅŸÄ±r: beceriler yargÄ±yÄ±, `opsaudit` hesabÄ± taÅŸÄ±r.

## Neden dÃ¼rÃ¼stlÃ¼k bloÄŸu?

Ã‡Ã¼nkÃ¼ sayÄ± hiÃ§bir zaman bulgunun tamamÄ± deÄŸildir. "%99 zamanÄ±nda" ile "%55 OTIF" aynÄ± sipariÅŸleri anlatÄ±r â€” fark dÃ¶rt tanÄ±m tercihidir ve tanÄ±mlarÄ± kontrol eden, hikayeyi kontrol eder. Bu aracÄ±n duruÅŸu: dÃ¼rÃ¼stÃ§e hesapla, yÃ¼ksek sesle ifÅŸa et ve Ã§ekinceleri makine-okur yap ki Ã§Ä±ktÄ±yÄ± Ã¶zetleyen bir yapay zeka bile onlarÄ± gÃ¶rmek zorunda kalsÄ±n. Her komutun arkasÄ±ndaki metodoloji, grafikler ve sentetik verilerle *Ã¶lÃ§Ã¼m dÃ¼rÃ¼stlÃ¼ÄŸÃ¼* serisinde gÃ¶sterilmiÅŸtir: [otif-analytics](https://github.com/gulmezeren2-byte/otif-analytics) Â· [forecast-accuracy-lab](https://github.com/gulmezeren2-byte/forecast-accuracy-lab) Â· [abc-xyz-inventory](https://github.com/gulmezeren2-byte/abc-xyz-inventory) Â· [auto-report-pipeline](https://github.com/gulmezeren2-byte/auto-report-pipeline)

## Yol haritasÄ±

- [ ] PyPI yayÄ±nÄ±
- [ ] `opsaudit report weekly` â€” haftalÄ±k rapor sÃ¶zleÅŸmesinin tamamÄ± tek komutta
- [ ] MCP sunucu sarmalayÄ±cÄ±sÄ± (aynÄ± motorlar, araÃ§-Ã§aÄŸrÄ±sÄ± arayÃ¼zÃ¼)
- [ ] Kesikli talep iÃ§in Croston/SBA kÄ±yaslarÄ±
- [ ] Excel (`.xlsx`) girdi desteÄŸi

## HakkÄ±nda

**[Eren GÃ¼lmez](https://www.linkedin.com/in/erengulmez)** tarafÄ±ndan tasarlandÄ± ve geliÅŸtirildi â€” endÃ¼stri mÃ¼hendisi, Ä°stanbul. Ã–lÃ§Ã¼m sistemleri tasarlar ve onlarÄ± hayata geÃ§irmek iÃ§in modern araÃ§larÄ± yÃ¶netirim; bu CLI serinin makine dairesidir â€” yeniden kullanÄ±m iÃ§in paketlenmiÅŸ hali.

## Lisans

[MIT](LICENSE)
