import { guard, accessToken } from "./_pt.js";

export default async function handler(req, res) {
  if (req.method !== "POST") return res.status(405).json({ error: "POST only" });
  if (!guard(req, res)) return;
  try {
    const { board_id, title, description, link, image_url, image_base64, content_type } = req.body || {};
    if (!board_id || !link) return res.status(400).json({ error: "board_id and link required" });

    const media = image_base64
      ? { source_type: "image_base64", content_type: content_type || "image/png", data: image_base64 }
      : { source_type: "image_url", url: image_url };
    if (!image_base64 && !image_url)
      return res.status(400).json({ error: "image_url or image_base64 required" });

    const at = await accessToken();
    const r = await fetch("https://api.pinterest.com/v5/pins", {
      method: "POST",
      headers: { Authorization: "Bearer " + at, "Content-Type": "application/json" },
      body: JSON.stringify({
        board_id,
        media_source: media,
        title: (title || "").slice(0, 100),
        description: (description || "").slice(0, 800),
        link,
      }),
    });
    const j = await r.json();
    res.status(r.status).json(j);
  } catch (e) {
    res.status(500).json({ error: String(e.message || e) });
  }
}
