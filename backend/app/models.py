"""Pydantic models for API I/O. MongoDB documents use string `id` (uuid)."""

import uuid
from datetime import datetime, timezone, date
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, ConfigDict


def _id() -> str:
    return str(uuid.uuid4())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---- Auth ----
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AdminInfo(BaseModel):
    email: EmailStr
    name: str


class TokenResponse(BaseModel):
    token: str
    admin: AdminInfo


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=20)
    password: str = Field(min_length=8)


# ---- SiteSettings ----
class SiteSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default="site-settings")
    siteName: str = "AIA Legnano"
    tagline: str = "Sezione Associazione Italiana Arbitri"
    footerTagline: str = (
        "Punto di riferimento per arbitri associati, aspiranti arbitri e appassionati dell'Alto Milanese."
    )
    address: str = "Via XX Settembre, Legnano (MI)"
    phone: str = "+39 0331 000000"
    email: str = "legnano@aia-figc.it"
    facebookUrl: str = "https://www.facebook.com/aialegnano"
    instagramUrl: str = "https://www.instagram.com/aia_legnano/"
    instagramFollowers: str = ""
    instagramFollowing: str = ""
    mapEmbedUrl: str = ""
    foundedYear: str = "1927"
    associatedCount: str = "150"
    formationPortalUrl: str = "https://www.aia-figc.it/"
    articleCategories: List[str] = Field(
        default_factory=lambda: [
            "Vita sezionale",
            "Regolamento",
            "Successi",
            "Corso arbitri",
            "Comunicazioni",
        ]
    )
    documentSections: List[str] = Field(
        default_factory=lambda: [
            "Regolamenti del giuoco del calcio",
            "Regolamenti A.I.A.",
            "Documentazione amministrativa CRA/CPA",
            "Documentazione amministrativa Sezioni",
            "Assemblea Sezionale Elettiva",
            "Assemblea Sezionale Ordinaria",
            "Assemblea Regionale Elettiva",
            "Assemblea Generale Elettiva",
        ]
    )
    updatedAt: str = Field(default_factory=_now)


# ---- NavItem ----
class NavItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=_id)
    label: str
    href: str
    order: int = 0
    enabled: bool = True
    highlight: bool = False


# ---- Page ----
class Page(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=_id)
    slug: str
    title: str
    template: str = "custom"  # custom | system
    status: str = "published"
    eyebrow: str = ""
    heading: str = ""
    summary: str = ""
    image: str = ""
    bodyHtml: str = ""
    blocks: List[dict] = Field(default_factory=list)  # CMS composable blocks
    primaryCtaLabel: str = ""
    primaryCtaHref: str = ""
    secondaryCtaLabel: str = ""
    secondaryCtaHref: str = ""
    metaTitle: str = ""
    metaDescription: str = ""
    showInMenu: bool = False
    menuLabel: str = ""
    menuOrder: int = 100
    menuHighlight: bool = False
    updatedAt: str = Field(default_factory=_now)


# ---- Article ----
class Article(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=_id)
    slug: str
    title: str
    category: str = "Vita sezionale"
    excerpt: str = ""
    bodyHtml: str = ""
    coverUrl: str = ""
    coverInGallery: bool = False  # copertina anche nella galleria pubblica
    bodyInGallery: bool = False  # immagini nel corpo articolo nella galleria pubblica
    authorName: str = "Redazione AIA Legnano"
    relatedMemberIds: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    legacyWpId: Optional[int] = None  # ID WordPress sorgente (import)
    portalOnly: bool = False  # True = solo area riservata, non sul sito pubblico
    status: str = "published"  # published | draft
    publishedAt: str = Field(default_factory=_now)
    metaTitle: str = ""
    metaDescription: str = ""
    createdAt: str = Field(default_factory=_now)
    updatedAt: str = Field(default_factory=_now)


class ArticleCreate(BaseModel):
    slug: Optional[str] = None
    title: str
    category: str = "Vita sezionale"
    excerpt: str = ""
    bodyHtml: str = ""
    coverUrl: str = ""
    coverInGallery: bool = False
    bodyInGallery: bool = False
    authorName: str = "Redazione AIA Legnano"
    relatedMemberIds: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    portalOnly: bool = False
    status: str = "published"
    publishedAt: Optional[str] = None


class ArticleCategoryCreate(BaseModel):
    name: str


# ---- Event ----
class ContentAttachment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=_id)
    fileName: str = ""
    fileUrl: str = ""
    fileSize: int = 0
    mimeType: str = ""


class Event(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=_id)
    date: str  # YYYY-MM-DD
    orario: str = "09:00"  # HH:MM (fuso Europe/Rome)
    orarioFine: str = ""  # HH:MM opzionale; vuoto = durata default (2h) in calendario
    titolo: str
    descrizione: str = ""
    luogo: str = ""
    tipo: str = "Riunione"
    invitedMemberIds: List[str] = Field(
        default_factory=list
    )  # vuoto = tutti (se anche invitedRoleGroups vuoto)
    invitedRoleGroups: List[str] = Field(
        default_factory=list
    )  # AE, AA, … cds, collaboratore, ors; vuoto = nessun filtro ruolo
    portalOnly: bool = False  # True = solo area associati, non sul sito pubblico
    attachments: List[ContentAttachment] = Field(default_factory=list)
    utilityMaterial: List[ContentAttachment] = Field(
        default_factory=list
    )  # solo Utility (RTO)
    createdAt: str = Field(default_factory=_now)


