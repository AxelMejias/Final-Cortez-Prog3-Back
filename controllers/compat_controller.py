import os
import json
import time
import secrets
import hashlib
import logging
from datetime import datetime
from datetime import date
from typing import Any, Dict, List, Optional

import requests
from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from config.database import get_db
from models.bill import BillModel
from models.category import CategoryModel
from models.client import ClientModel
from models.enums import DeliveryMethod, PaymentType, Status
from models.order import OrderModel
from models.order_detail import OrderDetailModel
from models.product import ProductModel

router = APIRouter(prefix="/api", tags=["Compat"])
logger = logging.getLogger(__name__)

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "admin-secret-123")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@emelyn.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
PLACEHOLDER_IMAGE = os.getenv(
    "PLACEHOLDER_IMAGE",
    "https://via.placeholder.com/400x400.png?text=Producto"
)

# Estado en memoria para MVP
carts: Dict[str, List[Dict[str, Any]]] = {}
favorites: Dict[str, List[Dict[str, Any]]] = {}
bills: List[Dict[str, Any]] = []

RESET_TOKENS_FILE = os.getenv(
    "RESET_TOKENS_FILE",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "reset_tokens.json")),
)

FAVORITES_FILE = os.getenv(
    "FAVORITES_FILE",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "favorites.json")),
)

N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")
CLOUDINARY_UPLOAD_PRESET = os.getenv("CLOUDINARY_UPLOAD_PRESET", "")
CLOUDINARY_FOLDER = os.getenv("CLOUDINARY_FOLDER", "libreria-emelyn/productos")
CLOUDINARY_TIMEOUT = int(os.getenv("CLOUDINARY_TIMEOUT", "30"))


