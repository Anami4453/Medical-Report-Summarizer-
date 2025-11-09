import React, { useState } from "react";
import { motion } from "framer-motion";
import { Link, useNavigate } from "react-router-dom";
import { token } from "../services/api";

export default function Login() {
  // backend expects username (signup collects username)
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await token(username, password);
      const access = res.data?.access;
      if (access) {
        localStorage.setItem("access_token", access);
        if (res.data.refresh) localStorage.setItem("refresh_token", res.data.refresh);
        // Redirect user to Upload page after successful login
        navigate("/upload");
      } else {
        setError("Login failed: no token returned");
      }
    } catch (err) {
      const data = err.response?.data;
      if (data) {
        if (typeof data === "string") setError(data);
        else if (typeof data === "object") {
          const parts = Object.entries(data).map(([k, v]) => (Array.isArray(v) ? v.join(" ") : String(v)));
          // prefer detail if present
          setError(data.detail || parts.join(" | "));
        } else setError(JSON.stringify(data));
      } else {
        setError("Login failed. Check credentials.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex justify-center items-center min-h-screen bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 px-4">
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="backdrop-blur-lg bg-white/10 p-6 sm:p-8 rounded-2xl shadow-2xl border border-white/20 w-full max-w-md text-white"
      >
        <h2 className="text-3xl font-bold mb-6 text-center">Login</h2>
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm mb-1">Username</label>
            <input
              type="text"
              className="w-full p-2 rounded-md bg-white/20 border border-white/30 text-white placeholder-gray-200 focus:outline-none focus:ring-2 focus:ring-yellow-300"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter your username"
              required
            />
          </div>
          <div>
            <label className="block text-sm mb-1">Password</label>
            <input
              type="password"
              className="w-full p-2 rounded-md bg-white/20 border border-white/30 text-white placeholder-gray-200 focus:outline-none focus:ring-2 focus:ring-yellow-300"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
            />
          </div>
          {error && <p className="text-red-300 text-sm text-center">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-yellow-400 text-black py-2 rounded-md font-semibold hover:bg-yellow-300 transition disabled:opacity-50"
          >
            {loading ? "Logging in..." : "Login"}
          </button>
        </form>
        <p className="mt-4 text-center text-sm">
          Don’t have an account?{" "}
          <Link to="/signup" className="text-yellow-300 hover:underline">
            Sign Up
          </Link>
        </p>
      </motion.div>
    </div>
  );
}
