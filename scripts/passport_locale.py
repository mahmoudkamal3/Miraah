#!/usr/bin/env python3
"""Validated bilingual names and ISO3→ISO2 for Mir’ah Passport Power.

English display names are curated short labels for UI (not VisaIndex copy).
Arabic names cover every passport/destination ISO3 in the MVP dataset.
ISO2 codes follow ISO 3166-1; XK uses user-assigned XK for Kosovo.
"""

from __future__ import annotations

# ISO 3166-1 alpha-3 → alpha-2 for passport dataset countries only.
ISO3_TO_ISO2: dict[str, str] = {
    "AFG": "AF", "AGO": "AO", "ALB": "AL", "AND": "AD", "ARE": "AE", "ARG": "AR",
    "ARM": "AM", "ATG": "AG", "AUS": "AU", "AUT": "AT", "AZE": "AZ", "BDI": "BI",
    "BEL": "BE", "BEN": "BJ", "BFA": "BF", "BGD": "BD", "BGR": "BG", "BHR": "BH",
    "BHS": "BS", "BIH": "BA", "BLR": "BY", "BLZ": "BZ", "BOL": "BO", "BRA": "BR",
    "BRB": "BB", "BRN": "BN", "BTN": "BT", "BWA": "BW", "CAF": "CF", "CAN": "CA",
    "CHE": "CH", "CHL": "CL", "CHN": "CN", "CIV": "CI", "CMR": "CM", "COD": "CD",
    "COG": "CG", "COL": "CO", "COM": "KM", "CPV": "CV", "CRI": "CR", "CUB": "CU",
    "CYP": "CY", "CZE": "CZ", "DEU": "DE", "DJI": "DJ", "DMA": "DM", "DNK": "DK",
    "DOM": "DO", "DZA": "DZ", "ECU": "EC", "EGY": "EG", "ERI": "ER", "ESP": "ES",
    "EST": "EE", "ETH": "ET", "FIN": "FI", "FJI": "FJ", "FRA": "FR", "FSM": "FM",
    "GAB": "GA", "GBR": "GB", "GEO": "GE", "GHA": "GH", "GIN": "GN", "GMB": "GM",
    "GNB": "GW", "GNQ": "GQ", "GRC": "GR", "GRD": "GD", "GTM": "GT", "GUY": "GY",
    "HKG": "HK", "HND": "HN", "HRV": "HR", "HTI": "HT", "HUN": "HU", "IDN": "ID",
    "IND": "IN", "IRL": "IE", "IRN": "IR", "IRQ": "IQ", "ISL": "IS", "ISR": "IL",
    "ITA": "IT", "JAM": "JM", "JOR": "JO", "JPN": "JP", "KAZ": "KZ", "KEN": "KE",
    "KGZ": "KG", "KHM": "KH", "KIR": "KI", "KNA": "KN", "KOR": "KR", "KWT": "KW",
    "LAO": "LA", "LBN": "LB", "LBR": "LR", "LBY": "LY", "LCA": "LC", "LIE": "LI",
    "LKA": "LK", "LSO": "LS", "LTU": "LT", "LUX": "LU", "LVA": "LV", "MAC": "MO",
    "MAR": "MA", "MCO": "MC", "MDA": "MD", "MDG": "MG", "MDV": "MV", "MEX": "MX",
    "MHL": "MH", "MKD": "MK", "MLI": "ML", "MLT": "MT", "MMR": "MM", "MNE": "ME",
    "MNG": "MN", "MOZ": "MZ", "MRT": "MR", "MUS": "MU", "MWI": "MW", "MYS": "MY",
    "NAM": "NA", "NER": "NE", "NGA": "NG", "NIC": "NI", "NLD": "NL", "NOR": "NO",
    "NPL": "NP", "NRU": "NR", "NZL": "NZ", "OMN": "OM", "PAK": "PK", "PAN": "PA",
    "PER": "PE", "PHL": "PH", "PLW": "PW", "PNG": "PG", "POL": "PL", "PRK": "KP",
    "PRT": "PT", "PRY": "PY", "PSE": "PS", "QAT": "QA", "ROU": "RO", "RUS": "RU",
    "RWA": "RW", "SAU": "SA", "SDN": "SD", "SEN": "SN", "SGP": "SG", "SLB": "SB",
    "SLE": "SL", "SLV": "SV", "SMR": "SM", "SOM": "SO", "SRB": "RS", "SSD": "SS",
    "STP": "ST", "SUR": "SR", "SVK": "SK", "SVN": "SI", "SWE": "SE", "SWZ": "SZ",
    "SYC": "SC", "SYR": "SY", "TCD": "TD", "TGO": "TG", "THA": "TH", "TJK": "TJ",
    "TKM": "TM", "TLS": "TL", "TON": "TO", "TTO": "TT", "TUN": "TN", "TUR": "TR",
    "TUV": "TV", "TWN": "TW", "TZA": "TZ", "UGA": "UG", "UKR": "UA", "URY": "UY",
    "USA": "US", "UZB": "UZ", "VAT": "VA", "VCT": "VC", "VEN": "VE", "VNM": "VN",
    "VUT": "VU", "WSM": "WS", "XKX": "XK", "YEM": "YE", "ZAF": "ZA", "ZMB": "ZM",
    "ZWE": "ZW",
}

