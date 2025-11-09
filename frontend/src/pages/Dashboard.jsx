import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { deleteReport, listReports } from "../services/api";
import toast, { Toaster } from "react-hot-toast";

export default function Dashboard() {
  const [reports, setReports] = useState([]);
  const [openMenu, setOpenMenu] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [pendingDeletes, setPendingDeletes] = useState({});

  const handleRemove = async (reportId) => {
    const confirmRemove = window.confirm("Remove this report? This will remove it from your uploads.");
    if (!confirmRemove) return;

    const token = localStorage.getItem("access_token");
    if (!token) {
      // not logged in: remove locally
      setReports((prev) => prev.filter((r) => r.id !== reportId));
      return;
    }

    try {
      // remove from UI immediately
      const reportObj = reports.find((r) => r.id === reportId);
      setReports((prev) => prev.filter((r) => r.id !== reportId));

  // show undo toast and delay server delete by 6s to allow undo
      const timer = setTimeout(async () => {
        try {
          await deleteReport(token, reportId);
          toast.success("Report deleted");
        } catch (e) {
          console.error("Delete failed", e);
          toast.error("Failed to delete on server");
          // optionally re-add locally
          setReports((prev) => [reportObj, ...prev]);
        } finally {
          setPendingDeletes((prev) => {
            const copy = { ...prev };
            delete copy[reportId];
            return copy;
          });
        }
      }, 6000);

      setPendingDeletes((prev) => ({ ...prev, [reportId]: { report: reportObj, timer } }));

      toast((t) => (
        <span>
          Report removed
          <button
            onClick={() => {
              // undo: cancel timer and restore
              setPendingDeletes((prev) => {
                const entry = prev[reportId];
                if (entry) {
                  clearTimeout(entry.timer);
                }
                const copy = { ...prev };
                delete copy[reportId];
                return copy;
              });
              setReports((prev) => [reportObj, ...prev]);
              toast.dismiss(t.id);
            }}
            className="ml-3 underline"
          >
            Undo
          </button>
        </span>
      ));
    } catch (e) {
      console.error("Delete flow failed", e);
      toast.error("Could not remove report");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const fetchReports = async () => {
      const token = localStorage.getItem("access_token");
      if (!token) return; // don't fetch if not authenticated

      setLoading(true);
      setError(null);
      try {
        const res = await listReports(token);
        // res.data expected to be an array of reports
        // also fetch summaries and map latest summary per report
        let summaries = [];
        try {
          const sres = await (await import("../services/api")).listSummaries(token);
          summaries = sres.data || [];
        } catch (e) {
          summaries = [];
        }
        const latestByReport = {};
        for (const s of summaries) {
          // summaries endpoint returns items ordered by -created_at; take first seen as latest
          if (!latestByReport[s.report]) latestByReport[s.report] = s;
        }

        const mapped = (res.data || []).map((r) => {
          const filename = r.original_file ? r.original_file.split('/').pop() : '';
          const parts = filename.split('.');
          const ext = parts.length > 1 ? parts[parts.length - 1].toLowerCase() : '';
          // Prefer AI-generated summary if available
          let snippet = null;
          const latest = latestByReport[r.id];
          if (latest && latest.summary_text) {
            const cleaned = (latest.summary_text || '').replace(/\s+/g, ' ').trim();
            snippet = cleaned.slice(0, 180);
          } else {
            // Only show snippet for text-like files (pdf/docx/txt/html/doc/rtf)
            const textLikeExts = ["pdf", "docx", "doc", "txt", "md", "rtf", "html", "htm"];
            if (textLikeExts.includes(ext) && r.extracted_text) {
              // normalize whitespace and take a short slice
              const cleaned = (r.extracted_text || '').replace(/\s+/g, ' ').trim();
              // if cleaned contains too many non-printable chars, skip
              const nonprint = (cleaned.match(/[^\x20-\x7E]/g) || []).length;
              if (nonprint < 40) snippet = cleaned.slice(0, 180);
            }
          }

          return {
            id: r.id,
            name: filename || `Report ${r.id}`,
            date: r.uploaded_at || r.created_at || null,
            snippet,
          };
        });
        setReports(mapped);
      } catch (err) {
        console.error('Failed to load reports', err);
        setError('Could not load reports. Are you signed in?');
      } finally {
        setLoading(false);
      }
    };

    fetchReports();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 text-white p-8">
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="max-w-5xl mx-auto"
      >
        <h2 className="text-4xl font-bold mb-6 text-center">
          Your Uploaded Reports
        </h2>

        <Toaster position="top-right" />

        {(() => {
          const token = localStorage.getItem("access_token");
          if (!token) {
            return (
              <div className="text-center text-white/80 p-8 bg-white/5 rounded-2xl">
                <p className="mb-4">You are not signed in — your uploaded reports will appear here.</p>
                <div className="flex items-center justify-center gap-4">
                  <Link to="/login" className="px-4 py-2 bg-yellow-400 text-black rounded-md">Login</Link>
                  <Link to="/signup" className="px-4 py-2 border border-white/20 rounded-md">Signup</Link>
                </div>
                <p className="mt-4 text-sm text-white/60">Or upload a report after signing in to see it listed.</p>
              </div>
            );
          }

          return reports.length === 0 ? (
            <p className="text-center text-white/80">No reports found.</p>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {reports.map((report) => (
                <motion.div
                  key={report.id}
                  whileHover={{ scale: 1.05 }}
                  className="relative backdrop-blur-lg bg-white/10 p-6 rounded-2xl shadow-lg border border-white/20 transition"
                >
                  {/* three-dots menu */}
                  <div className="absolute top-4 right-4">
                    <button
                      aria-label="report-menu"
                      className="text-white/80 hover:text-white"
                      onClick={() => setOpenMenu(openMenu === report.id ? null : report.id)}
                    >
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="12" cy="5" r="1.6" fill="currentColor" />
                        <circle cx="12" cy="12" r="1.6" fill="currentColor" />
                        <circle cx="12" cy="19" r="1.6" fill="currentColor" />
                      </svg>
                    </button>

                    {openMenu === report.id && (
                      <div className="mt-2 bg-white/5 rounded-md shadow-lg py-1 w-40 text-right">
                        <button
                          onClick={() => handleRemove(report.id)}
                          className="block w-full text-left px-3 py-2 text-sm text-red-300 hover:bg-white/10"
                        >
                          Remove
                        </button>
                      </div>
                    )}
                  </div>

                  <h3 className="text-lg sm:text-xl font-semibold mb-2 text-yellow-300 break-words">
                    {report.name}
                  </h3>
                  {report.snippet && (
                    <p
                      className="text-sm mb-2 text-white/80 break-words"
                      style={{ display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}
                    >
                      {report.snippet}...
                    </p>
                  )}
                  <p className="text-sm mb-4 text-white/70 break-words">
                    Uploaded on {report.date}
                  </p>
                  <Link
                    to={`/reports/${report.id}`}
                    className="inline-block px-4 py-2 bg-yellow-400 text-black rounded-md font-medium hover:bg-yellow-300 transition"
                  >
                    View Summary
                  </Link>
                </motion.div>
              ))}
            </div>
          );
        })()}
      </motion.div>
    </div>
  );
}
