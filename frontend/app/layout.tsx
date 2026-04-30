import "./globals.css";

export const metadata = {
  title: "نت رادار",
  description: "وضعیت دسترسی به سرویس‌های اینترنتی در ایران",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fa" dir="rtl">
      <body>
        <div className="page-wrapper">
          {children}
        </div>
      </body>
    </html>
  );
}
