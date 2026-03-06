# backend/app/src/processor/normalizer_letras.py
import re
import unicodedata
from collections import Counter

# Lista de ruidos y onomatopeyas avanzada para limpieza total
RUIDOS = [
    r'\b('
    # Balbuceos y aire
    r'va+a+|bu+u+|ha+y+|ay+|a+h+|hay+|uh+h+|ah+h+|oh+h+|huh+|'
    # Fonemas y relleno vocal
    r'o+h+|e+h+|u+h+|y+o+|y+e+h+|m+h+|m+m+m+|u+m+|la+|na+|da+|pa+|ra+|'
    # Repeticiones de sílabas
    r've+(\s+ve+)+|la+(\sla+)+|na+(\sna+)+|da+(\sda+)+|pa+(\spa+)+|ra+(\sra+)+|ma+(\sma+)+|ta+(\sta+)+|ba+(\sba+)+|ha+(\sha+)+|da-da-da+|da-da+|la-la-la+|ve-ve-ve+|'
    # Ad-libs urbanos
    r'br+r+|pr+r+|tr+a+|r+a+|plo+|pau+|paw+|piu+(\s+piu+)+|pum+|pumba+(\s+pumba+)*|bam+(\s+bam+)*|pon+|skere+|wuh+|ey+(\sey+)+|o+ye+|dale+|eso+|vaya+|mue+velo+|fuego+|su+ela+|du+ro+|fuera+|'
    # Exclamaciones dialectales
    r'ay+(\say+)*|ehy+|ole+|epa+|aja+|uy+|viva+|ale+|ojalá+|tiki+(\s+tiki+)*|taka+(\s+taka+)*|chi+ki+|tralará+|larala+|larailo+|lolailo+|lerelere+|'
    # Ruidos fisiológicos y de gesto
    r'jaj+a+|jej+e+|jij+i+|shh+|cof+(\s+cof+)*|mwah+|mua+(\s+mua+)*|sh+t+|grunt|yee-haw|woo-hoo+|hee-hee|au+w|'
    # Objetos, animales y acción
    r'rin+(\s+rin+)*|tic+(\s+tic+)*|clin+(\s+clin+)*|pumba+(\s+pumba+)*|catapum+|zas+|paf+|chof+|plas+|bang+|bum+|boom+|miau+|guau+|quiquiriquí+|pío+(\s+pío+)*|clink|clank|ring+|'
    # Muletillas y repeticiones de producción
    r'check+|yeah+|oh yeah+|oh no+|uh huh+|wow+|yow+|ah-oh+|oooh+|eyo+|yo yo|hey hey|ajá|vroom+|zoom+|ddu-du+|waka-waka|tupa-tupa|tukutum|chiki-ta'
    r')\b'
]

def normalizar_letra_super_analitica(letra: str) -> dict:
    """
    Normalizador SUPER ANALÍTICO para NLP:
    - Limpieza completa de tildes, acentos y caracteres extraños
    - Eliminación de ruidos y onomatopeyas
    - Preserva y cuenta signos de emoción (!, ?)
    - Detecta versos, estrofas y coros/repeticiones
    - Genera métricas de emociones por verso
    - Detecta frases clave por frecuencia de palabras
    """
    if not letra:
        return {
            "letra_limpia": "",
            "num_exclamaciones": 0,
            "num_interrogaciones": 0,
            "num_versos": 0,
            "num_estrofas": 0,
            "num_ruidos": 0,
            "num_coros": 0,
            "versos": [],
            "estrofas": [],
            "emocion_por_verso": [],
            "frases_clave": []
        }

    # Contar símbolos de emoción
    num_exclamaciones = letra.count("!")
    num_interrogaciones = letra.count("?")

    # Normalización básica
    letra_limpia = letra.lower()
    letra_limpia = unicodedata.normalize("NFKD", letra_limpia)
    letra_limpia = "".join(c for c in letra_limpia if not unicodedata.combining(c))

    # Eliminar etiquetas y secciones
    letra_limpia = re.sub(r'\[.*?\]|\(.*?\)|\{.*?\}', ' ', letra_limpia)

    # Contar y eliminar ruidos
    ruidos_detectados = 0
    for ruido in RUIDOS:
        matches = re.findall(ruido, letra_limpia, flags=re.IGNORECASE)
        ruidos_detectados += len(matches)
        letra_limpia = re.sub(ruido, ' ', letra_limpia, flags=re.IGNORECASE)

    # Mantener solo letras, números, espacios y signos de emoción
    letra_limpia = re.sub(r'[^a-z0-9¡!?\s\n]', ' ', letra_limpia)

    # Normalizar espacios y saltos de línea
    letra_limpia = re.sub(r'\r\n|\r|\n', '\n', letra_limpia)
    letra_limpia = re.sub(r'\n{2,}', '\n', letra_limpia)
    letra_limpia = re.sub(r'[ \t]+', ' ', letra_limpia)
    letra_limpia = re.sub(r' \n|\n ', '\n', letra_limpia)
    letra_limpia = letra_limpia.strip()

    # Separar versos y estrofas
    versos = [v.strip() for v in letra_limpia.split('\n') if v.strip()]
    num_versos = len(versos)

    estrofas = []
    for v in letra_limpia.split('\n\n'):
        est = [x.strip() for x in v.split('\n') if x.strip()]
        if est:
            estrofas.append(est)
    num_estrofas = len(estrofas)

    # Detectar coros (versos repetidos)
    contador_versos = Counter(versos)
    coros = [v for v, c in contador_versos.items() if c > 1]
    num_coros = len(coros)

    # Métricas de emoción por verso
    emocion_por_verso = [{"verso": v, "exclamaciones": v.count("!"), "interrogaciones": v.count("?")} for v in versos]

    # Frases clave (palabras más frecuentes)
    palabras = re.findall(r'\b[a-z0-9]{2,}\b', letra_limpia)
    frecuencias = Counter(palabras)
    frases_clave = [p for p, _ in frecuencias.most_common(10)]

    return {
        "letra_limpia": letra_limpia,
        "num_exclamaciones": num_exclamaciones,
        "num_interrogaciones": num_interrogaciones,
        "num_versos": num_versos,
        "num_estrofas": num_estrofas,
        "num_ruidos": ruidos_detectados,
        "num_coros": num_coros,
        "versos": versos,
        "estrofas": estrofas,
        "emocion_por_verso": emocion_por_verso,
        "frases_clave": frases_clave
    }