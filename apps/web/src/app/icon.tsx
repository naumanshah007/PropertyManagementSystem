import { ImageResponse } from "next/og";

// Auto-wired favicon for every route (Next App Router convention).
export const size = { width: 32, height: 32 };
export const contentType = "image/png";

export default function Icon() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          borderRadius: 8,
          background: "linear-gradient(135deg, #22d3ee 0%, #8b5cf6 100%)",
          color: "#040814",
          fontSize: 22,
          fontWeight: 800,
          fontFamily: "system-ui, sans-serif",
        }}
      >
        T
      </div>
    ),
    { ...size },
  );
}
