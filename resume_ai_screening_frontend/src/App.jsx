import React, { useRef, useState } from "react";
import axios from "axios";
import styles from "./App.module.css";

const API_BASE = "http://localhost:8000";

function ResultsTable({ results, highlight }) {
  const [sortKey, setSortKey] = useState(
    highlight === "vector" ? "vector_match_score" : "spacy_match_score"
  );
  const [sortOrder, setSortOrder] = useState("desc");

  const getSortValue = (r, key) => {
    if (key === "resume_score") return r.resume_score ?? r.vector_match_score ?? 0;
    if (key === "spacy_match_score") return r.spacy_match_score ?? 0;
    if (key === "vector_match_score") return r.vector_match_score ?? 0;
    return "";
  };

  const sortedResults = [...results].sort((a, b) => {
    const aVal = getSortValue(a, sortKey);
    const bVal = getSortValue(b, sortKey);
    if (sortOrder === "asc") return aVal - bVal;
    return bVal - aVal;
  });

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortOrder("desc");
    }
  };

  return (
    <table className={styles.resultsTable}>
      <thead>
        <tr>
          <th>Name</th>
          <th>Email</th>
          <th style={{ cursor: "pointer" }} onClick={() => handleSort("resume_score")}>
            Score {sortKey === "resume_score" ? (sortOrder === "asc" ? "▲" : "▼") : ""}
          </th>
          <th style={{ cursor: "pointer" }} onClick={() => handleSort("spacy_match_score")}>
            SpaCy {sortKey === "spacy_match_score" ? (sortOrder === "asc" ? "▲" : "▼") : ""}
          </th>
          <th style={{ cursor: "pointer" }} onClick={() => handleSort("vector_match_score")}>
            Vector {sortKey === "vector_match_score" ? (sortOrder === "asc" ? "▲" : "▼") : ""}
          </th>
          <th>PDF</th>
        </tr>
      </thead>
      <tbody>
        {sortedResults.map((r) => (
          <tr key={r.resume_id}>
            <td>{r.name}</td>
            <td>{r.email}</td>
            <td>
              {r.resume_score !== undefined
                ? r.resume_score
                : r.vector_match_score?.toFixed(2)}
            </td>
            <td>
              {highlight === "spacy" ? (
                <b>{r.spacy_match_score !== undefined ? r.spacy_match_score : "-"}</b>
              ) : (
                r.spacy_match_score !== undefined ? r.spacy_match_score : "-"
              )}
            </td>
            <td>
              {highlight === "vector" ? (
                <b>{r.vector_match_score !== undefined ? r.vector_match_score.toFixed(2) : "-"}</b>
              ) : (
                r.vector_match_score !== undefined ? r.vector_match_score.toFixed(2) : "-"
              )}
            </td>
            <td>
              {r.pdf_path ? (
                <a
                  href={`${API_BASE}/${r.pdf_path}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={styles.link}
                  style={{ whiteSpace: "nowrap" }}
                >
                  View PDF
                </a>
              ) : (
                "-"
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function App() {
  // State for screening
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [jdText, setJdText] = useState("");
  const [topK, setTopK] = useState(5);
  const resumesInput = useRef();
  const jdFileInput = useRef();

  // State for semantic search
  const [searchResults, setSearchResults] = useState(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchText, setSearchText] = useState("");
  const searchFileInput = useRef();
  const [searchTopK, setSearchTopK] = useState(5);

  // Resume screening handler
  const handleScreening = async (e) => {
    e.preventDefault();
    setResults(null);
    setLoading(true);

    const form = new FormData();
    for (const file of resumesInput.current.files) {
      form.append("resumes", file);
    }
    if (jdFileInput.current.files[0]) {
      form.append("jd_file", jdFileInput.current.files[0]);
    }
    if (jdText.trim() && !jdFileInput.current.files[0]) {
      form.append("jd_text", jdText);
    }
    form.append("top_k", topK);

    try {
      const res = await axios.post(`${API_BASE}/ai_screener/`, form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResults(res.data);
    } catch (err) {
      alert("Error: " + (err.response?.data?.detail || err.message));
    }
    setLoading(false);
  };

  // Semantic search handler
  const handleSemanticSearch = async (e) => {
    e.preventDefault();
    setSearchResults(null);
    setSearchLoading(true);

    const form = new FormData();
    if (searchFileInput.current.files[0]) {
      form.append("query_file", searchFileInput.current.files[0]);
    }
    if (searchText.trim() && !searchFileInput.current.files[0]) {
      form.append("query_text", searchText);
    }
    form.append("top_k", searchTopK);

    try {
      const res = await axios.post(`${API_BASE}/similarity_search/`, form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setSearchResults(res.data.results);
    } catch (err) {
      alert("Error: " + (err.response?.data?.detail || err.message));
    }
    setSearchLoading(false);
  };

  return (
    <div className={styles.container}>
      <h1>Resume Screening (SpaCy + FAISS)</h1>

      {/* Resume Screening Form */}
      <form onSubmit={handleScreening}>
        <label>
          Upload Resumes (PDF, multiple):
          <input type="file" accept="application/pdf" multiple ref={resumesInput} required />
        </label>
        <label>
          Upload JD (PDF):
          <input type="file" accept="application/pdf" ref={jdFileInput} />
        </label>
        <div style={{ textAlign: "center", margin: "10px 0" }}>
          <b>or</b>
        </div>
        <label>
          Paste JD Text:
          <textarea
            rows={5}
            value={jdText}
            onChange={(e) => setJdText(e.target.value)}
            placeholder="Paste job description here"
          />
        </label>
        <label>
          Top K Results:
          <input
            type="number"
            min={1}
            max={20}
            value={topK}
            onChange={(e) => setTopK(e.target.value)}
            style={{ width: 60, marginLeft: 8 }}
          />
        </label>
        <button type="submit" disabled={loading}>
          {loading ? "Screening..." : "Screen Resumes"}
        </button>
      </form>

      {loading && <div className={styles.loading}>Loading...</div>}
      {results && (
        <>
          <h2>Screening Results</h2>
          <ResultsTable results={results} highlight="spacy" />
        </>
      )}

      <hr style={{ margin: "40px 0" }} />

      {/* Semantic Search Form */}
      <h2>Semantic Search (RAG) - Search in Full DB</h2>
      <form onSubmit={handleSemanticSearch}>
        <label>
          Upload Query (PDF):
          <input type="file" accept="application/pdf" ref={searchFileInput} />
        </label>
        <div style={{ textAlign: "center", margin: "10px 0" }}>
          <b>or</b>
        </div>
        <label>
          Paste Query Text:
          <textarea
            rows={4}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            placeholder="Paste search text or JD here"
          />
        </label>
        <label>
          Top K Results:
          <input
            type="number"
            min={1}
            max={20}
            value={searchTopK}
            onChange={(e) => setSearchTopK(e.target.value)}
            style={{ width: 60, marginLeft: 8 }}
          />
        </label>
        <button type="submit" disabled={searchLoading}>
          {searchLoading ? "Searching..." : "Semantic Search"}
        </button>
      </form>

      {searchLoading && <div className={styles.loading}>Searching...</div>}
      {searchResults && (
        <>
          <h3>Semantic Search Results</h3>
          <ResultsTable results={searchResults} highlight="vector" />
        </>
      )}
    </div>
  );
}

export default App;
