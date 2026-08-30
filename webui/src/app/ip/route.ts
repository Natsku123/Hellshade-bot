import { ImageResponse } from "next/og";
import { createElement } from "react";

export const runtime = "edge";
export const dynamic = "force-dynamic";

export function GET(request: Request) {
  const clientIp =
    request.headers.get("x-real-ip") ??
    request.headers.get("x-forwarded-for") ??
    "Unknown";

  return new ImageResponse(
    createElement(
      "div",
      {
        style: {
          alignItems: "center",
          backgroundColor: "white",
          color: "black",
          display: "flex",
          fontFamily: "Arial, sans-serif",
          fontSize: 50,
          height: "100%",
          justifyContent: "center",
          width: "100%",
        },
      },
      clientIp,
    ),
    { width: 588, height: 350 },
  );
}