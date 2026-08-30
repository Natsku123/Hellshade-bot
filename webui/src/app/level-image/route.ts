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

export async function GET(request: Request) {
  const arialMt = await fetch(
    new URL("../../../node_modules/@fontsource/arimo/files/arimo-latin-400-normal.woff", import.meta.url),
  ).then((response) => response.arrayBuffer());
  const { searchParams } = new URL(request.url);
  const name = searchParams.get("name") ?? "[NAME]";
  const currentExp = parseInteger(searchParams.get("current_exp"), 0);
  const neededExp = parseInteger(searchParams.get("needed_exp"), 1000);
  const level = parseInteger(searchParams.get("level"), 0);
  const icon = searchParams.get("icon");
  const progress = neededExp === 0 ? 0 : Math.min(currentExp / neededExp, 1);
  const percentage = `${(progress * 100).toFixed(2)}%`;
  const markerCenter = 15 + progress * 550;

  return new ImageResponse(
    createElement(
      "div",
      {
        style: {
          backgroundColor: "white",
          color: "black",
          display: "flex",
          fontFamily: "ArialMT, Arial, sans-serif",
          height: "100%",
          position: "relative",
          width: "100%",
        },
      },
      createElement(
        "div",
        {
          style: {
            display: "flex",
            fontSize: 34,
            left: 130,
            lineHeight: 1,
            position: "absolute",
            top: 58,
          },
        },
        icon
          ? createElement("img", {
              height: 100,
              src: icon,
              style: { left: -110, objectFit: "cover", position: "absolute", top: -38 },
              width: 100,
            })
          : null,
        createElement("span", null, name),
      ),
      createElement(
        "div",
        { style: { fontSize: 34, left: 20, lineHeight: 1, position: "absolute", top: 153 } },
        `Level ${level}`,
      ),
      createElement(
        "div",
        {
          style: {
            backgroundColor: "rgb(242, 153, 74)",
            borderRadius: 9,
            display: "flex",
            height: 39,
            left: 17,
            overflow: "hidden",
            position: "absolute",
            top: 211,
            width: 554,
          },
        },
        createElement("div", {
          style: { backgroundColor: "#FFE698", height: 37, margin: 1, width: progress * 552 },
        }),
      ),
      createElement(
        "div",
        {
          style: {
            fontSize: 14,
            lineHeight: 1,
            position: "absolute",
            right: 18,
            top: 189,
          },
        },
        `Experience: ${currentExp} / ${neededExp}`,
      ),
      createElement(
        "div",
        {
          style: {
            fontSize: 24,
            left: markerCenter,
            lineHeight: 1,
            position: "absolute",
            top: 277,
            transform: "translateX(-50%)",
          },
        },
        percentage,
      ),
      createElement(
        "div",
        {
          style: {
            fontSize: 24,
            left: markerCenter + 4,
            lineHeight: 1,
            position: "absolute",
            top: 251,
            transform: "translateX(-50%)",
          },
        },
        "↑",
      ),
      createElement(
        "div",
        {
          style: {
            bottom: 17,
            color: "gray",
            fontSize: 14,
            left: 20,
            lineHeight: 1,
            position: "absolute",
          },
        },
        new Date().toISOString().slice(0, 10),
      ),
    ),
    {
      ...IMAGE_SIZE,
      fonts: [{ data: await arialMt, name: "ArialMT", style: "normal", weight: 400 }],
    },
  );
}