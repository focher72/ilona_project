import os
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from supabase import Client

BASE_DIR = Path(__file__).parent
app = FastAPI(title="Онлайн доска жалоб и предложений команды веба")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SUPABASE_KEY = Secret key (sb_secret_...) или legacy service_role JWT.
# Эти ключи дают полный доступ к БД и обходят RLS, поэтому используются ТОЛЬКО
# на сервере (Vercel → Environment Variables) и никогда не попадают в браузер.
_SUPABASE_URL = os.environ.get("SUPABASE_URL")
_SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supa: Client | None = None
if _SUPABASE_URL and _SUPABASE_KEY:
    try:
        supa = Client(_SUPABASE_URL, _SUPABASE_KEY)
    except Exception:
        logger.exception("Не удалось инициализировать Supabase клиент")

TicketType = Literal["problems", "ideas", "good", "progress"]
TicketStatus = Literal["problems", "ideas", "good", "progress", "done"]


class TicketCreate(BaseModel):
    type: TicketType
    status: TicketType
    comment: str = Field(min_length=1, max_length=1200)
    author: str | None = Field(default=None, max_length=60)


class TicketUpdate(BaseModel):
    type: TicketType | None = None
    status: TicketStatus | None = None
    comment: str | None = Field(default=None, max_length=1200)
    author: str | None = Field(default=None, max_length=60)
    resolution_comment: str | None = Field(default=None, max_length=1200)
    resolution_author: str | None = Field(default=None, max_length=60)


def _require_db() -> None:
    if supa is None:
        raise HTTPException(
            status_code=503,
            detail="База данных не настроена (SUPABASE_URL/SUPABASE_KEY)",
        )


def _run(query: Any) -> Any:
    """Выполнить запрос Supabase и превратить ошибки в HTTPException."""
    try:
        response = query.execute()
    except Exception as exc:
        logger.exception("Supabase query failed")
        raise HTTPException(status_code=502, detail=f"Supabase error: {exc}") from exc

    error = getattr(response, "error", None)
    if error:
        message = getattr(error, "message", str(error))
        logger.error("Supabase returned error: %s", message)
        raise HTTPException(status_code=502, detail=message)

    return response.data


@app.get("/")
def index():
    """Главная страница: одностраничный сайт (SPA)."""
    return FileResponse(BASE_DIR / "index.html")


@app.get("/api/health")
def health():
    """Проверка работоспособности бэкенда и наличия конфигурации Supabase."""
    return {
        "status": "ok",
        "supabase_connected": supa is not None,
    }


@app.get("/api/tickets")
def list_tickets():
    """Список всех тикетов."""
    _require_db()
    return _run(supa.table("tickets").select("*").order("id"))


@app.post("/api/tickets")
def create_ticket(payload: TicketCreate):
    """Создание нового тикета."""
    _require_db()
    data = {
        "type": payload.type,
        "status": payload.status,
        "comment": payload.comment.strip(),
        "author": (payload.author or "").strip() or None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    rows = _run(supa.table("tickets").insert(data))
    if not rows:
        raise HTTPException(status_code=502, detail="Пустой ответ от Supabase")
    return rows[0]


@app.patch("/api/tickets/{ticket_id}")
def update_ticket(ticket_id: int, payload: TicketUpdate):
    """Обновление тикета (перемещение по колонкам, решение)."""
    _require_db()
    updates = {
        k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None
    }
    if not updates:
        return {"ok": True}
    _run(supa.table("tickets").update(updates).eq("id", ticket_id))
    return {"ok": True}


@app.delete("/api/tickets/{ticket_id}")
def delete_ticket(ticket_id: int):
    """Удаление тикета."""
    _require_db()
    _run(supa.table("tickets").delete().eq("id", ticket_id))
    return {"ok": True}