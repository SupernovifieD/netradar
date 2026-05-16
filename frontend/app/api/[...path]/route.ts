import { NextRequest, NextResponse } from "next/server";
import { frontendConfig } from "@/lib/config";

export const dynamic = "force-dynamic";

const DEFAULT_INTERNAL_API_BASE = frontendConfig.api.defaultInternalBase;
const HOP_BY_HOP_HEADERS = new Set([
  "connection",
  "content-encoding",
  "content-length",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailer",
  "transfer-encoding",
  "upgrade",
]);

type RouteContext = {
  params: Promise<{
    path?: string[];
  }>;
};

function trimTrailingSlash(value: string): string {
  return value.endsWith("/") ? value.slice(0, -1) : value;
}

function getInternalApiBase(): string {
  return trimTrailingSlash(
    process.env.NETRADAR_API_INTERNAL_URL ??
      process.env.NETRADAR_API_URL ??
      DEFAULT_INTERNAL_API_BASE
  );
}

function buildTargetUrl(request: NextRequest, pathSegments: string[]): string {
  const target = new URL(`${getInternalApiBase()}/${pathSegments.join("/")}`);
  target.search = request.nextUrl.search;
  return target.toString();
}

function buildRequestHeaders(request: NextRequest): Headers {
  const headers = new Headers(request.headers);
  headers.delete("host");

  for (const header of HOP_BY_HOP_HEADERS) {
    headers.delete(header);
  }

  return headers;
}

function buildResponseHeaders(response: Response): Headers {
  const headers = new Headers(response.headers);

  for (const header of HOP_BY_HOP_HEADERS) {
    headers.delete(header);
  }

  return headers;
}

async function proxyRequest(request: NextRequest, context: RouteContext): Promise<NextResponse> {
  const { path = [] } = await context.params;
  const method = request.method.toUpperCase();
  const hasBody = method !== "GET" && method !== "HEAD";

  const response = await fetch(buildTargetUrl(request, path), {
    method,
    headers: buildRequestHeaders(request),
    body: hasBody ? await request.arrayBuffer() : undefined,
    cache: "no-store",
  });

  return new NextResponse(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: buildResponseHeaders(response),
  });
}

export const GET = proxyRequest;
export const HEAD = proxyRequest;
export const POST = proxyRequest;
export const PUT = proxyRequest;
export const PATCH = proxyRequest;
export const DELETE = proxyRequest;
export const OPTIONS = proxyRequest;