def load_favorites() -> Dict[str, List[Dict[str, Any]]]:
    try:
        if not os.path.exists(FAVORITES_FILE):
            return {}
        with open(FAVORITES_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_favorites(favs: Dict[str, List[Dict[str, Any]]]):
    os.makedirs(os.path.dirname(FAVORITES_FILE), exist_ok=True)
    with open(FAVORITES_FILE, "w", encoding="utf-8") as file:
        json.dump(favs, file, ensure_ascii=False, indent=2)


def load_reset_tokens() -> Dict[str, Dict[str, Any]]:
    try:
        if not os.path.exists(RESET_TOKENS_FILE):
            return {}
        with open(RESET_TOKENS_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_reset_tokens(tokens: Dict[str, Dict[str, Any]]):
    os.makedirs(os.path.dirname(RESET_TOKENS_FILE), exist_ok=True)
    with open(RESET_TOKENS_FILE, "w", encoding="utf-8") as file:
        json.dump(tokens, file, ensure_ascii=False, indent=2)


# Reset tokens still in memory (short-lived by nature)
reset_tokens: Dict[str, Dict[str, Any]] = load_reset_tokens()

# Carts and favorites in memory (acceptable for MVP)
carts: Dict[str, List[Dict[str, Any]]] = {}
favorites = load_favorites()

DEFAULT_PRODUCT_MEDIA = {
    "resma a4 autor 75g (500 hojas)": {
        "imagen": "https://http2.mlstatic.com/D_NQ_NP_936021-MLA44490732863_012021-O.webp",
        "descripcion": "Resma de papel de calidad para impresoras",
    },
    "cuaderno rivadavia tapa dura (araña)": {
        "imagen": "https://http2.mlstatic.com/D_NQ_NP_725697-MLA46665795415_072021-O.webp",
        "descripcion": "Cuaderno con tapa dura resistente",
    },
    "caja lápices faber castell x12": {
        "imagen": "https://http2.mlstatic.com/D_NQ_NP_661073-MLA45648582736_042021-O.webp",
        "descripcion": "Set de lápices de colores profesionales",
    },
    "set geometría (regla, escuadra, transp.)": {
        "imagen": "https://http2.mlstatic.com/D_NQ_NP_832626-MLA43868285918_102020-O.webp",
        "descripcion": "Juego completo de geometría para estudiantes",
    },
    "mochila escolar básica negra": {
        "imagen": "https://http2.mlstatic.com/D_NQ_NP_744795-MLA51822057771_102022-O.webp",
        "descripcion": "Mochila ergonómica y resistente",
    },
    "servicio: impresión byn x hoja": {
        "imagen": "https://cdn-icons-png.flaticon.com/512/3063/3063822.png",
        "descripcion": "Servicio de impresión en blanco y negro",
    },
}


class RegisterBody(BaseModel):
    nombre: str
    email: str
    password: str


class LoginBody(BaseModel):
    email: str
    password: str


class CategoryBody(BaseModel):
    nombre: str


class CategoryRenameBody(BaseModel):
    nuevo: str


class ProductBody(BaseModel):
    nombre: str
    categoria: str
    precio: float
    imagen: Optional[str] = None
    descripcion: Optional[str] = None
    stock: Optional[int] = 0


class BillBody(BaseModel):
    usuarioEmail: str
    usuarioNombre: str
    productos: List[Dict[str, Any]]
    total: float


class BillStateBody(BaseModel):
    estado: str


def verify_admin(x_admin_token: Optional[str] = Header(default=None)):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Token de admin inválido")


def to_product_json(product: ProductModel) -> Dict[str, Any]:
    categoria = product.category.name if product.category else "Sin Categoría"

    # Use DB columns directly; fall back to defaults for legacy data
    image_url = product.image
    description = product.description

    if not image_url:
        media = DEFAULT_PRODUCT_MEDIA.get((product.name or "").strip().lower(), {})
        image_url = media.get("imagen") if isinstance(media, dict) else None
    if not description:
        media = DEFAULT_PRODUCT_MEDIA.get((product.name or "").strip().lower(), {})
        description = media.get("descripcion") if isinstance(media, dict) else None

    return {
        "_id": str(product.id_key),
        "id": str(product.id_key),
        "nombre": product.name,
        "categoria": categoria,
        "precio": float(product.price or 0),
        "imagen": image_url or PLACEHOLDER_IMAGE,
        "descripcion": description or f"Producto de calidad premium de nuestra librería Emelyn. Ideal para todo tipo de uso escolar y profesional.",
        "stock": int(product.stock or 0),
    }


def get_or_create_category(db: Session, name: str) -> CategoryModel:
    normalized = name.strip()
    # Try exact match first (handles accented chars that SQLite lower() can't)
    category = db.query(CategoryModel).filter(CategoryModel.name == normalized).first()
    if category:
        return category
    # Fallback: case-insensitive (works for ASCII)
    category = db.query(CategoryModel).filter(func.lower(CategoryModel.name) == normalized.lower()).first()
    if category:
        return category

    category = CategoryModel(name=normalized)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def upload_image_to_cloudinary(file: UploadFile) -> str:
    if not file:
        raise HTTPException(status_code=400, detail="Imagen requerida")

    if not CLOUDINARY_CLOUD_NAME:
        return PLACEHOLDER_IMAGE

    try:
        content = file.file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Archivo de imagen vacío")

        upload_url = f"https://api.cloudinary.com/v1_1/{CLOUDINARY_CLOUD_NAME}/image/upload"
        files = {"file": (file.filename or "producto.jpg", content, file.content_type or "application/octet-stream")}

        data: Dict[str, Any] = {"folder": CLOUDINARY_FOLDER}

        if CLOUDINARY_UPLOAD_PRESET:
            data["upload_preset"] = CLOUDINARY_UPLOAD_PRESET
        else:
            if not CLOUDINARY_API_KEY or not CLOUDINARY_API_SECRET:
                return PLACEHOLDER_IMAGE

            timestamp = int(time.time())
            signature_base = f"folder={CLOUDINARY_FOLDER}&timestamp={timestamp}{CLOUDINARY_API_SECRET}"
            signature = hashlib.sha1(signature_base.encode("utf-8")).hexdigest()

            data.update({
                "api_key": CLOUDINARY_API_KEY,
                "timestamp": timestamp,
                "signature": signature,
            })

        response = requests.post(upload_url, data=data, files=files, timeout=CLOUDINARY_TIMEOUT)
        if not response.ok:
            logger.error("Cloudinary upload failed: %s", response.text)
            raise HTTPException(status_code=502, detail="Error al subir imagen a Cloudinary")

        payload = response.json()
        return payload.get("secure_url") or payload.get("url") or PLACEHOLDER_IMAGE
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected Cloudinary upload error: %s", exc)
        raise HTTPException(status_code=500, detail="Error interno al subir imagen")


def status_to_label(status: Optional[Status]) -> str:
    if status == Status.DELIVERED:
        return "Entregado"
    if status == Status.IN_PROGRESS:
        return "En camino"
    if status == Status.CANCELED:
        return "Cancelado"
    return "Procesando"


def label_to_status(label: str) -> Status:
    normalized = (label or "").strip().lower()
    if normalized == "entregado":
        return Status.DELIVERED
    if normalized == "en camino":
        return Status.IN_PROGRESS
    if normalized == "cancelado":
        return Status.CANCELED
    return Status.PENDING


def to_bill_json(order: OrderModel) -> Dict[str, Any]:
    bill = order.bill
    client = order.client
    products = []

    for detail in order.order_details or []:
        product_name = detail.product.name if detail.product else f"Producto #{detail.product_id or ''}".strip()
        products.append({
            "nombre": product_name,
            "cantidad": int(detail.quantity or 0),
            "precio": float(detail.price or 0),
        })

    order_date = order.date or datetime.now()

    return {
        "id": str(bill.id_key if bill else order.id_key),
        "_id": str(bill.id_key if bill else order.id_key),
        "usuarioEmail": client.email if client else "",
        "usuarioNombre": (client.name if client and client.name else "Cliente"),
        "productos": products,
        "total": float(order.total or (bill.total if bill else 0) or 0),
        "fecha": order_date.strftime("%Y-%m-%d"),
        "hora": order_date.strftime("%H:%M"),
        "estado": status_to_label(order.status),
        "billNumber": bill.bill_number if bill else None,
    }


@router.get("/productos")
def list_productos(
    q: Optional[str] = None,
    categoria: Optional[str] = None,
    precioMin: Optional[float] = None,
    precioMax: Optional[float] = None,
    conStock: Optional[bool] = False,
    sort: Optional[str] = None,
    page: int = 1,
    limit: int = 12,
    db: Session = Depends(get_db),
):
    query = db.query(ProductModel).options(joinedload(ProductModel.category)).outerjoin(CategoryModel)

    if q:
        query = query.filter(ProductModel.name.ilike(f"%{q}%"))
    if categoria:
        # Exact match first (handles accented chars that SQLite lower() can't)
        cat_filter = db.query(CategoryModel).filter(CategoryModel.name == categoria).first()
        if not cat_filter:
            cat_filter = db.query(CategoryModel).filter(func.lower(CategoryModel.name) == categoria.lower()).first()
        if cat_filter:
            query = query.filter(ProductModel.category_id == cat_filter.id_key)
        else:
            query = query.filter(ProductModel.category_id == -1)  # No match
    if precioMin is not None:
        query = query.filter(ProductModel.price >= precioMin)
    if precioMax is not None:
        query = query.filter(ProductModel.price <= precioMax)
    if conStock:
        query = query.filter(ProductModel.stock > 0)

    if sort == "nombre_asc":
        query = query.order_by(ProductModel.name.asc())
    elif sort == "nombre_desc":
        query = query.order_by(ProductModel.name.desc())
    elif sort == "precio_asc":
        query = query.order_by(ProductModel.price.asc())
    elif sort == "precio_desc":
        query = query.order_by(ProductModel.price.desc())
    else:
        query = query.order_by(ProductModel.id_key.desc())

    total = query.count()
    page = max(page, 1)
    limit = max(limit, 1)
    offset = (page - 1) * limit

    productos = query.offset(offset).limit(limit).all()

    return {
        "productos": [to_product_json(item) for item in productos],
        "paginacion": {
            "total": total,
            "pagina": page,
            "porPagina": limit,
            "totalPaginas": (total + limit - 1) // limit,
        },
    }


@router.get("/productos/{id_key}")
def get_producto(id_key: str, db: Session = Depends(get_db)):
    try:
        pid = int(id_key)
    except ValueError:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    product = (
        db.query(ProductModel)
        .options(joinedload(ProductModel.category))
        .filter(ProductModel.id_key == pid)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    return to_product_json(product)


@router.get("/categorias")
def get_categorias(db: Session = Depends(get_db)):
    categories = db.query(CategoryModel).order_by(CategoryModel.name.asc()).all()
    return [c.name for c in categories]


@router.post("/categorias")
def create_categoria(body: CategoryBody, db: Session = Depends(get_db), admin_check: None = Depends(verify_admin)):
    name = body.nombre.strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre de la categoría es requerido")

    exists = db.query(CategoryModel).filter(func.lower(CategoryModel.name) == name.lower()).first()
    if exists:
        raise HTTPException(status_code=400, detail="La categoría ya existe")

    category = CategoryModel(name=name)
    db.add(category)
    db.commit()
    return {"mensaje": "Categoría creada", "nombre": name}


@router.put("/categorias/{old_name}")
def rename_categoria(old_name: str, body: CategoryRenameBody, db: Session = Depends(get_db), admin_check: None = Depends(verify_admin)):
    old_name = old_name.strip()
    new_name = body.nuevo.strip()

    if not new_name:
        raise HTTPException(status_code=400, detail="El nuevo nombre es requerido")

    old_category = db.query(CategoryModel).filter(func.lower(CategoryModel.name) == old_name.lower()).first()
    if not old_category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    if old_name.lower() == new_name.lower():
        return {"mensaje": "Categoría actualizada", "anterior": old_name, "nueva": new_name, "productosActualizados": 0}

    target_category = db.query(CategoryModel).filter(func.lower(CategoryModel.name) == new_name.lower()).first()

    if target_category is None:
        target_category = CategoryModel(name=new_name)
        db.add(target_category)
        db.commit()
        db.refresh(target_category)

    updated = db.query(ProductModel).filter(ProductModel.category_id == old_category.id_key).update(
        {ProductModel.category_id: target_category.id_key}, synchronize_session=False
    )

    db.delete(old_category)
    db.commit()

    return {
        "mensaje": "Categoría actualizada",
        "anterior": old_name,
        "nueva": new_name,
        "productosActualizados": updated,
    }


@router.delete("/categorias/{name}")
def delete_categoria(name: str, db: Session = Depends(get_db), admin_check: None = Depends(verify_admin)):
    category = db.query(CategoryModel).filter(func.lower(CategoryModel.name) == name.lower()).first()
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    sin_categoria = get_or_create_category(db, "Sin Categoría")
    updated = db.query(ProductModel).filter(ProductModel.category_id == category.id_key).update(
        {ProductModel.category_id: sin_categoria.id_key}, synchronize_session=False
    )

    if category.id_key != sin_categoria.id_key:
        db.delete(category)
    db.commit()

    return {
        "mensaje": "Categoría eliminada (productos movidos a Sin Categoría)",
        "nombre": name,
        "productosAfectados": updated,
    }


@router.post("/register")
def register(body: RegisterBody, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    name = body.nombre.strip()

    exists = db.query(ClientModel).filter(func.lower(ClientModel.email) == email).first()
    if exists:
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    client = ClientModel(name=name, lastname="", email=email, telephone="0000000", password_hash=body.password)
    db.add(client)
    db.commit()
    db.refresh(client)

    return {
        "success": True,
        "usuario": {
            "id": client.id_key,
            "nombre": name,
            "email": email,
            "tipo": "cliente",
        },
    }


@router.post("/login")
def login(body: LoginBody, db: Session = Depends(get_db)):
    email = body.email.strip().lower()

    if email == ADMIN_EMAIL.lower() and body.password == ADMIN_PASSWORD:
        return {
            "success": True,
            "tipo": "admin",
            "admin": {
                "nombre": "Administrador",
                "email": ADMIN_EMAIL,
                "tipo": "admin",
            },
        }

    client = db.query(ClientModel).filter(func.lower(ClientModel.email) == email).first()
    if not client:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    if client.password_hash and client.password_hash != body.password:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    return {
        "success": True,
        "tipo": "cliente",
        "usuario": {
            "id": client.id_key,
            "nombre": (client.name or "Cliente"),
            "email": client.email,
            "tipo": "cliente",
        },
    }


@router.post("/logout")
def logout():
    return {"success": True}


@router.post("/forgot-password")
def forgot_password(body: Dict[str, Any], db: Session = Depends(get_db)):
    email = str((body or {}).get("email") or "").strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="Email requerido")

    client = db.query(ClientModel).filter(func.lower(ClientModel.email) == email).first()
    if not client:
        return {"success": True, "mensaje": "Si el email existe, se enviaron instrucciones"}

    token = secrets.token_urlsafe(32)
    expires_at = int(time.time()) + (15 * 60)
    reset_tokens[token] = {
        "email": email,
        "expiresAt": expires_at,
    }
    save_reset_tokens(reset_tokens)

    reset_link = f"{FRONTEND_URL.rstrip('/')}/reset-password?token={token}"

    if N8N_WEBHOOK_URL:
        payload = {
            "userEmail": client.email,
            "userName": client.name or "Cliente",
            "resetToken": token,
            "resetLink": reset_link,
            "expiryTime": "15 minutos",
        }
        try:
            requests.post(N8N_WEBHOOK_URL, json=payload, timeout=15)
        except Exception as exc:
            logger.warning("N8N webhook failed: %s", exc)

    return {"success": True, "mensaje": "Si el email existe, se enviaron instrucciones"}


@router.post("/reset-password")
def reset_password(body: Dict[str, Any]):
    token = str((body or {}).get("token") or "").strip()
    new_password = str((body or {}).get("newPassword") or "")
    confirm_password = str((body or {}).get("confirmPassword") or "")

    if not token or not new_password or not confirm_password:
        raise HTTPException(status_code=400, detail="Token y contraseña requeridos")

    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 6 caracteres")

    if new_password != confirm_password:
        raise HTTPException(status_code=400, detail="Las contraseñas no coinciden")

    token_info = reset_tokens.get(token)
    if not token_info:
        raise HTTPException(status_code=400, detail="Token inválido o expirado")

    if int(token_info.get("expiresAt", 0)) < int(time.time()):
        reset_tokens.pop(token, None)
        save_reset_tokens(reset_tokens)
        raise HTTPException(status_code=400, detail="Token inválido o expirado")

    email = str(token_info.get("email") or "").lower().strip()
    if not email:
        raise HTTPException(status_code=400, detail="Token inválido o expirado")

    # Update password in DB
    from config.database import SessionLocal
    db = SessionLocal()
    try:
        client = db.query(ClientModel).filter(func.lower(ClientModel.email) == email).first()
        if client:
            client.password_hash = new_password
            db.commit()
    finally:
        db.close()

    reset_tokens.pop(token, None)
    save_reset_tokens(reset_tokens)

    return {"success": True, "mensaje": "Contraseña actualizada"}


@router.get("/carrito/{email}")
def get_cart(email: str):
    return {"items": carts.get(email, [])}


@router.post("/carrito/{email}/agregar")
def add_cart_item(email: str, body: Dict[str, Any]):
    item = body.get("producto") if isinstance(body, dict) else None
    if not item:
        raise HTTPException(status_code=400, detail="Producto inválido")

    current = carts.setdefault(email, [])
    producto_id = str(item.get("id") or item.get("_id") or "")

    # Buscar si ya existe en el carrito
    for existing in current:
        eid = str(existing.get("id") or existing.get("_id") or "")
        if eid == producto_id and producto_id:
            existing["cantidad"] = existing.get("cantidad", 1) + 1
            return {"items": current}

    # Nuevo: agregar con cantidad 1
    item["cantidad"] = 1
    current.append(item)
    return {"items": current}


@router.put("/carrito/{email}/item/{producto_id}/cantidad")
def update_cart_quantity(email: str, producto_id: str, body: Dict[str, Any]):
    cantidad = body.get("cantidad", 1)
    if cantidad < 1:
        raise HTTPException(status_code=400, detail="Cantidad mínima es 1")

    current = carts.setdefault(email, [])
    for item in current:
        eid = str(item.get("id") or item.get("_id") or "")
        if eid == producto_id:
            item["cantidad"] = cantidad
            return {"items": current}

    raise HTTPException(status_code=404, detail="Producto no encontrado en carrito")


@router.delete("/carrito/{email}/index/{index}")
def delete_cart_item(email: str, index: int):
    current = carts.setdefault(email, [])
    if 0 <= index < len(current):
        current.pop(index)
    return {"items": current}


@router.delete("/carrito/{email}")
def clear_cart(email: str):
    carts[email] = []
    return {"items": []}


@router.get("/favoritos/{email}")
def get_favorites(email: str):
    return {"items": favorites.get(email, [])}


@router.post("/favoritos/{email}/agregar")
def add_favorite(email: str, body: Dict[str, Any]):
    product = body.get("producto") if isinstance(body, dict) else None
    if not product:
        raise HTTPException(status_code=400, detail="Producto inválido")

    product_id = str(product.get("id") or product.get("_id") or product.get("productoId") or "")
    current = favorites.setdefault(email, [])

    if not any(str(item.get("productoId")) == product_id for item in current):
        current.append({
            "productoId": product_id,
            "nombre": product.get("nombre"),
            "precio": product.get("precio"),
            "imagen": product.get("imagen", PLACEHOLDER_IMAGE),
            "categoria": product.get("categoria", "General"),
        })
        save_favorites(favorites)

    return {"items": current}


@router.delete("/favoritos/{email}/{producto_id}")
def remove_favorite(email: str, producto_id: str):
    current = favorites.setdefault(email, [])
    favorites[email] = [item for item in current if str(item.get("productoId")) != str(producto_id)]
    save_favorites(favorites)
    return {"items": favorites[email]}


@router.get("/boletas/{email}")
def get_bills_by_email(email: str, db: Session = Depends(get_db)):
    orders = (
        db.query(OrderModel)
        .options(
            joinedload(OrderModel.bill),
            joinedload(OrderModel.client),
            joinedload(OrderModel.order_details).joinedload(OrderDetailModel.product),
        )
        .join(ClientModel, OrderModel.client_id == ClientModel.id_key)
        .filter(func.lower(ClientModel.email) == email.lower())
        .order_by(OrderModel.id_key.desc())
        .all()
    )

    return [to_bill_json(order) for order in orders]


@router.post("/boletas")
def create_bill(body: BillBody, db: Session = Depends(get_db)):
    email = body.usuarioEmail.strip().lower()
    name = body.usuarioNombre.strip() if body.usuarioNombre else "Cliente"

    client = db.query(ClientModel).filter(func.lower(ClientModel.email) == email).first()
    if not client:
        client = ClientModel(name=name, lastname="", email=email, telephone="0000000")
        db.add(client)
        db.commit()
        db.refresh(client)

    bill_number = f"B-{datetime.now().strftime('%Y%m%d%H%M%S%f')[-14:]}"
    bill = BillModel(
        bill_number=bill_number,
        discount=0,
        date=date.today(),
        total=float(body.total or 0),
        payment_type=PaymentType.CARD,
        client_id=client.id_key,
    )
    db.add(bill)
    db.commit()
    db.refresh(bill)

    order = OrderModel(
        date=datetime.now(),
        total=float(body.total or 0),
        delivery_method=DeliveryMethod.HOME_DELIVERY,
        status=Status.PENDING,
        client_id=client.id_key,
        bill_id=bill.id_key,
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    for product in body.productos or []:
        product_name = str(product.get("nombre") or "").strip()
        quantity = int(product.get("cantidad") or 1)
        price = float(product.get("precio") or 0)

        product_model = None
        if product_name:
            product_model = db.query(ProductModel).filter(func.lower(ProductModel.name) == product_name.lower()).first()
            if not product_model:
                fallback_category = get_or_create_category(db, "Sin Categoría")
                product_model = ProductModel(
                    name=product_name,
                    price=max(price, 0),
                    stock=0,
                    category_id=fallback_category.id_key,
                )
                db.add(product_model)
                db.commit()
                db.refresh(product_model)

        detail = OrderDetailModel(
            quantity=max(quantity, 1),
            price=price,
            order_id=order.id_key,
            product_id=product_model.id_key if product_model else None,
        )
        db.add(detail)

    db.commit()

    order = (
        db.query(OrderModel)
        .options(
            joinedload(OrderModel.bill),
            joinedload(OrderModel.client),
            joinedload(OrderModel.order_details).joinedload(OrderDetailModel.product),
        )
        .filter(OrderModel.id_key == order.id_key)
        .first()
    )

    boleta = to_bill_json(order)

    # Enviar email de confirmación via n8n
    if N8N_WEBHOOK_URL:
        productos_lista = []
        for p in (body.productos or []):
            productos_lista.append({
                "nombre": p.get("nombre", ""),
                "cantidad": int(p.get("cantidad", 1)),
                "precio": float(p.get("precio", 0)),
                "subtotal": float(p.get("precio", 0)) * int(p.get("cantidad", 1)),
            })

        webhook_payload = {
            "tipo": "boleta",
            "userEmail": email,
            "userName": name,
            "boletaId": boleta.get("id", ""),
            "boletaNumero": boleta.get("billNumber", ""),
            "fecha": boleta.get("fecha", ""),
            "hora": boleta.get("hora", ""),
            "productos": productos_lista,
            "total": float(body.total or 0),
            "estado": "Procesando",
        }
        try:
            requests.post(N8N_WEBHOOK_URL, json=webhook_payload, timeout=15)
        except Exception as exc:
            logger.warning("N8N webhook (boleta) failed: %s", exc)

    return {"mensaje": "Boleta registrada", "boleta": boleta}


@router.get("/admin/usuarios")
def admin_users(admin_check: None = Depends(verify_admin), db: Session = Depends(get_db)):
    users = (
        db.query(ClientModel)
        .options(joinedload(ClientModel.bills))
        .order_by(ClientModel.id_key.desc())
        .all()
    )

    response = []
    for user in users:
        total = sum(float(bill.total or 0) for bill in (user.bills or []))
        count = len(user.bills or [])
        if count == 0:
            continue
        response.append({
            "email": user.email,
            "nombre": user.name or "Cliente",
            "totalCompras": total,
            "cantidadBoletas": count,
        })

    return response


@router.get("/admin/usuarios/{email}/boletas")
def admin_user_bills(email: str, admin_check: None = Depends(verify_admin), db: Session = Depends(get_db)):
    orders = (
        db.query(OrderModel)
        .options(
            joinedload(OrderModel.bill),
            joinedload(OrderModel.client),
            joinedload(OrderModel.order_details).joinedload(OrderDetailModel.product),
        )
        .join(ClientModel, OrderModel.client_id == ClientModel.id_key)
        .filter(func.lower(ClientModel.email) == email.lower())
        .order_by(OrderModel.id_key.desc())
        .all()
    )
    return [to_bill_json(order) for order in orders]


@router.get("/admin/boletas")
def admin_bills(admin_check: None = Depends(verify_admin), db: Session = Depends(get_db)):
    orders = (
        db.query(OrderModel)
        .options(
            joinedload(OrderModel.bill),
            joinedload(OrderModel.client),
            joinedload(OrderModel.order_details).joinedload(OrderDetailModel.product),
        )
        .order_by(OrderModel.id_key.desc())
        .all()
    )
    return [to_bill_json(order) for order in orders]


@router.put("/admin/boletas/{bill_id}")
def admin_update_bill(bill_id: str, body: BillStateBody, admin_check: None = Depends(verify_admin), db: Session = Depends(get_db)):
    try:
        bid = int(bill_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Boleta no encontrada")

    order = (
        db.query(OrderModel)
        .options(
            joinedload(OrderModel.bill),
            joinedload(OrderModel.client),
            joinedload(OrderModel.order_details).joinedload(OrderDetailModel.product),
        )
        .filter(OrderModel.bill_id == bid)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Boleta no encontrada")

    order.status = label_to_status(body.estado)
    db.commit()
    db.refresh(order)

    return {"mensaje": "Estado actualizado", "boleta": to_bill_json(order)}


@router.post("/admin/upload-imagen")
def admin_upload_image(imagen: Optional[UploadFile] = File(default=None), admin_check: None = Depends(verify_admin)):
    image_url = upload_image_to_cloudinary(imagen)
    return {"url": image_url}


@router.post("/productos")
def admin_create_product(body: ProductBody, db: Session = Depends(get_db), admin_check: None = Depends(verify_admin)):
    try:
        category = get_or_create_category(db, body.categoria)

        product = ProductModel(
            name=body.nombre,
            price=body.precio,
            stock=body.stock or 0,
            image=body.imagen or PLACEHOLDER_IMAGE,
            description=body.descripcion or f"Producto {body.nombre}",
            category_id=category.id_key,
        )
        db.add(product)
        db.commit()
        db.refresh(product)

        product = db.query(ProductModel).options(joinedload(ProductModel.category)).filter(ProductModel.id_key == product.id_key).first()

        return {"mensaje": "Producto creado", "producto": to_product_json(product)}
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        logger.exception("Error creando producto: %s", exc)
        raise HTTPException(status_code=500, detail=f"Error al crear producto: {str(exc)}")


@router.put("/productos/{id_key}")
def admin_update_product(id_key: str, body: ProductBody, db: Session = Depends(get_db), admin_check: None = Depends(verify_admin)):
    try:
        pid = int(id_key)
    except ValueError:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    product = db.query(ProductModel).filter(ProductModel.id_key == pid).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    category = get_or_create_category(db, body.categoria)
    product.name = body.nombre
    product.price = body.precio
    product.stock = body.stock or 0
    product.image = body.imagen or product.image or PLACEHOLDER_IMAGE
    product.description = body.descripcion or product.description or f"Producto {body.nombre}"
    product.category_id = category.id_key

    db.commit()

    product = db.query(ProductModel).options(joinedload(ProductModel.category)).filter(ProductModel.id_key == pid).first()

    return {"mensaje": "Producto actualizado", "producto": to_product_json(product)}


@router.delete("/productos/{id_key}")
def admin_delete_product(id_key: str, db: Session = Depends(get_db), admin_check: None = Depends(verify_admin)):
    try:
        pid = int(id_key)
    except ValueError:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    product = db.query(ProductModel).filter(ProductModel.id_key == pid).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    db.delete(product)
    db.commit()

    return {"mensaje": "Producto eliminado"}
