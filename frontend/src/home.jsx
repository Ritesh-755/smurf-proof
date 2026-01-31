import { useEffect, useRef, useState } from "react";
import AMLGraph from "./AMLGraph";

const BASE_URL = "http://127.0.0.1:8000/api";

export default function GraphGuardHome() {
  const uploadPanelRef = useRef(null);
  const csvInputRef = useRef(null);

  const [canAnalyze, setCanAnalyze] = useState(false);
  const [showPopup, setShowPopup] = useState(false);
  const [popupMessage, setPopupMessage] = useState("");
  const [popupType, setPopupType] = useState("success");
  const [showGraph, setShowGraph] = useState(false);

  /* ================= FILE VALIDATION ================= */
  useEffect(() => {
    const csvInput = csvInputRef.current;
    if (!csvInput) return;

    const onFileChange = () => {
      const file = csvInput.files[0];
      console.log("[CSV] Selected:", file?.name);

      setCanAnalyze(false);

      if (!file || !file.name.endsWith(".csv")) {
        showError("Please upload a valid CSV file.");
        return;
      }

      const reader = new FileReader();
      reader.onload = e => {
        const text = e.target.result;
        const lines = text.split("\n");

        if (lines.length < 2 || !lines[0].includes(",")) {
          showError("Invalid CSV format.");
          return;
        }

        console.log("[CSV] Validation passed");
        showSuccess("Valid CSV detected. Ready to upload.");
      };

      reader.readAsText(file);
    };

    csvInput.addEventListener("change", onFileChange);
    return () => csvInput.removeEventListener("change", onFileChange);
  }, []);

  /* ================= HELPERS ================= */
  const showSuccess = msg => {
    setPopupType("success");
    setPopupMessage(msg);
    setShowPopup(true);
  };

  const showError = msg => {
    setPopupType("error");
    setPopupMessage(msg);
    setShowPopup(true);
  };

  const openUploader = () => {
    uploadPanelRef.current.classList.remove("hidden");
  };

  /* ================= UPLOAD CSV ================= */
  const uploadCsv = async () => {
    const file = csvInputRef.current.files[0];
    if (!file) return;

    console.log("[UPLOAD] Uploading CSV…");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${BASE_URL}/upload-csv/`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error();

      console.log("[UPLOAD] Success");
      setCanAnalyze(true);
      showSuccess("CSV uploaded successfully. You can now analyze.");
    } catch {
      showError("CSV upload failed.");
    }
  };

  /* ================= ANALYZE ================= */
  const analyze = async () => {
    console.log("[ANALYZE] Triggering backend analysis");

    try {
      const res = await fetch(`${BASE_URL}/analyze/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });

      if (!res.ok) throw new Error();

      console.log("[ANALYZE] Backend started");
      showSuccess("Analysis started. Rendering AML graph…");

      // ✅ THIS IS THE KEY
      setShowGraph(true);
    } catch {
      showError("Analysis failed.");
    }
  };

  return (
    <div className="bg-black text-white min-h-screen relative overflow-hidden">
      <div className="fixed inset-0 bg-gradient-to-b from-black via-slate-950 to-black" />

      {/* POPUP */}
      {showPopup && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
          <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 w-[340px] text-center">
            <h3
              className={`text-lg font-semibold mb-3 ${
                popupType === "success" ? "text-green-400" : "text-red-400"
              }`}
            >
              {popupType === "success" ? "Success" : "Error"}
            </h3>
            <p className="text-slate-300 mb-5">{popupMessage}</p>
            <button
              onClick={() => setShowPopup(false)}
              className="px-6 py-2 rounded-lg bg-cyan-500 text-black font-semibold"
            >
              OK
            </button>
          </div>
        </div>
      )}

      {/* HOME CONTENT */}
      {!showGraph && (
        <main className="relative min-h-screen flex items-center justify-center">
          <div className="max-w-3xl text-center">
            <h2 className="text-5xl font-extrabold mb-6">
              See Money Laundering
              <br />
              <span className="text-cyan-400">Before It Happens</span>
            </h2>

            <button
              onClick={openUploader}
              className="px-7 py-3 rounded-xl bg-cyan-500 text-black font-semibold"
            >
              Explore Live Graph
            </button>

            <div
              ref={uploadPanelRef}
              className="hidden mt-10 max-w-xl mx-auto bg-black/60 border border-slate-700 rounded-2xl p-6"
            >
              <input ref={csvInputRef} type="file" accept=".csv" />

              <button
                onClick={uploadCsv}
                className="mt-5 w-full px-6 py-3 bg-cyan-500 text-black rounded-xl"
              >
                Upload Transactions
              </button>

              {canAnalyze && (
                <button
                  onClick={analyze}
                  className="mt-4 w-full px-6 py-3 bg-green-500 text-black rounded-xl"
                >
                  Analyze Transactions
                </button>
              )}
            </div>
          </div>
        </main>
      )}

      {/* GRAPH */}
      {showGraph && <AMLGraph />}
    </div>
  );
}
