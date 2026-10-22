// Pinterest OAuth callback. Exchanges the authorization code for tokens and shows the
// refresh token ONCE to the person driving the flow. Secrets come from Vercel env vars,
// so they never pass through the agent.
export default async function handler(req, res) {
  const code = req.query.code;
  const id = process.env.PINTEREST_APP_ID;
  const secret = process.env.PINTEREST_APP_SECRET;
  const redirect =
    process.env.PINTEREST_REDIRECT_URI ||
    `https://${req.headers.host}/api/pinterest/callback`;

  res.setHeader("Content-Type", "text/html; charset=utf-8");
  if (!code) return res.status(400).send("<pre>missing ?code</pre>");
  if (!id || !secret)
    return res.status(500).send("<pre>PINTEREST_APP_ID / PINTEREST_APP_SECRET env vars are not set</pre>");

  try {
    const r = await fetch("https://api.pinterest.com/v5/oauth/token", {
      method: "POST",
      headers: {
        Authorization: "Basic " + Buffer.from(`${id}:${secret}`).toString("base64"),
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({
        grant_type: "authorization_code",
        code,
        redirect_uri: redirect,
      }),
    });
    const j = await r.json();
    if (!r.ok) return res.status(400).send(`<pre>${JSON.stringify(j, null, 2)}</pre>`);

    // Only the refresh token is shown; the access token is short-lived anyway.
    res.setHeader("Cache-Control", "no-store");
    return res.status(200).send(
      `<pre id="token" data-scope="${(j.scope || "").replace(/"/g, "")}">${j.refresh_token}</pre>`
    );
  } catch (e) {
    return res.status(500).send(`<pre>${String(e)}</pre>`);
  }
}
