import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { motion } from "framer-motion";

export default function ReportDetails() {
  const { id } = useParams();
  const [report, setReport] = useState(null);

  useEffect(() => {
    const fetchReport = async () => {
      const token = localStorage.getItem("access");
      const res = await fetch(`http://127.0.0.1:8000/api/reports/${id}/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) setReport(await res.json());
    };
    fetchReport();
  }, [id]);

  if (!report) return <p className="text-center mt-10">Loading...</p>;

  return (
    <motion.div
      className="max-w-3xl mx-auto bg-white/70 backdrop-blur-md p-4 sm:p-8 rounded-2xl shadow-lg mt-6"
      initial={{ opacity: 0, y: 25 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      <h2 className="text-2xl sm:text-3xl font-bold text-indigo-700 mb-4">Report Summary</h2>
      <p className="whitespace-pre-wrap text-gray-700 break-words">{report.extracted_text || "No text found."}</p>
    </motion.div>
  );
}
