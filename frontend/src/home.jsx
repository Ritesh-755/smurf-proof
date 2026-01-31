import { useEffect, useRef, useState } from "react";

const BASE_URL = "http://127.0.0.1:8000/api";

export default function GraphGuardHome() {
  const uploadPanelRef = useRef(null);
  const csvInputRef = useRef(null);

  const [canAnalyze, setCanAnalyze] = useState(false);
  const [showPopup, setShowPopup] = useState(false);
  const [popupMessage, setPopupMessage] = useState("");
  const [popupType, setPopupType] = useState("success"); // success | error

  /* =========================
     FILE VALIDATION
  ========================= */
  useEffect(() => {
    const csvInput = csvInputRef.current;
    if (!csvInput) return;

    const onFileChange = () => {
      const file = csvInput.files[0];
      console.log("[CSV] File selected:", file?.name);

      setCanAnalyze(false);

      if (!file || !file.name.endsWith(".csv")) {
        console.error("[CSV] Invalid file selected");
        showErrorPopup("Please upload a valid CSV file.");
        return;
      }

      const reader = new FileReader();
      reader.onload = e => {
        const text = e.target.result;
        const lines = text.split("\n");

        if (lines.length < 2 || !lines[0].includes(",")) {
          console.error("[CSV] Invalid CSV structure");
          showErrorPopup("Invalid CSV format. Check columns.");
          return;
        }

        console.log("[CSV] File validated successfully");
      };

      reader.readAsText(file);
    };

    csvInput.addEventListener("change", onFileChange);
    return () => csvInput.removeEventListener("change", onFileChange);
  }, []);

  /* =========================
     HELPERS
  ========================= */
  const showSuccessPopup = message => {
    setPopupType("success");
    setPopupMessage(message);
    setShowPopup(true);
  };

  const showErrorPopup = message => {
    setPopupType("error");
    setPopupMessage(message);
    setShowPopup(true);
  };

  const openUploader = () => {
    console.log("[UI] Open upload panel");
    uploadPanelRef.current.classList.remove("hidden");
  };

  /* =========================
     UPLOAD CSV
  ========================= */
  const uploadCsv = async () => {
    const file = csvInputRef.current?.files[0];
    if (!file) return;

    console.log("[UPLOAD] Starting CSV upload:", file.name);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${BASE_URL}/upload-csv/`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("Upload failed");

      console.log("[UPLOAD] CSV uploaded successfully");

      showSuccessPopup(
        "CSV uploaded successfully. You can now analyze transactions."
      );

      setCanAnalyze(true);
    } catch (error) {
      console.error("[UPLOAD] CSV upload failed:", error);
      showErrorPopup("CSV upload failed. Please try again.");
    }
  };

  /* =========================
     ANALYZE
  ========================= */
  const analyze = async () => {
    console.log("[ANALYZE] Analysis started");

    try {
      const res = await fetch(`${BASE_URL}/analyze/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });

      if (!res.ok) throw new Error("Analyze failed");

      console.log("[ANALYZE] Analysis triggered successfully");
      alert("✅ Analysis started successfully.");
    } catch (error) {
      console.error("[ANALYZE] Analysis failed:", error);
      alert("❌ Analysis failed.");
    }
  };

  return (
    <div className="bg-black text-white min-h-screen relative overflow-hidden">
      {/* Background */}
      <div className="fixed inset-0 bg-gradient-to-b from-black via-slate-950 to-black" />

      {/* Glow */}
      <div className="fixed inset-0 flex items-center justify-center pointer-events-none">
        <div className="w-[520px] h-[520px] rounded-full bg-cyan-500/20 blur-3xl animate-pulse" />
      </div>

      {/* Popup */}
      {showPopup && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
          <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 max-w-sm w-full text-center">
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
              className="px-6 py-2 rounded-lg bg-cyan-500 text-black font-semibold hover:bg-cyan-400"
            >
              OK
            </button>
          </div>
        </div>
      )}

      {/* Content */}
      <div className="relative min-h-screen flex flex-col">
        <div className="absolute top-6 left-8">
          <h1 className="text-xl font-semibold">
            <span className="text-cyan-400">Graph</span>Guard
          </h1>
        </div>

        <main className="flex-1 flex items-center justify-center px-6">
          <div className="max-w-3xl text-center">
            <h2 className="text-5xl font-extrabold mb-6">
              See Money Laundering
              <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">
                Before It Happens
              </span>
            </h2>

            <p className="text-slate-300 mb-10">
              Upload transaction data and detect laundering patterns instantly.
            </p>

            <button
              onClick={openUploader}
              className="px-7 py-3 rounded-xl bg-cyan-500 text-black font-semibold hover:bg-cyan-400"
            >
              Explore Live Graph
            </button>

            <div
              ref={uploadPanelRef}
              className="hidden mt-10 max-w-xl mx-auto bg-black/60 border border-slate-700 rounded-2xl p-6"
            >
              <input
                ref={csvInputRef}
                type="file"
                accept=".csv"
                className="block w-full text-sm text-slate-300 file:bg-slate-800 file:text-white file:rounded-lg cursor-pointer"
              />

              <button
                onClick={uploadCsv}
                className="mt-5 w-full px-6 py-3 rounded-xl bg-cyan-500 text-black font-semibold hover:bg-cyan-400"
              >
                Upload Transactions
              </button>

              {canAnalyze && (
                <button
                  onClick={analyze}
                  className="mt-4 w-full px-6 py-3 rounded-xl bg-green-500 text-black font-semibold hover:bg-green-400"
                >
                  Analyze Transactions
                </button>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
