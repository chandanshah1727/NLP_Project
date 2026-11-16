"""Typed-by-convention REST helpers for the FastAPI backend."""
import os
import requests
import streamlit as st

try:
    _secret_api_url = st.secrets.get("WASTE_API_URL")
except Exception:
    _secret_api_url = None

API_BASE_URL = (_secret_api_url or os.getenv("WASTE_API_URL") or "http://127.0.0.1:8000").rstrip("/")
TIMEOUT_SECONDS = 45

class APIError(RuntimeError):
    """Friendly error raised for connection, HTTP, or response failures."""

def request(method: str, path: str, **kwargs):
    try:
        response = requests.request(method, f"{API_BASE_URL}{path}", timeout=TIMEOUT_SECONDS, **kwargs)
        response.raise_for_status()
    except requests.Timeout as exc:
        raise APIError("The backend took too long to respond. Please try again.") from exc
    except requests.ConnectionError as exc:
        raise APIError("Backend is not responding. Start the FastAPI service and try again.") from exc
    except requests.HTTPError as exc:
        detail = "The backend rejected the request."
        try:
            detail = response.json().get("detail", detail)
        except (ValueError, AttributeError):
            pass
        raise APIError(detail) from exc
    except requests.RequestException as exc:
        raise APIError("The request could not be completed. Please try again.") from exc
    if not response.content:
        return None
    try:
        return response.json()
    except ValueError as exc:
        raise APIError("The backend returned an invalid response.") from exc

def get(path: str, **params): return request("GET", path, params=params)
def post(path: str, **kwargs): return request("POST", path, **kwargs)
def put(path: str, **kwargs): return request("PUT", path, **kwargs)
def delete(path: str):
    request("DELETE", path)
    return True

def health(): return get("/")
def predict_image(filename: str, content: bytes, content_type: str):
    return post("/predict", files={"file":(filename, content, content_type)})
def create_record(payload: dict): return post("/records", json=payload)
def get_records(**params): return get("/records", **params)
def get_record(record_id: int): return get(f"/records/{record_id}")
def update_record(record_id: int, payload: dict): return put(f"/records/{record_id}", json=payload)
def delete_record(record_id: int): return delete(f"/records/{record_id}")
def get_summary(**params): return get("/analytics/summary", **params)
def get_locations(**params): return get("/analytics/locations", **params)
def get_categories(**params): return get("/analytics/categories", **params)
def get_trends(**params): return get("/analytics/trends", **params)
def get_alerts(**params): return get("/alerts", **params)
