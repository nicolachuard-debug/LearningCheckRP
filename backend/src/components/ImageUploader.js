import React, { useRef, useState } from "react";
import "./ImageUploader.css";

export default function ImageUploader({ onAnalyze, loading, error }) {
  const [preview, setPreview] = useState(null);
  const [file, setFile] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef(null);

  const handleFile = (f) => {
    if (!f || !f.type.startsWith("image/")) return;
    setFile(f);
    setPreview(URL.createObjectURL(f));
  };

  const handleInputChange = (e) => {
    handleFile(e.target.files[0]);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    handleFile(e.dataTransfer.files[0]);
  };

  const handleSubmit = () => {
    if (file) onAnalyze(file);
  };

  const reset = () => {
    setFile(null);
    setPreview(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  return (
    <div className="uploader-container">
      <h1 className="uploader-title">
        📚 Trasforma i tuoi appunti in <span className="highlight">quiz</span>
      </h1>
      <p className="uploader-subtitle">
        Carica una foto di un documento, appunto o slide: genereremo domande per verificare quanto hai capito.
      </p>

      <div
        className={`dropzone ${dragOver ? "dragover" : ""} ${preview ? "has-preview" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => !preview && inputRef.current.click()}
      >
        {preview ? (
          <img src={preview} alt="Anteprima" className="preview-image" />
        ) : (
          <div className="dropzone-placeholder">
            <span className="dropzone-icon">🖼️</span>
            <p>Clicca o trascina qui un'immagine</p>
          </div>
        )}
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          onChange={handleInputChange}
          hidden
        />
      </div>

      {error && <p className="uploader-error">⚠️ {error}</p>}

      <div className="uploader-actions">
        {preview && !loading && (
          <button className="btn btn-secondary" onClick={reset}>
            Cambia immagine
          </button>
        )}
        <button
          className="btn btn-primary"
          onClick={handleSubmit}
          disabled={!file || loading}
        >
          {loading ? (
            <>
              <span className="spinner" /> Analisi in corso...
            </>
          ) : (
            "Genera il quiz ✨"
          )}
        </button>
      </div>
    </div>
  );
}
