/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./app/**/*.{js,ts,jsx,tsx,mdx}",
        "./components/**/*.{js,ts,jsx,tsx,mdx}",
    ],
    theme: {
        extend: {
            colors: {
                actuary: {
                    dark: "#0f172a",
                    primary: "#10b981",
                    secondary: "#6366f1",
                    risk: "#f43f5e"
                }
            }
        },
    },
    plugins: [],
}
