module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#050711",
        surface: "#0b1020",
        accent: "#20d3ca",
        accentPurple: "#7b2ff7"
      },
      boxShadow: {
        glow: "0 0 30px rgba(32, 211, 202, 0.4)"
      }
    }
  },
  plugins: []
};
