// Shared Pinterest helpers. Underscore-prefixed so Vercel does not expose it as a route.
export function guard(req, res) {
  const key = process.env.NP_API_KEY;
  if (!key) { res.status(500).json({ error: "NP_API_KEY not set" }); return false; }
  if (req.headers["x-api-key"] !== key) { res.status(401).json({ error: "unauthorized" }); return false; }
  return true;
}

export async function accessToken() {
  const id = process.env.PINTEREST_APP_ID;
  const secret = process.env.PINTEREST_APP_SECRET;
  const refresh = process.env.PINTEREST_REFRESH_TOKEN;
  if (!id || !secret || !refresh)
    throw new Error("PINTEREST_APP_ID / PINTEREST_APP_SECRET / PINTEREST_REFRESH_TOKEN not set");

  const r = await fetch("https://api.pinterest.com/v5/oauth/token", {
    method: "POST",
    headers: {
      Authorization: "Basic " + Buffer.from(`${id}:${secret}`).toString("base64"),
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: new URLSearchParams({ grant_type: "refresh_token", refresh_token: refresh }),
  });
  const j = await r.json();
  if (!r.ok || !j.access_token) throw new Error("refresh failed: " + JSON.stringify(j));
  return j.access_token;
}
