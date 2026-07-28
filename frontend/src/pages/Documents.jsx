import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { uploadDocument, listDocuments } from "../services/documentService";
import { logout } from "../services/authService";

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
                <th style={styles.th}>Fecha</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((doc) => (
                <tr key={doc.id}>
                  <td style={styles.td}>{doc.original_filename}</td>
                  <td style={styles.td}>{doc.status}</td>
                  <td style={styles.td}>{doc.uploaded_by}</td>
                  <td style={styles.td}>
                    {new Date(doc.uploaded_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

const styles = {
  container: {
    maxWidth: "800px",
    margin: "0 auto",
    padding: "40px 20px",
    fontFamily: "sans-serif",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "30px",
  },
  logoutButton: {
    padding: "8px 16px",
    backgroundColor: "#dc2626",
    color: "#fff",
    border: "none",
    borderRadius: "4px",
    cursor: "pointer",
  },
  uploadSection: {
    backgroundColor: "#f9fafb",
    padding: "20px",
    borderRadius: "8px",
    marginBottom: "30px",
  },
  uploadForm: {
    display: "flex",
    gap: "10px",
    alignItems: "center",
  },
  uploadButton: {
    padding: "8px 16px",
    backgroundColor: "#2563eb",
    color: "#fff",
    border: "none",
    borderRadius: "4px",
    cursor: "pointer",
  },
  success: {
    color: "#16a34a",
    marginTop: "10px",
  },
  error: {
    color: "#dc2626",
    marginTop: "10px",
  },
  listSection: {
    backgroundColor: "#fff",
  },
  empty: {
    color: "#666",
  },
  table: {
    width: "100%",
    borderCollapse: "collapse",
  },
  th: {
    textAlign: "left",
    padding: "10px",
    borderBottom: "2px solid #e5e7eb",
    fontSize: "13px",
    color: "#374151",
  },
  td: {
    padding: "10px",
    borderBottom: "1px solid #e5e7eb",
    fontSize: "14px",
  },
};

export default Documents;