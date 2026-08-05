import api from "./api";

export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await api.post("/documents/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

export async function listDocuments() {
  const response = await api.get("/documents/");
  return response.data;
}

export async function startReview(documentId) {
  const response = await api.post(`/documents/${documentId}/start-review`);
  return response.data;
}

export async function approveDocument(documentId, comment = "") {
  const response = await api.post(`/documents/${documentId}/approve`, { comment });
  return response.data;
}

export async function rejectDocument(documentId, comment = "") {
  const response = await api.post(`/documents/${documentId}/reject`, { comment });
  return response.data;
}