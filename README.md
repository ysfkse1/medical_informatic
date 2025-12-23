# AI Destekli Akıllı Hastane Yönetim Sistemi
## AI-Based Smart Hospital Management and Clinical Decision Support System

## Proje Tanımı
Bu proje, klasik hastane yönetim sistemlerinden farklı olarak yapay zekâ destekli triyaj, klinik karar destek sistemi (Clinical Decision Support System – CDSS) ve ilaç etkileşim analizi bileşenlerini içeren yenilikçi bir hastane yönetim sistemi geliştirmeyi amaçlamaktadır. Sistem; hasta ve doktor etkileşimini güçlendiren, randevu öncesinde yapılandırılmış klinik veri toplayan ve doktorun karar sürecini destekleyen modern bir sağlık bilişimi çözümüdür. Proje, Medical Informatics dersi kapsamında akademik amaçla tasarlanmıştır.

## Projenin Amacı
- Hasta ve doktor arasındaki etkileşimi dijitalleştirmek  
- Randevu öncesi yapay zekâ destekli triyaj uygulamak  
- Doktorlara klinik karar desteği sağlamak  
- Reçete yazımı sırasında olası ilaç etkileşimlerini tespit etmek  
- Yapay zekânın sağlık bilişiminde karar destekleyici rolünü göstermek  

## Klasik Sistemlerden Farkı
Klasik hastane bilgi sistemleri genellikle yalnızca randevu, hasta kaydı ve reçete yazımı gibi temel işlevleri sunmaktadır. Bu projede ise randevu öncesi triyaj, klinik risk analizi ve ilaç etkileşim kontrolü gibi yapay zekâ destekli karar mekanizmaları sisteme entegre edilmiştir.

## Kullanıcı Rolleri

### Hasta
- Sisteme kayıt ve giriş yapar  
- Kişisel ve klinik bilgilerini girer  
- Randevu almadan önce yapay zekâ destekli triyaj sorularını yanıtlar  
- Doktordan randevu alır  
- Geçmiş randevu ve reçetelerini görüntüler  

### Doktor
- Günlük ve haftalık randevuları görüntüler  
- Hastaya ait triyaj sonuçlarını ve risk analizlerini inceler  
- Yapay zekâ tarafından önerilen olası hastalıkları görür  
- Hastaya reçete yazar  
- Reçete yazımı sırasında ilaç etkileşim uyarıları alır  

### Yapay Zekâ Modülleri
- Semptom analizi  
- Risk seviyesi belirleme  
- Olası hastalık tahmini  
- İlaç–ilaç ve ilaç–hasta etkileşim analizi  

## Hasta Akışı
1. Hasta sisteme giriş yapar  
2. Kişisel sağlık bilgilerini doldurur  
3. Randevu öncesinde yapay zekâ destekli triyaj sürecine yönlendirilir  
4. Triyaj sonuçları doktora iletilir  
5. Hasta doktordan randevu alır  
6. Doktor hasta bilgilerini ve yapay zekâ raporlarını inceler  
7. Doktor reçete yazar  
8. Sistem ilaç etkileşimlerini analiz ederek uyarı üretir  

## Yapay Zekâ Destekli Triyaj Sistemi
Triyaj sürecinde hastadan aşağıdaki bilgiler toplanır:
- Ana şikayet  
- Şikayetin süresi  
- Ağrı seviyesi  
- Ateş durumu  
- Nefes darlığı  
- Daha önce benzer durum yaşanıp yaşanmadığı  

Bu veriler analiz edilerek doktora sunulmak üzere risk seviyesi ve olası hastalıkları içeren özet bir rapor oluşturulur. Yapay zekâ tanı koymaz, yalnızca karar desteği sağlar.

## Doktor Paneli
Doktor panelinde aşağıdaki bilgiler görüntülenir:
- Günlük ve haftalık randevu listesi  
- Hasta demografik bilgileri  
- Triyaj özet raporu  
- Risk değerlendirmesi  
- Klinik uyarılar  

## Reçete ve İlaç Etkileşim Sistemi
Doktor reçete yazarken sistem aşağıdaki kontrolleri otomatik olarak gerçekleştirir:
- İlaç–ilaç etkileşimleri  
- İlaç–hasta etkileşimleri (yaş, kilo, cinsiyet, kronik hastalıklar)  
- Alerji riski  
- Olası yan etkiler  

Bu analizler sonucunda doktora bilgilendirici uyarılar sunulur.

## Sistem Mimarisi
Hasta arayüzü, yapay zekâ triyaj modülü, backend API, veritabanı, doktor paneli ve klinik karar destek bileşenlerinden oluşan modüler bir mimari tasarlanmıştır.

## Veri Güvenliği ve Etik
- Hasta verileri güvenli ve şifreli şekilde saklanır  
- Rol bazlı erişim kontrolü uygulanır  
- KVKK ve GDPR ilkeleri gözetilir  
- Yapay zekâ çıktıları bağlayıcı değildir  
- Klinik sorumluluk doktora aittir  

## Medical Informatics Açısından Önemi
Bu proje, klinik karar destek sistemlerine örnek teşkil eden, hasta merkezli veri yaklaşımını benimseyen ve yapay zekânın sağlık bilişimindeki kullanımını etik çerçevede ele alan bir çalışmadır.

## Gelecek Geliştirmeler
- Laboratuvar sonuçlarının entegrasyonu  
- Görüntü işleme destekli tanı yardımcı sistemleri  
- Mobil uygulama desteği  
- Uzaktan hasta takibi  
- Yapay zekâ öğrenme ve geri bildirim mekanizmaları  

## Sonuç
Bu çalışma, modern sağlık sistemlerinde ihtiyaç duyulan akıllı, güvenli ve doktoru destekleyen bir hastane yönetim sistemi sunmaktadır. Yapay zekâ, tanı koyan değil, klinik karar sürecini destekleyen bir bileşen olarak konumlandırılmıştır.

## Proje Sahibi
Yusuf Köse  
Galatasaray Üniversitesi  
Medical Informatics

wd