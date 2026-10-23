import { guard, accessToken, envStatus, base } from "./_pt.js";

export default async function handler(req, res) {
  if (req.method !== "POST") return res.status(405).json({ error: "POST only" });
  if (!guard(req, res)) return;
  try {
    const { name, description } = req.body || {};
    if (!name) return res.status(400).json({ error: "name required" });
    const at = await accessToken();
    const r = await fetch(base(req.body?.env) + "/boards", {
      method: "POST",
      headers: { Authorization: "Bearer " + at, "Content-Type": "application/json" },
      body: JSON.stringify({ name, description: description || "" }),
    });
    const j = await r.json();
    res.status(r.status).json({ id: j.id, name: j.name, error: j.message });
  } catch (e) {
    res.status(500).json({ error: String(e.message || e), env: envStatus() });
  }
}
