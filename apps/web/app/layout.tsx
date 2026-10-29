import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = { title: "Quorvexis | Cloud Defense Command", description: "Unified cloud risk and security operations" };
export default function RootLayout({children}:{children:React.ReactNode}) { return <html lang="en"><body>{children}</body></html>; }
