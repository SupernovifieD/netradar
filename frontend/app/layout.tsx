import "./globals.css";

export const metadata = {
  title: "NetRadar",
  description: "Availability and performance dashboard for internet services",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" dir="ltr">
      <body>
        <div className="page-wrapper">
          {children}
        </div>
      </body>
    </html>
  );
}
