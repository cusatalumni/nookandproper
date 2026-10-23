import { guard, accessToken } from "./_pt.js";

export default async function handler(req, res) {
  if (!guard(req, res)) return;
  try {
    const at = await accessToken();
    const r = await fetch("https://api.pinterest.com/v5/boards?page_size=100", {
      headers: { Authorization: "Bearer " + at },
    });
    const j = await r.json();
    res.status(r.status).json((j.items || []).map((b) => ({ id: b.id, name: b.name })));
  } catch (e) {
    res.status(500).json({ error: String(e.message || e) });
  }
}
