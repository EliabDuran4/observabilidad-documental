import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  uploadDocument,
  listDocuments,
  startReview,
  approveDocument,
  rejectDocument,
  analyzeDocument,
} from "../services/documentService";
import { logout } from "../services/authService";

const STATUS_LABELS = {
  recibido: { label: "Recibido", color: "#6b7280" },
  en_revision: { label: "En revisión", color: "#d97706" },
  aprobado: { label: "Aprobado", color: "#16a34a" },
  rechazado: { label: "Rechazado", color: "#dc2626" },
};

function Documents() {
  const [documents, setDocuments] = useState([]);
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const fetchDocuments = async () => {
    try {
      const data = await listDocuments();
      setDocuments(data.documents);
    } catch (err) {
      setError("No se pudieron cargar los documentos");
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setMessage("");
    setError("");
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) {
      setError("Selecciona un archivo primero");
      return;
    }
    setUploading(true);
    setError("");
    setMessage("");
    try {
      await uploadDocument(file);
      setMessage("Documento subido exitosamente");
      setFile(null);
      e.target.reset();
      fetchDocuments();
    } catch (err) {
      setError("Error al subir el documento. Verifica el formato (.pdf, .docx, .doc)");
    } finally {
      setUploading(false);
    }
  };

  const handleAction = async (action, documentId) => {
    setError("");
    setMessage("");
    try {
      if (action === "start-review") await startReview(documentId);
      if (action === "approve") await approveDocument(documentId, "Aprobado desde interfaz");
      if (action === "reject") await rejectDocument(documentId, "Rechazado desde interfaz");
      setMessage("Estado actualizado correctamente");
      fetchDocuments();
    } catch (err) {
      setError("No se pudo actualizar el estado del documento");
    }
  };

  const handleAnalyze = async (documentId) => {
    setError("");
    setMessage("");
  try {
     await analyzeDocument(documentId);
     setMessage("Análisis generado correctamente");
     fetchDocuments();
   }  catch (err) {
      setError("No se pudo generar el análisis (verifica créditos de la API)");
   }
  };

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2>Sistema de Observabilidad Documental</h2>
        <button style={styles.logoutButton} onClick={handleLogout}>
          Cerrar sesión
        </button>
      </div>

      <div style={styles.uploadSection}>
        <h3>Subir documento</h3>
        <form onSubmit={handleUpload} style={styles.uploadForm}>
          <input type="file" accept=".pdf,.docx,.doc" onChange={handleFileChange} />
          <button style={styles.uploadButton} type="submit" disabled={uploading}>
            {uploading ? "Subiendo..." : "Subir"}
          </button>
        </form>
        {message && <p style={styles.success}>{message}</p>}
        {error && <p style={styles.error}>{error}</p>}
      </div>

      <div style={styles.listSection}>
        <h3>Documentos cargados ({documents.length})</h3>
        {documents.length === 0 ? (
          <p style={styles.empty}>No hay documentos cargados todavía.</p>
        ) : (
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>Nombre</th>
                <th style={styles.th}>Estado</th>
                <th style={styles.th}>Subido por</th>
                <th style={styles.th}>Revisado por</th>
                <th style={styles.th}>Acciones</th>
                <th style={styles.th}>Análisis IA</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((doc) => {
                const statusInfo = STATUS_LABELS[doc.status] || { label: doc.status, color: "#000" };
                return (
                  <tr key={doc.id}>
                    <td style={styles.td}>{doc.original_filename}</td>
                    <td style={styles.td}>
                      <span style={{ ...styles.badge, backgroundColor: statusInfo.color }}>
                        {statusInfo.label}
                      </span>
                    </td>
                    <td style={styles.td}>{doc.uploaded_by}</td>
                    <td style={styles.td}>{doc.reviewed_by || "-"}</td>
                    <td style={styles.td}>{doc.ai_analysis || "-"}</td>
                    <td style={styles.td}>
                      {doc.status === "recibido" && (
                        <button
                          style={styles.actionButton}
                          onClick={() => handleAction("start-review", doc.id)}
                        >
                          Iniciar revisión
                        </button>
                      )}
                      {doc.status === "en_revision" && (
                        <>
                          <button
                            style={{ ...styles.actionButton, backgroundColor: "#16a34a" }}
                            onClick={() => handleAction("approve", doc.id)}
                          >
                            Aprobar
                          </button>
                          <button
                            style={{ ...styles.actionButton, backgroundColor: "#dc2626" }}
                            onClick={() => handleAction("reject", doc.id)}
                          >
                            Rechazar
                          </button>
                          <button
                            style={{ ...styles.actionButton, backgroundColor: "#7c3aed" }}
                            onClick={() => handleAnalyze(doc.id)}
                          >
                            Analizar con IA
                          </button>
                        </>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

const styles = {
  container: { maxWidth: "900px", margin: "0 auto", padding: "40px 20px", fontFamily: "sans-serif", color: "#0F172A" },
  header: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "30px" },
  logoutButton: { padding: "8px 16px", backgroundColor: "#dc2626", color: "#fff", border: "none", borderRadius: "4px", cursor: "pointer" },
  uploadSection: { backgroundColor: "#FFFFFF", padding: "20px", borderRadius: "8px", marginBottom: "30px", boxShadow: "0 1px 4px rgba(0,0,0,0.08)" },
  uploadForm: { display: "flex", gap: "10px", alignItems: "center" },
  uploadButton: { padding: "8px 16px", backgroundColor: "#3B82F6", color: "#fff", border: "none", borderRadius: "4px", cursor: "pointer" },
  success: { color: "#16a34a", marginTop: "10px" },
  error: { color: "#dc2626", marginTop: "10px" },
  listSection: { backgroundColor: "#FFFFFF", padding: "20px", borderRadius: "8px", boxShadow: "0 1px 4px rgba(0,0,0,0.08)" },
  empty: { color: "#666" },
  table: { width: "100%", borderCollapse: "collapse" },
  th: { textAlign: "left", padding: "10px", borderBottom: "2px solid #e5e7eb", fontSize: "13px", color: "#0F172A" },
  td: { padding: "10px", borderBottom: "1px solid #e5e7eb", fontSize: "14px", color: "#0F172A" },
  badge: { color: "#fff", padding: "4px 10px", borderRadius: "12px", fontSize: "12px" },
  actionButton: { padding: "6px 12px", marginRight: "6px", backgroundColor: "#3B82F6", color: "#fff", border: "none", borderRadius: "4px", cursor: "pointer", fontSize: "12px" },
};

export default Documents;