import { ImageResponse } from "next/og";
import { createElement } from "react";

export const runtime = "edge";
export const dynamic = "force-dynamic";

const IMAGE_SIZE = { width: 588, height: 350 };

function parseInteger(value: string | null, defaultValue: number): number {
  if (value === null) {
    return defaultValue;
  }

  const parsed = Number(value);
  return Number.isInteger(parsed) ? parsed : defaultValue;
}

export function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const name = searchParams.get("name") ?? "[NAME]";
  const currentExp = parseInteger(searchParams.get("current_exp"), 0);
  const neededExp = parseInteger(searchParams.get("needed_exp"), 1000);
  const level = parseInteger(searchParams.get("level"), 0);
  const icon = searchParams.get("icon");
  const progress = neededExp === 0 ? 0 : Math.min(currentExp / neededExp, 1);
  const percentage = `${(progress * 100).toFixed(2)}%`;

  return new ImageResponse(
    createElement(
      "div",
      {
        style: {
          alignItems: "stretch",
          backgroundColor: "white",
          color: "black",
          display: "flex",
          flexDirection: "column",
          fontFamily: "Arial, sans-serif",
          height: "100%",
          padding: "20px 17px",
          position: "relative",
          width: "100%",
        },
      },
      createElement(
        "div",
        { style: { alignItems: "center", display: "flex", fontSize: 34, height: 100 } },
        icon
          ? createElement("img", {
              height: 100,
              src: icon,
              style: { marginRight: 10, objectFit: "cover" },
              width: 100,
            })
          : null,
        createElement("span", null, name),
      ),
      createElement("div", { style: { fontSize: 34, marginTop: 36 } }, `Level ${level}`),
      createElement(
        "div",
        {
          style: {
            backgroundColor: "#f2994a",
            borderRadius: 9,
            display: "flex",
            height: 39,
            marginTop: 18,
            overflow: "hidden",
            width: "100%",
          },
        },
        createElement("div", {
          style: { backgroundColor: "#ffe698", height: "100%", width: `${progress * 100}%` },
        }),
      ),
      createElement(
        "div",
        { style: { fontSize: 14, marginTop: -64, textAlign: "right" } },
        `Experience: ${currentExp} / ${neededExp}`,
      ),
      createElement(
        "div",
        {
          style: {
            alignItems: "center",
            display: "flex",
            fontSize: 24,
            justifyContent: "center",
            marginTop: 76,
          },
        },
        `↑ ${percentage}`,
      ),
      createElement(
        "div",
        { style: { color: "gray", fontSize: 14, marginTop: "auto" } },
        new Date().toISOString().slice(0, 10),
      ),
    ),
    IMAGE_SIZE,
  );
}