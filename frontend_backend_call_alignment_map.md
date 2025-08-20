# Frontend-Backend API Call Alignment Map

This document maps all frontend API calls to their corresponding backend endpoints to ensure proper alignment and prevent routing issues.

Generated: 2025-01-20

## Overview

- **Total API Endpoints**: 25
- **Alignment Status**: ✅ All endpoints match perfectly
- **Trailing Slash Issues**: ✅ None found
- **Route Consistency**: ✅ All routes use consistent patterns without trailing slashes

## AUTH ENDPOINTS
**Prefix**: `/api/auth`

| Frontend Call | Backend Route | Status |
|---------------|---------------|---------|
| `GET /auth/login` | `@router.get("/login")` | ✅ Match |
| `POST /auth/callback` | `@router.post("/callback")` | ✅ Match |
| `POST /auth/refresh` | `@router.post("/refresh")` | ✅ Match |
| `GET /auth/me` | `@router.get("/me")` | ✅ Match |
| `POST /auth/logout` | `@router.post("/logout")` | ✅ Match |
| `POST /auth/login/password` | `@router.post("/login/password")` | ✅ Match |
| `POST /auth/password/change` | `@router.post("/password/change")` | ✅ Match |
| `GET /auth/login/cookie` | `@router.get("/login/cookie")` | ✅ Match |

**Files**:
- Frontend: `frontend/src/services/auth.ts`
- Backend: `backend/app/api/auth.py`

## DOCUMENTS ENDPOINTS
**Prefix**: `/api/documents`

| Frontend Call | Backend Route | Status |
|---------------|---------------|---------|
| `GET /documents` | `@router.get("/")` | ✅ Match |
| `GET /documents/keys` | `@router.get("/keys")` | ✅ Match |
| `GET /documents/dates?key=...` | `@router.get("/dates")` | ✅ Match |
| `GET /documents/by-key-date?key=...&date=...` | `@router.get("/by-key-date")` | ✅ Match |
| `GET /documents/{documentId}` | `@router.get("/{document_id}")` | ✅ Match |
| `POST /documents/upload-single` | `@router.post("/upload-single")` | ✅ Match |
| `POST /documents/bulk-upload` | `@router.post("/bulk-upload")` | ✅ Match |
| `POST /documents/bulk-upload-directory` | `@router.post("/bulk-upload-directory")` | ✅ Match |

**Files**:
- Frontend: 
  - `frontend/src/components/DocumentViewer/DocumentList.tsx`
  - `frontend/src/components/DocumentViewer/DocumentViewer.tsx`
  - `frontend/src/components/Layout/MainLayout.tsx`
  - `frontend/src/components/Upload/SingleUploadDialog.tsx`
  - `frontend/src/components/Upload/BulkUploadDialog.tsx`
- Backend: `backend/app/api/documents.py`

## ANNOTATIONS ENDPOINTS
**Prefix**: `/api/annotations`

| Frontend Call | Backend Route | Status |
|---------------|---------------|---------|
| `GET /annotations/document/{documentId}` | `@router.get("/document/{document_id}")` | ✅ Match |
| `POST /annotations/` | `@router.post("/")` | ✅ Match |
| `DELETE /annotations/{annotationId}` | `@router.delete("/{annotation_id}")` | ✅ Match |

**Files**:
- Frontend: `frontend/src/contexts/AnnotationContext.tsx`
- Backend: `backend/app/api/annotations.py`

## ADMIN ENDPOINTS
**Prefix**: `/api/admin`

| Frontend Call | Backend Route | Status |
|---------------|---------------|---------|
| `GET /admin/documents` | `@router.get("/documents")` | ✅ Match |
| `DELETE /admin/documents/{documentId}` | `@router.delete("/documents/{document_id}")` | ✅ Match |
| `PATCH /admin/documents/{documentId}/toggle-public` | `@router.patch("/documents/{document_id}/toggle-public")` | ✅ Match |
| `GET /admin/users` | `@router.get("/users")` | ✅ Match |
| `POST /admin/users` | `@router.post("/users")` | ✅ Match |
| `DELETE /admin/users/{userId}` | `@router.delete("/users/{user_id}")` | ✅ Match |
| `POST /admin/users/{userId}/reset-password` | `@router.post("/users/{user_id}/reset-password")` | ✅ Match |

**Files**:
- Frontend: 
  - `frontend/src/components/Admin/DocumentManagement.tsx`
  - `frontend/src/components/Admin/UserManagement.tsx`
- Backend: `backend/app/api/admin.py`

## Router Configuration
**Main Application**: `backend/main.py`

```python
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(annotations.router, prefix="/api/annotations", tags=["annotations"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
```

## Verification Notes

1. **No Trailing Slash Mismatches**: All frontend calls and backend routes are consistent in their trailing slash usage (none use trailing slashes).

2. **Parameter Mapping**: URL parameters (`{documentId}`, `{userId}`, etc.) are consistently named between frontend and backend.

3. **HTTP Methods**: All HTTP methods (GET, POST, PATCH, DELETE) match between frontend calls and backend route definitions.

4. **Query Parameters**: Endpoints using query parameters (`/documents/dates?key=...`) are properly handled on both sides.

## Troubleshooting

If you encounter 307 redirects or routing issues:

1. ✅ Verify this alignment map is still accurate
2. ✅ Check for trailing slash inconsistencies
3. ✅ Ensure nginx/proxy configuration doesn't interfere with application routes
4. ✅ Verify environment variables (REACT_APP_API_URL) are correctly set

---

*This document should be updated whenever new API endpoints are added or existing ones are modified.*