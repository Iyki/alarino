import { buildBackendUrl, filterForwardHeaders } from "@/lib/api-proxy";

const BODY_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);

export const runtime = "nodejs";

async function proxyRequest(request: Request, params: { path: string[] }) {
  if (!params.path.length) {
    return Response.json({ message: "Missing API path." }, { status: 400 });
  }

  const incomingUrl = new URL(request.url);
  const targetUrl = buildBackendUrl(params.path, incomingUrl.search);

  let body: ArrayBuffer | undefined;
  if (BODY_METHODS.has(request.method.toUpperCase())) {
    body = await request.arrayBuffer();
  }

  try {
    const backendResponse = await fetch(targetUrl, {
      method: request.method,
      headers: filterForwardHeaders(request.headers),
      body,
      redirect: "manual"
    });

    return new Response(backendResponse.body, {
      status: backendResponse.status,
      statusText: backendResponse.statusText,
      headers: filterForwardHeaders(backendResponse.headers)
    });
  } catch {
    return Response.json(
      {
        success: false,
        status: 502,
        message: "Backend is unreachable.",
        data: null
      },
      { status: 502 }
    );
  }
}

interface RouteContext {
  params: Promise<{ path: string[] }>;
}

export async function GET(request: Request, context: RouteContext) {
  return proxyRequest(request, await context.params);
}

export async function POST(request: Request, context: RouteContext) {
  return proxyRequest(request, await context.params);
}

export async function PUT(request: Request, context: RouteContext) {
  return proxyRequest(request, await context.params);
}

export async function PATCH(request: Request, context: RouteContext) {
  return proxyRequest(request, await context.params);
}

export async function DELETE(request: Request, context: RouteContext) {
  return proxyRequest(request, await context.params);
}

export async function OPTIONS(request: Request, context: RouteContext) {
  return proxyRequest(request, await context.params);
}

export async function HEAD(request: Request, context: RouteContext) {
  return proxyRequest(request, await context.params);
}
