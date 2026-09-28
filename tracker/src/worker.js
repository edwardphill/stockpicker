// Cloudflare Worker: the logged front door for agents.
//
// Serves the same files as the GitHub Pages site (proxied, cached 5 min) and
// records every request, JavaScript or not, to Workers Analytics Engine:
// path, client class (ai-bot / script / browser / other), bot name, user agent,
// country, referer, accept header and status. Links inside text responses are
// rewritten to this host so an agent that starts at /llms.txt stays logged.
//
// Deploy: see ../README.md. No secrets needed.

const AI_BOTS = [
  /GPTBot/i, /ChatGPT-User/i, /OAI-SearchBot/i,
  /ClaudeBot/i, /Claude-User/i, /Claude-SearchBot/i, /anthropic-ai/i,
  /PerplexityBot/i, /Perplexity-User/i,
  /Google-Extended/i, /GoogleOther/i, /Gemini/i,
  /Bytespider/i, /CCBot/i, /Amazonbot/i, /Applebot-Extended/i,
  /cohere-ai/i, /meta-externalagent/i, /meta-externalfetcher/i,
  /DuckAssistBot/i, /YouBot/i, /Diffbot/i, /MistralAI-User/i,
  /Timpibot/i, /omgili/i, /ImagesiftBot/i, /PetalBot/i,
];
const SCRIPT_CLIENTS = [
  /python-requests/i, /python-httpx/i, /python-urllib/i, /aiohttp/i,
  /curl\//i, /Wget/i, /Go-http-client/i, /node-fetch/i, /undici/i, /axios/i,
  /okhttp/i, /Java\//i, /libwww/i, /Scrapy/i, /HTTPie/i, /Deno/i, /Bun\//i,
];
const TEXT_TYPES = /^(text\/|application\/(json|xml|javascript))/i;

function classify(ua) {
  if (!ua) return ["none", ""];
  for (const re of AI_BOTS) { const m = ua.match(re); if (m) return ["ai-bot", m[0]]; }
  for (const re of SCRIPT_CLIENTS) { const m = ua.match(re); if (m) return ["script", m[0].replace(/\/$/, "")]; }
  if (/Mozilla\//.test(ua)) return ["browser", ""];
  return ["other", ua.split(/[\s/]/)[0].slice(0, 40)];
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.pathname === "/_health") return new Response("ok", { headers: { "content-type": "text/plain" } });

    const origin = (env.ORIGIN || "https://edwardphill.github.io/stockpicker").replace(/\/$/, "");
    const path = url.pathname === "/" ? "/index.html" : url.pathname;
    const ua = request.headers.get("user-agent") || "";
    const [cls, bot] = classify(ua);

    const upstream = await fetch(origin + path + url.search, {
      headers: { "user-agent": "stockpicker-agent-tracker/1.0 (+https://github.com/edwardphill/stockpicker)" },
      cf: { cacheTtl: 300, cacheEverything: true },
    });

    if (env.AGENT_VISITS) {
      try {
        env.AGENT_VISITS.writeDataPoint({
          blobs: [
            path,                                              // blob1
            cls,                                               // blob2
            bot,                                               // blob3
            ua.slice(0, 200),                                  // blob4
            request.cf?.country || "",                         // blob5
            (request.headers.get("referer") || "").slice(0, 200), // blob6
            (request.headers.get("accept") || "").slice(0, 100),  // blob7
            request.method,                                    // blob8
          ],
          doubles: [upstream.status],
          indexes: [cls],
        });
      } catch (e) { /* logging must never break serving */ }
    }

    const type = upstream.headers.get("content-type") || "";
    const headers = new Headers(upstream.headers);
    headers.set("x-served-by", "stockpicker-agent-tracker");
    headers.set("access-control-allow-origin", "*");
    headers.delete("content-length");

    if (upstream.ok && TEXT_TYPES.test(type)) {
      // Keep agents on this host: absolute links to the Pages site become links here.
      const body = (await upstream.text()).replaceAll(origin, url.origin);
      return new Response(body, { status: upstream.status, headers });
    }
    return new Response(upstream.body, { status: upstream.status, headers });
  },
};