# Short English UI labels (Mir’ah Passport Power).
NAME_EN: dict[str, str] = {
    "AFG": "Afghanistan", "AGO": "Angola", "ALB": "Albania", "AND": "Andorra",
    "ARE": "United Arab Emirates", "ARG": "Argentina", "ARM": "Armenia",
    "ATG": "Antigua and Barbuda", "AUS": "Australia", "AUT": "Austria",
    "AZE": "Azerbaijan", "BDI": "Burundi", "BEL": "Belgium", "BEN": "Benin",
    "BFA": "Burkina Faso", "BGD": "Bangladesh", "BGR": "Bulgaria", "BHR": "Bahrain",
    "BHS": "Bahamas", "BIH": "Bosnia and Herzegovina", "BLR": "Belarus",
    "BLZ": "Belize", "BOL": "Bolivia", "BRA": "Brazil", "BRB": "Barbados",
    "BRN": "Brunei", "BTN": "Bhutan", "BWA": "Botswana", "CAF": "Central African Republic",
    "CAN": "Canada", "CHE": "Switzerland", "CHL": "Chile", "CHN": "China",
    "CIV": "Côte d’Ivoire", "CMR": "Cameroon", "COD": "DR Congo", "COG": "Congo",
    "COL": "Colombia", "COM": "Comoros", "CPV": "Cabo Verde", "CRI": "Costa Rica",
    "CUB": "Cuba", "CYP": "Cyprus", "CZE": "Czechia", "DEU": "Germany",
    "DJI": "Djibouti", "DMA": "Dominica", "DNK": "Denmark", "DOM": "Dominican Republic",
    "DZA": "Algeria", "ECU": "Ecuador", "EGY": "Egypt", "ERI": "Eritrea",
    "ESP": "Spain", "EST": "Estonia", "ETH": "Ethiopia", "FIN": "Finland",
    "FJI": "Fiji", "FRA": "France", "FSM": "Micronesia", "GAB": "Gabon",
    "GBR": "United Kingdom", "GEO": "Georgia", "GHA": "Ghana", "GIN": "Guinea",
    "GMB": "Gambia", "GNB": "Guinea-Bissau", "GNQ": "Equatorial Guinea",
    "GRC": "Greece", "GRD": "Grenada", "GTM": "Guatemala", "GUY": "Guyana",
    "HKG": "Hong Kong", "HND": "Honduras", "HRV": "Croatia", "HTI": "Haiti",
    "HUN": "Hungary", "IDN": "Indonesia", "IND": "India", "IRL": "Ireland",
    "IRN": "Iran", "IRQ": "Iraq", "ISL": "Iceland", "ISR": "Israel",
    "ITA": "Italy", "JAM": "Jamaica", "JOR": "Jordan", "JPN": "Japan",
    "KAZ": "Kazakhstan", "KEN": "Kenya", "KGZ": "Kyrgyzstan", "KHM": "Cambodia",
    "KIR": "Kiribati", "KNA": "Saint Kitts and Nevis", "KOR": "South Korea",
    "KWT": "Kuwait", "LAO": "Laos", "LBN": "Lebanon", "LBR": "Liberia",
    "LBY": "Libya", "LCA": "Saint Lucia", "LIE": "Liechtenstein", "LKA": "Sri Lanka",
    "LSO": "Lesotho", "LTU": "Lithuania", "LUX": "Luxembourg", "LVA": "Latvia",
    "MAC": "Macao", "MAR": "Morocco", "MCO": "Monaco", "MDA": "Moldova",
    "MDG": "Madagascar", "MDV": "Maldives", "MEX": "Mexico", "MHL": "Marshall Islands",
    "MKD": "North Macedonia", "MLI": "Mali", "MLT": "Malta", "MMR": "Myanmar",
    "MNE": "Montenegro", "MNG": "Mongolia", "MOZ": "Mozambique", "MRT": "Mauritania",
    "MUS": "Mauritius", "MWI": "Malawi", "MYS": "Malaysia", "NAM": "Namibia",
    "NER": "Niger", "NGA": "Nigeria", "NIC": "Nicaragua", "NLD": "Netherlands",
    "NOR": "Norway", "NPL": "Nepal", "NRU": "Nauru", "NZL": "New Zealand",
    "OMN": "Oman", "PAK": "Pakistan", "PAN": "Panama", "PER": "Peru",
    "PHL": "Philippines", "PLW": "Palau", "PNG": "Papua New Guinea", "POL": "Poland",
    "PRK": "North Korea", "PRT": "Portugal", "PRY": "Paraguay", "PSE": "Palestine",
    "QAT": "Qatar", "ROU": "Romania", "RUS": "Russia", "RWA": "Rwanda",
    "SAU": "Saudi Arabia", "SDN": "Sudan", "SEN": "Senegal", "SGP": "Singapore",
    "SLB": "Solomon Islands", "SLE": "Sierra Leone", "SLV": "El Salvador",
    "SMR": "San Marino", "SOM": "Somalia", "SRB": "Serbia", "SSD": "South Sudan",
    "STP": "São Tomé and Príncipe", "SUR": "Suriname", "SVK": "Slovakia",
    "SVN": "Slovenia", "SWE": "Sweden", "SWZ": "Eswatini", "SYC": "Seychelles",
    "SYR": "Syria", "TCD": "Chad", "TGO": "Togo", "THA": "Thailand",
    "TJK": "Tajikistan", "TKM": "Turkmenistan", "TLS": "Timor-Leste", "TON": "Tonga",
    "TTO": "Trinidad and Tobago", "TUN": "Tunisia", "TUR": "Türkiye", "TUV": "Tuvalu",
    "TWN": "Taiwan", "TZA": "Tanzania", "UGA": "Uganda", "UKR": "Ukraine",
    "URY": "Uruguay", "USA": "United States", "UZB": "Uzbekistan", "VAT": "Vatican City",
    "VCT": "Saint Vincent and the Grenadines", "VEN": "Venezuela", "VNM": "Vietnam",
    "VUT": "Vanuatu", "WSM": "Samoa", "XKX": "Kosovo", "YEM": "Yemen",
    "ZAF": "South Africa", "ZMB": "Zambia", "ZWE": "Zimbabwe",
}

