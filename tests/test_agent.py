import pytest
from httpx import AsyncClient
from src.main import app

@pytest.mark.asyncio
async def test_chat_greeting():
    """Test respuesta a saludo"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/chat", json={
            "message": "Hola",
            "session_id": "test_greeting"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "greeting"
        assert "[FAQ]" in data["response"]
        assert "[Agente]" in data["response"]

@pytest.mark.asyncio
async def test_faq_request():
    """Test solicitud de FAQ"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/chat", json={
            "message": "[FAQ]",
            "session_id": "test_faq"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "faq_request"
        assert "página de FAQ" in data["response"]

@pytest.mark.asyncio
async def test_out_of_scope():
    """Test pregunta fuera de alcance"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/chat", json={
            "message": "¿Cuál es el sentido de la vida?",
            "session_id": "test_oos"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "out_of_scope"
        assert "solo puedo ayudarte con temas relacionados" in data["response"]

@pytest.mark.asyncio
async def test_health_check():
    """Test health endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert "services" in data