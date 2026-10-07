import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AgriLink",
  description: "AgriLink: fresh produce from local farmers, with pooled transport",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
