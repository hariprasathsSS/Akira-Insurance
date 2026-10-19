import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/features/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        paper: "#FAF8F3",
        surface: {
          DEFAULT: "#FFFEFB",
          muted: "#F3F0E9",
        },
        ink: {
          DEFAULT: "#242A33",
          muted: "#66707A",
        },
        aoi: {
          DEFAULT: "#344A73",
          deep: "#253653",
          wash: "#DCE5F1",
        },
        sakura: {
          DEFAULT: "#E8C7CC",
          soft: "#F6E8E8",
        },
        matcha: {
          DEFAULT: "#B8C8AD",
          soft: "#EAF0E5",
        },
        plum: "#8D7185",
        washi: {
          border: "#E5E0D7",
          borderStrong: "#CFC8BC",
        },
        status: {
          successText: "#2F6548",
          warningText: "#875A1D",
          dangerText: "#9B3C43",
          dangerSoft: "#F8E8E7",
        },
      },
      fontFamily: {
        sans: ["var(--font-sans)", "Inter", "Manrope", "system-ui", "sans-serif"],
        serif: ["var(--font-serif)", "Newsreader", "Noto Serif", "serif"],
      },
      borderRadius: {
        sm: "8px",
        md: "14px",
        lg: "20px",
        xl: "28px",
        pill: "999px",
      },
      boxShadow: {
        soft: "0 8px 28px rgba(44, 54, 70, 0.06)",
        card: "0 3px 12px rgba(44, 54, 70, 0.045), 0 16px 36px rgba(44, 54, 70, 0.035)",
        dialog: "0 24px 72px rgba(32, 42, 57, 0.18)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