# Arabic UI labels for every passport/destination in the MVP dataset.
NAME_AR: dict[str, str] = {
    "AFG": "أفغانستان", "AGO": "أنغولا", "ALB": "ألبانيا", "AND": "أندورا",
    "ARE": "الإمارات", "ARG": "الأرجنتين", "ARM": "أرمينيا", "ATG": "أنتيغوا وباربودا",
    "AUS": "أستراليا", "AUT": "النمسا", "AZE": "أذربيجان", "BDI": "بوروندي",
    "BEL": "بلجيكا", "BEN": "بنين", "BFA": "بوركينا فاسو", "BGD": "بنغلاديش",
    "BGR": "بلغاريا", "BHR": "البحرين", "BHS": "الباهاما", "BIH": "البوسنة والهرسك",
    "BLR": "بيلاروس", "BLZ": "بليز", "BOL": "بوليفيا", "BRA": "البرازيل",
    "BRB": "باربادوس", "BRN": "بروناي", "BTN": "بوتان", "BWA": "بوتسوانا",
    "CAF": "جمهورية أفريقيا الوسطى", "CAN": "كندا", "CHE": "سويسرا", "CHL": "تشيلي",
    "CHN": "الصين", "CIV": "ساحل العاج", "CMR": "الكاميرون", "COD": "الكونغو الديمقراطية",
    "COG": "الكونغو", "COL": "كولومبيا", "COM": "جزر القمر", "CPV": "الرأس الأخضر",
    "CRI": "كوستاريكا", "CUB": "كوبا", "CYP": "قبرص", "CZE": "التشيك",
    "DEU": "ألمانيا", "DJI": "جيبوتي", "DMA": "دومينيكا", "DNK": "الدنمارك",
    "DOM": "جمهورية الدومينيكان", "DZA": "الجزائر", "ECU": "الإكوادور", "EGY": "مصر",
    "ERI": "إريتريا", "ESP": "إسبانيا", "EST": "إستونيا", "ETH": "إثيوبيا",
    "FIN": "فنلندا", "FJI": "فيجي", "FRA": "فرنسا", "FSM": "ميكرونيزيا",
    "GAB": "الغابون", "GBR": "المملكة المتحدة", "GEO": "جورجيا", "GHA": "غانا",
    "GIN": "غينيا", "GMB": "غامبيا", "GNB": "غينيا بيساو", "GNQ": "غينيا الاستوائية",
    "GRC": "اليونان", "GRD": "غرينادا", "GTM": "غواتيمالا", "GUY": "غيانا",
    "HKG": "هونغ كونغ", "HND": "هندوراس", "HRV": "كرواتيا", "HTI": "هايتي",
    "HUN": "المجر", "IDN": "إندونيسيا", "IND": "الهند", "IRL": "أيرلندا",
    "IRN": "إيران", "IRQ": "العراق", "ISL": "آيسلندا", "ISR": "إسرائيل",
    "ITA": "إيطاليا", "JAM": "جامايكا", "JOR": "الأردن", "JPN": "اليابان",
    "KAZ": "كازاخستان", "KEN": "كينيا", "KGZ": "قيرغيزستان", "KHM": "كمبوديا",
    "KIR": "كيريباس", "KNA": "سانت كيتس ونيفيس", "KOR": "كوريا الجنوبية",
    "KWT": "الكويت", "LAO": "لاوس", "LBN": "لبنان", "LBR": "ليبيريا",
    "LBY": "ليبيا", "LCA": "سانت لوسيا", "LIE": "ليختنشتاين", "LKA": "سريلانكا",
    "LSO": "ليسوتو", "LTU": "ليتوانيا", "LUX": "لوكسمبورغ", "LVA": "لاتفيا",
    "MAC": "ماكاو", "MAR": "المغرب", "MCO": "موناكو", "MDA": "مولدوفا",
    "MDG": "مدغشقر", "MDV": "المالديف", "MEX": "المكسيك", "MHL": "جزر مارشال",
    "MKD": "مقدونيا الشمالية", "MLI": "مالي", "MLT": "مالطا", "MMR": "ميانمار",
    "MNE": "الجبل الأسود", "MNG": "منغوليا", "MOZ": "موزمبيق", "MRT": "موريتانيا",
    "MUS": "موريشيوس", "MWI": "ملاوي", "MYS": "ماليزيا", "NAM": "ناميبيا",
    "NER": "النيجر", "NGA": "نيجيريا", "NIC": "نيكاراغوا", "NLD": "هولندا",
    "NOR": "النرويج", "NPL": "نيبال", "NRU": "ناورو", "NZL": "نيوزيلندا",
    "OMN": "عمان", "PAK": "باكستان", "PAN": "بنما", "PER": "بيرو",
    "PHL": "الفلبين", "PLW": "بالاو", "PNG": "بابوا غينيا الجديدة", "POL": "بولندا",
    "PRK": "كوريا الشمالية", "PRT": "البرتغال", "PRY": "باراغواي", "PSE": "فلسطين",
    "QAT": "قطر", "ROU": "رومانيا", "RUS": "روسيا", "RWA": "رواندا",
    "SAU": "السعودية", "SDN": "السودان", "SEN": "السنغال", "SGP": "سنغافورة",
    "SLB": "جزر سليمان", "SLE": "سيراليون", "SLV": "السلفادور", "SMR": "سان مارينو",
    "SOM": "الصومال", "SRB": "صربيا", "SSD": "جنوب السودان", "STP": "ساو تومي وبرينسيبي",
    "SUR": "سورينام", "SVK": "سلوفاكيا", "SVN": "سلوفينيا", "SWE": "السويد",
    "SWZ": "إسواتيني", "SYC": "سيشل", "SYR": "سوريا", "TCD": "تشاد",
    "TGO": "توغو", "THA": "تايلاند", "TJK": "طاجيكستان", "TKM": "تركمانستان",
    "TLS": "تيمور الشرقية", "TON": "تونغا", "TTO": "ترينيداد وتوباغو", "TUN": "تونس",
    "TUR": "تركيا", "TUV": "توفالو", "TWN": "تايوان", "TZA": "تنزانيا",
    "UGA": "أوغندا", "UKR": "أوكرانيا", "URY": "أوروغواي", "USA": "الولايات المتحدة",
    "UZB": "أوزبكستان", "VAT": "الفاتيكان", "VCT": "سانت فينسنت والغرينادين",
    "VEN": "فنزويلا", "VNM": "فيتنام", "VUT": "فانواتو", "WSM": "ساموا",
    "XKX": "كوسوفو", "YEM": "اليمن", "ZAF": "جنوب أفريقيا", "ZMB": "زامبيا",
    "ZWE": "زيمبابوي",
}


def validate_locale_coverage(codes: set[str]) -> None:
    missing_en = sorted(code for code in codes if code not in NAME_EN)
    missing_ar = sorted(code for code in codes if code not in NAME_AR)
    missing_iso2 = sorted(code for code in codes if code not in ISO3_TO_ISO2)
    problems = []
    if missing_en:
        problems.append(f"Missing English names: {missing_en}")
    if missing_ar:
        problems.append(f"Missing Arabic names: {missing_ar}")
    if missing_iso2:
        problems.append(f"Missing ISO2 codes: {missing_iso2}")
    if problems:
        raise ValueError("; ".join(problems))
