import './globals.css';

export default function RootLayout({ children }) {
  return (
    <html lang="en" data-theme="light">
      <body>{children}</body>
    </html>
  );
}
