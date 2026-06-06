export async function GET() {
  try {
    const res = await fetch("https://status.anthropic.com/api/v2/status.json", {
      cache: "no-store",
    });
    const data = await res.json();
    const indicator: string = data?.status?.indicator ?? "none";
    const description: string = data?.status?.description ?? "Unknown";
    const isDown = indicator !== "none";
    return Response.json({ isDown, indicator, description });
  } catch {
    return Response.json({ isDown: true, indicator: "unknown", description: "Status unreachable" });
  }
}
