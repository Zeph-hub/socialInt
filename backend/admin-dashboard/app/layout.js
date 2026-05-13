import "./globals.css";

export const metadata = {
  title: "Social Intelligence Platform Admin",
  description: "Admin dashboard for the Social Media Data Pipeline",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
