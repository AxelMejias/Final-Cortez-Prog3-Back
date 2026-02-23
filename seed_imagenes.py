"""
Script para actualizar las imágenes de los productos ya cargados.
Uso:
  python seed_imagenes.py                          # contra Render
  python seed_imagenes.py http://localhost:4000     # contra local
"""

import sys
import requests
import time

# ── Configuración ──────────────────────────────────────────────
API_URL = sys.argv[1] if len(sys.argv) > 1 else "https://final-cortez-prog3-back.onrender.com"
API_URL = API_URL.rstrip("/")
ADMIN_TOKEN = "admin-secret-123"
HEADERS = {"x-admin-token": ADMIN_TOKEN, "Content-Type": "application/json"}

# ── Imágenes por producto ──────────────────────────────────────
# nombre_producto → url_imagen
IMAGENES = {
    # ─── Cuadernos y Anotadores ───
    "Cuaderno Rivadavia Tapa Dura 98 hojas": "https://http2.mlstatic.com/D_NQ_NP_725697-MLA46665795415_072021-O.webp",
    "Cuaderno Rivadavia Tapa Dura 48 hojas": "https://http2.mlstatic.com/D_NQ_NP_986498-MLA46665795417_072021-O.webp",
    "Cuaderno Rivadavia Tapa Flexible 48 hojas": "https://http2.mlstatic.com/D_NQ_NP_637017-MLA48658741498_122021-O.webp",
    "Cuaderno Espiralado A4 80 hojas": "https://http2.mlstatic.com/D_NQ_NP_648585-MLA48856001578_012022-O.webp",
    "Cuaderno Espiralado A4 120 hojas": "https://http2.mlstatic.com/D_NQ_NP_931081-MLA50437278498_062022-O.webp",
    "Cuaderno Universitario Ledesma 80 hojas": "https://http2.mlstatic.com/D_NQ_NP_781498-MLA49018947498_022022-O.webp",
    "Repuesto Rivadavia Rayado x 480 hojas": "https://http2.mlstatic.com/D_NQ_NP_806966-MLA44367660253_122020-O.webp",
    "Repuesto Rivadavia Cuadriculado x 480 hojas": "https://http2.mlstatic.com/D_NQ_NP_625565-MLA46665803793_072021-O.webp",
    "Anotador Espiralado A6": "https://http2.mlstatic.com/D_NQ_NP_990267-MLA50282647794_062022-O.webp",
    "Block de Dibujo Canson A4": "https://http2.mlstatic.com/D_NQ_NP_887782-MLA47530735498_092021-O.webp",

    # ─── Lápices y Colores ───
    "Lápiz Negro HB Faber Castell": "https://http2.mlstatic.com/D_NQ_NP_699498-MLA44802858498_022021-O.webp",
    "Lápiz Negro 2B Faber Castell": "https://http2.mlstatic.com/D_NQ_NP_988370-MLA46018305498_052021-O.webp",
    "Caja Lápices de Colores Faber Castell x12": "https://http2.mlstatic.com/D_NQ_NP_661073-MLA45648582736_042021-O.webp",
    "Caja Lápices de Colores Faber Castell x24": "https://http2.mlstatic.com/D_NQ_NP_836557-MLA45648610672_042021-O.webp",
    "Caja Lápices de Colores Faber Castell x36": "https://http2.mlstatic.com/D_NQ_NP_815532-MLA48225058217_112021-O.webp",
    "Lápices Acuarelables Faber Castell x12": "https://http2.mlstatic.com/D_NQ_NP_773498-MLA48225042143_112021-O.webp",
    "Crayones Cera Jovi x12": "https://http2.mlstatic.com/D_NQ_NP_696498-MLA49613947498_042022-O.webp",
    "Lápiz Mecánico 0.5mm Pentel": "https://http2.mlstatic.com/D_NQ_NP_882027-MLA44490740637_012021-O.webp",
    "Minas 0.5mm HB Pentel x 12": "https://http2.mlstatic.com/D_NQ_NP_697925-MLA47229498498_082021-O.webp",
    "Sacapuntas Metálico Simple": "https://http2.mlstatic.com/D_NQ_NP_626291-MLA48225067187_112021-O.webp",
    "Sacapuntas Doble con Depósito": "https://http2.mlstatic.com/D_NQ_NP_738285-MLA50146293842_052022-O.webp",

    # ─── Bolígrafos y Marcadores ───
    "Bolígrafo Bic Cristal Azul": "https://http2.mlstatic.com/D_NQ_NP_862227-MLA44490724453_012021-O.webp",
    "Bolígrafo Bic Cristal Negro": "https://http2.mlstatic.com/D_NQ_NP_744026-MLA44490732785_012021-O.webp",
    "Bolígrafo Bic Cristal Rojo": "https://http2.mlstatic.com/D_NQ_NP_949942-MLA44490732787_012021-O.webp",
    "Pack Bolígrafos Bic x10 Surtidos": "https://http2.mlstatic.com/D_NQ_NP_823498-MLA50312278498_062022-O.webp",
    "Microfibra Filgo Punta Media Negra": "https://http2.mlstatic.com/D_NQ_NP_732698-MLA48658741502_122021-O.webp",
    "Set Microfibras Filgo x10 Colores": "https://http2.mlstatic.com/D_NQ_NP_685498-MLA49613931498_042022-O.webp",
    "Roller Pilot V5 Azul": "https://http2.mlstatic.com/D_NQ_NP_807032-MLA47229534498_082021-O.webp",
    "Marcador Permanente Negro Edding 300": "https://http2.mlstatic.com/D_NQ_NP_685498-MLA47530735502_092021-O.webp",
    "Resaltador Filgo Amarillo": "https://http2.mlstatic.com/D_NQ_NP_628498-MLA48856001582_012022-O.webp",
    "Set Resaltadores Filgo x4 Colores": "https://http2.mlstatic.com/D_NQ_NP_729498-MLA50282647798_062022-O.webp",

    # ─── Gomas y Correctores ───
    "Goma de Borrar Staedtler Mars Plastic": "https://http2.mlstatic.com/D_NQ_NP_846498-MLA44802858502_022021-O.webp",
    "Goma Lapiz/Tinta Staedtler Doble": "https://http2.mlstatic.com/D_NQ_NP_985498-MLA46018305502_052021-O.webp",
    "Corrector Líquido Liquid Paper": "https://http2.mlstatic.com/D_NQ_NP_637498-MLA48225058221_112021-O.webp",
    "Cinta Correctora Pilot 5mm x 6m": "https://http2.mlstatic.com/D_NQ_NP_748498-MLA49018947502_022022-O.webp",

    # ─── Papelería ───
    "Resma A4 Autor 75g 500 hojas": "https://http2.mlstatic.com/D_NQ_NP_936021-MLA44490732863_012021-O.webp",
    "Resma A4 Autor 80g 500 hojas": "https://http2.mlstatic.com/D_NQ_NP_794498-MLA45648582740_042021-O.webp",
    "Resma Oficio 75g 500 hojas": "https://http2.mlstatic.com/D_NQ_NP_882498-MLA46665803797_072021-O.webp",
    "Papel Glasé x10 hojas": "https://http2.mlstatic.com/D_NQ_NP_691498-MLA48658741506_122021-O.webp",
    "Cartulina Blanca A4 x10": "https://http2.mlstatic.com/D_NQ_NP_754498-MLA50437278502_062022-O.webp",
    "Cartulina Color A4 x10": "https://http2.mlstatic.com/D_NQ_NP_629498-MLA49613947502_042022-O.webp",
    "Papel Afiche Blanco 70x100cm": "https://http2.mlstatic.com/D_NQ_NP_820498-MLA47530735506_092021-O.webp",
    "Papel Afiche Color 70x100cm": "https://http2.mlstatic.com/D_NQ_NP_935498-MLA48856001586_012022-O.webp",
    "Papel Crepe Varios Colores": "https://http2.mlstatic.com/D_NQ_NP_741498-MLA50282647802_062022-O.webp",
    "Sobre Manila A4": "https://http2.mlstatic.com/D_NQ_NP_856498-MLA44367660257_122020-O.webp",

    # ─── Útiles de Geometría ───
    "Set Geometría Completo (4 piezas)": "https://http2.mlstatic.com/D_NQ_NP_832626-MLA43868285918_102020-O.webp",
    "Regla Plástica 30cm Pizzini": "https://http2.mlstatic.com/D_NQ_NP_648498-MLA44802858506_022021-O.webp",
    "Regla Metálica 30cm": "https://http2.mlstatic.com/D_NQ_NP_795498-MLA46018305506_052021-O.webp",
    "Compás Escolar Pizzini": "https://http2.mlstatic.com/D_NQ_NP_937498-MLA48225042147_112021-O.webp",
    "Compás Técnico Profesional": "https://http2.mlstatic.com/D_NQ_NP_826498-MLA49018947506_022022-O.webp",
    "Transportador 180° Plástico": "https://http2.mlstatic.com/D_NQ_NP_719498-MLA50146293846_052022-O.webp",
    "Escuadra 45° 20cm": "https://http2.mlstatic.com/D_NQ_NP_831498-MLA47229498502_082021-O.webp",
    "Escuadra 60° 20cm": "https://http2.mlstatic.com/D_NQ_NP_924498-MLA48225067191_112021-O.webp",

    # ─── Mochilas y Cartucheras ───
    "Mochila Escolar Negra Básica": "https://http2.mlstatic.com/D_NQ_NP_744795-MLA51822057771_102022-O.webp",
    "Mochila Escolar con Carro": "https://http2.mlstatic.com/D_NQ_NP_835498-MLA50312278502_062022-O.webp",
    "Mochila Urbana Gris": "https://http2.mlstatic.com/D_NQ_NP_942498-MLA49613931502_042022-O.webp",
    "Cartuchera de Tela Simple": "https://http2.mlstatic.com/D_NQ_NP_625498-MLA48658741510_122021-O.webp",
    "Cartuchera 2 Pisos con Útiles": "https://http2.mlstatic.com/D_NQ_NP_738498-MLA50437278506_062022-O.webp",
    "Cartuchera de Silicona": "https://http2.mlstatic.com/D_NQ_NP_849498-MLA47530735510_092021-O.webp",

    # ─── Adhesivos y Cintas ───
    "Plasticola 40g": "https://http2.mlstatic.com/D_NQ_NP_931498-MLA44490724457_012021-O.webp",
    "Plasticola 250g": "https://http2.mlstatic.com/D_NQ_NP_825498-MLA45648610676_042021-O.webp",
    "Barra de Pegamento Pritt 20g": "https://http2.mlstatic.com/D_NQ_NP_716498-MLA46665795419_072021-O.webp",
    "Cinta Scotch Transparente 18mm x 25m": "https://http2.mlstatic.com/D_NQ_NP_938498-MLA48856001590_012022-O.webp",
    "Cinta de Papel (Enmascarar) 18mm x 50m": "https://http2.mlstatic.com/D_NQ_NP_847498-MLA50282647806_062022-O.webp",
    "Voligoma 30ml": "https://http2.mlstatic.com/D_NQ_NP_729498-MLA44367660261_122020-O.webp",
    "Cinta Bifaz 12mm x 10m": "https://http2.mlstatic.com/D_NQ_NP_638498-MLA44802858510_022021-O.webp",

    # ─── Tijeras y Corte ───
    "Tijera Escolar Punta Roma 13cm": "https://http2.mlstatic.com/D_NQ_NP_827498-MLA46018305510_052021-O.webp",
    "Tijera Multiuso Acero 21cm": "https://http2.mlstatic.com/D_NQ_NP_936498-MLA48225058225_112021-O.webp",
    "Trincheta Chica 9mm": "https://http2.mlstatic.com/D_NQ_NP_748498-MLA49018947510_022022-O.webp",
    "Trincheta Grande 18mm": "https://http2.mlstatic.com/D_NQ_NP_839498-MLA50146293850_052022-O.webp",

    # ─── Organización ───
    "Carpeta Escolar 3 Anillos N3": "https://http2.mlstatic.com/D_NQ_NP_924498-MLA47229534502_082021-O.webp",
    "Carpeta Oficio 2 Anillos": "https://http2.mlstatic.com/D_NQ_NP_837498-MLA48225067195_112021-O.webp",
    "Bibliorato A4 Lomo Ancho": "https://http2.mlstatic.com/D_NQ_NP_746498-MLA50312278506_062022-O.webp",
    "Folio A4 Cristal x100": "https://http2.mlstatic.com/D_NQ_NP_935498-MLA49613947506_042022-O.webp",
    "Separadores A4 x6 Colores": "https://http2.mlstatic.com/D_NQ_NP_828498-MLA48658741514_122021-O.webp",
    "Clips Metálicos x100": "https://http2.mlstatic.com/D_NQ_NP_739498-MLA50437278510_062022-O.webp",
    "Broches Clips Doble x12": "https://http2.mlstatic.com/D_NQ_NP_651498-MLA47530735514_092021-O.webp",
    "Abrochadora Pinza Metal": "https://http2.mlstatic.com/D_NQ_NP_842498-MLA44490732789_012021-O.webp",
    "Broches para Abrochadora 24/6 x1000": "https://http2.mlstatic.com/D_NQ_NP_953498-MLA45648582744_042021-O.webp",
    "Perforadora 2 Agujeros Metal": "https://http2.mlstatic.com/D_NQ_NP_826498-MLA46665803801_072021-O.webp",

    # ─── Arte y Manualidades ───
    "Témperas Alba x6 Colores": "https://http2.mlstatic.com/D_NQ_NP_737498-MLA48856001594_012022-O.webp",
    "Témperas Alba x12 Colores": "https://http2.mlstatic.com/D_NQ_NP_948498-MLA50282647810_062022-O.webp",
    "Acuarelas Acuarelín x12": "https://http2.mlstatic.com/D_NQ_NP_639498-MLA44367660265_122020-O.webp",
    "Pincel Escolar Nº8": "https://http2.mlstatic.com/D_NQ_NP_750498-MLA44802858514_022021-O.webp",
    "Set Pinceles Escolares x6": "https://http2.mlstatic.com/D_NQ_NP_861498-MLA46018305514_052021-O.webp",
    "Plastilina x12 Colores": "https://http2.mlstatic.com/D_NQ_NP_972498-MLA48225042151_112021-O.webp",

    # ─── Servicios de Impresión ───
    "Impresión B/N x hoja": "https://cdn-icons-png.flaticon.com/512/3063/3063822.png",
    "Impresión Color x hoja": "https://cdn-icons-png.flaticon.com/512/2612/2612824.png",
    "Fotocopia B/N x hoja": "https://cdn-icons-png.flaticon.com/512/4726/4726038.png",
    "Anillado Plástico": "https://cdn-icons-png.flaticon.com/512/2541/2541988.png",
    "Laminado A4": "https://cdn-icons-png.flaticon.com/512/2612/2612796.png",
}


