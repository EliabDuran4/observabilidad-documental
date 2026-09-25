import React, { useState } from "react";
import { reviewDocument, decideDocument, deleteDocument, downloadDocument } from "../services/documentService";
import { getRoles } from "../services/authService";

const CATEGORY_LABEL = {
  contratos_corporativo: "Contratos y Corporativo",
  litigioso: "Litigioso",
  regulatorio_compliance: "Regulatorio / Compliance",
  propiedad_intelectual: "Propiedad Intelectual",
};

export default function DocumentRow({ doc, onUpdate }) {
  const [comment, setComment] = useState("");
  const [busy, setBusy] = useState(false);
  const roles = getRoles();
  const isRevisor = roles.includes("revisor_documental");
  const isAdmin = roles.includes("admin_documental");
  const canDownload = isRevisor || isAdmin;

  const act = async (fn, status) => {
    setBusy(true);
    try {
      await fn(doc.id, status, comment || undefined);
      setComment("");
      onUpdate();
    } finally {
      setBusy(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm(`¿Eliminar "${doc.original_filename}"? Esta acción no se puede deshacer.`)) return;
    setBusy(true);
    try {
      await deleteDocument(doc.id);
      onUpdate();
    } catch {
      alert("No se pudo eliminar el documento");
    } finally {
      setBusy(false);
    }
  };

  const handleDownload = async () => {
    setBusy(true);
    try {
      await downloadDocument(doc.id, doc.original_filename);
    } catch {
      alert("No se pudo descargar el documento");
    } finally {
      setBusy(false);
    }
  };

  const showRevisorActions = isRevisor && (doc.status === "recibido" || doc.status === "en_revision");
  const showAdminActions = isAdmin && doc.status === "revisado";
  const showCommentInput = showRevisorActions || showAdminActions;

  return (
    <tr>
      <td>{doc.original_filename}</td>
      <td>{CATEGORY_LABEL[doc.category] || doc.category}</td>
      <td><span className={`badge badge-${doc.status}`}>{doc.status.replace("_", " ")}</span></td>
      <td>{doc.uploaded_by}</td>
      <td>{doc.uploaded_at ? new Date(doc.uploaded_at).toLocaleDateString() : "-"}</td>
      <td>
        {showCommentInput && (
          <input
            className="action-btn comment-input"
            placeholder="Comentario"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            disabled={busy}
          />
        )}

        {canDownload && (
          <button className="action-btn review" disabled={busy} onClick={handleDownload}>
            Descargar
          </button>
        )}

        {isRevisor && doc.status === "recibido" && (
          <button className="action-btn review" disabled={busy} onClick={() => act(reviewDocument, "en_revision")}>
            Iniciar revisión
          </button>
        )}

        {isRevisor && doc.status === "en_revision" && (
          <>
            <button className="action-btn review" disabled={busy} onClick={() => act(reviewDocument, "revisado")}>
              Revisado
            </button>
            <button className="action-btn correction" disabled={busy} onClick={() => act(reviewDocument, "correccion")}>
              Corrección
            </button>
          </>
        )}

        {isAdmin && doc.status === "revisado" && (
          <>
            <button className="action-btn approve" disabled={busy} onClick={() => act(decideDocument, "aprobado")}>
              Aprobar
            </button>
            <button className="action-btn reject" disabled={busy} onClick={() => act(decideDocument, "rechazado")}>
              Rechazar
            </button>
          </>
        )}

        {isAdmin && (
          <button className="action-btn delete" disabled={busy} onClick={handleDelete}>
            Eliminar
          </button>
        )}

        {!showRevisorActions && !showAdminActions && !isAdmin && !canDownload && "-"}
      </td>
    </tr>
  );
}