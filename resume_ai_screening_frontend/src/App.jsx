import React, { useRef, useState, useEffect } from "react";
import axios from "axios";
import styles from "./App.module.css";

const API_BASE = "http://localhost:8000";

// Theme Toggle Switch
function ThemeSwitch({ theme, setTheme }) {
  return (
    <div className={styles.themeSwitchWrapper}>
      <span className={styles.themeIcon}>🌞</span>
      <label className={styles.switch}>
        <input
          type="checkbox"
          checked={theme === "dark"}
          onChange={() => setTheme(theme === "light" ? "dark" : "light")}
          aria-label="Toggle light/dark mode"
        />
        <span className={styles.slider}></span>
      </label>
      <span className={styles.themeIcon}>🌙</span>
    </div>
  );
}

// Custom Stepper
function Stepper({ value, setValue, min = 1, max = 20 }) {
  const handleChange = (e) => {
    let val = parseInt(e.target.value, 10);
    if (isNaN(val)) val = min;
    if (val < min) val = min;
    if (val > max) val = max;
    setValue(val);
  };
  const handleStep = (delta) => {
    setValue((prev) => {
      let next = prev + delta;
      if (next < min) next = min;
      if (next > max) next = max;
      return next;
    });
  };
  return (
    <div className={styles.stepper}>
      <button
        type="button"
        className={styles.stepperBtn}
        onClick={() => handleStep(-1)}
        aria-label="Decrease"
        disabled={value <= min}
      >–</button>
      <input
        type="number"
        min={min}
        max={max}
        value={value}
        onChange={handleChange}
        className={styles.stepperInput}
        aria-label="Top K"
      />
      <button
        type="button"
        className={styles.stepperBtn}
        onClick={() => handleStep(1)}
        aria-label="Increase"
        disabled={value >= max}
      >+</button>
    </div>
  );
}

// Score color logic
function getScoreClass(score) {
  if (score === undefined || score === null) return "";
  if (score >= 90) return "scoreStrongGreen";
  if (score >= 75) return "scoreLightGreen";
  if (score >= 60) return "scoreGold";
  if (score >= 40) return "scoreDarkYellow";
  return "scoreLightRed";
}