def main():
    # 1. Obtener todos los productos actuales (limit alto para traer todos)
    print(f"Obteniendo productos de {API_URL}/api/productos ...")
    r = requests.get(f"{API_URL}/api/productos", params={"limit": 500}, timeout=30)
    if r.status_code != 200:
        print(f"Error obteniendo productos: {r.status_code}")
        return

    productos = r.json()
    if isinstance(productos, dict) and "productos" in productos:
        productos = productos["productos"]

    print(f"Encontrados {len(productos)} productos. Actualizando imágenes...")
    print("=" * 60)

    ok = 0
    skip = 0
    errores = []

    for i, prod in enumerate(productos, 1):
        nombre = prod.get("nombre", "")
        pid = prod.get("_id") or prod.get("id")
        imagen_nueva = IMAGENES.get(nombre)

        if not imagen_nueva:
            skip += 1
            print(f"  [{i}/{len(productos)}] - {nombre} (sin imagen definida, skip)")
            continue

        payload = {
            "nombre": nombre,
            "categoria": prod.get("categoria", "Sin Categoría"),
            "precio": prod.get("precio", 0),
            "stock": prod.get("stock", 0),
            "imagen": imagen_nueva,
            "descripcion": prod.get("descripcion", ""),
        }

        try:
            resp = requests.put(f"{API_URL}/api/productos/{pid}", json=payload, headers=HEADERS, timeout=30)
            if resp.status_code == 200:
                ok += 1
                print(f"  [{i}/{len(productos)}] ✓ {nombre}")
            else:
                msg = resp.text[:120]
                errores.append((nombre, msg))
                print(f"  [{i}/{len(productos)}] ✗ {nombre} → {resp.status_code}: {msg}")
        except Exception as e:
            errores.append((nombre, str(e)))
            print(f"  [{i}/{len(productos)}] ✗ {nombre} → {e}")

        if i % 10 == 0:
            time.sleep(0.5)

    print("=" * 60)
    print(f"Resultado: {ok} actualizados, {skip} sin imagen, {len(errores)} errores")
    if errores:
        print("\nErrores:")
        for nombre, msg in errores:
            print(f"  - {nombre}: {msg}")


if __name__ == "__main__":
    main()
