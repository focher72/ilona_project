import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from supabase import Client

BASE_DIR = Path(__file__).parent
app = FastAPI(title="Онлайн доска жалоб и предложений команды веба")

_SUPABASE_URL = os.environ.get("SUPABASE_URL")
_SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supa: Client | None = None
if _SUPABASE_URL and _SUPABASE_KEY:
    supa = Client(_SUPABASE_URL, _SUPABASE_KEY)


class TicketCreate(BaseModel):
    type: str
    status: str
    comment: str
    author: str | None = None


class TicketUpdate(BaseModel):
    type: str | None = None
    status: str | None = None
    comment: str | None = None
    author: str | None = None
    resolution_comment: str | None = None
    resolution_author: str | None = None


@app.get("/")
def index():
    """Главная страница: одностраничный сайт (SPA)."""
    return FileResponse(BASE_DIR / "index.html")


@app.get("/api/health")
def health():
    """Проверка работоспособности бэкенда."""
    return {
        "status": "ok",
        "supabase_connected": bool(_SUPABASE_URL and _SUPABASE_KEY),
    }


@app.get("/api/tickets")
def list_tickets():
    """Список всех тикетов из Supabase (таблица tickets)."""
    if supa is None:
        raise HTTPException(status_code=503, detail="База данных не настроена (SUPABASE_URL/SUPABASE_KEY)")
    response = supa.table("tickets").select("*").order("id").execute()
    if response.error:
        raise HTTPException(status_code=500, detail=response.error.message)
    return response.data


@app.post("/api/tickets")
def create_ticket(payload: TicketCreate):
    """Создание нового тикета."""
    if supa is None:
        raise HTTPException(status_code=503, detail="База данных не настроена (SUPABASE_URL/SUPABASE_KEY)")
    payload_dict = payload.model_dump()
    data = {
        "type": payload_dict["type"],
        "status": payload_dict["status"],
        "comment": payload_dict["comment"],
        "author": payload_dict.get("author") or None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    response = supa.table("tickets").insert(data).execute()
    if response.error:
        raise HTTPException(status_code=500, detail=response.error.message)
    return {"id": response.data[0]["id"]}


@app.patch("/api/tickets/{ticket_id}")
def update_ticket(ticket_id: int, payload: TicketUpdate):
    """Обновление тикета (перемещение по колонкам, решение)."""
    if supa is None:
        raise HTTPException(status_code=503, detail="База данных не настроена (SUPABASE_URL/SUPABASE_KEY)")
    updates = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
    if updates.get("status") == "done":
        updates["resolution_comment"] = updates.get("resolution_comment") or ""
        updates["resolution_author"] = updates.get("resolution_author") or ""
    response = supa.table("tickets").update(updates).eq("id", ticket_id).execute()
    if response.error:
        raise HTTPException(status_code=500, detail=response.error.message)
    return {"ok": True}


@app.delete("/api/tickets/{ticket_id}")
def delete_ticket(ticket_id: int):
    """Удаление тикета."""
    if supa is None:
        raise HTTPException(status_code=503, detail="База данных не настроена (SUPABASE_URL/SUPABASE_KEY)")
    response = supa.table("tickets").delete().eq("id", ticket_id).execute()
    if response.error:
        raise HTTPException(status_code=500, detail=response.error.message)
    return {"ok": True}
