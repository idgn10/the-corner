"""Dibujos de "Como grabar" (SVG escrito a mano, sin archivos): visto desde arriba y de lado.

Las medidas son las de boxeo/recording.py. Los colores de las manos, los del video con esqueleto
(izquierda azul, derecha naranja). Los textos van dentro del SVG con letra del sistema: al mostrarse como
imagen no cargan la letra de la app.
"""
from boxeo.render import LEFT_COLOR, RIGHT_COLOR, hex_color

LEFT, RIGHT = hex_color(LEFT_COLOR), hex_color(RIGHT_COLOR)   # los del esqueleto del video
INK, GRAY, LINE, PAPER, VIEW = "#161616", "#6B6B66", "#BDBCB4", "#F7F7F7", "#E2A27E"
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"


def top_view():
    """Desde arriba, guardia de diestro: la persona mira y golpea hacia arriba (la nariz lo marca) y el movil queda a
    unos 2 m, a 45 grados, entre su frente y su hombro adelantado (el izquierdo)."""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 280" font-family="{FONT}">
<rect width="340" height="280" rx="18" fill="{PAPER}"/>
<path d="M119 109 L278 177 L187 268 Z" fill="{VIEW}" fill-opacity=".22"/>
<line x1="225" y1="181" x2="225" y2="62" stroke="{GRAY}" stroke-width="2" stroke-dasharray="5 5"/>
<path d="M218 66 L225 52 L232 66 Z" fill="{GRAY}"/>
<text x="225" y="40" text-anchor="middle" font-size="14" fill="{GRAY}">Hacia donde miras y golpeas</text>
<line x1="125" y1="115" x2="203" y2="193" stroke="{INK}" stroke-width="1.6"/>
<circle cx="203" cy="193" r="2.5" fill="{INK}"/>
<path d="M225 173 A42 42 0 0 0 195.3 185.3" fill="none" stroke="{INK}" stroke-width="1.6"/>
<text x="204" y="165" text-anchor="middle" font-size="13.5" font-weight="700" fill="{INK}">45°</text>
<rect x="133" y="139" width="56" height="24" rx="12" fill="#FFFFFF" stroke="{INK}" stroke-width="1.4"/>
<text x="161" y="156" text-anchor="middle" font-size="13.5" font-weight="700" fill="{INK}">≈ 2 m</text>
<g stroke="{LINE}" stroke-width="2.5" stroke-linecap="round">
<line x1="119" y1="109" x2="104" y2="104"/><line x1="119" y1="109" x2="121" y2="93"/><line x1="119" y1="109" x2="104" y2="122"/>
</g>
<rect x="102" y="104.5" width="34" height="9" rx="3" fill="{INK}" transform="rotate(-45 119 109)"/>
<circle cx="123" cy="113" r="2.4" fill="{VIEW}"/>
<text x="16" y="68" font-size="15" font-weight="800" fill="{INK}">Tu móvil</text>
<text x="16" y="86" font-size="13.5" fill="{GRAY}">en vertical, a 1,2 m</text>
<text x="16" y="102" font-size="13.5" fill="{GRAY}">del suelo</text>
<g transform="translate(225 215)">
<ellipse cx="-16" cy="-6" rx="6" ry="11" fill="{LINE}" transform="rotate(-10 -16 -6)"/>
<ellipse cx="17" cy="20" rx="6" ry="11" fill="{LINE}" transform="rotate(30 17 20)"/>
<line x1="-27.7" y1="-16" x2="-14" y2="-31" stroke="{LEFT}" stroke-width="6" stroke-linecap="round" stroke-opacity=".55"/>
<line x1="27.7" y1="16" x2="15" y2="-19" stroke="{RIGHT}" stroke-width="6" stroke-linecap="round" stroke-opacity=".55"/>
<ellipse cx="0" cy="0" rx="32" ry="13" fill="{INK}" transform="rotate(30)"/>
<path d="M-4.5 -10 L2 -24 L8.5 -10 Z" fill="#D3D1BA" stroke="{INK}" stroke-width="2" stroke-linejoin="round"/>
<circle cx="2" cy="-3" r="12" fill="#D3D1BA" stroke="{INK}" stroke-width="2"/>
<circle cx="-14" cy="-31" r="6.5" fill="{LEFT}" stroke="{INK}" stroke-width="1.2"/>
<circle cx="15" cy="-19" r="6.5" fill="{RIGHT}" stroke="{INK}" stroke-width="1.2"/>
<text x="0" y="52" text-anchor="middle" font-size="14" font-weight="800" fill="{INK}">Tú</text>
</g>
<polyline points="152,238 172,238 193,205" fill="none" stroke="{INK}" stroke-width="1.2"/>
<text x="148" y="235" text-anchor="end" font-size="13.5" font-weight="700" fill="{INK}">Hombro</text>
<text x="148" y="251" text-anchor="end" font-size="13.5" font-weight="700" fill="{INK}">adelantado</text>
</svg>'''


def side_view():
    """De lado: el movil a 1,2 m del suelo y el encuadre con un palmo de margen arriba y abajo."""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 300" font-family="{FONT}">
<rect width="240" height="300" rx="18" fill="{PAPER}"/>
<path d="M46 160 L240 82 L240 336 Z" fill="{VIEW}" fill-opacity=".22"/>
<line x1="46" y1="160" x2="240" y2="82" stroke="{VIEW}" stroke-width="1.4" stroke-dasharray="4 4"/>
<line x1="46" y1="160" x2="200" y2="296" stroke="{VIEW}" stroke-width="1.4" stroke-dasharray="4 4"/>
<line x1="8" y1="262" x2="232" y2="262" stroke="{LINE}" stroke-width="2"/>
<g stroke="{LINE}" stroke-width="2.5" stroke-linecap="round">
<line x1="40" y1="182" x2="24" y2="262"/><line x1="40" y1="182" x2="56" y2="262"/><line x1="40" y1="182" x2="40" y2="262"/>
</g>
<rect x="34" y="148" width="12" height="36" rx="3" fill="{INK}"/>
<circle cx="46" cy="160" r="2.4" fill="{VIEW}"/>
<g stroke="{INK}" stroke-width="1.4">
<line x1="70" y1="166" x2="70" y2="262"/><line x1="65" y1="166" x2="75" y2="166"/><line x1="65" y1="262" x2="75" y2="262"/>
</g>
<text x="78" y="234" font-size="13.5" font-weight="700" fill="{INK}">1,2 m</text>
<g stroke="{INK}" stroke-width="1.4">
<line x1="46" y1="44" x2="180" y2="44"/><line x1="46" y1="39" x2="46" y2="49"/><line x1="180" y1="39" x2="180" y2="49"/>
</g>
<text x="113" y="34" text-anchor="middle" font-size="13.5" font-weight="700" fill="{INK}">≈ 2 m</text>
<g stroke="{INK}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" fill="none">
<line x1="180" y1="146" x2="180" y2="206"/>
<line x1="180" y1="206" x2="170" y2="262"/><line x1="180" y1="206" x2="193" y2="262"/>
<polyline points="181,153 184,174 172,147"/>
</g>
<circle cx="180" cy="133" r="11" fill="#D3D1BA" stroke="{INK}" stroke-width="2"/>
<polyline points="179,153 169,172 160,142" fill="none" stroke="{LEFT}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="172" cy="146" r="5" fill="{RIGHT}" stroke="{INK}" stroke-width="1.2"/>
<circle cx="160" cy="141" r="5" fill="{LEFT}" stroke="{INK}" stroke-width="1.2"/>
<g stroke="{INK}" stroke-width="1.4" fill="none">
<polyline points="205,106 210,106 210,122 205,122"/><polyline points="205,262 210,262 210,278 205,278"/>
<line x1="210" y1="106" x2="222" y2="86"/>
</g>
<text x="232" y="66" text-anchor="end" font-size="13.5" font-weight="700" fill="{INK}">Un palmo</text>
<text x="232" y="80" text-anchor="end" font-size="13.5" font-weight="700" fill="{INK}">de margen</text>
</svg>'''