class EventUtilityMaterialUpdate(BaseModel):
    utilityMaterial: List[ContentAttachment] = Field(default_factory=list)


# ---- Official ----
class Official(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=_id)
    role: str
    firstName: str
    lastName: str
    photoUrl: str = ""
    bioHtml: str = ""
    isPresident: bool = False
    sortOrder: int = 0


# ---- Member award (premio) ----
class MemberAward(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=_id)
    title: str
    year: Optional[int] = None
    description: str = ""
    sortOrder: int = 0


# ---- Member ----
class Member(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=_id)
    slug: str
    firstName: str
    lastName: str
    passwordHash: str = ""
    emailVisibile: bool = False
    telefonoVisibile: bool = False
    memberRole: str = (
        "arbitro"  # arbitro | assistente | consiglio_direttivo | osservatore
    )
    observerType: str = ""  # oa | ot (solo se memberRole=osservatore)
    organigrammaKind: str = ""  # "" | cds | collaboratore | ors
    boardTitle: str = ""  # incarico organigramma (es. Segretario, Area Informatica)
    isPresident: bool = False  # calcolato da incarico CDS + parola Presidente
    category: str = ""  # categoria sportiva (solo AE / AA)
    role: str = ""  # codice AIA: AE | AA | AB | AFR | OA | OT
    kind: str = "associato"  # legacy
    yearStart: Optional[int] = None
    meccanografico: str = ""
    photoUrl: str = ""
    bio: str = ""
    chiSiamoText: str = ""  # testo medio mostrato su card Presidente in "Chi siamo"
    presidentLongBio: str = ""  # testo lungo solo nel profilo del Presidente
    bioHtml: str = ""
    email: str = ""
    phone: str = ""
    notes: str = ""
    emailNotifyEvents: bool = False
    emailNotifyEventLeadHours: int = 24  # 24 | 12 | 6 | 1 ore prima dell'evento
    emailNotifyComunicazioni: bool = False
    emailNotifyMessages: bool = False
    awards: List[MemberAward] = Field(default_factory=list)
    createdAt: str = Field(default_factory=_now)
    updatedAt: str = Field(default_factory=_now)


class MemberCreate(BaseModel):
    slug: Optional[str] = None
    firstName: str
    lastName: str
    passwordHash: str = ""
    emailVisibile: bool = False
    telefonoVisibile: bool = False
    memberRole: str = "arbitro"
    observerType: str = ""
    organigrammaKind: str = ""
    boardTitle: str = ""
    isPresident: bool = False
    category: str = ""
    role: str = ""
    kind: str = "associato"
    yearStart: Optional[int] = None
    meccanografico: str = ""
    photoUrl: str = ""
    bio: str = ""
    chiSiamoText: str = ""
    presidentLongBio: str = ""
    bioHtml: str = ""
    email: str = ""
    phone: str = ""
    notes: str = ""
    emailNotifyEvents: bool = False
    emailNotifyEventLeadHours: int = 24
    emailNotifyComunicazioni: bool = False
    emailNotifyMessages: bool = False
    awards: List[MemberAward] = Field(default_factory=list)


# ---- Designation ----
class Designation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=_id)
    matchDate: str  # ISO date
    championship: str = ""  # campionato
    girone: str = ""
    matchDay: str = ""  # giornata
    matchHome: str = ""
    matchAway: str = ""
    category: str = ""  # legacy / display aggregate
    matchLabel: str = ""  # gara (casa - ospite)
    role: str = ""
    memberName: str = ""
    memberId: Optional[str] = None
    memberSlug: str = ""  # link profilo associato
    status: str = "published"  # published | pending_approval
    source: str = "manual"  # manual | aia-figc-lombardia
    externalId: Optional[str] = None
    refereeSection: str = ""
    gareCode: str = ""
    syncedAt: Optional[str] = None
    createdAt: str = Field(default_factory=_now)


class DesignationSyncRequest(BaseModel):
    """Optional overrides for AIA FIGC sync."""

    sectionGare: Optional[str] = None  # es. 3-270 Legnano
    filterSection: Optional[str] = (
        None  # es. Legnano — solo nominativi di quella sezione
    )
    replaceExisting: bool = True
    maxDesPages: Optional[int] = None  # limit for testing


# ---- Documents (downloads) ----
class Document(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=_id)
    title: str
    description: str = ""
    fileUrl: str
    fileSize: str = ""
    category: str = "Documentazione amministrativa Sezioni"
    sortOrder: int = 0
    source: str = ""
    sourceUrl: str = ""
    section: str = ""
    createdAt: str = Field(default_factory=_now)


# ---- Site gallery (carosello home) ----
GALLERY_ASPECTS = ("16:9", "9:16")


