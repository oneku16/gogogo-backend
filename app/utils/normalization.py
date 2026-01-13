from typing import Dict

CITY_MAPPING: Dict[str, str] = {
    # Russian
    "нарын": "Naryn",
    "бишкек": "Bishkek",
    "ош": "Osh",
    "каракол": "Karakol",
    "балыкчы": "Balykchy",
    "чолпон-ата": "Cholpon-Ata",
    "джалал-абад": "Jalal-Abad",
    "джалал абад": "Jalal-Abad",
    "манас": "Manas",
    "талас": "Talas",
    "баткен": "Batken",
    
    # Kyrgyz (Cyrillic)
    "нарын": "Naryn",
    "бишкек": "Bishkek",
    "ош": "Osh",
    "каракол": "Karakol",
    "балыкчы": "Balykchy",
    "чолпон-ата": "Cholpon-Ata",
    "жалал-абад": "Jalal-Abad",
    "талас": "Talas",
    "баткен": "Batken",
    "манас": "Manas",
    
    # Common variations
    "issykkul": "Issyk-Kul",
    "issyk-kul": "Issyk-Kul",
    "ыссык-кол": "Issyk-Kul",
    "ысык-көл": "Issyk-Kul"
}

def normalize_location(text: str) -> str:
    """
    Normalizes location text to a canonical English name if found in the mapping.
    Otherwise returns the original text stripped of whitespace.
    """
    if not text:
        return text
        
    cleaned = text.strip().lower()
    return CITY_MAPPING.get(cleaned, text.strip())
