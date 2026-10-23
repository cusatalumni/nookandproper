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
    // A one-click copy button, because selecting long strings in a chat window is painful.
    res.setHeader("Cache-Control", "no-store");
    const tok = String(j.refresh_token).replace(/[<>&]/g, "");
    return res.status(200).send(`<!doctype html><meta charset="utf-8">
<title>Pinterest token</title>
<style>
 body{font:16px/1.6 -apple-system,Segoe UI,Roboto,sans-serif;max-width:760px;margin:60px auto;padding:0 20px;color:#241f1b}
 code{display:block;background:#f5efe7;border:1px solid #e2d6c6;border-radius:10px;padding:16px;word-break:break-all;font-size:14px}
 button{margin:18px 0;background:#a8593c;color:#fff;border:0;border-radius:40px;padding:14px 28px;font-size:16px;font-weight:700;cursor:pointer}
 p{color:#6d635a}
</style>
<h1>Refresh token</h1>
<p>Click copy, then paste it into Vercel as <b>PINTEREST_REFRESH_TOKEN</b>.</p>
<code id="t">${tok}</code>
<button onclick="navigator.clipboard.writeText(document.getElementById('t').textContent).then(()=>{this.textContent='Copied'})">Copy token</button>
<p>Treat this like a password. It lets an app post to your Pinterest account.</p>`);
  } catch (e) {
    return res.status(500).send(`<pre>${String(e)}</pre>`);
  }
}