// Results table with OpenAI HR Score as "Score"
function ResultsTable({ results, highlight }) {
  const [sortKey, setSortKey] = useState("openai_hr_score");
  const [sortOrder, setSortOrder] = useState("desc");

  const getSortValue = (r, key) => {
    if (key === "openai_hr_score") return r.openai_hr_score ?? 0;
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
    <div className={styles.tableCard}>
      <table className={styles.resultsTable}>
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th style={{ cursor: "pointer" }} onClick={() => handleSort("openai_hr_score")}>
              Score {sortKey === "openai_hr_score" ? (sortOrder === "asc" ? "▲" : "▼") : ""}
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
              <td className={styles[getScoreClass(r.openai_hr_score)]}>
                {r.openai_hr_score !== undefined ? r.openai_hr_score : "-"}
              </td>
              <td className={styles[getScoreClass(r.spacy_match_score)]}>
                {highlight === "spacy" ? (
                  <b>{r.spacy_match_score !== undefined ? r.spacy_match_score : "-"}</b>
                ) : (
                  r.spacy_match_score !== undefined ? r.spacy_match_score : "-"
                )}
              </td>
              <td className={styles[getScoreClass(r.vector_match_score)]}>
                {highlight === "vector" ? (
                  <b>{r.vector_match_score !== undefined ? r.vector_match_score.toFixed(2) : "-"}</b>
                ) : (
                  r.vector_match_score !== undefined ? r.vector_match_score.toFixed(2) : "-"
                )}
              </td>
              <td>
                {r.pdf_path ? (
                  <>
                    <a
                      href={`${API_BASE}/${r.pdf_path}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className={styles.neonBtn}
                      style={{ marginRight: 8 }}
                    >
                      View PDF
                    </a>
                    <a
                      href={`${API_BASE}/${r.pdf_path}`}
                      download
                      className={styles.neonBtn}
                    >
                      Download
                    </a>
                  </>
                ) : (
                  "-"
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function App() {
  // THEME STATE
  const [theme, setTheme] = useState(() => {
    const stored = localStorage.getItem("theme");
    if (stored) return stored;
    return "dark";
  });
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  // Resume screening state
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [jdText, setJdText] = useState("");
  const [topK, setTopK] = useState(5);
  const resumesInput = useRef();
  const jdFileInput = useRef();
  const [error, setError] = useState(null);

  // Semantic search state
  const [searchResults, setSearchResults] = useState(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchText, setSearchText] = useState("");
  const searchFileInput = useRef();
  const [searchTopK, setSearchTopK] = useState(5);
  const [searchError, setSearchError] = useState(null);

  // Resume screening handler
  const handleScreening = async (e) => {
    e.preventDefault();
    setResults(null);
    setError(null);
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
      setError(err.response?.data?.detail || err.message);
    }
    setLoading(false);
  };

  // Semantic search handler
  const handleSemanticSearch = async (e) => {
    e.preventDefault();
    setSearchResults(null);
    setSearchError(null);
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
      setSearchError(err.response?.data?.detail || err.message);
    }
    setSearchLoading(false);
  };

  // Clear DB handler
  const handleClearDB = async () => {
    if (
      window.confirm(
        "Are you sure you want to delete ALL database and FAISS data? This cannot be undone."
      )
    ) {
      try {
        const res = await fetch(`${API_BASE}/clear_db/`, {
          method: "POST",
        });
        const data = await res.json();
        if (res.ok) {
          alert(data.status || "Database cleared!");
          setResults(null);
          setSearchResults(null);
        } else {
          alert(data.error || "Failed to clear database.");
        }
      } catch (e) {
        alert("Error clearing database.");
      }
    }
  };

  return (
    <div className={styles.container}>
      <ThemeSwitch theme={theme} setTheme={setTheme} />
      <h1 className={styles.neonText}>Resume Screening</h1>
      <button
        onClick={handleClearDB}
        style={{
          background: "red",
          color: "white",
          margin: "1em 0",
          padding: "0.5em 1.5em",
          border: "none",
          borderRadius: "6px",
          fontWeight: "bold",
          cursor: "pointer",
          fontSize: "1em"
        }}
      >
        Clear All Data
      </button>
      <p className={styles.subtitle}>
        AI-powered, advanced HR evaluator for your hiring needs.
      </p>

      {/* Resume Screening Form */}
      <form onSubmit={handleScreening} className={styles.formSection}>
        <label>
          Upload Resumes (PDF, multiple):
          <input type="file" accept="application/pdf" multiple ref={resumesInput} required />
        </label>
        <label>
          Upload JD (PDF):
          <input type="file" accept="application/pdf" ref={jdFileInput} />
        </label>
        <div className={styles.orDivider}>
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
        {/* Top K stepper row */}
        <div className={styles.stepperRow}>
          <span className={styles.stepperLabel}>Top K Results:</span>
          <Stepper value={topK} setValue={setTopK} min={1} max={20} />
          <span className={styles.helpText}>Number of top matches to display (1-20)</span>
        </div>
        {error && <div className={styles.error}>{error}</div>}
        <button type="submit" disabled={loading} className={styles.neonBtn}>
          {loading ? <span className={styles.spinner}></span> : null}
          {loading ? "Screening..." : "Screen Resumes"}
        </button>
      </form>

      {loading && <div className={styles.loading}><span className={styles.spinner}></span>Loading...</div>}
      {results && (
        <>
          <h2 className={styles.neonSub}>Screening Results</h2>
          <ResultsTable results={results} highlight="spacy" />
        </>
      )}

      <hr className={styles.sectionDivider} />

      {/* Semantic Search Form */}
      <h2 className={styles.neonSub}>Semantic Search (RAG) - Search in Full DB</h2>
      <form onSubmit={handleSemanticSearch} className={styles.formSection}>
        <label>
          Upload Query (PDF):
          <input type="file" accept="application/pdf" ref={searchFileInput} />
        </label>
        <div className={styles.orDivider}>
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
        <div className={styles.stepperRow}>
          <span className={styles.stepperLabel}>Top K Results:</span>
          <Stepper value={searchTopK} setValue={setSearchTopK} min={1} max={20} />
          <span className={styles.helpText}>Number of top matches to display (1-20)</span>
        </div>
        {searchError && <div className={styles.error}>{searchError}</div>}
        <button type="submit" disabled={searchLoading} className={styles.neonBtn}>
          {searchLoading ? <span className={styles.spinner}></span> : null}
          {searchLoading ? "Searching..." : "Semantic Search"}
        </button>
      </form>
      {searchLoading && <div className={styles.loading}><span className={styles.spinner}></span>Searching...</div>}
      {searchResults && (
        <>
          <h3 className={styles.neonSub}>Semantic Search Results</h3>
          <ResultsTable results={searchResults} highlight="vector" />
        </>
      )}

      <footer className={styles.footer}>
        <span>
          Made with <span className={styles.heart}>♥</span> for hiring teams.
        </span>
      </footer>
    </div>
  );
}

export default App;
