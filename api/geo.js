// Country of the visitor, from Vercel's edge headers. No cookie, nothing stored.
export default function handler(req, res) {
  const country =
    req.headers["x-vercel-ip-country"] ||
    (req.headers["accept-language"] || "").match(/-([A-Z]{2})\b/)?.[1] ||
    "US";
  res.setHeader("Cache-Control", "public, max-age=3600");
  res.status(200).json({ country: String(country).toUpperCase(), region: String(country).toUpperCase() });
}