class GalleryImage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=_id)
    url: str
    path: str = ""
    sourceUrl: str = ""  # originale per ri-ritaglio
    caption: str = ""
    category: str = ""
    photoDate: str = ""  # YYYY-MM-DD, automatica
    aspect: str = "16:9"  # 16:9 | 9:16
    contentHash: str = ""
    phash: str = ""
    sortOrder: int = 0
    status: str = "approved"  # approved | pending | rejected
    source: str = "admin"  # admin | article | member | instagram
    memberId: str = ""
    memberName: str = ""
    memberIds: List[str] = Field(default_factory=list)
    cropEdited: bool = False  # ritaglio manuale admin: non rigenerare da articolo
    articleId: str = ""
    createdAt: str = Field(default_factory=_now)
    updatedAt: str = Field(default_factory=_now)


class GalleryImageCreate(BaseModel):
    url: str
    path: str = ""
    sourceUrl: str = ""
    caption: str = ""
    category: str = ""
    photoDate: str = ""
    aspect: str = "16:9"
    sortOrder: int = 0
    memberIds: List[str] = Field(default_factory=list)


class GalleryImageUpdate(BaseModel):
    caption: str = ""
    sortOrder: int = 0
    status: Optional[str] = None
    category: Optional[str] = None
    url: Optional[str] = None
    path: Optional[str] = None
    sourceUrl: Optional[str] = None
    aspect: Optional[str] = None
    memberIds: Optional[List[str]] = None


# ---- Gallery Album ----
class Album(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=_id)
    slug: str
    title: str
    description: str = ""
    eventDate: str = ""
    coverUrl: str = ""
    images: List[dict] = Field(default_factory=list)  # [{url, caption}]
    sortOrder: int = 0
    createdAt: str = Field(default_factory=_now)


# ---- Testimonial ----
class Testimonial(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=_id)
    name: str
    role: str = ""
    quote: str
    photoUrl: str = ""
    memberId: Optional[str] = None
    memberSlug: str = ""
    status: str = "published"  # published | pending
    sortOrder: int = 0


# ---- Lead (Corso arbitri) ----
class LeadCreate(BaseModel):
    firstName: str
    lastName: str
    age: Optional[int] = None
    phone: str = ""
    email: EmailStr
    contactPreference: str = "email"  # email | phone
    message: str = ""


class Lead(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=_id)
    firstName: str
    lastName: str
    age: Optional[int] = None
    phone: str = ""
    email: str
    contactPreference: str = "email"
    message: str = ""
    status: str = "new"  # new | contacted | archived
    createdAt: str = Field(default_factory=_now)


# ---- Contact message ----
class ContactCreate(BaseModel):
    name: str
    email: EmailStr
    subject: str = ""
    body: str


class ContactMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=_id)
    name: str
    email: str
    subject: str = ""
    body: str = ""
    status: str = "new"
    createdAt: str = Field(default_factory=_now)


# ---- Utility (area associati) ----
class UtilityPolo(BaseModel):
    bodyHtml: str = ""


class UtilityItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=_id)
    section: str  # link_utili (lezioni tecniche = eventi tipo rto)
    title: str
    description: str = ""
    url: str = ""
    fileUrl: str = ""
    sortOrder: int = 0
    createdAt: str = Field(default_factory=_now)


# ---- Portale associati ----
class PortalLoginRequest(BaseModel):
    codice: str
    password: str


class PresenzaEventoUpdate(BaseModel):
    memberId: str
    stato: str  # PRESENTE | ASSENTE | IN_DUBBIO | NON_RISPOSTO


class NotificaInternaCreate(BaseModel):
    testo: str
    tipo: str = "GENERALE"
    link: str = ""
    memberIds: List[str] = Field(default_factory=list)
    allArbitri: bool = False


class MessaggioInternoCreate(BaseModel):
    destinatarioId: str = ""
    testo: str = ""
    replyToId: str = ""
    tipo: str = "text"
    attachmentUrl: str = ""
    attachmentName: str = ""
    attachmentMime: str = ""


class MessaggioModificaBody(BaseModel):
    testo: str


class MessaggioReazioneBody(BaseModel):
    emoji: str


class GruppoChatCreate(BaseModel):
    name: str
    memberIds: List[str] = Field(default_factory=list)
    photoUrl: str = ""
    description: str = ""


class GruppoChatUpdate(BaseModel):
    name: Optional[str] = None
    photoUrl: Optional[str] = None
    description: Optional[str] = None


class ComunicazioneInternaCreate(BaseModel):
    title: str
    bodyHtml: str = ""
    testo: str = ""
    allMembers: bool = False
    memberIds: List[str] = Field(default_factory=list)
    roleGroups: List[str] = Field(
        default_factory=list
    )  # AE, AA, … cds, collaboratore, ors
    allowReplies: bool = True
    attachments: List[ContentAttachment] = Field(default_factory=list)


class ComunicazioneRispostaCreate(BaseModel):
    testo: str


class PreferitoCreate(BaseModel):
    tipo: str  # DOCUMENTO | MEDIA | QUIZ
    elementoId: str
