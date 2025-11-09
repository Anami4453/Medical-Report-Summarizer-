import React from "react";
import { Routes, Route, Link } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Upload from "./pages/Upload";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import ReportDetails from "./pages/ReportDetails";

export default function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-cyan-50 to-emerald-50">
      {/* 🌈 Premium Medical Navbar */}
      <nav className="bg-gradient-to-r from-cyan-500 via-sky-600 to-emerald-500 shadow-xl py-6 px-10 flex justify-between items-center text-white rounded-b-2xl backdrop-blur-md">
        <div className="text-2xl font-extrabold tracking-wide drop-shadow-md">
          🩺 MedReport AI
        </div>

        <div className="space-x-6 text-sm font-semibold">
          <Link
            to="/"
            className="hover:text-yellow-200 hover:drop-shadow-lg transition-all duration-300 hover:scale-105"
          >
            Dashboard
          </Link>
          <Link
            to="/upload"
            className="hover:text-yellow-200 hover:drop-shadow-lg transition-all duration-300 hover:scale-105"
          >
            Upload
          </Link>
          <Link
            to="/login"
            className="hover:text-yellow-200 hover:drop-shadow-lg transition-all duration-300 hover:scale-105"
          >
            Login
          </Link>
          <Link
            to="/signup"
            className="hover:text-yellow-200 hover:drop-shadow-lg transition-all duration-300 hover:scale-105"
          >
            Sign Up
          </Link>
        </div>
      </nav>

      {/* 🧾 Page Routes */}
      <main className="p-10">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/reports/:id" element={<ReportDetails />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
        </Routes>
      </main>
    </div>
  );
}
