import React, { useState } from "react";
import { motion } from "framer-motion";
import toast, { Toaster } from "react-hot-toast";
import { uploadReport, createSummary } from "../services/api";

export default function Upload() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState("");

  const handleFileChange = (e) => setFile(e.target.files[0]);

  const handleUpload = async (e) => {
    e.preventDefault();
    setSummary("");
    if (!file) {
      toast.error("Please select a file first!");
      return;
    }

    const token = localStorage.getItem("access_token");
    if (!token) {
      toast.error("You must be logged in to upload.");
      return;
    }

    setLoading(true);
    try {
      const fd = new FormData();
      fd.append("original_file", file);

      // upload report
      const res = await uploadReport(token, fd);
      toast.success("File uploaded successfully!");
      setFile(null);

      // get created report id
      const report = res.data;
      const id = report.id || report.pk;
      if (id) {
        // request summarization
        const sumRes = await createSummary(token, id);
        // summarize endpoint returns { summary: ... } or similar
        const text = sumRes.data?.summary || sumRes.data?.summary_text || sumRes.data?.summary_text || JSON.stringify(sumRes.data);
        setSummary(text);
      } else {
        setSummary("Uploaded but could not determine report id to summarize.");
      }
    } catch (err) {
      console.error(err);
      toast.error("Upload failed. Check console for details.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex justify-center items-center min-h-screen bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 text-white px-4">
      <Toaster position="top-right" />
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="backdrop-blur-lg bg-white/10 p-6 sm:p-10 rounded-2xl shadow-2xl border border-white/20 w-full max-w-lg text-center"
      >
        <h2 className="text-3xl font-bold mb-6">Upload Your Medical Report</h2>

        <form onSubmit={handleUpload} className="space-y-6">
          <div className="p-4 sm:p-6 border-2 border-dashed border-white/40 rounded-xl hover:border-yellow-300 transition">
            <label className="block cursor-pointer">
              <input
                type="file"
                accept=".pdf,.docx,.jpg,.png"
                className="hidden"
                onChange={handleFileChange}
              />
              <div className="text-white/80">
                {file ? (
                  <p className="font-medium text-yellow-300 break-words">{file.name}</p>
                ) : (
                  <p>Click to select your report</p>
                )}
              </div>
            </label>
          </div>

          <button
            type="submit"
            disabled={loading}
            className={`w-full py-2 rounded-md font-semibold transition ${
              loading
                ? "bg-yellow-300/70 cursor-not-allowed"
                : "bg-yellow-400 hover:bg-yellow-300 text-black"
            }`}
          >
            {loading ? "Uploading..." : "Upload"}
          </button>
        </form>

        {summary && (
          <div className="mt-8 bg-white/5 p-6 rounded-lg text-left">
            <h3 className="text-xl font-semibold mb-2">Summary</h3>
            <p className="text-sm text-white/90 whitespace-pre-wrap">{summary}</p>
          </div>
        )}
      </motion.div>
    </div>
  );
}
